"""
Prometheus metrics collection for the API.
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time

# Reconciliation metrics
reconciliation_total = Counter(
    'reconciliation_total',
    'Total number of reconciliations',
    ['status']  # status: completed, failed, processing
)

reconciliation_duration_seconds = Histogram(
    'reconciliation_duration_seconds',
    'Reconciliation processing time in seconds',
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0]
)

reconciliation_success_rate = Gauge(
    'reconciliation_success_rate',
    'Success rate of reconciliations (0-1)'
)

# API metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# User activity metrics
active_users = Gauge(
    'active_users',
    'Number of active users'
)

user_logins_total = Counter(
    'user_logins_total',
    'Total number of user logins'
)

# LLM metrics
llm_calls_total = Counter(
    'llm_calls_total',
    'Total number of LLM API calls',
    ['status']  # status: success, error
)

llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total number of LLM tokens used'
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect API metrics."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract endpoint (simplified)
        endpoint = request.url.path.split('?')[0]
        if endpoint.startswith('/api/'):
            endpoint = endpoint.replace('/api/', '')
        
        # Record metrics
        api_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        api_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response


def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest()


def record_reconciliation(status: str, duration: float):
    """Record reconciliation metrics."""
    reconciliation_total.labels(status=status).inc()
    reconciliation_duration_seconds.observe(duration)


def record_llm_call(status: str, tokens: int = 0):
    """Record LLM call metrics."""
    llm_calls_total.labels(status=status).inc()
    if tokens > 0:
        llm_tokens_total.inc(tokens)

