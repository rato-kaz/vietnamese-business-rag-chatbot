from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from ..entities.conversation import Message, ChatResponse, IntentType
from ..entities.document import DocumentChunk, RetrievalResult
from ..entities.form import FormTemplate, FormData, FormCollectionState


class EmbeddingService(ABC):
    """Interface for embedding service."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        pass


class LLMService(ABC):
    """Interface for LLM service."""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response from LLM."""
        pass
    
    @abstractmethod
    async def stream_response(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response from LLM."""
        pass


class IntentClassificationService(ABC):
    """Interface for intent classification."""
    
    @abstractmethod
    async def classify_intent(
        self, 
        text: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify user intent."""
        pass


class RerankingService(ABC):
    """Interface for document reranking."""
    
    @abstractmethod
    async def rerank_documents(
        self, 
        query: str, 
        documents: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Rerank documents based on query relevance."""
        pass


class DocumentProcessingService(ABC):
    """Interface for document processing."""
    
    @abstractmethod
    async def process_document(self, file_path: str) -> List[DocumentChunk]:
        """Process document into chunks."""
        pass
    
    @abstractmethod
    async def process_directory(self, directory_path: str) -> List[DocumentChunk]:
        """Process all documents in directory."""
        pass


class TemplateService(ABC):
    """Interface for template management."""
    
    @abstractmethod
    async def get_template(self, template_name: str) -> Optional[FormTemplate]:
        """Get template by name."""
        pass
    
    @abstractmethod
    async def validate_field_value(
        self, 
        field_name: str, 
        value: str, 
        template: FormTemplate
    ) -> tuple[bool, str]:
        """Validate field value."""
        pass
    
    @abstractmethod
    async def generate_document(
        self, 
        template_name: str, 
        form_data: FormData
    ) -> str:
        """Generate document from template and data."""
        pass


class CacheService(ABC):
    """Interface for caching service."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache."""
        pass


class MetricsService(ABC):
    """Interface for metrics collection."""
    
    @abstractmethod
    async def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter metric."""
        pass
    
    @abstractmethod
    async def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record histogram metric."""
        pass
    
    @abstractmethod
    async def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric."""
        pass