from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(str, Enum):
    """Intent types for classification."""
    LEGAL = "legal"
    BUSINESS = "business"
    GENERAL = "general"


@dataclass
class Message:
    """Single message in conversation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole = MessageRole.USER
    content: str = ""
    intent: Optional[IntentType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "intent": self.intent.value if self.intent else None,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SourceDocument:
    """Source document reference."""
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    chunk_title: Optional[str] = None
    score: float = 0.0
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type,
            "document_number": self.document_number,
            "chunk_title": self.chunk_title,
            "score": self.score,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "metadata": self.metadata
        }


@dataclass
class ChatResponse:
    """Response from chatbot."""
    message: str
    intent: Optional[IntentType] = None
    sources: List[SourceDocument] = field(default_factory=list)
    form_active: bool = False
    current_field: Optional[str] = None
    collected_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "intent": self.intent.value if self.intent else None,
            "sources": [source.to_dict() for source in self.sources],
            "form_active": self.form_active,
            "current_field": self.current_field,
            "collected_data": self.collected_data,
            "metadata": self.metadata
        }


@dataclass
class Conversation:
    """Complete conversation session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, message: Message) -> None:
        """Add message to conversation."""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_context(self, max_messages: int = 6) -> str:
        """Get recent conversation context."""
        recent_messages = self.messages[-max_messages:]
        context_parts = []
        
        for msg in recent_messages:
            role = "Người dùng" if msg.role == MessageRole.USER else "Bot"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)
    
    def get_intent_distribution(self) -> Dict[str, int]:
        """Get distribution of intents in conversation."""
        intent_counts = {}
        for msg in self.messages:
            if msg.role == MessageRole.ASSISTANT and msg.intent:
                intent = msg.intent.value
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
        return intent_counts
    
    def clear(self) -> None:
        """Clear all messages."""
        self.messages.clear()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "message_count": self.get_message_count(),
            "intent_distribution": self.get_intent_distribution()
        }