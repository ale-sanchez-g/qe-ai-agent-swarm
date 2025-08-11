# filepath: planner/memory_manager.py
"""
Memory management for the MCP Agent Planner
"""

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from langchain.memory import ConversationSummaryBufferMemory, ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
import sqlite3
import threading

class ConversationMemory:
    """Manages conversation memory for chat sessions with intelligent context management"""
    
    def __init__(self, session_id: str, max_token_limit: int = 4000):
        self.session_id = session_id
        self.max_token_limit = max_token_limit
        
        # Initialize LangChain memory
        self.llm = ChatAnthropic(model="claude-3-sonnet-20240229")
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=max_token_limit,
            return_messages=True,
            moving_summary_buffer="The conversation history has been summarized to preserve key context."
        )
        
        # Load existing conversation if exists
        self._load_conversation()
    
    def add_user_message(self, message: str):
        """Add a user message to memory"""
        self.memory.chat_memory.add_user_message(message)
        self._save_conversation()
        print(f"[DEBUG] Added user message. Total messages: {len(self.memory.chat_memory.messages)}")
    
    def add_ai_message(self, message: str):
        """Add an AI response to memory"""
        self.memory.chat_memory.add_ai_message(message)
        self._save_conversation()
        print(f"[DEBUG] Added AI message. Total messages: {len(self.memory.chat_memory.messages)}")
        
        # Log if summary buffer is being used
        if hasattr(self.memory, 'moving_summary_buffer') and self.memory.moving_summary_buffer:
            print(f"[DEBUG] Summary buffer active: {len(self.memory.moving_summary_buffer)} chars")
    
    def get_conversation_context(self) -> str:
        """Get the current conversation context for the LLM using the buffer"""
        # Use the summary buffer which automatically manages long conversations
        if hasattr(self.memory, 'buffer') and self.memory.buffer:
            return self.memory.buffer
        
        # Fallback to recent messages if buffer is empty
        recent_messages = self.get_recent_messages_smart(15)
        context_messages = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        return context_messages
    
    def get_recent_messages(self, count: int = 10) -> List[BaseMessage]:
        """Get recent messages from the conversation (legacy method)"""
        messages = self.memory.chat_memory.messages
        return messages[-count:] if len(messages) > count else messages
    
    def get_recent_messages_smart(self, count: int = 15) -> List[BaseMessage]:
        """Get recent messages from the conversation with intelligent windowing"""
        messages = self.memory.chat_memory.messages
        
        # If we have fewer messages than the window, return all
        if len(messages) <= count:
            return messages
        
        # Always include the first message (for context) and the recent messages
        if len(messages) > count:
            # Include first message + most recent (count-1) messages
            first_message = [messages[0]]
            recent_messages = messages[-(count-1):]
            return first_message + recent_messages
        
        return messages[-count:]
    
    def get_full_conversation_context(self) -> str:
        """Get comprehensive conversation context combining summary and recent messages"""
        # Get the summary buffer if available
        summary = ""
        if hasattr(self.memory, 'moving_summary_buffer') and self.memory.moving_summary_buffer:
            summary = f"Previous conversation summary: {self.memory.moving_summary_buffer}\n\n"
        
        # Get recent messages for immediate context
        recent_messages = self.get_recent_messages_smart(10)
        recent_context = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        
        return f"{summary}Recent conversation:\n{recent_context}"
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.memory.clear()
        self._save_conversation()
    
    def _load_conversation(self):
        """Load conversation from persistent storage"""
        db_path = Path("memory") / f"{self.session_id}.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT message_type, content, timestamp 
                    FROM messages 
                    ORDER BY timestamp ASC
                """)
                
                for msg_type, content, timestamp in cursor.fetchall():
                    if msg_type == "human":
                        self.memory.chat_memory.add_user_message(content)
                    elif msg_type == "ai":
                        self.memory.chat_memory.add_ai_message(content)
                
                conn.close()
            except Exception as e:
                print(f"Error loading conversation: {e}")
    
    def _save_conversation(self):
        """Save conversation to persistent storage"""
        db_path = Path("memory")
        db_path.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(db_path / f"{self.session_id}.db"))
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Clear and re-insert all messages (simple approach)
        cursor.execute("DELETE FROM messages")
        
        for message in self.memory.chat_memory.messages:
            msg_type = "human" if isinstance(message, HumanMessage) else "ai"
            cursor.execute(
                "INSERT INTO messages (message_type, content) VALUES (?, ?)",
                (msg_type, message.content)
            )
        
        conn.commit()
        conn.close()

class SessionManager:
    """Manages multiple conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationMemory] = {}
        self.session_timeouts: Dict[str, datetime] = {}
        self.cleanup_interval = timedelta(hours=24)  # Clean up after 24 hours
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def get_or_create_session(self, session_id: str) -> ConversationMemory:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(session_id)
        
        self.session_timeouts[session_id] = datetime.now() + self.cleanup_interval
        return self.sessions[session_id]
    
    def remove_session(self, session_id: str):
        """Remove a session from memory"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_timeouts:
            del self.session_timeouts[session_id]
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_sessions = [
            sid for sid, timeout in self.session_timeouts.items()
            if now > timeout
        ]
        
        for session_id in expired_sessions:
            self.remove_session(session_id)
    
    def _start_cleanup_thread(self):
        """Start background thread for session cleanup"""
        def cleanup_worker():
            while True:
                self._cleanup_expired_sessions()
                threading.Event().wait(3600)  # Check every hour
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

# Global session manager
session_manager = SessionManager()