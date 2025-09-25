from fastapi import APIRouter, HTTPException
from datetime import datetime
import psutil
import os

from src.application.dependencies import get_container
from src.application.config import settings
from src.infrastructure.logging.context import get_logger
from src.api.models import SystemStatsResponse, HealthResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Test all major components
        health_status = "healthy"
        
        container = get_container()
        
        # Test metrics service
        try:
            metrics_service = container.get_metrics_service()
            await metrics_service.increment_counter("health_check.requests")
        except Exception as e:
            logger.warning(f"Metrics service unhealthy: {e}")
            health_status = "degraded"
        
        # Test document repository
        try:
            document_repo = container.get_document_repo()
            await document_repo.get_stats()
        except Exception as e:
            logger.warning(f"Document repository unhealthy: {e}")
            health_status = "degraded"
        
        return HealthResponse(
            status=health_status,
            timestamp=datetime.now(),
            version="2.0.0"
        )
        
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version="2.0.0"
        )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats():
    """Get comprehensive system statistics."""
    try:
        container = get_container()
        
        # Get conversation stats
        conversation_repo = container.get_conversation_repo()
        conv_stats = conversation_repo.get_stats()
        
        # Get document stats
        document_repo = container.get_document_repo()
        doc_stats = await document_repo.get_stats()
        
        # Get template stats
        template_repo = container.get_template_repo()
        templates = await template_repo.list_templates()
        
        # Get system resource usage
        memory_info = psutil.virtual_memory()
        memory_usage = f"{memory_info.percent}% ({memory_info.used // (1024**3)}GB / {memory_info.total // (1024**3)}GB)"
        
        return SystemStatsResponse(
            active_sessions=conv_stats.get("total_conversations", 0),
            total_documents=doc_stats.get("total_chunks", 0),
            available_templates=len(templates),
            system_uptime="N/A",  # Implement proper uptime tracking
            memory_usage=memory_usage
        )
        
    except Exception as e:
        logger.error(
            "Failed to get system stats",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system stats: {str(e)}"
        )


@router.get("/info")
async def get_system_info():
    """Get detailed system information."""
    try:
        # System info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        # Container info
        container = get_container()
        
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
            "application": {
                "environment": settings.environment,
                "debug": settings.debug,
                "log_level": settings.log_level,
                "models": {
                    "embedding": settings.embedding_model,
                    "reranking": settings.rerank_model,
                    "intent": settings.intent_model,
                    "main_llm": settings.main_llm_model
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
        logger.error(
            "Failed to get system info",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting system info: {str(e)}"
        )


@router.get("/metrics")
async def get_metrics():
    """Get application metrics."""
    try:
        container = get_container()
        metrics_service = container.get_metrics_service()
        
        # Get metrics summary
        metrics_summary = metrics_service.get_metrics_summary()
        
        return {
            "metrics": metrics_summary,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(
            "Failed to get metrics",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metrics: {str(e)}"
        )


@router.get("/cache")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        container = get_container()
        cache_service = container.get_cache_service()
        
        # Get cache stats
        cache_stats = cache_service.get_stats()
        
        return {
            "cache_stats": cache_stats,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(
            "Failed to get cache stats",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cache stats: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache():
    """Clear application cache."""
    try:
        container = get_container()
        cache_service = container.get_cache_service()
        
        await cache_service.clear()
        
        logger.info("Cache cleared successfully")
        
        return {
            "message": "Cache cleared successfully",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(
            "Failed to clear cache",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing cache: {str(e)}"
        )