"""
Metrics endpoint for Prometheus.
"""

from fastapi import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

