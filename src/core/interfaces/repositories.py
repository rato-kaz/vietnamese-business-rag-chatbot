from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..entities.conversation import Conversation, Message
from ..entities.document import DocumentChunk, RetrievalResult
from ..entities.form import FormTemplate


class ConversationRepository(ABC):
    """Repository interface for conversations."""
    
    @abstractmethod
    async def save_conversation(self, conversation: Conversation) -> None:
        """Save conversation."""
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete conversation."""
        pass
    
    @abstractmethod
    async def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """List conversations."""
        pass


class DocumentRepository(ABC):
    """Repository interface for documents."""
    
    @abstractmethod
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save document chunks."""
        pass
    
    @abstractmethod
    async def search_chunks(
        self, 
        query: str, 
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Search document chunks."""
        pass
    
    @abstractmethod
    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Get chunk by ID."""
        pass
    
    @abstractmethod
    async def delete_all_chunks(self) -> None:
        """Delete all chunks."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        pass


class TemplateRepository(ABC):
    """Repository interface for form templates."""
    
    @abstractmethod
    async def get_template(self, template_name: str) -> Optional[FormTemplate]:
        """Get template by name."""
        pass
    
    @abstractmethod
    async def list_templates(self) -> List[FormTemplate]:
        """List all templates."""
        pass
    
    @abstractmethod
    async def save_template(self, template: FormTemplate) -> None:
        """Save template."""
        pass