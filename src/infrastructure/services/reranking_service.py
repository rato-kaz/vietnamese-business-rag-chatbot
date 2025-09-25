import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import CrossEncoder

from src.core.interfaces.services import RerankingService
from src.core.entities.document import RetrievalResult
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class CrossEncoderRerankingService(RerankingService):
    """Cross-encoder implementation of reranking service."""
    
    def __init__(
        self,
        model_name: str = "cross-encoder/multilingual-MiniLM-L-12-v2",
        device: str = "cuda",
        max_workers: int = 2
    ):
        self.model_name = model_name
        self.device = device
        
        # Initialize model
        try:
            self.model = CrossEncoder(model_name, device=device)
            
            logger.info(
                "Reranking model loaded",
                extra={
                    "model_name": model_name,
                    "device": device
                }
            )
        except Exception as e:
            logger.error(
                "Failed to load reranking model",
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
    
    async def rerank_documents(
        self,
        query: str,
        documents: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Rerank documents based on query relevance."""
        try:
            if len(documents) <= 1:
                logger.debug("Only one or no documents to rerank, returning as-is")
                return documents
            
            logger.debug(
                "Reranking documents",
                extra={
                    "query_length": len(query),
                    "document_count": len(documents)
                }
            )
            
            def _rerank_sync():
                # Prepare query-document pairs
                query_doc_pairs = []
                for result in documents:
                    # Create representative text for the document
                    doc_text = result.chunk.content
                    
                    # Add metadata context if available
                    metadata = result.chunk.metadata
                    if metadata.chunk_title:
                        doc_text = f"{metadata.chunk_title}: {doc_text}"
                    
                    query_doc_pairs.append([query, doc_text])
                
                # Get reranking scores
                rerank_scores = self.model.predict(query_doc_pairs)
                return rerank_scores
            
            # Run reranking in thread pool
            rerank_scores = await asyncio.get_event_loop().run_in_executor(
                self.executor, _rerank_sync
            )
            
            # Update documents with rerank scores
            for i, result in enumerate(documents):
                result.rerank_score = float(rerank_scores[i])
            
            # Sort by rerank score (descending)
            reranked_documents = sorted(
                documents,
                key=lambda x: x.rerank_score,
                reverse=True
            )
            
            logger.debug(
                "Documents reranked successfully",
                extra={
                    "query_length": len(query),
                    "document_count": len(documents),
                    "score_range": {
                        "min": min(rerank_scores),
                        "max": max(rerank_scores),
                        "mean": sum(rerank_scores) / len(rerank_scores)
                    }
                }
            )
            
            return reranked_documents
            
        except Exception as e:
            logger.error(
                "Failed to rerank documents",
                extra={
                    "query_length": len(query),
                    "document_count": len(documents),
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Return original documents if reranking fails
            logger.warning("Returning original document order due to reranking failure")
            return documents
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_type": "cross-encoder"
        }