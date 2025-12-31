"""
Custom middleware for the API.
"""

import os
import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import ReconciliationException, RateLimitError

logger = logging.getLogger(__name__)

# Get CORS origins for error responses
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


def add_cors_headers(response: Response, request: Request) -> Response:
    """Add CORS headers to a response."""
    origin = request.headers.get("origin")
    if origin and origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    elif "*" in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions and converting them to proper HTTP responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle exceptions."""
        try:
            response = await call_next(request)
            return response
        except ReconciliationException as e:
            logger.error(f"Reconciliation error: {e.message}", extra={
                "error_code": e.error_code,
                "status_code": e.status_code,
                "details": e.details
            })
            response = JSONResponse(
                status_code=e.status_code,
                content=e.to_dict()
            )
            return add_cors_headers(response, request)
        except HTTPException as e:
            # Re-raise HTTPException as-is
            raise e
        except Exception as e:
            error_message = str(e)
            logger.error(f"Unexpected error: {error_message}", exc_info=True)
            response = JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {
                        "error": error_message
                    }
                }
            )
            return add_cors_headers(response, request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}  # In production, use Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/health", "/"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries (simple cleanup)
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip]
                if current_time - t < 60
            ]
        
        # Check rate limit
        if client_ip in self.request_counts:
            if len(self.request_counts[client_ip]) >= self.requests_per_minute:
                retry_after = 60 - (current_time - self.request_counts[client_ip][0])
                raise RateLimitError(retry_after=int(retry_after))
            self.request_counts[client_ip].append(current_time)
        else:
            self.request_counts[client_ip] = [current_time]
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.request_counts.get(client_ip, []))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response

