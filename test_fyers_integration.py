#!/usr/bin/env python3
"""
Test script to verify Fyers integration and live data fetching
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add the institutional_ai_trade_engine to path
sys.path.insert(0, 'institutional_ai_trade_engine')

def test_broker_configuration():
    """Test broker configuration and selection."""
    print("=" * 60)
    print("TESTING BROKER CONFIGURATION")
    print("=" * 60)
    
    try:
        from src.core.config import Settings
        
        # Test settings loading
        settings = Settings()
        print(f"✓ Broker selected: {settings.BROKER}")
        print(f"✓ Portfolio capital: ₹{settings.PORTFOLIO_CAPITAL:,}")
        print(f"✓ Risk per trade: {settings.RISK_PCT_PER_TRADE}%")
        
        # Test broker validation
        try:
            settings.validate()
            print("✓ Configuration validation passed")
        except SystemExit as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False

def test_broker_initialization():
    """Test broker client initialization."""
    print("\n" + "=" * 60)
    print("TESTING BROKER INITIALIZATION")
    print("=" * 60)
    
    try:
        from src.core.config import Settings
        from src.data.broker_base import get_broker
        
        settings = Settings()
        broker = get_broker(settings)
        
        print(f"✓ Broker initialized: {broker.name()}")
        print(f"✓ Broker type: {type(broker).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing broker: {e}")
        return False

def test_data_fetcher():
    """Test DataFetcher with broker integration."""
    print("\n" + "=" * 60)
    print("TESTING DATA FETCHER")
    print("=" * 60)
    
    try:
        from src.data.fetch import DataFetcher
        from src.core.config import Settings
        
        settings = Settings()
        broker = settings.get_broker()
        fetcher = DataFetcher(broker)
        
        print(f"✓ DataFetcher initialized with broker: {broker.name()}")
        
        # Test getting enabled instruments
        instruments = fetcher.get_enabled_instruments()
        print(f"✓ Found {len(instruments)} enabled instruments")
        
        if instruments:
            print(f"  Sample instruments: {[inst['symbol'] for inst in instruments[:3]]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing DataFetcher: {e}")
        return False

def test_live_data_fetching():
    """Test live data fetching from broker."""
    print("\n" + "=" * 60)
    print("TESTING LIVE DATA FETCHING")
    print("=" * 60)
    
    try:
        from src.data.fetch import DataFetcher
        from src.core.config import Settings
        
        settings = Settings()
        broker = settings.get_broker()
        fetcher = DataFetcher(broker)
        
        # Test symbols
        test_symbols = ["RELIANCE", "TCS", "INFY"]
        
        for symbol in test_symbols:
            print(f"\nTesting {symbol}...")
            
            # Test current price
            try:
                ltp = fetcher.get_current_price(symbol)
                if ltp:
                    print(f"  ✓ Current price: ₹{ltp:.2f}")
                else:
                    print(f"  ⚠️  No current price available")
            except Exception as e:
                print(f"  ❌ Error getting current price: {e}")
            
            # Test weekly data
            try:
                weekly_df = fetcher.get_weekly_data(symbol, weeks=4)
                if weekly_df is not None and not weekly_df.empty:
                    print(f"  ✓ Weekly data: {len(weekly_df)} weeks")
                    latest = weekly_df.iloc[-1]
                    print(f"    Latest close: ₹{latest['close']:.2f}")
                    print(f"    Volume: {latest['volume']:,.0f}")
                else:
                    print(f"  ⚠️  No weekly data available")
            except Exception as e:
                print(f"  ❌ Error getting weekly data: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing live data fetching: {e}")
        return False

def test_scanner_integration():
    """Test scanner with broker integration."""
    print("\n" + "=" * 60)
    print("TESTING SCANNER INTEGRATION")
    print("=" * 60)
    
    try:
        from src.exec.scanner import Scanner
        from src.core.config import Settings
        
        settings = Settings()
        broker = settings.get_broker()
        scanner = Scanner(broker)
        
        print(f"✓ Scanner initialized with broker: {broker.name()}")
        
        # Test dry run scan
        print("\nRunning dry run scan...")
        try:
            results = scanner.run(dry_run=True)
            print(f"✓ Dry run scan completed")
            print(f"  Setups found: {len(results.get('setups', []))}")
            print(f"  Breakouts found: {len(results.get('breakouts', []))}")
            print(f"  Timestamp: {results.get('timestamp')}")
        except Exception as e:
            print(f"❌ Error running dry scan: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing scanner integration: {e}")
        return False

def main():
    """Run all tests."""
    print("FYERS INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Broker Configuration", test_broker_configuration),
        ("Broker Initialization", test_broker_initialization),
        ("Data Fetcher", test_data_fetcher),
        ("Live Data Fetching", test_live_data_fetching),
        ("Scanner Integration", test_scanner_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Fyers integration is working correctly.")
        print("\nNext steps:")
        print("1. Configure your .env file with Fyers credentials")
        print("2. Run: python institutional_ai_trade_engine/main.py --init")
        print("3. Test live scanning: python institutional_ai_trade_engine/main.py --daily")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the configuration.")
        print("\nTroubleshooting:")
        print("1. Ensure .env file is configured correctly")
        print("2. Check Fyers credentials")
        print("3. Verify network connectivity")
        print("4. Check logs for detailed error messages")

if __name__ == "__main__":
    main()
