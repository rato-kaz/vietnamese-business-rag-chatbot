from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import psutil
import os

from ..models import SystemStatsResponse, HealthResponse
from ..dependencies import get_session_manager, get_chatbot
from ..session_manager import SessionManager
from src.chatbot import ConversationalRAGChatbot

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check system health
        health_status = "healthy"
        
        # Test chatbot initialization
        try:
            chatbot = get_chatbot()
            health_status = "healthy"
        except Exception:
            health_status = "degraded"
        
        return HealthResponse(
            status=health_status,
            timestamp=datetime.now(),
            version="1.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="1.0.0"
        )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    session_manager: SessionManager = Depends(get_session_manager),
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get comprehensive system statistics."""
    try:
        chatbot_stats = chatbot.get_system_stats()
        
        # Get system resource usage
        memory_info = psutil.virtual_memory()
        memory_usage = f"{memory_info.percent}% ({memory_info.used // (1024**3)}GB / {memory_info.total // (1024**3)}GB)"
        
        # Calculate uptime (placeholder - implement proper tracking)
        uptime = "N/A"
        
        return SystemStatsResponse(
            active_sessions=session_manager.get_active_session_count(),
            total_documents=chatbot_stats.get("retriever_stats", {}).get("total_documents", 0),
            available_templates=chatbot_stats.get("available_templates", 0),
            system_uptime=uptime,
            memory_usage=memory_usage
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")


@router.get("/info")
async def get_system_info():
    """Get detailed system information."""
    try:
        # System info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        return {
            "system": {
                "cpu_cores": cpu_count,
                "cpu_usage_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory_info.total / (1024**3), 2),
                    "used_gb": round(memory_info.used / (1024**3), 2),
                    "percent": memory_info.percent
                },
                "disk": {
                    "total_gb": round(disk_info.total / (1024**3), 2),
                    "used_gb": round(disk_info.used / (1024**3), 2),
                    "percent": round((disk_info.used / disk_info.total) * 100, 2)
                }
            },
            "environment": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.name,
                "working_directory": os.getcwd()
            },
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system info: {str(e)}")


@router.post("/gc")
async def garbage_collect():
    """Force garbage collection."""
    try:
        import gc
        
        # Get memory usage before
        memory_before = psutil.virtual_memory().used / (1024**3)
        
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory usage after
        memory_after = psutil.virtual_memory().used / (1024**3)
        memory_freed = memory_before - memory_after
        
        return {
            "message": "Garbage collection completed",
            "objects_collected": collected,
            "memory_freed_gb": round(memory_freed, 3),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during garbage collection: {str(e)}")


@router.get("/models")
async def get_model_info(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get information about loaded models."""
    try:
        return {
            "embedding_model": {
                "name": chatbot.config['embeddings']['model_name'],
                "device": chatbot.config['embeddings']['device']
            },
            "reranking_model": {
                "name": chatbot.config['reranking']['model_name'],
                "device": chatbot.config['reranking']['device']
            },
            "intent_classifier": {
                "provider": chatbot.config['intent_classifier']['provider'],
                "model": chatbot.config['intent_classifier']['model_name']
            },
            "main_llm": {
                "provider": chatbot.config['main_llm']['provider'],
                "model": chatbot.config['main_llm']['model_name']
            },
            "vector_store": {
                "type": chatbot.config['vector_store']['type'],
                "url": chatbot.config['vector_store']['url']
            },
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")


@router.post("/restart")
async def restart_system():
    """Restart system components (use with caution)."""
    try:
        # In a production environment, this would restart services
        # For now, just return a message
        return {
            "message": "System restart initiated",
            "note": "This is a placeholder - implement actual restart logic for production",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restarting system: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    lines: int = 100,
    level: str = "INFO"
):
    """Get system logs."""
    try:
        # This is a placeholder - implement actual log reading
        # In production, you'd read from log files or logging service
        
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "System running normally",
                "component": "api"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO", 
                "message": "Chatbot initialized successfully",
                "component": "chatbot"
            }
        ]
        
        return {
            "logs": logs[-lines:],
            "total_lines": len(logs),
            "level_filter": level,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")