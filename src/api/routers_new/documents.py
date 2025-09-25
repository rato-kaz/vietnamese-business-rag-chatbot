from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from typing import List
import os
import shutil
from datetime import datetime

from src.application.dependencies import get_container
from src.infrastructure.logging.context import get_logger, LoggingContext
from src.api.models import DocumentStatsResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/load")
async def load_documents(background_tasks: BackgroundTasks):
    """Load documents into the knowledge base."""
    try:
        logger.info("Starting document loading process")
        
        def load_docs():
            try:
                from src.infrastructure.services.document_processing_service import DocumentProcessingService
                from src.application.config import settings
                
                container = get_container()
                document_repo = container.get_document_repo()
                embedding_service = container.get_embedding_service()
                
                # Create document processing service
                doc_processor = DocumentProcessingService(
                    embedding_service=embedding_service
                )
                
                # Process documents
                chunks = doc_processor.process_directory(settings.documents_dir)
                
                if chunks:
                    # Save to repository
                    import asyncio
                    asyncio.run(document_repo.save_chunks(chunks))
                    
                    logger.info(
                        "Documents loaded successfully",
                        extra={"chunk_count": len(chunks)}
                    )
                    return True
                else:
                    logger.warning("No documents found to load")
                    return False
                    
            except Exception as e:
                logger.error(
                    "Error loading documents",
                    extra={"error": str(e)},
                    exc_info=True
                )
                return False
        
        background_tasks.add_task(load_docs)
        
        # Record metrics
        container = get_container()
        metrics_service = container.get_metrics_service()
        await metrics_service.increment_counter("documents.load_started")
        
        return {
            "message": "Document loading started in background",
            "status": "processing",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(
            "Failed to start document loading",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error starting document loading: {str(e)}"
        )


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats():
    """Get document statistics."""
    try:
        container = get_container()
        document_repo = container.get_document_repo()
        
        stats = await document_repo.get_stats()
        
        logger.debug("Document stats retrieved", extra={"stats": stats})
        
        return DocumentStatsResponse(
            total_documents=stats.get("total_chunks", 0),
            embedding_model=stats.get("embedding_model", ""),
            reranker_model=stats.get("reranker_model", ""),
            collection_name=stats.get("collection_name", "")
        )
        
    except Exception as e:
        logger.error(
            "Failed to get document stats",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document stats: {str(e)}"
        )


@router.get("/search")
async def search_documents(
    query: str,
    top_k: int = 5
):
    """Search documents in the knowledge base."""
    try:
        logger.info(
            "Searching documents",
            extra={
                "query_length": len(query),
                "top_k": top_k
            }
        )
        
        container = get_container()
        document_repo = container.get_document_repo()
        
        # Search documents
        results = await document_repo.search_chunks(
            query=query,
            top_k=top_k
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.chunk.content[:500] + "..." if len(result.chunk.content) > 500 else result.chunk.content,
                "metadata": result.chunk.metadata.to_dict(),
                "score": result.score,
                "rerank_score": result.rerank_score
            })
        
        logger.info(
            "Document search completed",
            extra={
                "query_length": len(query),
                "results_count": len(formatted_results)
            }
        )
        
        # Record metrics
        metrics_service = container.get_metrics_service()
        await metrics_service.increment_counter("documents.searches")
        await metrics_service.record_histogram("documents.search_results", len(formatted_results))
        
        return {
            "query": query,
            "total_results": len(formatted_results),
            "results": formatted_results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(
            "Failed to search documents",
            extra={
                "query": query,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )


@router.post("/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload and process new documents."""
    uploaded_files = []
    
    try:
        logger.info(
            "Starting document upload",
            extra={"file_count": len(files)}
        )
        
        # Create upload directory
        from src.application.config import settings
        upload_dir = settings.upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded files
        for file in files:
            if not file.filename.endswith('.docx'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file.filename}"
                )
            
            file_path = os.path.join(upload_dir, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append({
                "filename": file.filename,
                "size": os.path.getsize(file_path),
                "path": file_path
            })
        
        # Process documents in background
        def process_uploaded_docs():
            try:
                from src.infrastructure.services.document_processing_service import DocumentProcessingService
                
                container = get_container()
                document_repo = container.get_document_repo()
                embedding_service = container.get_embedding_service()
                
                # Create document processing service
                doc_processor = DocumentProcessingService(
                    embedding_service=embedding_service
                )
                
                # Process uploaded documents
                chunks = doc_processor.process_directory(upload_dir)
                
                if chunks:
                    # Save to repository
                    import asyncio
                    asyncio.run(document_repo.save_chunks(chunks))
                    
                    logger.info(
                        "Uploaded documents processed successfully",
                        extra={"chunk_count": len(chunks)}
                    )
                    return True
                else:
                    logger.warning("No valid documents found in upload")
                    return False
                    
            except Exception as e:
                logger.error(
                    "Error processing uploaded documents",
                    extra={"error": str(e)},
                    exc_info=True
                )
                return False
        
        background_tasks.add_task(process_uploaded_docs)
        
        # Record metrics
        container = get_container()
        metrics_service = container.get_metrics_service()
        await metrics_service.increment_counter("documents.uploaded", tags={"count": str(len(files))})
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files,
            "processing_status": "started",
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        # Clean up uploaded files on error
        for file_info in uploaded_files:
            try:
                os.remove(file_info["path"])
            except:
                pass
        raise
        
    except Exception as e:
        # Clean up uploaded files on error
        for file_info in uploaded_files:
            try:
                os.remove(file_info["path"])
            except:
                pass
        
        logger.error(
            "Failed to upload documents",
            extra={
                "file_count": len(files),
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading documents: {str(e)}"
        )


@router.delete("/clear")
async def clear_documents():
    """Clear all documents from the knowledge base."""
    try:
        logger.info("Clearing all documents")
        
        container = get_container()
        document_repo = container.get_document_repo()
        
        await document_repo.delete_all_chunks()
        
        logger.info("All documents cleared successfully")
        
        # Record metrics
        metrics_service = container.get_metrics_service()
        await metrics_service.increment_counter("documents.cleared")
        
        return {
            "message": "All documents cleared from knowledge base",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(
            "Failed to clear documents",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing documents: {str(e)}"
        )