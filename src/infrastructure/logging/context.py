import contextvars
import logging
from typing import Optional, Dict, Any
import uuid


# Context variables for request-scoped data
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'correlation_id', default=None
)
session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'session_id', default=None
)
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'user_id', default=None
)


class LoggingContext:
    """Context manager for logging context."""
    
    def __init__(
        self,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **extra_context
    ):
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        self.session_id = session_id
        self.user_id = user_id
        self.extra_context = extra_context
        self.tokens = {}
    
    def __enter__(self):
        """Enter context."""
        self.tokens['correlation_id'] = correlation_id_var.set(self.correlation_id)
        
        if self.session_id:
            self.tokens['session_id'] = session_id_var.set(self.session_id)
        
        if self.user_id:
            self.tokens['user_id'] = user_id_var.set(self.user_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        for var_name, token in self.tokens.items():
            if var_name == 'correlation_id':
                correlation_id_var.reset(token)
            elif var_name == 'session_id':
                session_id_var.reset(token)
            elif var_name == 'user_id':
                user_id_var.reset(token)


class ContextualLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information."""
    
    def process(self, msg, kwargs):
        """Process log message with context."""
        # Get context variables
        extra = kwargs.get('extra', {})
        
        # Add correlation ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            extra['correlation_id'] = correlation_id
        
        # Add session ID
        session_id = session_id_var.get()
        if session_id:
            extra['session_id'] = session_id
        
        # Add user ID
        user_id = user_id_var.get()
        if user_id:
            extra['user_id'] = user_id
        
        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(name: str) -> ContextualLoggerAdapter:
    """Get logger with contextual information."""
    logger = logging.getLogger(name)
    return ContextualLoggerAdapter(logger, {})


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id_var.get()


def get_session_id() -> Optional[str]:
    """Get current session ID."""
    return session_id_var.get()


def get_user_id() -> Optional[str]:
    """Get current user ID."""
    return user_id_var.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)


def set_session_id(session_id: str) -> None:
    """Set session ID for current context."""
    session_id_var.set(session_id)


def set_user_id(user_id: str) -> None:
    """Set user ID for current context."""
    user_id_var.set(user_id)