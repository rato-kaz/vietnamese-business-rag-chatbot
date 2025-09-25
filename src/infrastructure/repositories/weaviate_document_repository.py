from typing import List, Dict, Any, Optional
import weaviate
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.core.interfaces.repositories import DocumentRepository
from src.core.entities.document import DocumentChunk, RetrievalResult, DocumentMetadata
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class WeaviateDocumentRepository(DocumentRepository):
    """Weaviate implementation of document repository."""
    
    def __init__(
        self,
        weaviate_url: str = "http://localhost:8080",
        collection_name: str = "LegalDocuments",
        timeout: tuple = (5, 15)
    ):
        self.weaviate_url = weaviate_url
        self.collection_name = collection_name
        self.timeout = timeout
        
        # Initialize client
        self.client = weaviate.Client(
            url=weaviate_url,
            timeout_config=timeout
        )
        
        # Thread pool for sync operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize schema
        self._initialize_schema()
    
    def _initialize_schema(self) -> None:
        """Initialize Weaviate schema."""
        try:
            schema = {
                "class": self.collection_name,
                "description": "Vietnamese legal documents for business registration",
                "vectorizer": "none",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "source", "dataType": ["string"]},
                    {"name": "source_file", "dataType": ["string"]},
                    {"name": "document_number", "dataType": ["string"]},
                    {"name": "document_type", "dataType": ["string"]},
                    {"name": "document_title", "dataType": ["text"]},
                    {"name": "issue_date", "dataType": ["string"]},
                    {"name": "issuing_agency", "dataType": ["string"]},
                    {"name": "effective_date", "dataType": ["string"]},
                    {"name": "expiry_date", "dataType": ["string"]},
                    {"name": "confidential_level", "dataType": ["string"]},
                    {"name": "issue_year", "dataType": ["int"]},
                    {"name": "law_field", "dataType": ["string"]},
                    {"name": "article_code", "dataType": ["string"]},
                    {"name": "dieu_code", "dataType": ["string"]},
                    {"name": "dieu_title", "dataType": ["string"]},
                    {"name": "chunk_title", "dataType": ["string"]},
                    {"name": "khoan_code", "dataType": ["string"]},
                    {"name": "entity_type", "dataType": ["string"]},
                    {"name": "chunk_id", "dataType": ["string"]}
                ]
            }
            
            # Check if class exists
            existing_schema = self.client.schema.get()
            class_names = [cls["class"] for cls in existing_schema.get("classes", [])]
            
            if self.collection_name not in class_names:
                self.client.schema.create_class(schema)
                logger.info(f"Created Weaviate class: {self.collection_name}")
            else:
                logger.info(f"Weaviate class already exists: {self.collection_name}")
                
        except Exception as e:
            logger.error(
                "Failed to initialize Weaviate schema",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def save_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Save document chunks to Weaviate."""
        try:
            logger.info(
                "Saving chunks to Weaviate",
                extra={"chunk_count": len(chunks)}
            )
            
            def _save_chunks_sync():
                with self.client.batch(batch_size=100) as batch:
                    for chunk in chunks:
                        # Prepare properties
                        properties = {
                            "content": chunk.content,
                            "chunk_id": chunk.id,
                            **self._metadata_to_properties(chunk.metadata)
                        }
                        
                        # Remove None values
                        properties = {k: v for k, v in properties.items() if v is not None}
                        
                        # Add to batch
                        batch.add_data_object(
                            data_object=properties,
                            class_name=self.collection_name,
                            vector=chunk.embedding
                        )
            
            # Run in thread pool
            await asyncio.get_event_loop().run_in_executor(
                self.executor, _save_chunks_sync
            )
            
            logger.info(
                "Successfully saved chunks to Weaviate",
                extra={"chunk_count": len(chunks)}
            )
            
        except Exception as e:
            logger.error(
                "Failed to save chunks to Weaviate",
                extra={
                    "chunk_count": len(chunks),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def search_chunks(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Search document chunks in Weaviate."""
        try:
            logger.debug(
                "Searching chunks in Weaviate",
                extra={
                    "query_length": len(query),
                    "top_k": top_k,
                    "filters": filters
                }
            )
            
            def _search_chunks_sync():
                # Build search query
                search_query = (
                    self.client.query
                    .get(self.collection_name, [
                        "content", "chunk_id", "source", "document_type", 
                        "document_title", "article_code", "dieu_code", 
                        "chunk_title", "khoan_code", "issuing_agency", 
                        "issue_date", "document_number"
                    ])
                    .with_limit(top_k)
                    .with_additional(["distance"])
                )
                
                # Add vector search if query embedding is available
                # Note: In real implementation, you'd need to embed the query first
                # For now, we'll use text search
                if hasattr(self, 'embed_query'):
                    query_vector = self.embed_query(query)
                    search_query = search_query.with_near_vector({
                        "vector": query_vector
                    })
                else:
                    # Use text search as fallback
                    search_query = search_query.with_near_text({
                        "concepts": [query]
                    })
                
                # Add filters if provided
                if filters:
                    where_filter = self._build_where_filter(filters)
                    if where_filter:
                        search_query = search_query.with_where(where_filter)
                
                return search_query.do()
            
            # Run search in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _search_chunks_sync
            )
            
            # Process results
            retrieval_results = []
            if "data" in result and "Get" in result["data"]:
                items = result["data"]["Get"].get(self.collection_name, [])
                
                for item in items:
                    # Reconstruct metadata
                    metadata = self._properties_to_metadata(item)
                    
                    # Create document chunk
                    chunk = DocumentChunk(
                        id=item.get("chunk_id", ""),
                        content=item.get("content", ""),
                        metadata=metadata
                    )
                    
                    # Calculate score
                    score = 1 - item["_additional"]["distance"]
                    
                    retrieval_results.append(RetrievalResult(
                        chunk=chunk,
                        score=score
                    ))
            
            logger.debug(
                "Search completed",
                extra={
                    "query_length": len(query),
                    "results_count": len(retrieval_results)
                }
            )
            
            return retrieval_results
            
        except Exception as e:
            logger.error(
                "Failed to search chunks in Weaviate",
                extra={
                    "query_length": len(query),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Get chunk by ID from Weaviate."""
        try:
            def _get_chunk_sync():
                result = (
                    self.client.query
                    .get(self.collection_name, [
                        "content", "chunk_id", "source", "document_type",
                        "document_title", "article_code", "dieu_code",
                        "chunk_title", "khoan_code", "issuing_agency",
                        "issue_date", "document_number"
                    ])
                    .with_where({
                        "path": ["chunk_id"],
                        "operator": "Equal",
                        "valueString": chunk_id
                    })
                    .with_limit(1)
                    .do()
                )
                return result
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _get_chunk_sync
            )
            
            if "data" in result and "Get" in result["data"]:
                items = result["data"]["Get"].get(self.collection_name, [])
                if items:
                    item = items[0]
                    metadata = self._properties_to_metadata(item)
                    
                    return DocumentChunk(
                        id=item.get("chunk_id", ""),
                        content=item.get("content", ""),
                        metadata=metadata
                    )
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get chunk from Weaviate",
                extra={
                    "chunk_id": chunk_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def delete_all_chunks(self) -> None:
        """Delete all chunks from Weaviate."""
        try:
            def _delete_all_sync():
                self.client.schema.delete_class(self.collection_name)
                self._initialize_schema()
            
            await asyncio.get_event_loop().run_in_executor(
                self.executor, _delete_all_sync
            )
            
            logger.info("All chunks deleted from Weaviate")
            
        except Exception as e:
            logger.error(
                "Failed to delete all chunks from Weaviate",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics."""
        try:
            def _get_stats_sync():
                result = (
                    self.client.query
                    .aggregate(self.collection_name)
                    .with_meta_count()
                    .do()
                )
                return result
            
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor, _get_stats_sync
            )
            
            count = 0
            if "data" in result and "Aggregate" in result["data"]:
                aggregate_data = result["data"]["Aggregate"].get(self.collection_name, [])
                if aggregate_data:
                    count = aggregate_data[0].get("meta", {}).get("count", 0)
            
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "weaviate_url": self.weaviate_url
            }
            
        except Exception as e:
            logger.error(
                "Failed to get stats from Weaviate",
                extra={"error": str(e)},
                exc_info=True
            )
            return {"error": str(e)}
    
    def _metadata_to_properties(self, metadata: DocumentMetadata) -> Dict[str, Any]:
        """Convert metadata to Weaviate properties."""
        return {
            "source": metadata.source,
            "source_file": metadata.source_file,
            "document_number": metadata.document_number,
            "document_type": metadata.document_type.value if metadata.document_type else None,
            "document_title": metadata.document_title,
            "issue_date": metadata.issue_date,
            "issuing_agency": metadata.issuing_agency,
            "effective_date": metadata.effective_date,
            "expiry_date": metadata.expiry_date,
            "confidential_level": metadata.confidential_level,
            "issue_year": metadata.issue_year,
            "law_field": metadata.law_field,
            "article_code": metadata.article_code,
            "dieu_code": metadata.dieu_code,
            "dieu_title": metadata.dieu_title,
            "chunk_title": metadata.chunk_title,
            "khoan_code": metadata.khoan_code,
            "entity_type": metadata.entity_type.value if metadata.entity_type else None
        }
    
    def _properties_to_metadata(self, properties: Dict[str, Any]) -> DocumentMetadata:
        """Convert Weaviate properties to metadata."""
        from src.core.entities.document import DocumentType, EntityType
        
        # Convert document type
        doc_type = None
        if properties.get("document_type"):
            try:
                doc_type = DocumentType(properties["document_type"])
            except ValueError:
                pass
        
        # Convert entity type
        entity_type = None
        if properties.get("entity_type"):
            try:
                entity_type = EntityType(properties["entity_type"])
            except ValueError:
                pass
        
        return DocumentMetadata(
            source=properties.get("source", ""),
            source_file=properties.get("source_file", ""),
            document_number=properties.get("document_number"),
            document_type=doc_type,
            document_title=properties.get("document_title"),
            issue_date=properties.get("issue_date"),
            issuing_agency=properties.get("issuing_agency"),
            effective_date=properties.get("effective_date"),
            expiry_date=properties.get("expiry_date"),
            confidential_level=properties.get("confidential_level", "Công khai"),
            issue_year=properties.get("issue_year"),
            law_field=properties.get("law_field", "khac"),
            article_code=properties.get("article_code"),
            dieu_code=properties.get("dieu_code"),
            dieu_title=properties.get("dieu_title"),
            chunk_title=properties.get("chunk_title"),
            khoan_code=properties.get("khoan_code"),
            entity_type=entity_type
        )
    
    def _build_where_filter(self, filters: Dict[str, Any]) -> Optional[Dict]:
        """Build where filter for Weaviate query."""
        conditions = []
        
        for field, value in filters.items():
            if value is not None:
                if isinstance(value, list):
                    # Multiple values with OR
                    or_conditions = []
                    for v in value:
                        or_conditions.append({
                            "path": [field],
                            "operator": "Equal",
                            "valueString": str(v)
                        })
                    
                    if len(or_conditions) == 1:
                        conditions.append(or_conditions[0])
                    else:
                        conditions.append({
                            "operator": "Or",
                            "operands": or_conditions
                        })
                else:
                    conditions.append({
                        "path": [field],
                        "operator": "Equal",
                        "valueString": str(value)
                    })
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {
            "operator": "And",
            "operands": conditions
        }