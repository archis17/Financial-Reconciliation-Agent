#!/usr/bin/env python3
"""
Run FastAPI server.

Usage:
    python api/run.py
    or
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import uvicorn
from api.main import app

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    if workers > 1:
        # Multi-worker mode (production)
        uvicorn.run(
            "api.main:app",
            host=host,
            port=port,
            workers=workers,
            reload=False
        )
    else:
        # Single worker mode (development)
    uvicorn.run(
        app,
            host=host,
            port=port,
            reload=reload
    )

