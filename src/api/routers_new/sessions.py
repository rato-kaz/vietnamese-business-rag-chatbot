from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime

from src.application.dependencies import get_container
from src.core.entities.conversation import Conversation
from src.infrastructure.logging.context import get_logger, LoggingContext
from src.api.models import SessionResponse, SessionInfoResponse, ConversationEntry

logger = get_logger(__name__)
router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionResponse)
async def create_session():
    """Create a new chat session."""
    try:
        # Create new conversation
        conversation = Conversation()
        
        # Save to repository
        container = get_container()
        conversation_repo = container.get_conversation_repo()
        await conversation_repo.save_conversation(conversation)
        
        logger.info(
            "Session created",
            extra={"session_id": conversation.id}
        )
        
        # Record metrics
        metrics_service = container.get_metrics_service()
        await metrics_service.increment_counter("sessions.created")
        
        return SessionResponse(
            session_id=conversation.id,
            created_at=conversation.created_at,
            status="active"
        )
        
    except Exception as e:
        logger.error(
            "Failed to create session",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error creating session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """Get information about a specific session."""
    
    with LoggingContext(session_id=session_id):
        try:
            container = get_container()
            conversation_repo = container.get_conversation_repo()
            
            conversation = await conversation_repo.get_conversation(session_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            
            # Get current intent from last assistant message
            current_intent = None
            form_active = False
            
            for msg in reversed(conversation.messages):
                if msg.role.value == "assistant":
                    current_intent = msg.intent
                    # Check if form is active based on metadata
                    form_active = msg.metadata.get("form_active", False)
                    break
            
            logger.debug(
                "Session info retrieved",
                extra={
                    "session_id": session_id,
                    "message_count": conversation.get_message_count()
                }
            )
            
            return SessionInfoResponse(
                session_id=session_id,
                conversation_length=conversation.get_message_count(),
                current_intent=current_intent,
                form_active=form_active,
                created_at=conversation.created_at,
                last_activity=conversation.updated_at
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to get session info",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error getting session info: {str(e)}"
            )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    
    with LoggingContext(session_id=session_id):
        try:
            container = get_container()
            conversation_repo = container.get_conversation_repo()
            
            # Check if session exists
            conversation = await conversation_repo.get_conversation(session_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            
            # Delete session
            await conversation_repo.delete_conversation(session_id)
            
            logger.info(
                "Session deleted",
                extra={"session_id": session_id}
            )
            
            # Record metrics
            metrics_service = container.get_metrics_service()
            await metrics_service.increment_counter("sessions.deleted")
            
            return {
                "message": f"Session {session_id} deleted successfully",
                "timestamp": datetime.now()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to delete session",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting session: {str(e)}"
            )


@router.post("/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    
    with LoggingContext(session_id=session_id):
        try:
            container = get_container()
            conversation_repo = container.get_conversation_repo()
            
            conversation = await conversation_repo.get_conversation(session_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            
            # Clear conversation
            conversation.clear()
            await conversation_repo.save_conversation(conversation)
            
            logger.info(
                "Session conversation cleared",
                extra={"session_id": session_id}
            )
            
            # Record metrics
            metrics_service = container.get_metrics_service()
            await metrics_service.increment_counter("sessions.cleared")
            
            return {
                "message": f"Session {session_id} conversation cleared",
                "timestamp": datetime.now()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to clear session",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error clearing session: {str(e)}"
            )


@router.get("/{session_id}/history", response_model=List[ConversationEntry])
async def get_conversation_history(
    session_id: str,
    limit: int = 100,
    offset: int = 0
):
    """Get conversation history for a session."""
    
    with LoggingContext(session_id=session_id):
        try:
            container = get_container()
            conversation_repo = container.get_conversation_repo()
            
            conversation = await conversation_repo.get_conversation(session_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            
            # Apply pagination
            messages = conversation.messages[offset:offset + limit]
            
            # Convert to API format
            history = []
            for msg in messages:
                history.append(ConversationEntry(
                    role=msg.role.value,
                    content=msg.content,
                    intent=msg.intent,
                    timestamp=msg.timestamp.isoformat()
                ))
            
            logger.debug(
                "Conversation history retrieved",
                extra={
                    "session_id": session_id,
                    "total_messages": len(conversation.messages),
                    "returned_messages": len(history)
                }
            )
            
            return history
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to get conversation history",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error getting conversation history: {str(e)}"
            )


@router.get("/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get detailed statistics for a session."""
    
    with LoggingContext(session_id=session_id):
        try:
            container = get_container()
            conversation_repo = container.get_conversation_repo()
            
            conversation = await conversation_repo.get_conversation(session_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session {session_id} not found"
                )
            
            # Calculate statistics
            message_count = conversation.get_message_count()
            user_messages = len([msg for msg in conversation.messages if msg.role.value == "user"])
            bot_messages = len([msg for msg in conversation.messages if msg.role.value == "assistant"])
            intent_distribution = conversation.get_intent_distribution()
            
            # Get current state
            current_intent = None
            form_active = False
            
            for msg in reversed(conversation.messages):
                if msg.role.value == "assistant":
                    current_intent = msg.intent.value if msg.intent else None
                    form_active = msg.metadata.get("form_active", False)
                    break
            
            stats = {
                "session_id": session_id,
                "message_count": message_count,
                "user_messages": user_messages,
                "bot_messages": bot_messages,
                "intent_distribution": intent_distribution,
                "current_intent": current_intent,
                "form_active": form_active,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.debug(
                "Session stats retrieved",
                extra={"session_id": session_id, "stats": stats}
            )
            
            return stats
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Failed to get session stats",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error getting session stats: {str(e)}"
            )