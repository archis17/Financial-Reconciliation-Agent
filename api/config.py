"""
Configuration management for the API.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "Financial Reconciliation API"
    api_version: str = "1.0.0"
    api_docs_url: str = "/api/docs"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # File Upload
    max_upload_size_mb: int = 50
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # LLM Configuration
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 500
    
    # Redis (optional)
    redis_url: str = ""
    
    # Cache
    cache_ttl: int = 3600
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env (like DATABASE_URL)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()

