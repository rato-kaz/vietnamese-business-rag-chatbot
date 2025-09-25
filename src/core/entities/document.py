from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import uuid


class DocumentType(str, Enum):
    """Document types."""
    LAW = "Luật"
    DECREE = "Nghị định"
    CIRCULAR = "Thông tư"
    DECISION = "Quyết định"


class EntityType(str, Enum):
    """Entity types for document chunks."""
    DOCUMENT = "document"
    ARTICLE_SECTION = "article_section"
    CHAPTER = "chapter"
    SECTION = "section"


@dataclass
class DocumentMetadata:
    """Document metadata."""
    source: str
    source_file: str
    document_number: Optional[str] = None
    document_type: Optional[DocumentType] = None
    document_title: Optional[str] = None
    issue_date: Optional[str] = None
    issuing_agency: Optional[str] = None
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    confidential_level: str = "Công khai"
    issue_year: Optional[int] = None
    law_field: str = "khac"
    article_code: Optional[str] = None
    dieu_code: Optional[str] = None
    dieu_title: Optional[str] = None
    chunk_title: Optional[str] = None
    khoan_code: Optional[str] = None
    entity_type: Optional[EntityType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "source_file": self.source_file,
            "document_number": self.document_number,
            "document_type": self.document_type.value if self.document_type else None,
            "document_title": self.document_title,
            "issue_date": self.issue_date,
            "issuing_agency": self.issuing_agency,
            "effective_date": self.effective_date,
            "expiry_date": self.expiry_date,
            "confidential_level": self.confidential_level,
            "issue_year": self.issue_year,
            "law_field": self.law_field,
            "article_code": self.article_code,
            "dieu_code": self.dieu_code,
            "dieu_title": self.dieu_title,
            "chunk_title": self.chunk_title,
            "khoan_code": self.khoan_code,
            "entity_type": self.entity_type.value if self.entity_type else None
        }


@dataclass
class DocumentChunk:
    """Document chunk with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    embedding: Optional[list] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class RetrievalResult:
    """Result from document retrieval."""
    chunk: DocumentChunk
    score: float
    rerank_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rerank_score": self.rerank_score
        }