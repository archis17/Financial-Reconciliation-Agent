#!/usr/bin/env python3
"""
Run FastAPI server.

Usage:
    python api/run.py
    or
    uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
"""

import uvicorn
from api.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )

