import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer

from src.core.interfaces.services import EmbeddingService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class SentenceTransformerEmbeddingService(EmbeddingService):
    """SentenceTransformer implementation of embedding service."""
    
    def __init__(
        self,
        model_name: str = "bkai-foundation-models/vietnamese-bi-encoder",
        device: str = "cuda",
        max_workers: int = 2
    ):
        self.model_name = model_name
        self.device = device
        
        # Initialize model
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(
                "Embedding model loaded",
                extra={
                    "model_name": model_name,
                    "device": device
                }
            )
        except Exception as e:
            logger.error(
                "Failed to load embedding model",
                extra={
                    "model_name": model_name,
                    "device": device,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
        # Thread pool for CPU-intensive operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        try:
            logger.debug(
                "Generating embedding",
                extra={"text_length": len(text)}
            )
            
            def _embed_sync():
                embedding = self.model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
            
            # Run in thread pool to avoid blocking
            embedding = await asyncio.get_event_loop().run_in_executor(
                self.executor, _embed_sync
            )
            
            logger.debug(
                "Embedding generated",
                extra={
                    "text_length": len(text),
                    "embedding_dim": len(embedding)
                }
            )
            
            return embedding
            
        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                extra={
                    "text_length": len(text),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        try:
            logger.info(
                "Generating batch embeddings",
                extra={
                    "batch_size": len(texts),
                    "total_chars": sum(len(text) for text in texts)
                }
            )
            
            def _embed_batch_sync():
                embeddings = self.model.encode(texts, convert_to_tensor=False)
                return [emb.tolist() for emb in embeddings]
            
            # Run in thread pool
            embeddings = await asyncio.get_event_loop().run_in_executor(
                self.executor, _embed_batch_sync
            )
            
            logger.info(
                "Batch embeddings generated",
                extra={
                    "batch_size": len(texts),
                    "embedding_dim": len(embeddings[0]) if embeddings else 0
                }
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "Failed to generate batch embeddings",
                extra={
                    "batch_size": len(texts),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "embedding_dim": self.model.get_sentence_embedding_dimension(),
            "max_seq_length": self.model.max_seq_length
        }