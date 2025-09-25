from fastapi import Depends
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.chatbot import ConversationalRAGChatbot
from src.api.session_manager import SessionManager

# Global instances
_chatbot_instance = None
_session_manager_instance = None


def get_chatbot() -> ConversationalRAGChatbot:
    """
    Dependency to get chatbot instance.
    
    Returns:
        ConversationalRAGChatbot instance
    """
    global _chatbot_instance
    
    if _chatbot_instance is None:
        try:
            _chatbot_instance = ConversationalRAGChatbot()
            print("✅ Chatbot instance created for dependencies")
        except Exception as e:
            print(f"❌ Failed to create chatbot instance: {e}")
            raise e
    
    return _chatbot_instance


def get_session_manager() -> SessionManager:
    """
    Dependency to get session manager instance.
    
    Returns:
        SessionManager instance
    """
    global _session_manager_instance
    
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
        
        # Set default chatbot for session manager
        try:
            chatbot = get_chatbot()
            _session_manager_instance.set_default_chatbot(chatbot)
            print("✅ Session manager instance created for dependencies")
        except Exception as e:
            print(f"❌ Failed to set default chatbot for session manager: {e}")
    
    return _session_manager_instance


def cleanup_dependencies():
    """Clean up dependency instances."""
    global _chatbot_instance, _session_manager_instance
    
    if _session_manager_instance:
        _session_manager_instance.cleanup_all_sessions()
        _session_manager_instance = None
    
    _chatbot_instance = None
    print("🧹 Dependencies cleaned up")