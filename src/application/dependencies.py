from typing import Dict, Any
from functools import lru_cache

from src.application.config import settings
from src.core.interfaces.repositories import ConversationRepository, DocumentRepository, TemplateRepository
from src.core.interfaces.services import (
    EmbeddingService, LLMService, IntentClassificationService, 
    RerankingService, MetricsService, CacheService
)
from src.core.use_cases.chat_use_case import ChatUseCase

from src.infrastructure.repositories.memory_conversation_repository import MemoryConversationRepository
from src.infrastructure.repositories.weaviate_document_repository import WeaviateDocumentRepository
from src.infrastructure.services.embedding_service import SentenceTransformerEmbeddingService
from src.infrastructure.services.llm_service import GeminiLLMService, GroqLLMService
from src.infrastructure.services.intent_classification_service import GroqIntentClassificationService
from src.infrastructure.services.reranking_service import CrossEncoderRerankingService
from src.infrastructure.services.metrics_service import InMemoryMetricsService
from src.infrastructure.services.cache_service import InMemoryCacheService

from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class DependencyContainer:
    """Dependency injection container."""
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize all dependencies."""
        if self._initialized:
            return
        
        logger.info("Initializing dependency container")
        
        try:
            # Initialize services
            await self._initialize_services()
            
            # Initialize repositories
            await self._initialize_repositories()
            
            # Initialize use cases
            await self._initialize_use_cases()
            
            self._initialized = True
            logger.info("Dependency container initialized successfully")
            
        except Exception as e:
            logger.error(
                "Failed to initialize dependency container",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def _initialize_services(self):
        """Initialize service dependencies."""
        logger.info("Initializing services")
        
        # Cache service
        self._instances["cache_service"] = InMemoryCacheService(
            default_ttl=settings.cache_ttl_seconds,
            max_size=settings.cache_max_size
        )
        
        # Metrics service
        self._instances["metrics_service"] = InMemoryMetricsService(
            retention_hours=settings.metrics_retention_hours
        )
        
        # Embedding service
        self._instances["embedding_service"] = SentenceTransformerEmbeddingService(
            model_name=settings.embedding_model,
            device=settings.device,
            max_workers=settings.max_workers
        )
        
        # Reranking service
        self._instances["reranking_service"] = CrossEncoderRerankingService(
            model_name=settings.rerank_model,
            device=settings.device,
            max_workers=settings.max_workers
        )
        
        # Intent classification service
        self._instances["intent_service"] = GroqIntentClassificationService(
            api_key=settings.groq_api_key,
            model_name=settings.intent_model,
            temperature=settings.intent_temperature
        )
        
        # Main LLM service
        self._instances["llm_service"] = GeminiLLMService(
            api_key=settings.gemini_api_key,
            model_name=settings.main_llm_model,
            temperature=settings.main_llm_temperature,
            max_tokens=settings.max_tokens
        )
        
        logger.info("Services initialized")
    
    async def _initialize_repositories(self):
        """Initialize repository dependencies."""
        logger.info("Initializing repositories")
        
        # Conversation repository
        self._instances["conversation_repo"] = MemoryConversationRepository(
            cleanup_interval_minutes=settings.conversation_timeout_minutes
        )
        
        # Document repository
        self._instances["document_repo"] = WeaviateDocumentRepository(
            weaviate_url=settings.weaviate_url,
            collection_name=settings.weaviate_collection_name
        )
        
        # Template repository (placeholder - implement based on your needs)
        # For now, we'll create a simple in-memory one
        from src.infrastructure.repositories.memory_template_repository import MemoryTemplateRepository
        self._instances["template_repo"] = MemoryTemplateRepository(
            templates_dir=settings.templates_dir
        )
        
        logger.info("Repositories initialized")
    
    async def _initialize_use_cases(self):
        """Initialize use case dependencies."""
        logger.info("Initializing use cases")
        
        # Chat use case
        self._instances["chat_use_case"] = ChatUseCase(
            conversation_repo=self._instances["conversation_repo"],
            document_repo=self._instances["document_repo"],
            template_repo=self._instances["template_repo"],
            intent_service=self._instances["intent_service"],
            llm_service=self._instances["llm_service"],
            reranking_service=self._instances["reranking_service"],
            metrics_service=self._instances["metrics_service"],
            cache_service=self._instances["cache_service"]
        )
        
        logger.info("Use cases initialized")
    
    def get(self, name: str) -> Any:
        """Get dependency by name."""
        if not self._initialized:
            raise RuntimeError("Container not initialized. Call initialize() first.")
        
        if name not in self._instances:
            raise KeyError(f"Dependency '{name}' not found")
        
        return self._instances[name]
    
    def get_chat_use_case(self) -> ChatUseCase:
        """Get chat use case."""
        return self.get("chat_use_case")
    
    def get_conversation_repo(self) -> ConversationRepository:
        """Get conversation repository."""
        return self.get("conversation_repo")
    
    def get_document_repo(self) -> DocumentRepository:
        """Get document repository."""
        return self.get("document_repo")
    
    def get_template_repo(self) -> TemplateRepository:
        """Get template repository."""
        return self.get("template_repo")
    
    def get_embedding_service(self) -> EmbeddingService:
        """Get embedding service."""
        return self.get("embedding_service")
    
    def get_llm_service(self) -> LLMService:
        """Get LLM service."""
        return self.get("llm_service")
    
    def get_intent_service(self) -> IntentClassificationService:
        """Get intent classification service."""
        return self.get("intent_service")
    
    def get_reranking_service(self) -> RerankingService:
        """Get reranking service."""
        return self.get("reranking_service")
    
    def get_metrics_service(self) -> MetricsService:
        """Get metrics service."""
        return self.get("metrics_service")
    
    def get_cache_service(self) -> CacheService:
        """Get cache service."""
        return self.get("cache_service")
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up dependency container")
        
        # Add any cleanup logic here
        # For example, closing database connections, stopping background tasks, etc.
        
        self._instances.clear()
        self._initialized = False
        
        logger.info("Dependency container cleaned up")


# Global container instance
_container: DependencyContainer = None


@lru_cache()
def get_container() -> DependencyContainer:
    """Get global dependency container."""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


async def initialize_dependencies():
    """Initialize global dependencies."""
    container = get_container()
    await container.initialize()


async def cleanup_dependencies():
    """Cleanup global dependencies."""
    container = get_container()
    await container.cleanup()