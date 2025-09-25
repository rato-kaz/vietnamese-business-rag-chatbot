from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File
from typing import List
import os
import shutil
from datetime import datetime

from ..models import DocumentStatsResponse
from ..dependencies import get_chatbot
from src.chatbot import ConversationalRAGChatbot

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/load")
async def load_documents(
    background_tasks: BackgroundTasks,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Load documents into the knowledge base."""
    def load_docs():
        try:
            success = chatbot.add_documents_to_knowledge_base("data/documents/core")
            print(f"Document loading {'succeeded' if success else 'failed'}")
            return success
        except Exception as e:
            print(f"Error loading documents: {e}")
            return False
    
    background_tasks.add_task(load_docs)
    return {
        "message": "Document loading started in background",
        "status": "processing",
        "timestamp": datetime.now()
    }


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get document statistics."""
    try:
        stats = chatbot.get_system_stats()
        retriever_stats = stats.get("retriever_stats", {})
        
        return DocumentStatsResponse(
            total_documents=retriever_stats.get("total_documents", 0),
            embedding_model=retriever_stats.get("embedding_model", ""),
            reranker_model=retriever_stats.get("reranker_model", ""),
            collection_name=retriever_stats.get("collection_name", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document stats: {str(e)}")


@router.post("/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Upload and process new documents."""
    uploaded_files = []
    
    # Create upload directory if it doesn't exist
    upload_dir = "data/documents/uploaded"
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        # Save uploaded files
        for file in files:
            if not file.filename.endswith('.docx'):
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
            
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
                success = chatbot.add_documents_to_knowledge_base(upload_dir)
                print(f"Uploaded document processing {'succeeded' if success else 'failed'}")
                return success
            except Exception as e:
                print(f"Error processing uploaded documents: {e}")
                return False
        
        background_tasks.add_task(process_uploaded_docs)
        
        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files,
            "processing_status": "started",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        # Clean up uploaded files on error
        for file_info in uploaded_files:
            try:
                os.remove(file_info["path"])
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error uploading documents: {str(e)}")


@router.get("/search")
async def search_documents(
    query: str,
    top_k: int = 5,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Search documents in the knowledge base."""
    try:
        # Use the retriever to search documents
        retrieved_docs = chatbot.retriever.retrieve(query, top_k=top_k)
        
        results = []
        for doc in retrieved_docs:
            results.append({
                "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                "metadata": doc["metadata"],
                "score": doc.get("score", 0)
            })
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")


@router.delete("/clear")
async def clear_documents(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Clear all documents from the knowledge base."""
    try:
        success = chatbot.retriever.vector_store.clear_collection()
        
        if success:
            return {
                "message": "All documents cleared from knowledge base",
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear documents")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")


@router.get("/types")
async def get_document_types(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get available document types in the knowledge base."""
    try:
        # This would ideally query the vector store for unique document types
        # For now, return predefined types
        document_types = [
            {
                "type": "Luật",
                "description": "Luật do Quốc hội ban hành",
                "example": "Luật Doanh nghiệp 2020"
            },
            {
                "type": "Nghị định",
                "description": "Nghị định do Chính phủ ban hành",
                "example": "Nghị định 01/2021/NĐ-CP"
            },
            {
                "type": "Thông tư",
                "description": "Thông tư do các Bộ ban hành",
                "example": "Thông tư 02/2023/TT-BKHĐT"
            },
            {
                "type": "Quyết định",
                "description": "Quyết định của các cơ quan quản lý",
                "example": "Quyết định 27/2018/QĐ-TTg"
            }
        ]
        
        return {
            "document_types": document_types,
            "total_types": len(document_types),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting document types: {str(e)}")


@router.get("/agencies")
async def get_issuing_agencies(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get list of document issuing agencies."""
    try:
        agencies = [
            {
                "code": "QH",
                "name": "Quốc hội",
                "description": "Cơ quan quyền lực nhà nước cao nhất"
            },
            {
                "code": "CP",
                "name": "Chính phủ",
                "description": "Cơ quan hành chính nhà nước cao nhất"
            },
            {
                "code": "BTC",
                "name": "Bộ Tài chính",
                "description": "Bộ quản lý về tài chính"
            },
            {
                "code": "BKHĐT",
                "name": "Bộ Kế hoạch và Đầu tư",
                "description": "Bộ quản lý về kế hoạch và đầu tư"
            },
            {
                "code": "TTg",
                "name": "Thủ tướng Chính phủ",
                "description": "Người đứng đầu Chính phủ"
            }
        ]
        
        return {
            "agencies": agencies,
            "total_agencies": len(agencies),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agencies: {str(e)}")