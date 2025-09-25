from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import yaml
import os
import sys
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Add parent directory to path to import chatbot modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.chatbot import ConversationalRAGChatbot
from src.api.models import *
from src.api.session_manager import SessionManager
from src.api.dependencies import get_chatbot, get_session_manager
from src.api.middleware import logging_middleware, rate_limiting_middleware
from src.api.routers import chat, documents, sessions, system, templates

# Initialize FastAPI app
app = FastAPI(
    title="Vietnamese Business Registration RAG Chatbot API",
    description="API for RAG chatbot specialized in Vietnamese business registration consulting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(logging_middleware)
app.middleware("http")(rate_limiting_middleware)

# Include routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(sessions.router)
app.include_router(system.router)
app.include_router(templates.router)

# Global variables
session_manager = SessionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    print("🚀 Starting Vietnamese Business Registration RAG Chatbot API...")
    
    # Initialize chatbot
    try:
        chatbot = ConversationalRAGChatbot()
        session_manager.set_default_chatbot(chatbot)
        print("✅ Chatbot initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        raise e
    
    print("🎉 API server started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 Shutting down API server...")
    session_manager.cleanup_all_sessions()

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )

# Legacy chat endpoints (keep for backward compatibility)
@app.post("/chat/message", response_model=ChatResponse)
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

@app.post("/chat/stream")
async def stream_message(
    request: ChatRequest,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Stream chatbot response for real-time experience."""
    async def generate_response():
        try:
            chatbot = session_manager.get_session(request.session_id)
            
            # For now, we'll simulate streaming by yielding the complete response
            # In a real implementation, you'd integrate with streaming LLM APIs
            response = chatbot.process_message(request.message)
            
            # Yield the response as server-sent events
            yield f"data: {json.dumps(response)}\n\n"
            
        except Exception as e:
            error_response = {"error": str(e)}
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# Session management endpoints
@app.post("/sessions", response_model=SessionResponse)
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

@app.get("/sessions/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get information about a specific session."""
    try:
        chatbot = session_manager.get_session(session_id)
        stats = chatbot.get_system_stats()
        history = chatbot.get_conversation_history()
        
        return SessionInfoResponse(
            session_id=session_id,
            conversation_length=len(history),
            current_intent=stats.get("current_intent"),
            form_active=stats.get("form_active", False),
            created_at=datetime.now(),  # This should be tracked in session manager
            last_activity=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Delete a chat session."""
    try:
        session_manager.delete_session(session_id)
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@app.post("/sessions/{session_id}/clear")
async def clear_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Clear conversation history for a session."""
    try:
        chatbot = session_manager.get_session(session_id)
        chatbot.clear_conversation()
        return {"message": f"Session {session_id} conversation cleared"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@app.get("/sessions/{session_id}/history", response_model=List[ConversationEntry])
async def get_conversation_history(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """Get conversation history for a session."""
    try:
        chatbot = session_manager.get_session(session_id)
        history = chatbot.get_conversation_history()
        
        return [
            ConversationEntry(
                role=entry["role"],
                content=entry["content"],
                intent=entry.get("intent"),
                timestamp=entry.get("timestamp", "")
            )
            for entry in history
        ]
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

# Intent classification endpoint
@app.post("/classify-intent", response_model=IntentResponse)
async def classify_intent(
    request: IntentRequest,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Classify user intent."""
    try:
        result = chatbot.intent_classifier.classify_with_confidence(
            request.text,
            request.context or ""
        )
        
        return IntentResponse(
            intent=result["intent"],
            description=result["description"],
            confidence=1.0  # Placeholder - implement actual confidence scoring
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying intent: {str(e)}")

# Document management endpoints
@app.post("/documents/load")
async def load_documents(
    background_tasks: BackgroundTasks,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Load documents into the knowledge base."""
    def load_docs():
        try:
            success = chatbot.add_documents_to_knowledge_base("data/documents/core")
            return success
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False
    
    background_tasks.add_task(load_docs)
    return {"message": "Document loading started in background"}

@app.get("/documents/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get document statistics."""
    try:
        stats = chatbot.get_system_stats()
        retriever_stats = stats.get("retriever_stats", {})
        
        return DocumentStatsResponse(
            total_documents=retriever_stats.get("total_documents", 0),
            embedding_model=retriever_stats.get("embedding_model", ""),
            reranker_model=retriever_stats.get("reranker_model", ""),
            collection_name=retriever_stats.get("collection_name", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document stats: {str(e)}")

# System information endpoints
@app.get("/system/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    session_manager: SessionManager = Depends(get_session_manager),
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get system statistics."""
    try:
        chatbot_stats = chatbot.get_system_stats()
        
        return SystemStatsResponse(
            active_sessions=session_manager.get_active_session_count(),
            total_documents=chatbot_stats.get("retriever_stats", {}).get("total_documents", 0),
            available_templates=chatbot_stats.get("available_templates", 0),
            system_uptime="N/A",  # Implement proper uptime tracking
            memory_usage="N/A"    # Implement memory usage tracking
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")

# Template and form endpoints
@app.get("/templates", response_model=List[TemplateInfo])
async def get_templates(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get available form templates."""
    try:
        templates = chatbot.template_parser.get_all_form_fields()
        
        template_list = []
        for template_name, fields in templates.items():
            template_list.append(TemplateInfo(
                name=template_name,
                display_name=template_name.replace(".docx", "").replace("_", " ").title(),
                field_count=len(fields),
                required_fields=len([f for f in fields if f.get("required", False)])
            ))
        
        return template_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")

@app.get("/templates/{template_name}/fields", response_model=List[FormField])
async def get_template_fields(
    template_name: str,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get fields for a specific template."""
    try:
        fields = chatbot.template_parser.get_template_fields(template_name)
        
        return [
            FormField(
                field_name=field["field_name"],
                display_name=field["display_name"],
                field_type=field["field_type"],
                required=field.get("required", False),
                description=field.get("description", "")
            )
            for field in fields
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template fields: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )