"""
FastAPI Application Module.

This module provides REST API endpoints for the Financial Reconciliation Agent.
"""

from .main import app, create_app
from .exceptions import (
    ReconciliationException,
    ValidationError,
    FileProcessingError,
    MatchingError,
    LLMServiceError,
    ResourceNotFoundError,
    RateLimitError,
    ServiceUnavailableError
)
from .middleware import (
    ErrorHandlingMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware
)
from .cache import CacheService, cache, cached
from .config import Settings, settings

__all__ = [
    "app",
    "create_app",
    "ReconciliationException",
    "ValidationError",
    "FileProcessingError",
    "MatchingError",
    "LLMServiceError",
    "ResourceNotFoundError",
    "RateLimitError",
    "ServiceUnavailableError",
    "ErrorHandlingMiddleware",
    "RequestLoggingMiddleware",
    "RateLimitMiddleware",
    "CacheService",
    "cache",
    "cached",
    "Settings",
    "settings"
]

