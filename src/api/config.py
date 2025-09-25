import os
from typing import Optional
from pydantic import BaseSettings


class APISettings(BaseSettings):
    """API configuration settings."""
    
    # API Settings
    api_title: str = "Vietnamese Business Registration RAG Chatbot API"
    api_description: str = "API for RAG chatbot specialized in Vietnamese business registration consulting"
    api_version: str = "1.0.0"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Security Settings
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # CORS Settings
    cors_origins: list = ["*"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # seconds
    
    # Session Management
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 1000
    
    # Database Settings (if needed in future)
    database_url: Optional[str] = None
    
    # Redis Settings (for session storage/rate limiting)
    redis_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File Upload
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: list = [".docx", ".pdf", ".txt"]
    upload_dir: str = "data/documents/uploaded"
    
    # Background Tasks
    max_background_tasks: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = APISettings()