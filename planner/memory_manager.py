# filepath: planner/memory_manager.py
"""
Memory management for the MCP Agent Planner
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import sqlite3
import threading

# Configure structured logging for Dynatrace OTLP
logger = logging.getLogger("mcp_agent.memory_manager")
logger.setLevel(logging.INFO)

class ConversationMemory:
    """Manages conversation memory for chat sessions with intelligent context management"""
    
    def __init__(self, session_id: str, max_token_limit: int = 4000):
        self.session_id = session_id
        self.max_token_limit = max_token_limit
        self.messages: List[BaseMessage] = []
        self.summary_buffer: str = ""
        self.user_id: Optional[str] = None
        self.request_id: Optional[str] = None
        
        # Load existing conversation if exists
        self._load_conversation()
    
    def set_user_context(self, user_id: str, request_id: str):
        """Set user ID and request ID for this session"""
        self.user_id = user_id
        self.request_id = request_id
    
    def add_user_message(self, message: str, user_id: Optional[str] = None, request_id: Optional[str] = None):
        """Add a user message to memory with structured logging"""
        self.messages.append(HumanMessage(content=message))
        
        # Use provided values or session defaults
        uid = user_id or self.user_id or "anonymous"
        rid = request_id or self.request_id or str(uuid.uuid4())
        
        # Log with structured data for Dynatrace OTLP ingestion
        logger.info("User prompt", extra={
            "data": {
                "type": "user_prompt",
                "content": message[:500],  # Truncate for logging
                "content_length": len(message),
                "session_id": self.session_id,
                "user_id": uid,
                "request_id": rid,
                "message_count": len(self.messages),
                "timestamp": datetime.now().isoformat()
            }
        })
        
        self._save_conversation()
        print(f"[DEBUG] Added user message. Total messages: {len(self.messages)}")
    
    def add_ai_message(self, message: str, request_id: Optional[str] = None):
        """Add an AI response to memory with structured logging"""
        self.messages.append(AIMessage(content=message))
        
        # Use provided value or session default
        rid = request_id or self.request_id or str(uuid.uuid4())
        
        # Log with structured data for Dynatrace OTLP ingestion
        logger.info("AI response", extra={
            "data": {
                "type": "ai_response",
                "content": message[:500],  # Truncate for logging
                "content_length": len(message),
                "session_id": self.session_id,
                "user_id": self.user_id or "anonymous",
                "request_id": rid,
                "message_count": len(self.messages),
                "timestamp": datetime.now().isoformat()
            }
        })
        
        self._save_conversation()
        print(f"[DEBUG] Added AI message. Total messages: {len(self.messages)}")
        
        # Log if we have a lot of messages
        if len(self.messages) > 20:
            print(f"[DEBUG] Large conversation: {len(self.messages)} messages")

    def record_turn(self, user_message: str, ai_message: str, user_id: Optional[str] = None, request_id: Optional[str] = None):
        """Record a full user->assistant turn with context logging."""
        uid = user_id or self.user_id or "anonymous"
        rid = request_id or self.request_id or str(uuid.uuid4())
        
        try:
            # Log session context for this turn
            logger.info("Conversation turn", extra={
                "data": {
                    "type": "conversation_turn",
                    "session_id": self.session_id,
                    "user_id": uid,
                    "request_id": rid,
                    "conversation_turn": len(self.messages) // 2 + 1,
                    "timestamp": datetime.now().isoformat()
                }
            })
            
            self.add_user_message(user_message, user_id=uid, request_id=rid)
            self.add_ai_message(ai_message, request_id=rid)
            print(f"[DEBUG] Recorded turn. Total messages: {len(self.messages)}")
        except Exception as e:
            logger.error("record_turn failed", extra={
                "data": {
                    "type": "error",
                    "session_id": self.session_id,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            })
            print(f"[ERROR] record_turn failed: {e}")
    
    def get_conversation_context(self) -> str:
        """Get the current conversation context for the LLM"""
        # Get recent messages (last 15)
        recent_messages = self.get_recent_messages_smart(15)
        context_messages = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        return context_messages
    
    def get_recent_messages(self, count: int = 10) -> List[BaseMessage]:
        """Get recent messages from the conversation (legacy method)"""
        return self.messages[-count:] if len(self.messages) > count else self.messages
    
    def get_recent_messages_smart(self, count: int = 15) -> List[BaseMessage]:
        """Get recent messages from the conversation with intelligent windowing"""
        # If we have fewer messages than the window, return all
        if len(self.messages) <= count:
            return self.messages
        
        # Always include the first message (for context) and the recent messages
        if len(self.messages) > count:
            # Include first message + most recent (count-1) messages
            first_message = [self.messages[0]]
            recent_messages = self.messages[-(count-1):]
            return first_message + recent_messages
        
        return self.messages[-count:]
    
    def get_full_conversation_context(self) -> str:
        """Get comprehensive conversation context"""
        context = ""
        if self.summary_buffer:
            context = f"Previous conversation summary: {self.summary_buffer}\n\n"
        
        # Get recent messages for immediate context
        recent_messages = self.get_recent_messages_smart(10)
        recent_context = "\n".join([
            f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        
        return f"{context}Recent conversation:\n{recent_context}"
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.messages = []
        self.summary_buffer = ""
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
                        self.messages.append(HumanMessage(content=content))
                    elif msg_type == "ai":
                        self.messages.append(AIMessage(content=content))
                
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
        
        for message in self.messages:
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
        self.session_users: Dict[str, str] = {}  # Map session_id -> user_id
        self.cleanup_interval = timedelta(hours=24)  # Clean up after 24 hours
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> ConversationMemory:
        """Get existing session or create new one with user tracking"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(session_id)
        
        # Track user_id if provided
        if user_id:
            self.session_users[session_id] = user_id
            self.sessions[session_id].set_user_context(user_id, str(uuid.uuid4()))
        
        self.session_timeouts[session_id] = datetime.now() + self.cleanup_interval
        
        # Log session creation/access
        logger.info("Session access", extra={
            "data": {
                "type": "session_access",
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "action": "get_or_create",
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return self.sessions[session_id]
    
    def remove_session(self, session_id: str):
        """Remove a session from memory"""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_timeouts:
            del self.session_timeouts[session_id]
        if session_id in self.session_users:
            del self.session_users[session_id]
    
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