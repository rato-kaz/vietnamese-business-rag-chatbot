import os
import weaviate
import yaml
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from langchain.schema import Document
import numpy as np


class WeaviateVectorStore:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize Weaviate vector store."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize Weaviate client
        self.client = weaviate.Client(
            url=self.config['vector_store']['url'],
            timeout_config=(5, 15)
        )
        
        self.collection_name = self.config['vector_store']['collection_name']
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(
            self.config['embeddings']['model_name'],
            device=self.config['embeddings']['device']
        )
        
        # Create schema if not exists
        self._create_schema()
    
    def _create_schema(self):
        """Create Weaviate schema for legal documents."""
        schema = {
            "class": self.collection_name,
            "description": "Vietnamese legal documents for business registration",
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Document content"
                },
                {
                    "name": "source",
                    "dataType": ["string"],
                    "description": "Source filename"
                },
                {
                    "name": "source_file",
                    "dataType": ["string"],
                    "description": "Source file without extension"
                },
                {
                    "name": "document_number",
                    "dataType": ["string"],
                    "description": "Document number (e.g., 130/2017/TT-BTC)"
                },
                {
                    "name": "document_type",
                    "dataType": ["string"],
                    "description": "Type of document (Luật, Nghị định, Thông tư, Quyết định)"
                },
                {
                    "name": "document_title",
                    "dataType": ["text"],
                    "description": "Document title"
                },
                {
                    "name": "issue_date",
                    "dataType": ["string"],
                    "description": "Issue date"
                },
                {
                    "name": "issuing_agency",
                    "dataType": ["string"],
                    "description": "Issuing agency"
                },
                {
                    "name": "effective_date",
                    "dataType": ["string"],
                    "description": "Effective date"
                },
                {
                    "name": "expiry_date",
                    "dataType": ["string"],
                    "description": "Expiry date"
                },
                {
                    "name": "confidential_level",
                    "dataType": ["string"],
                    "description": "Confidentiality level"
                },
                {
                    "name": "issue_year",
                    "dataType": ["int"],
                    "description": "Year of issue"
                },
                {
                    "name": "law_field",
                    "dataType": ["string"],
                    "description": "Field of law"
                },
                {
                    "name": "article_code",
                    "dataType": ["string"],
                    "description": "Article code (e.g., Điều 1)"
                },
                {
                    "name": "dieu_code",
                    "dataType": ["string"],
                    "description": "Article code"
                },
                {
                    "name": "dieu_title",
                    "dataType": ["string"],
                    "description": "Article title"
                },
                {
                    "name": "chunk_title",
                    "dataType": ["string"],
                    "description": "Chunk title"
                },
                {
                    "name": "khoan_code",
                    "dataType": ["string"],
                    "description": "Section code (1., 2., a., b.)"
                },
                {
                    "name": "entity_type",
                    "dataType": ["string"],
                    "description": "Type of entity (article_section, document)"
                }
            ]
        }
        
        # Check if class exists
        try:
            existing_schema = self.client.schema.get()
            class_names = [cls["class"] for cls in existing_schema.get("classes", [])]
            
            if self.collection_name not in class_names:
                self.client.schema.create_class(schema)
                print(f"Created Weaviate class: {self.collection_name}")
            else:
                print(f"Weaviate class already exists: {self.collection_name}")
        except Exception as e:
            print(f"Error creating schema: {e}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to Weaviate."""
        try:
            with self.client.batch(batch_size=100) as batch:
                for doc in documents:
                    # Generate embedding
                    vector = self.embed_text(doc.page_content)
                    
                    # Prepare properties
                    properties = {
                        "content": doc.page_content,
                        "source": doc.metadata.get("source"),
                        "source_file": doc.metadata.get("source_file"),
                        "document_number": doc.metadata.get("document_number"),
                        "document_type": doc.metadata.get("document_type"),
                        "document_title": doc.metadata.get("document_title"),
                        "issue_date": doc.metadata.get("issue_date"),
                        "issuing_agency": doc.metadata.get("issuing_agency"),
                        "effective_date": doc.metadata.get("effective_date"),
                        "expiry_date": doc.metadata.get("expiry_date"),
                        "confidential_level": doc.metadata.get("confidential_level"),
                        "issue_year": doc.metadata.get("issue_year"),
                        "law_field": doc.metadata.get("law_field"),
                        "article_code": doc.metadata.get("article_code"),
                        "dieu_code": doc.metadata.get("dieu_code"),
                        "dieu_title": doc.metadata.get("dieu_title"),
                        "chunk_title": doc.metadata.get("chunk_title"),
                        "khoan_code": doc.metadata.get("khoan_code"),
                        "entity_type": doc.metadata.get("entity_type")
                    }
                    
                    # Remove None values
                    properties = {k: v for k, v in properties.items() if v is not None}
                    
                    batch.add_data_object(
                        data_object=properties,
                        class_name=self.collection_name,
                        vector=vector
                    )
            
            print(f"Successfully added {len(documents)} documents to Weaviate")
            return True
            
        except Exception as e:
            print(f"Error adding documents to Weaviate: {e}")
            return False
    
    def search(self, query: str, top_k: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for similar documents."""
        try:
            # Generate query embedding
            query_vector = self.embed_text(query)
            
            # Build search query
            search_query = (
                self.client.query
                .get(self.collection_name, [
                    "content", "source", "document_type", "document_title",
                    "article_code", "dieu_code", "chunk_title", "khoan_code",
                    "issuing_agency", "issue_date", "document_number"
                ])
                .with_near_vector({
                    "vector": query_vector
                })
                .with_limit(top_k)
                .with_additional(["distance"])
            )
            
            # Add filters if provided
            if filters:
                where_filter = self._build_where_filter(filters)
                if where_filter:
                    search_query = search_query.with_where(where_filter)
            
            result = search_query.do()
            
            # Process results
            documents = []
            if "data" in result and "Get" in result["data"]:
                items = result["data"]["Get"].get(self.collection_name, [])
                for item in items:
                    documents.append({
                        "content": item.get("content", ""),
                        "metadata": {
                            "source": item.get("source"),
                            "document_type": item.get("document_type"),
                            "document_title": item.get("document_title"),
                            "article_code": item.get("article_code"),
                            "dieu_code": item.get("dieu_code"),
                            "chunk_title": item.get("chunk_title"),
                            "khoan_code": item.get("khoan_code"),
                            "issuing_agency": item.get("issuing_agency"),
                            "issue_date": item.get("issue_date"),
                            "document_number": item.get("document_number")
                        },
                        "score": 1 - item["_additional"]["distance"]  # Convert distance to similarity
                    })
            
            return documents
            
        except Exception as e:
            print(f"Error searching in Weaviate: {e}")
            return []
    
    def _build_where_filter(self, filters: Dict) -> Optional[Dict]:
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
        
        # Multiple conditions with AND
        where_filter = {
            "operator": "And",
            "operands": conditions
        }
        
        return where_filter
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            result = (
                self.client.query
                .aggregate(self.collection_name)
                .with_meta_count()
                .do()
            )
            
            count = 0
            if "data" in result and "Aggregate" in result["data"]:
                aggregate_data = result["data"]["Aggregate"].get(self.collection_name, [])
                if aggregate_data:
                    count = aggregate_data[0].get("meta", {}).get("count", 0)
            
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "embedding_model": self.config['embeddings']['model_name']
            }
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            self.client.schema.delete_class(self.collection_name)
            self._create_schema()
            print(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False