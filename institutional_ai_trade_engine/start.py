#!/usr/bin/env python3
"""
Start script for Render deployment.
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "src.api.server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
