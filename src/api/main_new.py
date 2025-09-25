from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.application.config import settings
from src.application.dependencies import initialize_dependencies, cleanup_dependencies, get_container
from src.infrastructure.logging.config import LoggingConfig
from src.infrastructure.logging.middleware import logging_middleware
from src.infrastructure.logging.context import get_logger

from src.api.routers_new import chat, documents, sessions, system, templates

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    try:
        # Setup logging
        LoggingConfig.setup_logging(
            log_level=settings.log_level,
            log_format=settings.log_format,
            log_dir=settings.log_dir,
            enable_console=settings.enable_console_logging,
            enable_file=settings.enable_file_logging,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count
        )
        
        logger.info("API application starting up")
        
        # Initialize dependencies
        await initialize_dependencies()
        
        logger.info("API application startup completed")
        
        yield
        
    except Exception as e:
        logger.error(
            "API application startup failed",
            extra={"error": str(e)},
            exc_info=True
        )
        raise
    
    finally:
        # Cleanup
        logger.info("API application shutting down")
        await cleanup_dependencies()
        logger.info("API application shutdown completed")


# Create FastAPI app
app = FastAPI(
    title="Vietnamese Business Registration RAG Chatbot API",
    description="API for RAG chatbot specialized in Vietnamese business registration consulting",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(logging_middleware)

# Include routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(sessions.router)
app.include_router(system.router)
app.include_router(templates.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        container = get_container()
        
        # Basic health check
        metrics_service = container.get_metrics_service()
        await metrics_service.increment_counter("health_check.requests")
        
        return {
            "status": "healthy",
            "version": "2.0.0",
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Vietnamese Business Registration RAG Chatbot API",
        "version": "2.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )