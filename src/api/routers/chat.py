from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import json
import asyncio
from datetime import datetime

from ..models import *
from ..dependencies import get_session_manager
from ..session_manager import SessionManager

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Send a message to the chatbot."""
    try:
        # Get or create session
        chatbot = session_manager.get_session(request.session_id)
        
        # Process message
        response = chatbot.process_message(request.message)
        
        return ChatResponse(
            session_id=request.session_id,
            message=response["message"],
            intent=response.get("intent"),
            sources=response.get("sources", []),
            form_active=response.get("form_active", False),
            current_field=response.get("current_field"),
            collected_data=response.get("collected_data", {}),
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Stream chatbot response for real-time experience."""
    
    async def generate_response():
        try:
            chatbot = session_manager.get_session(request.session_id)
            
            # Simulate streaming by yielding chunks
            yield f"data: {json.dumps({'status': 'processing', 'session_id': request.session_id})}\n\n"
            
            # Process message (in real implementation, this would be streaming)
            response = chatbot.process_message(request.message)
            
            # Yield the complete response
            yield f"data: {json.dumps(response)}\n\n"
            yield f"data: {json.dumps({'status': 'complete'})}\n\n"
            
        except Exception as e:
            error_response = {
                "status": "error",
                "error": str(e),
                "session_id": request.session_id
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post("/batch", response_model=List[ChatResponse])
async def batch_messages(
    requests: List[ChatRequest],
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Process multiple messages in batch."""
    responses = []
    
    for request in requests:
        try:
            chatbot = session_manager.get_session(request.session_id)
            response = chatbot.process_message(request.message)
            
            chat_response = ChatResponse(
                session_id=request.session_id,
                message=response["message"],
                intent=response.get("intent"),
                sources=response.get("sources", []),
                form_active=response.get("form_active", False),
                current_field=response.get("current_field"),
                collected_data=response.get("collected_data", {}),
                timestamp=datetime.now()
            )
            responses.append(chat_response)
            
        except Exception as e:
            # Create error response
            error_response = ChatResponse(
                session_id=request.session_id,
                message=f"Error: {str(e)}",
                intent=None,
                sources=[],
                form_active=False,
                current_field=None,
                collected_data={},
                timestamp=datetime.now()
            )
            responses.append(error_response)
    
    return responses


@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    message_id: str,
    rating: int,
    comment: str = None
):
    """Submit feedback for a chat response."""
    # In a real implementation, you'd store this in a database
    feedback_data = {
        "session_id": session_id,
        "message_id": message_id,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now().isoformat()
    }
    
    # Log feedback (in production, save to database)
    print(f"Feedback received: {feedback_data}")
    
    return {"message": "Feedback submitted successfully", "feedback_id": f"fb_{session_id}_{message_id}"}


@router.get("/suggestions")
async def get_chat_suggestions(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get suggested questions based on current context."""
    try:
        chatbot = session_manager.get_session(session_id)
        stats = chatbot.get_system_stats()
        current_intent = stats.get("current_intent")
        
        # Predefined suggestions based on intent
        suggestions = {
            "legal": [
                "Điều luật nào quy định về vốn điều lệ tối thiểu?",
                "Thủ tục đăng ký kinh doanh mất bao lâu?",
                "Các loại hình doanh nghiệp có những gì?"
            ],
            "business": [
                "Tôi muốn tạo hồ sơ đăng ký công ty",
                "Cần chuẩn bị những giấy tờ gì?",
                "Chi phí đăng ký kinh doanh là bao nhiêu?"
            ],
            "general": [
                "Quy trình thành lập công ty như thế nào?",
                "Sự khác biệt giữa công ty TNHH và công ty cổ phần?",
                "Tôi có thể kinh doanh những ngành nghề nào?"
            ]
        }
        
        intent_suggestions = suggestions.get(current_intent, suggestions["general"])
        
        return {
            "session_id": session_id,
            "current_intent": current_intent,
            "suggestions": intent_suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")


@router.post("/export")
async def export_conversation(
    session_id: str,
    format: str = "json",
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Export conversation history."""
    try:
        chatbot = session_manager.get_session(session_id)
        history = chatbot.get_conversation_history()
        
        if format == "json":
            return {
                "session_id": session_id,
                "exported_at": datetime.now().isoformat(),
                "conversation": history
            }
        elif format == "text":
            # Convert to text format
            text_content = f"Conversation Export - Session: {session_id}\n"
            text_content += f"Exported at: {datetime.now().isoformat()}\n"
            text_content += "=" * 50 + "\n\n"
            
            for entry in history:
                role = "User" if entry["role"] == "user" else "Bot"
                text_content += f"{role}: {entry['content']}\n"
                if entry.get("timestamp"):
                    text_content += f"Time: {entry['timestamp']}\n"
                text_content += "\n"
            
            return {"session_id": session_id, "content": text_content, "format": "text"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'text'")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting conversation: {str(e)}")