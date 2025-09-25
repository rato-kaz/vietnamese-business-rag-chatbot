import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime


class LoggingConfig:
    """Centralized logging configuration."""
    
    @staticmethod
    def setup_logging(
        log_level: str = "INFO",
        log_format: str = "structured",
        log_dir: str = "logs",
        enable_console: bool = True,
        enable_file: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> None:
        """Setup comprehensive logging configuration."""
        
        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Define formatters
        formatters = {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "structured": {
                "()": "src.infrastructure.logging.formatters.StructuredFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            }
        }
        
        # Define handlers
        handlers = {}
        
        if enable_console:
            handlers["console"] = {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple" if log_format != "structured" else "structured",
                "stream": "ext://sys.stdout"
            }
        
        if enable_file:
            # Application logs
            handlers["file_app"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed" if log_format != "structured" else "structured",
                "filename": str(log_path / "app.log"),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8"
            }
            
            # Error logs
            handlers["file_error"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed" if log_format != "structured" else "structured",
                "filename": str(log_path / "error.log"),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8"
            }
            
            # API access logs
            handlers["file_api"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filename": str(log_path / "api.log"),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8"
            }
            
            # Chat interaction logs
            handlers["file_chat"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filename": str(log_path / "chat.log"),
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8"
            }
        
        # Define loggers
        loggers = {
            # Root logger
            "": {
                "level": log_level,
                "handlers": list(handlers.keys())
            },
            
            # API loggers
            "src.api": {
                "level": log_level,
                "handlers": ["file_api"] if enable_file else [],
                "propagate": True
            },
            
            # Chat loggers
            "src.core.use_cases.chat_use_case": {
                "level": log_level,
                "handlers": ["file_chat"] if enable_file else [],
                "propagate": True
            },
            
            # Infrastructure loggers
            "src.infrastructure": {
                "level": log_level,
                "handlers": list(handlers.keys()),
                "propagate": False
            },
            
            # External library loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["file_api"] if enable_file else ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["file_api"] if enable_file else ["console"],
                "propagate": False
            },
            "weaviate": {
                "level": "WARNING",
                "handlers": list(handlers.keys()),
                "propagate": False
            }
        }
        
        # Logging configuration
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": loggers
        }
        
        # Apply configuration
        logging.config.dictConfig(config)
        
        # Log initial message
        logger = logging.getLogger(__name__)
        logger.info(
            "Logging configured",
            extra={
                "log_level": log_level,
                "log_format": log_format,
                "log_dir": log_dir,
                "enable_console": enable_console,
                "enable_file": enable_file
            }
        )


def get_correlation_id() -> str:
    """Get correlation ID for request tracing."""
    import uuid
    return str(uuid.uuid4())[:8]


def setup_request_logging():
    """Setup request-specific logging context."""
    # This will be used by middleware to add correlation IDs
    pass