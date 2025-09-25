from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime

from src.application.dependencies import get_container
from src.core.entities.conversation import Conversation
from src.core.entities.form import FormCollectionState, FormData
from src.infrastructure.logging.context import get_logger, LoggingContext
from src.api.models import ChatRequest, ChatResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """Send a message to the chatbot using new architecture."""
    
    with LoggingContext(
        correlation_id=None,  # Will be auto-generated
        session_id=request.session_id
    ):
        try:
            logger.info(
                "Processing chat message",
                extra={
                    "session_id": request.session_id,
                    "message_length": len(request.message)
                }
            )
            
            # Get dependencies
            container = get_container()
            chat_use_case = container.get_chat_use_case()
            conversation_repo = container.get_conversation_repo()
            template_repo = container.get_template_repo()
            
            # Get or create conversation
            conversation = await conversation_repo.get_conversation(request.session_id)
            if not conversation:
                conversation = Conversation(id=request.session_id)
                await conversation_repo.save_conversation(conversation)
                
                logger.info(
                    "Created new conversation",
                    extra={"session_id": request.session_id}
                )
            
            # Check if we need to handle form state
            form_state = None
            if hasattr(request, 'form_state') and request.form_state:
                # Reconstruct form state from request
                # This would be implemented based on your form state management
                pass
            
            # Process message
            response = await chat_use_case.process_message(
                conversation_id=request.session_id,
                user_message=request.message,
                form_state=form_state
            )
            
            # Convert to API response format
            api_response = ChatResponse(
                session_id=request.session_id,
                message=response.message,
                intent=response.intent,
                sources=[
                    {
                        "document_type": source.document_type,
                        "document_number": source.document_number,
                        "chunk_title": source.chunk_title,
                        "score": source.score
                    }
                    for source in response.sources
                ],
                form_active=response.form_active,
                current_field=response.current_field,
                collected_data=response.collected_data,
                timestamp=datetime.now()
            )
            
            logger.info(
                "Chat message processed successfully",
                extra={
                    "session_id": request.session_id,
                    "intent": response.intent.value if response.intent else None,
                    "response_length": len(response.message)
                }
            )
            
            return api_response
            
        except Exception as e:
            logger.error(
                "Failed to process chat message",
                extra={
                    "session_id": request.session_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error processing message: {str(e)}"
            )


@router.get("/suggestions")
async def get_chat_suggestions(session_id: str):
    """Get chat suggestions based on context."""
    
    with LoggingContext(session_id=session_id):
        try:
            logger.debug(
                "Getting chat suggestions",
                extra={"session_id": session_id}
            )
            
            # Get conversation to analyze context
            container = get_container()
            conversation_repo = container.get_conversation_repo()
            
            conversation = await conversation_repo.get_conversation(session_id)
            
            # Determine current intent if available
            current_intent = "general"
            if conversation and conversation.messages:
                last_assistant_message = None
                for msg in reversed(conversation.messages):
                    if msg.role.value == "assistant" and msg.intent:
                        last_assistant_message = msg
                        break
                
                if last_assistant_message:
                    current_intent = last_assistant_message.intent.value
            
            # Predefined suggestions based on intent
            suggestions_map = {
                "legal": [
                    "Điều luật nào quy định về vốn điều lệ tối thiểu?",
                    "Thủ tục đăng ký kinh doanh mất bao lâu?",
                    "Các loại hình doanh nghiệp có những gì?",
                    "Quy định về người đại diện pháp luật như thế nào?"
                ],
                "business": [
                    "Tôi muốn tạo hồ sơ đăng ký công ty TNHH",
                    "Cần chuẩn bị những giấy tờ gì để đăng ký?",
                    "Chi phí đăng ký kinh doanh là bao nhiêu?",
                    "Thời gian xử lý hồ sơ đăng ký bao lâu?"
                ],
                "general": [
                    "Quy trình thành lập công ty như thế nào?",
                    "Sự khác biệt giữa công ty TNHH và công ty cổ phần?",
                    "Tôi có thể kinh doanh những ngành nghề nào?",
                    "Cần bao nhiêu vốn để thành lập công ty?"
                ]
            }
            
            suggestions = suggestions_map.get(current_intent, suggestions_map["general"])
            
            return {
                "session_id": session_id,
                "current_intent": current_intent,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(
                "Failed to get chat suggestions",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error getting suggestions: {str(e)}"
            )


@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    message_id: str,
    rating: int,
    comment: str = None
):
    """Submit feedback for a chat response."""
    
    with LoggingContext(session_id=session_id):
        try:
            logger.info(
                "Feedback submitted",
                extra={
                    "session_id": session_id,
                    "message_id": message_id,
                    "rating": rating,
                    "has_comment": bool(comment)
                }
            )
            
            # Record feedback metrics
            container = get_container()
            metrics_service = container.get_metrics_service()
            
            await metrics_service.increment_counter(
                "chat.feedback_submitted",
                tags={"rating": str(rating)}
            )
            
            await metrics_service.record_gauge(
                "chat.feedback_rating",
                rating,
                tags={"session_id": session_id}
            )
            
            # In a real implementation, you'd store this in a database
            feedback_data = {
                "session_id": session_id,
                "message_id": message_id,
                "rating": rating,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            }
            
            return {
                "message": "Feedback submitted successfully",
                "feedback_id": f"fb_{session_id}_{message_id}"
            }
            
        except Exception as e:
            logger.error(
                "Failed to submit feedback",
                extra={
                    "session_id": session_id,
                    "message_id": message_id,
                    "error": str(e)
                },
                exc_info=True
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Error submitting feedback: {str(e)}"
            )