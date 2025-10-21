#!/usr/bin/env python3
"""
Test script to run the scanner locally with MockExchange (no authentication needed).
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Override LOG_PATH to fix the directory issue
os.environ["LOG_PATH"] = "./data/"
# Use MockExchange for testing
os.environ["BROKER"] = "MOCK"

# Import and test scanner
try:
    from src.exec.scanner import run
    
    print("Testing scanner locally with MockExchange...")
    print("=" * 50)
    
    # Run scanner in dry run mode
    result = run(dry_run=True)
    
    print("Scanner completed successfully!")
    print(f"Total instruments: {result.get('total_instruments', 0)}")
    print(f"Scanned instruments: {len(result.get('scanned_instruments', []))}")
    print(f"Valid setups: {len(result.get('valid_setups', []))}")
    print(f"Breakouts: {len(result.get('breakouts', []))}")
    print(f"Errors: {len(result.get('errors', []))}")
    
    if result.get('errors'):
        print("\nErrors found:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result.get('scanned_instruments'):
        print(f"\nFirst few scanned instruments:")
        for i, instrument in enumerate(result['scanned_instruments'][:5]):
            print(f"  {i+1}. {instrument.get('symbol', 'Unknown')} - {instrument.get('current_price', 0):.2f}")
    
    print("\n" + "=" * 50)
    print("Local test completed!")
    
except Exception as e:
    print(f"Scanner test failed: {e}")
    import traceback
    traceback.print_exc()
