from typing import List, Dict, Optional
import asyncio
import threading
from datetime import datetime, timedelta

from src.core.interfaces.repositories import ConversationRepository
from src.core.entities.conversation import Conversation
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class MemoryConversationRepository(ConversationRepository):
    """In-memory implementation of conversation repository."""
    
    def __init__(self, cleanup_interval_minutes: int = 60):
        self._conversations: Dict[str, Conversation] = {}
        self._lock = threading.RLock()
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        
        # Start cleanup task
        self._start_cleanup_task()
    
    async def save_conversation(self, conversation: Conversation) -> None:
        """Save conversation to memory."""
        try:
            with self._lock:
                self._conversations[conversation.id] = conversation
                
            logger.debug(
                "Conversation saved",
                extra={
                    "conversation_id": conversation.id,
                    "message_count": conversation.get_message_count()
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to save conversation",
                extra={
                    "conversation_id": conversation.id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation from memory."""
        try:
            with self._lock:
                conversation = self._conversations.get(conversation_id)
                
            if conversation:
                logger.debug(
                    "Conversation retrieved",
                    extra={
                        "conversation_id": conversation_id,
                        "message_count": conversation.get_message_count()
                    }
                )
            else:
                logger.debug(
                    "Conversation not found",
                    extra={"conversation_id": conversation_id}
                )
                
            return conversation
            
        except Exception as e:
            logger.error(
                "Failed to get conversation",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete conversation from memory."""
        try:
            with self._lock:
                if conversation_id in self._conversations:
                    del self._conversations[conversation_id]
                    logger.info(
                        "Conversation deleted",
                        extra={"conversation_id": conversation_id}
                    )
                else:
                    logger.warning(
                        "Conversation not found for deletion",
                        extra={"conversation_id": conversation_id}
                    )
                    
        except Exception as e:
            logger.error(
                "Failed to delete conversation",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """List conversations with pagination."""
        try:
            with self._lock:
                conversations = list(self._conversations.values())
            
            # Sort by updated_at descending
            conversations.sort(key=lambda c: c.updated_at, reverse=True)
            
            # Apply pagination
            paginated = conversations[offset:offset + limit]
            
            logger.debug(
                "Conversations listed",
                extra={
                    "total_count": len(conversations),
                    "limit": limit,
                    "offset": offset,
                    "returned_count": len(paginated)
                }
            )
            
            return paginated
            
        except Exception as e:
            logger.error(
                "Failed to list conversations",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """Get repository statistics."""
        with self._lock:
            total_conversations = len(self._conversations)
            total_messages = sum(
                conv.get_message_count() 
                for conv in self._conversations.values()
            )
            
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages
        }
    
    def clear_all(self) -> None:
        """Clear all conversations."""
        with self._lock:
            count = len(self._conversations)
            self._conversations.clear()
            
        logger.info(
            "All conversations cleared",
            extra={"cleared_count": count}
        )
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        def cleanup_expired():
            while True:
                try:
                    self._cleanup_expired_conversations()
                    # Sleep for cleanup interval
                    import time
                    time.sleep(self.cleanup_interval.total_seconds())
                except Exception as e:
                    logger.error(
                        "Error in cleanup task",
                        extra={"error": str(e)},
                        exc_info=True
                    )
                    # Sleep for 1 minute before retrying
                    import time
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_expired, daemon=True)
        cleanup_thread.start()
        logger.info("Cleanup task started")
    
    def _cleanup_expired_conversations(self) -> None:
        """Clean up expired conversations."""
        cutoff_time = datetime.now() - self.cleanup_interval
        expired_ids = []
        
        with self._lock:
            for conv_id, conversation in self._conversations.items():
                if conversation.updated_at < cutoff_time:
                    expired_ids.append(conv_id)
            
            # Remove expired conversations
            for conv_id in expired_ids:
                del self._conversations[conv_id]
        
        if expired_ids:
            logger.info(
                "Expired conversations cleaned up",
                extra={
                    "expired_count": len(expired_ids),
                    "cutoff_time": cutoff_time.isoformat()
                }
            )