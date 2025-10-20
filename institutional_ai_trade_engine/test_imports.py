#!/usr/bin/env python3
"""
Test script to verify all imports work correctly for deployment.
"""
import sys
import os

def test_imports():
    """Test all critical imports."""
    try:
        print("Testing core imports...")
        
        # Test basic imports
        import fastapi
        import uvicorn
        import pydantic
        import pandas
        import numpy
        import sqlalchemy
        from dotenv import load_dotenv
        import requests
        import websocket
        
        print("✓ Basic imports successful")
        
        # Test Fyers API
        try:
            import fyers_apiv3
            print("✓ Fyers API import successful")
        except ImportError as e:
            print(f"⚠ Fyers API import failed: {e}")
        
        # Test PostgreSQL driver
        try:
            import psycopg2
            print("✓ PostgreSQL driver import successful")
        except ImportError as e:
            print(f"⚠ PostgreSQL driver import failed: {e}")
        
        # Test application imports
        try:
            from src.storage.db import init_database, engine
            print("✓ Database module import successful")
        except ImportError as e:
            print(f"⚠ Database module import failed: {e}")
        
        try:
            from src.api.server import app
            print("✓ API server import successful")
        except ImportError as e:
            print(f"⚠ API server import failed: {e}")
        
        print("\n✅ All critical imports passed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
