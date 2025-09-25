import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

from .context import LoggingContext, set_correlation_id, set_session_id, get_logger

logger = get_logger(__name__)


class LoggingMiddleware:
    """Middleware for comprehensive request/response logging."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request with logging."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())[:8]
        
        # Extract request info
        request = Request(scope, receive)
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Extract session ID from headers or query params
        session_id = (
            request.headers.get("x-session-id") or 
            request.query_params.get("session_id")
        )
        
        start_time = time.time()
        
        # Set context
        with LoggingContext(
            correlation_id=correlation_id,
            session_id=session_id
        ):
            # Log request
            logger.info(
                "Request started",
                extra={
                    "event_type": "request_start",
                    "method": method,
                    "url": url,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "content_length": request.headers.get("content-length"),
                    "content_type": request.headers.get("content-type")
                }
            )
            
            # Process request
            status_code = 500
            response_size = 0
            error_info = None
            
            try:
                # Create response wrapper to capture info
                async def send_wrapper(message):
                    nonlocal status_code, response_size
                    
                    if message["type"] == "http.response.start":
                        status_code = message["status"]
                        # Add correlation ID to response headers
                        headers = list(message.get("headers", []))
                        headers.append([b"x-correlation-id", correlation_id.encode()])
                        message["headers"] = headers
                    
                    elif message["type"] == "http.response.body":
                        body = message.get("body", b"")
                        response_size += len(body)
                    
                    await send(message)
                
                await self.app(scope, receive, send_wrapper)
                
            except Exception as e:
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                
                logger.error(
                    "Request failed with exception",
                    extra={
                        "event_type": "request_error",
                        **error_info
                    },
                    exc_info=True
                )
                
                # Send error response
                error_response = JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "correlation_id": correlation_id
                    },
                    headers={"x-correlation-id": correlation_id}
                )
                await error_response(scope, receive, send)
                status_code = 500
            
            finally:
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Log response
                log_level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
                
                logger.log(
                    log_level,
                    "Request completed",
                    extra={
                        "event_type": "request_end",
                        "method": method,
                        "url": url,
                        "status_code": status_code,
                        "processing_time": processing_time,
                        "response_size": response_size,
                        "client_ip": client_ip,
                        **({} if not error_info else error_info)
                    }
                )


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Simple logging middleware function."""
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())[:8]
    
    # Extract session ID
    session_id = (
        request.headers.get("x-session-id") or 
        request.query_params.get("session_id")
    )
    
    start_time = time.time()
    
    # Set context
    set_correlation_id(correlation_id)
    if session_id:
        set_session_id(session_id)
    
    # Log request
    logger.info(
        "Request started",
        extra={
            "event_type": "request_start",
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["x-correlation-id"] = correlation_id
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log response
        log_level = (
            logging.ERROR if response.status_code >= 500 
            else logging.WARNING if response.status_code >= 400 
            else logging.INFO
        )
        
        logger.log(
            log_level,
            "Request completed",
            extra={
                "event_type": "request_end",
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "processing_time": processing_time
            }
        )
        
        return response
        
    except Exception as e:
        # Log error
        processing_time = time.time() - start_time
        
        logger.error(
            "Request failed",
            extra={
                "event_type": "request_error",
                "method": request.method,
                "url": str(request.url),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "processing_time": processing_time
            },
            exc_info=True
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "correlation_id": correlation_id
            },
            headers={"x-correlation-id": correlation_id}
        )