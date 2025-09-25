from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
import logging
from typing import Callable
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next: Callable):
    """Middleware for request/response logging."""
    # Generate request ID
    request_id = str(uuid.uuid4())[:8]
    
    # Log request
    start_time = time.time()
    logger.info(f"[{request_id}] {request.method} {request.url}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"[{request_id}] Response: {response.status_code} - {process_time:.4f}s")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(f"[{request_id}] Error: {str(e)} - {process_time:.4f}s")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "detail": str(e)
            },
            headers={
                "X-Request-ID": request_id,
                "X-Process-Time": str(process_time)
            }
        )


async def rate_limiting_middleware(request: Request, call_next: Callable):
    """Simple rate limiting middleware."""
    # This is a basic implementation - for production use Redis or similar
    # For now, we'll just add headers for rate limiting info
    
    response = await call_next(request)
    
    # Add rate limiting headers
    response.headers["X-RateLimit-Limit"] = "100"
    response.headers["X-RateLimit-Remaining"] = "99"
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 3600)
    
    return response


class ErrorHandlerMiddleware:
    """Custom error handling middleware."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            # Log the error
            logger.error(f"Unhandled error: {str(e)}")
            
            # Send error response
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred"
                }
            )
            await response(scope, receive, send)