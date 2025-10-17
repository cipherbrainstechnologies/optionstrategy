#!/usr/bin/env python3
"""
Test script to verify the trading engine setup.
"""
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test all module imports."""
    print("🧪 Testing module imports...")
    
    try:
        # Core modules
        from core.config import Config
        from core.risk import size_position
        from core.scheduler import run as run_scheduler
        print("✅ Core modules imported successfully")
        
        # Data modules
        from data.angel_client import AngelClient
        from data.indicators import compute
        from data.fetch import DataFetcher
        from data.index_watch import monitor
        print("✅ Data modules imported successfully")
        
        # Strategy modules
        from strategy.three_week_inside import detect_3wi
        from strategy.filters import filters_ok
        print("✅ Strategy modules imported successfully")
        
        # Execution modules
        from exec.scanner import run as run_scanner
        from exec.tracker import run as run_tracker
        from exec.near_breakout import run as run_near_breakout
        from exec.eod_report import run as run_eod_report
        print("✅ Execution modules imported successfully")
        
        # Alert modules
        from alerts.telegram import send_alert
        from alerts.sheets import update_master_sheet
        print("✅ Alert modules imported successfully")
        
        # Storage modules
        from storage.db import init_database
        from storage.ledger import log_trade
        print("✅ Storage modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    print("\n🔧 Testing configuration...")
    
    try:
        from core.config import Config
        
        # Test basic config
        print(f"   Portfolio Capital: ₹{Config.PORTFOLIO_CAPITAL:,}")
        print(f"   Risk Percentage: {Config.RISK_PCT}%")
        print(f"   Timezone: {Config.TIMEZONE}")
        print(f"   Paper Mode: {Config.PAPER_MODE}")
        
        # Test validation (will fail without credentials)
        try:
            Config.validate()
            print("✅ Configuration validation passed")
        except ValueError as e:
            print(f"⚠️  Configuration validation failed (expected): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_database():
    """Test database operations."""
    print("\n💾 Testing database...")
    
    try:
        from storage.db import init_database, get_db_session
        from sqlalchemy import text
        
        # Initialize database
        init_database()
        print("✅ Database initialized")
        
        # Test connection
        db = get_db_session()
        try:
            result = db.execute(text("SELECT COUNT(*) FROM instruments")).fetchone()
            print(f"✅ Database connection successful (instruments: {result[0]})")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_indicators():
    """Test technical indicators."""
    print("\n📊 Testing technical indicators...")
    
    try:
        import pandas as pd
        import numpy as np
        from data.indicators import compute
        
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        sample_data = pd.DataFrame({
            'open': 100 + np.random.randn(100).cumsum(),
            'high': 105 + np.random.randn(100).cumsum(),
            'low': 95 + np.random.randn(100).cumsum(),
            'close': 100 + np.random.randn(100).cumsum(),
            'volume': 1000000 + np.random.randint(-100000, 100000, 100)
        })
        
        # Compute indicators
        result = compute(sample_data)
        
        # Check if indicators were added
        expected_indicators = ['RSI', 'WMA20', 'WMA50', 'WMA100', 'ATR', 'ATR_PCT', 'VOL_X20D']
        missing = [ind for ind in expected_indicators if ind not in result.columns]
        
        if missing:
            print(f"❌ Missing indicators: {missing}")
            return False
        
        print("✅ Technical indicators computed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Indicators error: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Institutional AI Trade Engine Setup\n")
    
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Technical Indicators", test_indicators)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! The trading engine is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())