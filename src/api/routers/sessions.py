from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

from ..models import *
from ..dependencies import get_session_manager
from ..session_manager import SessionManager

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse)
async def create_session(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Create a new chat session."""
    session_id = session_manager.create_session()
    return SessionResponse(
        session_id=session_id,
        created_at=datetime.now(),
        status="active"
    )


@router.get("/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get information about a specific session."""
    try:
        session_info = session_manager.get_session_info(session_id)
        
        return SessionInfoResponse(
            session_id=session_id,
            conversation_length=session_info.get("conversation_length", 0),
            current_intent=session_info.get("current_intent"),
            form_active=session_info.get("form_active", False),
            created_at=session_info.get("created_at", datetime.now()),
            last_activity=session_info.get("last_activity", datetime.now())
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session info: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Delete a chat session."""
    try:
        session_manager.delete_session(session_id)
        return {
            "message": f"Session {session_id} deleted successfully",
            "timestamp": datetime.now()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@router.post("/{session_id}/clear")
async def clear_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Clear conversation history for a session."""
    try:
        chatbot = session_manager.get_session(session_id)
        chatbot.clear_conversation()
        return {
            "message": f"Session {session_id} conversation cleared",
            "timestamp": datetime.now()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing session: {str(e)}")


@router.get("/{session_id}/history", response_model=List[ConversationEntry])
async def get_conversation_history(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get conversation history for a session."""
    try:
        chatbot = session_manager.get_session(session_id)
        history = chatbot.get_conversation_history()
        
        # Apply pagination
        paginated_history = history[offset:offset + limit]
        
        return [
            ConversationEntry(
                role=entry["role"],
                content=entry["content"],
                intent=entry.get("intent"),
                timestamp=entry.get("timestamp", "")
            )
            for entry in paginated_history
        ]
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")


@router.get("", response_model=List[str])
async def list_sessions(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """List all active sessions."""
    try:
        session_ids = session_manager.get_all_session_ids()
        return session_ids
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")


@router.get("/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get detailed statistics for a session."""
    try:
        chatbot = session_manager.get_session(session_id)
        stats = chatbot.get_system_stats()
        history = chatbot.get_conversation_history()
        
        # Calculate additional stats
        message_count = len(history)
        user_messages = len([msg for msg in history if msg["role"] == "user"])
        bot_messages = len([msg for msg in history if msg["role"] == "assistant"])
        
        # Intent distribution
        intent_counts = {}
        for msg in history:
            if msg["role"] == "assistant" and msg.get("intent"):
                intent = msg["intent"]
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        return {
            "session_id": session_id,
            "message_count": message_count,
            "user_messages": user_messages,
            "bot_messages": bot_messages,
            "intent_distribution": intent_counts,
            "current_intent": stats.get("current_intent"),
            "form_active": stats.get("form_active", False),
            "timestamp": datetime.now()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting session stats: {str(e)}")


@router.post("/{session_id}/reset")
async def reset_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Reset a session (clear conversation and form state)."""
    try:
        chatbot = session_manager.get_session(session_id)
        chatbot.clear_conversation()
        
        # Reset form collection state
        chatbot.form_collection_state = {
            "active": False,
            "current_field_index": 0,
            "collected_data": {},
            "questions": chatbot.template_parser.generate_form_collection_questions()
        }
        
        return {
            "message": f"Session {session_id} reset successfully",
            "timestamp": datetime.now()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")