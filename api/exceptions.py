"""
Custom exception classes for the API.
"""

from typing import Optional, Dict, Any


class ReconciliationException(Exception):
    """Base exception for reconciliation errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "RECONCILIATION_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize reconciliation exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(ReconciliationException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, **(details or {})}
        )


class FileProcessingError(ReconciliationException):
    """Exception for file processing errors."""
    
    def __init__(self, message: str, filename: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            status_code=422,
            details={"filename": filename, **(details or {})}
        )


class MatchingError(ReconciliationException):
    """Exception for matching errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MATCHING_ERROR",
            status_code=500,
            details=details or {}
        )


class LLMServiceError(ReconciliationException):
    """Exception for LLM service errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="LLM_SERVICE_ERROR",
            status_code=503,
            details=details or {}
        )


class ResourceNotFoundError(ReconciliationException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class RateLimitError(ReconciliationException):
    """Exception for rate limiting errors."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details
        )


class ServiceUnavailableError(ReconciliationException):
    """Exception for service unavailable errors."""
    
    def __init__(self, message: str, service: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service} if service else {}
        )

