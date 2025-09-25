import uuid
from typing import Dict, Optional
import threading
import time
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.chatbot import ConversationalRAGChatbot


class SessionManager:
    """Manages chat sessions for the FastAPI backend."""
    
    def __init__(self, session_timeout_minutes: int = 60):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Session timeout in minutes
        """
        self.sessions: Dict[str, ConversationalRAGChatbot] = {}
        self.session_timestamps: Dict[str, datetime] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.default_chatbot: Optional[ConversationalRAGChatbot] = None
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def set_default_chatbot(self, chatbot: ConversationalRAGChatbot):
        """Set the default chatbot instance."""
        self.default_chatbot = chatbot
    
    def create_session(self) -> str:
        """
        Create a new chat session.
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        with self.lock:
            # Create new chatbot instance for this session
            if self.default_chatbot:
                # Use the same configuration as default chatbot
                chatbot = ConversationalRAGChatbot()
            else:
                chatbot = ConversationalRAGChatbot()
            
            self.sessions[session_id] = chatbot
            self.session_timestamps[session_id] = datetime.now()
        
        print(f"✅ Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> ConversationalRAGChatbot:
        """
        Get chatbot instance for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Chatbot instance
            
        Raises:
            ValueError: If session not found
        """
        with self.lock:
            if session_id not in self.sessions:
                # Auto-create session if it doesn't exist
                print(f"🔄 Auto-creating session: {session_id}")
                self.create_session_with_id(session_id)
            
            # Update last activity timestamp
            self.session_timestamps[session_id] = datetime.now()
            return self.sessions[session_id]
    
    def create_session_with_id(self, session_id: str) -> str:
        """
        Create a session with specific ID.
        
        Args:
            session_id: Desired session ID
            
        Returns:
            Session ID
        """
        with self.lock:
            if session_id in self.sessions:
                # Session already exists, just update timestamp
                self.session_timestamps[session_id] = datetime.now()
                return session_id
            
            # Create new chatbot instance
            if self.default_chatbot:
                chatbot = ConversationalRAGChatbot()
            else:
                chatbot = ConversationalRAGChatbot()
            
            self.sessions[session_id] = chatbot
            self.session_timestamps[session_id] = datetime.now()
        
        print(f"✅ Created session with ID: {session_id}")
        return session_id
    
    def delete_session(self, session_id: str):
        """
        Delete a chat session.
        
        Args:
            session_id: Session ID to delete
            
        Raises:
            ValueError: If session not found
        """
        with self.lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            del self.sessions[session_id]
            del self.session_timestamps[session_id]
        
        print(f"🗑️ Deleted session: {session_id}")
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if session exists
        """
        with self.lock:
            return session_id in self.sessions
    
    def get_active_session_count(self) -> int:
        """
        Get number of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self.lock:
            return len(self.sessions)
    
    def get_all_session_ids(self) -> list[str]:
        """
        Get all active session IDs.
        
        Returns:
            List of session IDs
        """
        with self.lock:
            return list(self.sessions.keys())
    
    def cleanup_all_sessions(self):
        """Clean up all sessions."""
        with self.lock:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                try:
                    self.delete_session(session_id)
                except ValueError:
                    pass  # Session already deleted
        
        print("🧹 Cleaned up all sessions")
    
    def _cleanup_expired_sessions(self):
        """Background thread to cleanup expired sessions."""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                with self.lock:
                    for session_id, timestamp in self.session_timestamps.items():
                        if current_time - timestamp > self.session_timeout:
                            expired_sessions.append(session_id)
                
                # Delete expired sessions
                for session_id in expired_sessions:
                    try:
                        self.delete_session(session_id)
                        print(f"🕐 Expired session cleaned up: {session_id}")
                    except ValueError:
                        pass  # Session already deleted
                
                # Sleep for 5 minutes before next cleanup
                time.sleep(300)
                
            except Exception as e:
                print(f"❌ Error in session cleanup: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_session_info(self, session_id: str) -> dict:
        """
        Get information about a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session information dictionary
        """
        with self.lock:
            if session_id not in self.sessions:
                raise ValueError(f"Session {session_id} not found")
            
            chatbot = self.sessions[session_id]
            stats = chatbot.get_system_stats()
            
            return {
                "session_id": session_id,
                "created_at": self.session_timestamps[session_id],
                "last_activity": self.session_timestamps[session_id],
                "conversation_length": stats.get("conversation_length", 0),
                "current_intent": stats.get("current_intent"),
                "form_active": stats.get("form_active", False)
            }
    
    def update_session_activity(self, session_id: str):
        """
        Update session activity timestamp.
        
        Args:
            session_id: Session ID
        """
        with self.lock:
            if session_id in self.session_timestamps:
                self.session_timestamps[session_id] = datetime.now()