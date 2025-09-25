from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    """Intent types for classification."""
    LEGAL = "legal"
    BUSINESS = "business"
    GENERAL = "general"


class FieldType(str, Enum):
    """Form field types."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"


# Request models
class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID")
    context: Optional[str] = Field(None, description="Additional context")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Điều 15 Luật Doanh nghiệp quy định gì?",
                "session_id": "session_123",
                "context": None
            }
        }


class IntentRequest(BaseModel):
    """Request model for intent classification."""
    text: str = Field(..., description="Text to classify")
    context: Optional[str] = Field(None, description="Context for classification")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Tôi muốn tạo hồ sơ đăng ký công ty",
                "context": None
            }
        }


# Response models
class SourceInfo(BaseModel):
    """Information about document sources."""
    document_type: Optional[str] = Field(None, description="Type of document")
    document_number: Optional[str] = Field(None, description="Document number")
    chunk_title: Optional[str] = Field(None, description="Chunk title")
    score: Optional[float] = Field(None, description="Relevance score")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    session_id: str = Field(..., description="Session ID")
    message: str = Field(..., description="Bot response message")
    intent: Optional[IntentType] = Field(None, description="Classified intent")
    sources: List[SourceInfo] = Field(default_factory=list, description="Source documents")
    form_active: bool = Field(False, description="Whether form collection is active")
    current_field: Optional[str] = Field(None, description="Current form field being collected")
    collected_data: Dict[str, Any] = Field(default_factory=dict, description="Collected form data")
    timestamp: datetime = Field(..., description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "session_123",
                "message": "Theo Điều 15 Luật Doanh nghiệp...",
                "intent": "legal",
                "sources": [
                    {
                        "document_type": "Luật",
                        "document_number": "68/2014/QH13",
                        "chunk_title": "Điều 15",
                        "score": 0.95
                    }
                ],
                "form_active": False,
                "current_field": None,
                "collected_data": {},
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class IntentResponse(BaseModel):
    """Response model for intent classification."""
    intent: IntentType = Field(..., description="Classified intent")
    description: str = Field(..., description="Intent description")
    confidence: float = Field(..., description="Classification confidence")


class SessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str = Field(..., description="Created session ID")
    created_at: datetime = Field(..., description="Session creation time")
    status: str = Field(..., description="Session status")


class SessionInfoResponse(BaseModel):
    """Response model for session information."""
    session_id: str = Field(..., description="Session ID")
    conversation_length: int = Field(..., description="Number of messages in conversation")
    current_intent: Optional[IntentType] = Field(None, description="Current intent")
    form_active: bool = Field(False, description="Whether form collection is active")
    created_at: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity time")


class ConversationEntry(BaseModel):
    """Single conversation entry."""
    role: str = Field(..., description="Role (user or assistant)")
    content: str = Field(..., description="Message content")
    intent: Optional[IntentType] = Field(None, description="Message intent")
    timestamp: str = Field(..., description="Message timestamp")


class DocumentStatsResponse(BaseModel):
    """Response model for document statistics."""
    total_documents: int = Field(..., description="Total number of documents")
    embedding_model: str = Field(..., description="Embedding model name")
    reranker_model: str = Field(..., description="Reranker model name")
    collection_name: str = Field(..., description="Vector store collection name")


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""
    active_sessions: int = Field(..., description="Number of active sessions")
    total_documents: int = Field(..., description="Total documents in knowledge base")
    available_templates: int = Field(..., description="Number of available templates")
    system_uptime: str = Field(..., description="System uptime")
    memory_usage: str = Field(..., description="Memory usage")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="System status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")


class FormField(BaseModel):
    """Form field definition."""
    field_name: str = Field(..., description="Field name")
    display_name: str = Field(..., description="Display name")
    field_type: FieldType = Field(..., description="Field type")
    required: bool = Field(False, description="Whether field is required")
    description: str = Field("", description="Field description")


class TemplateInfo(BaseModel):
    """Template information."""
    name: str = Field(..., description="Template name")
    display_name: str = Field(..., description="Display name")
    field_count: int = Field(..., description="Number of fields")
    required_fields: int = Field(..., description="Number of required fields")


# Error models
class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")