import logging
import json
import traceback
from datetime import datetime
from typing import Dict, Any


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add thread/process info
        if record.thread:
            log_data["thread_id"] = record.thread
            log_data["thread_name"] = record.threadName
        
        if record.process:
            log_data["process_id"] = record.process
            log_data["process_name"] = record.processName
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from LoggerAdapter or extra parameter
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'lineno', 'funcName', 'created', 
                              'msecs', 'relativeCreated', 'thread', 'threadName', 
                              'processName', 'process', 'exc_info', 'exc_text', 
                              'stack_info', 'getMessage'}:
                    try:
                        # Only add JSON serializable values
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        return json.dumps(log_data, ensure_ascii=False, separators=(',', ':'))


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        # Add color
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # Format message
        formatted = super().format(record)
        
        return formatted


class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records."""
    
    def __init__(self, context_provider=None):
        super().__init__()
        self.context_provider = context_provider
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record."""
        
        # Add correlation ID if available
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id and self.context_provider:
            correlation_id = self.context_provider.get_correlation_id()
        
        if correlation_id:
            record.correlation_id = correlation_id
        
        # Add session ID if available
        session_id = getattr(record, 'session_id', None)
        if not session_id and self.context_provider:
            session_id = self.context_provider.get_session_id()
        
        if session_id:
            record.session_id = session_id
        
        return True


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_execution_time(
        self, 
        operation: str, 
        execution_time: float,
        **kwargs
    ) -> None:
        """Log execution time for an operation."""
        self.logger.info(
            f"Performance metric: {operation}",
            extra={
                "operation": operation,
                "execution_time": execution_time,
                "unit": "seconds",
                **kwargs
            }
        )
    
    def log_memory_usage(
        self, 
        operation: str, 
        memory_usage: float,
        **kwargs
    ) -> None:
        """Log memory usage for an operation."""
        self.logger.info(
            f"Memory usage: {operation}",
            extra={
                "operation": operation,
                "memory_usage": memory_usage,
                "unit": "MB",
                **kwargs
            }
        )


class AuditLogger:
    """Logger for audit events."""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str,
        **kwargs
    ) -> None:
        """Log user action for audit purposes."""
        self.logger.info(
            f"User action: {action}",
            extra={
                "event_type": "user_action",
                "user_id": user_id,
                "action": action,
                "resource": resource,
                "result": result,
                **kwargs
            }
        )
    
    def log_system_event(
        self,
        event_type: str,
        description: str,
        **kwargs
    ) -> None:
        """Log system event for audit purposes."""
        self.logger.info(
            f"System event: {event_type}",
            extra={
                "event_type": "system_event",
                "description": description,
                **kwargs
            }
        )