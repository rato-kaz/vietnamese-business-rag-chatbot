import os
import re
import docx
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.core.entities.document import DocumentChunk, DocumentMetadata, DocumentType, EntityType
from src.core.interfaces.services import EmbeddingService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class DocumentProcessingService:
    """Service for processing legal documents."""
    
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        
        # Document type mappings
        self.document_type_mapping = {
            'luật': DocumentType.LAW,
            'nghị định': DocumentType.DECREE,
            'thông tư': DocumentType.CIRCULAR,
            'quyết định': DocumentType.DECISION,
            'tt': DocumentType.CIRCULAR,
            'nđ-cp': DocumentType.DECREE,
            'qđ': DocumentType.DECISION
        }
        
        # Agency mappings
        self.agency_mapping = {
            'qh': 'Quốc hội',
            'ttg': 'Thủ tướng Chính phủ',
            'btc': 'Bộ Tài chính',
            'bkhđt': 'Bộ Kế hoạch và Đầu tư',
            'cp': 'Chính phủ'
        }
    
    def process_directory(self, directory_path: str) -> List[DocumentChunk]:
        """Process all documents in a directory."""
        directory = Path(directory_path)
        all_chunks = []
        
        if not directory.exists():
            logger.warning(f"Directory not found: {directory_path}")
            return all_chunks
        
        logger.info(f"Processing documents in: {directory_path}")
        
        for file_path in directory.rglob("*.docx"):
            try:
                chunks = self.process_document(str(file_path))
                all_chunks.extend(chunks)
                logger.info(f"Processed {file_path.name}: {len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}", exc_info=True)
        
        logger.info(f"Total chunks processed: {len(all_chunks)}")
        return all_chunks
    
    def process_document(self, file_path: str) -> List[DocumentChunk]:
        """Process a single document."""
        try:
            # Load document content
            content = self._load_docx_content(file_path)
            if not content.strip():
                logger.warning(f"Empty document: {file_path}")
                return []
            
            # Extract metadata from filename and content
            filename = Path(file_path).name
            base_metadata = self._extract_metadata_from_filename(filename)
            metadata = self._extract_metadata_from_content(content, base_metadata)
            
            # Chunk document by articles
            chunks = self._chunk_by_articles(content, metadata)
            
            if not chunks:
                # Fallback to simple chunking
                chunk_metadata = metadata.copy()
                chunk_metadata.entity_type = EntityType.DOCUMENT
                
                chunk = DocumentChunk(
                    content=content,
                    metadata=chunk_metadata
                )
                chunks = [chunk]
            
            # Generate embeddings for chunks
            for chunk in chunks:
                embedding = await self.embedding_service.embed_text(chunk.content)
                chunk.embedding = embedding
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}", exc_info=True)
            return []
    
    def _load_docx_content(self, file_path: str) -> str:
        """Load content from .docx file."""
        try:
            doc = docx.Document(file_path)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
            return content
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return ""
    
    def _extract_metadata_from_filename(self, filename: str) -> DocumentMetadata:
        """Extract metadata from filename patterns."""
        metadata = DocumentMetadata(
            source=filename,
            source_file=Path(filename).stem
        )
        
        # Pattern: _130_2017_TT-BTC_373081.docx
        pattern1 = r"_(\d+)_(\d{4})_([A-Z\-]+)_\d+\.docx"
        match1 = re.search(pattern1, filename)
        if match1:
            number, year, agency_code = match1.groups()
            metadata.document_number = f"{number}/{year}/{agency_code}"
            metadata.issue_year = int(year)
            
            # Determine document type and agency
            agency_lower = agency_code.lower()
            for key, value in self.agency_mapping.items():
                if key in agency_lower:
                    metadata.issuing_agency = value
                    break
            
            if 'tt' in agency_lower:
                metadata.document_type = DocumentType.CIRCULAR
            elif 'nd' in agency_lower:
                metadata.document_type = DocumentType.DECREE
            elif 'qd' in agency_lower:
                metadata.document_type = DocumentType.DECISION
        
        # Pattern: Luật-03-2022-QH15.docx
        pattern2 = r"(Luật|Nghị định|Thông tư|Quyết định)-(\d+)-(\d{4})-([A-Z0-9]+)\.docx"
        match2 = re.search(pattern2, filename)
        if match2:
            doc_type, number, year, agency_code = match2.groups()
            metadata.document_type = self.document_type_mapping.get(doc_type.lower())
            metadata.document_number = f"{number}/{year}/{agency_code}"
            metadata.issue_year = int(year)
            
            agency_lower = agency_code.lower()
            for key, value in self.agency_mapping.items():
                if key in agency_lower:
                    metadata.issuing_agency = value
                    break
        
        return metadata
    
    def _extract_metadata_from_content(self, content: str, base_metadata: DocumentMetadata) -> DocumentMetadata:
        """Extract additional metadata from content."""
        metadata = base_metadata
        
        # Extract document title
        lines = content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not re.match(r'^(Điều|Chương|\d+\.)', line):
                if not metadata.document_title:
                    metadata.document_title = line
                    break
        
        # Extract dates
        date_patterns = [
            r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})",
            r"(\d{1,2})/(\d{1,2})/(\d{4})"
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                day, month, year = matches[0]
                try:
                    date_str = f"{day:0>2}/{month:0>2}/{year}"
                    if not metadata.issue_date:
                        metadata.issue_date = date_str
                except:
                    pass
        
        return metadata
    
    def _chunk_by_articles(self, content: str, metadata: DocumentMetadata) -> List[DocumentChunk]:
        """Chunk document by articles and sections."""
        chunks = []
        
        # Split by articles (Điều)
        article_pattern = r'(Điều\s+\d+[.\s]*[^\n]*)'
        articles = re.split(article_pattern, content)
        
        current_article = None
        current_article_title = None
        
        for i, section in enumerate(articles):
            if re.match(r'Điều\s+\d+', section.strip()):
                current_article = section.strip()
                current_article_title = section.strip()
            elif section.strip() and current_article:
                # Further split by numbered items
                item_pattern = r'(\n\s*[0-9a-z]+\.\s*)'
                items = re.split(item_pattern, section)
                
                current_item_content = ""
                current_khoan_code = None
                
                for j, item in enumerate(items):
                    if re.match(r'\n\s*[0-9a-z]+\.\s*', item):
                        # Save previous item
                        if current_item_content.strip():
                            chunk_metadata = self._create_chunk_metadata(
                                metadata, current_article, current_article_title, current_khoan_code
                            )
                            
                            chunk = DocumentChunk(
                                content=current_item_content.strip(),
                                metadata=chunk_metadata
                            )
                            chunks.append(chunk)
                        
                        # Start new item
                        current_khoan_code = item.strip()
                        current_item_content = ""
                    else:
                        current_item_content += item
                
                # Add last item
                if current_item_content.strip():
                    chunk_metadata = self._create_chunk_metadata(
                        metadata, current_article, current_article_title, current_khoan_code
                    )
                    
                    chunk = DocumentChunk(
                        content=current_item_content.strip(),
                        metadata=chunk_metadata
                    )
                    chunks.append(chunk)
        
        return chunks
    
    def _create_chunk_metadata(
        self, 
        base_metadata: DocumentMetadata, 
        article_code: str, 
        article_title: str,
        khoan_code: Optional[str]
    ) -> DocumentMetadata:
        """Create metadata for document chunk."""
        chunk_metadata = DocumentMetadata(
            source=base_metadata.source,
            source_file=base_metadata.source_file,
            document_number=base_metadata.document_number,
            document_type=base_metadata.document_type,
            document_title=base_metadata.document_title,
            issue_date=base_metadata.issue_date,
            issuing_agency=base_metadata.issuing_agency,
            effective_date=base_metadata.effective_date,
            expiry_date=base_metadata.expiry_date,
            confidential_level=base_metadata.confidential_level,
            issue_year=base_metadata.issue_year,
            law_field=base_metadata.law_field,
            article_code=article_code,
            dieu_code=article_code,
            dieu_title=article_title,
            chunk_title=f"{article_code}" + (f" - {khoan_code}" if khoan_code else ""),
            khoan_code=khoan_code,
            entity_type=EntityType.ARTICLE_SECTION
        )
        
        return chunk_metadata