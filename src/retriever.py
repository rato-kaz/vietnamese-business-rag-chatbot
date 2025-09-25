import yaml
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder
from .vector_store import WeaviateVectorStore


class EnhancedRetriever:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize enhanced retriever with reranking."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize vector store
        self.vector_store = WeaviateVectorStore(config_path)
        
        # Initialize reranker
        self.reranker = CrossEncoder(
            self.config['reranking']['model_name'],
            device=self.config['reranking']['device']
        )
        
        self.top_k = self.config['retrieval']['top_k']
        self.rerank_top_k = self.config['retrieval']['rerank_top_k']
        self.similarity_threshold = self.config['retrieval']['similarity_threshold']
    
    def retrieve(self, query: str, filters: Optional[Dict] = None, conversation_context: Optional[str] = None) -> List[Dict]:
        """
        Retrieve relevant documents with reranking.
        
        Args:
            query: User query
            filters: Optional filters for search
            conversation_context: Previous conversation context for better retrieval
            
        Returns:
            List of relevant documents with scores
        """
        # Enhance query with conversation context if available
        enhanced_query = self._enhance_query_with_context(query, conversation_context)
        
        # Initial retrieval
        initial_docs = self.vector_store.search(
            enhanced_query, 
            top_k=self.top_k,
            filters=filters
        )
        
        if not initial_docs:
            return []
        
        # Filter by similarity threshold
        filtered_docs = [
            doc for doc in initial_docs 
            if doc['score'] >= self.similarity_threshold
        ]
        
        if not filtered_docs:
            return []
        
        # Rerank documents
        reranked_docs = self._rerank_documents(enhanced_query, filtered_docs)
        
        # Return top reranked documents
        return reranked_docs[:self.rerank_top_k]
    
    def _enhance_query_with_context(self, query: str, context: Optional[str]) -> str:
        """Enhance query with conversation context."""
        if not context:
            return query
        
        # Simple context enhancement - can be improved with more sophisticated methods
        enhanced_query = f"Bối cảnh: {context}\nCâu hỏi: {query}"
        return enhanced_query
    
    def _rerank_documents(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Rerank documents using cross-encoder."""
        if len(documents) <= 1:
            return documents
        
        try:
            # Prepare query-document pairs for reranking
            query_doc_pairs = []
            for doc in documents:
                # Create a representative text for the document
                doc_text = doc['content']
                if doc['metadata'].get('chunk_title'):
                    doc_text = f"{doc['metadata']['chunk_title']}: {doc_text}"
                
                query_doc_pairs.append([query, doc_text])
            
            # Get reranking scores
            rerank_scores = self.reranker.predict(query_doc_pairs)
            
            # Update documents with new scores
            for i, doc in enumerate(documents):
                doc['rerank_score'] = float(rerank_scores[i])
                doc['original_score'] = doc['score']
                doc['score'] = float(rerank_scores[i])  # Use rerank score as main score
            
            # Sort by rerank score
            reranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
            
            return reranked_docs
            
        except Exception as e:
            print(f"Error in reranking: {e}")
            # Return original documents if reranking fails
            return documents
    
    def retrieve_for_intent(self, query: str, intent: str, conversation_context: Optional[str] = None) -> List[Dict]:
        """
        Retrieve documents based on query and intent.
        
        Args:
            query: User query
            intent: Classified intent (legal, business, general)
            conversation_context: Previous conversation context
            
        Returns:
            List of relevant documents
        """
        # Set filters based on intent
        filters = None
        if intent == "legal":
            # For legal questions, focus on law documents
            filters = {
                "document_type": ["Luật", "Nghị định", "Thông tư", "Quyết định"]
            }
        elif intent == "business":
            # For business registration, focus on relevant regulations
            filters = {
                "law_field": "dang_ky_kinh_doanh"  # If this field exists
            }
        # For general intent, no specific filters
        
        return self.retrieve(query, filters, conversation_context)
    
    def get_document_summary(self, documents: List[Dict]) -> str:
        """Create a summary of retrieved documents for context."""
        if not documents:
            return ""
        
        summary_parts = []
        for i, doc in enumerate(documents[:3], 1):  # Top 3 documents
            metadata = doc['metadata']
            source_info = []
            
            if metadata.get('document_type'):
                source_info.append(metadata['document_type'])
            if metadata.get('document_number'):
                source_info.append(metadata['document_number'])
            if metadata.get('chunk_title'):
                source_info.append(metadata['chunk_title'])
            
            source_str = " - ".join(source_info) if source_info else "Tài liệu"
            summary_parts.append(f"{i}. {source_str}")
        
        return "Tài liệu tham khảo:\n" + "\n".join(summary_parts)
    
    def add_documents(self, documents) -> bool:
        """Add documents to the vector store."""
        return self.vector_store.add_documents(documents)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics."""
        vector_stats = self.vector_store.get_stats()
        retrieval_stats = {
            "top_k": self.top_k,
            "rerank_top_k": self.rerank_top_k,
            "similarity_threshold": self.similarity_threshold,
            "reranker_model": self.config['reranking']['model_name']
        }
        
        return {**vector_stats, **retrieval_stats}