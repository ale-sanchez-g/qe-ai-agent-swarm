# filepath: planner/memory_manager.py
"""
Memory management for the MCP Agent Planner
"""

import sqlite3
import threading
from typing import List, Dict
from datetime import datetime, timedelta
from pathlib import Path


class ConversationMemory:
    """Manages conversation memory for chat sessions"""
    
    def __init__(self, session_id: str, max_messages: int = 50):
        self.session_id = session_id
        self.max_messages = max_messages
        self.messages: List[Dict[str, str]] = []
        
        # Load existing conversation if exists
        self._load_conversation()
    
    def add_user_message(self, message: str):
        """Add a user message to memory"""
        self.messages.append({"role": "user", "content": message})
        self._trim_messages()
        self._save_conversation()
    
    def add_ai_message(self, message: str):
        """Add an AI response to memory"""
        self.messages.append({"role": "assistant", "content": message})
        self._trim_messages()
        self._save_conversation()

    def record_turn(self, user_message: str, ai_message: str):
        """Record a full user->assistant turn"""
        self.add_user_message(user_message)
        self.add_ai_message(ai_message)
    
    def get_conversation_context(self) -> str:
        """Get the current conversation as a string"""
        return "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in self.messages
        ])
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, str]]:
        """Get recent messages"""
        return self.messages[-count:] if len(self.messages) > count else self.messages
    
    def clear_memory(self):
        """Clear the conversation memory"""
        self.messages = []
        self._save_conversation()
    
    def _trim_messages(self):
        """Keep only recent N messages"""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def _load_conversation(self):
        """Load conversation from SQLite"""
        db_path = Path("memory") / f"{self.session_id}.db"
        if not db_path.exists():
            return
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content FROM messages ORDER BY timestamp ASC
            """)
            
            self.messages = [
                {"role": role, "content": content}
                for role, content in cursor.fetchall()
            ]
            conn.close()
        except Exception as e:
            print(f"Error loading conversation: {e}")
    
    def _save_conversation(self):
        """Save conversation to SQLite"""
        db_path = Path("memory")
        db_path.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(str(db_path / f"{self.session_id}.db"))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Clear and re-insert
        cursor.execute("DELETE FROM messages")
        for msg in self.messages:
            cursor.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (msg["role"], msg["content"])
            )
        
        conn.commit()
        conn.close()


class SessionManager:
    """Manages multiple conversation sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationMemory] = {}
        self.session_timeouts: Dict[str, datetime] = {}
        self.cleanup_interval = timedelta(hours=24)
        self._start_cleanup_thread()
    
    def get_or_create_session(self, session_id: str) -> ConversationMemory:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(session_id)
        
        self.session_timeouts[session_id] = datetime.now() + self.cleanup_interval
        return self.sessions[session_id]
    
    def remove_session(self, session_id: str):
        """Remove a session"""
        self.sessions.pop(session_id, None)
        self.session_timeouts.pop(session_id, None)
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [sid for sid, timeout in self.session_timeouts.items() if now > timeout]
        for session_id in expired:
            self.remove_session(session_id)
    
    def _start_cleanup_thread(self):
        """Start background cleanup"""
        def cleanup_worker():
            while True:
                self._cleanup_expired_sessions()
                threading.Event().wait(3600)
        
        threading.Thread(target=cleanup_worker, daemon=True).start()


# Global session manager
session_manager = SessionManager()