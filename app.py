#!/usr/bin/env python3
"""
Main application entry point for Render deployment.
"""
import sys
import os

# Add the institutional_ai_trade_engine directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'institutional_ai_trade_engine'))

# Import the FastAPI app
from src.api.server import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
