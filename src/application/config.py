import os
from typing import Optional
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class ApplicationSettings(BaseSettings):
    """Application configuration settings."""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # API Keys
    groq_api_key: str
    gemini_api_key: str
    
    # Weaviate Configuration
    weaviate_url: str = "http://localhost:8080"
    weaviate_collection_name: str = "LegalDocuments"
    
    # Model Configuration
    embedding_model: str = "bkai-foundation-models/vietnamese-bi-encoder"
    rerank_model: str = "cross-encoder/multilingual-MiniLM-L-12-v2"
    intent_model: str = "llama3-8b-8192"
    main_llm_model: str = "gemini-2.0-flash-exp"
    device: str = "cuda"
    
    # LLM Parameters
    intent_temperature: float = 0.1
    main_llm_temperature: float = 0.7
    max_tokens: int = 2048
    
    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Retrieval Settings
    retrieval_top_k: int = 10
    rerank_top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Conversation Settings
    conversation_timeout_minutes: int = 60
    max_conversation_history: int = 50
    
    # Cache Settings
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 10000
    
    # Metrics Settings
    metrics_retention_hours: int = 24
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "structured"
    log_dir: str = "logs"
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Directories
    documents_dir: str = "data/documents/core"
    templates_dir: str = "templates"
    upload_dir: str = "data/documents/uploaded"
    
    # Performance Settings
    max_workers: int = 4
    request_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = ApplicationSettings()