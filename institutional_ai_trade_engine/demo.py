#!/usr/bin/env python3
"""
Demonstration script for the Institutional AI Trade Engine.
"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def demo_3wi_detection():
    """Demonstrate 3WI pattern detection."""
    print("🔍 Demonstrating 3WI Pattern Detection")
    print("=" * 50)
    
    from strategy.three_week_inside import detect_3wi, calculate_breakout_strength
    from data.indicators import compute_weekly_indicators
    
    # Create realistic weekly data with a 3WI pattern
    np.random.seed(42)
    weeks = 52
    
    # Base trend
    trend = np.linspace(100, 120, weeks)
    noise = np.random.randn(weeks) * 2
    
    # Create a 3WI pattern around week 30-32
    close_prices = trend + noise
    close_prices[30] = 110  # Mother candle high
    close_prices[31] = 109  # Inside week 1
    close_prices[32] = 108  # Inside week 2
    close_prices[33] = 112  # Breakout
    
    weekly_data = pd.DataFrame({
        'open': close_prices - np.random.rand(weeks) * 2,
        'high': close_prices + np.random.rand(weeks) * 3,
        'low': close_prices - np.random.rand(weeks) * 3,
        'close': close_prices,
        'volume': 1000000 + np.random.randint(-100000, 100000, weeks)
    })
    
    # Add timestamps
    weekly_data['timestamp'] = pd.date_range('2023-01-01', periods=weeks, freq='W')
    
    # Compute indicators
    weekly_data = compute_weekly_indicators(weekly_data)
    
    # Detect 3WI patterns
    patterns = detect_3wi(weekly_data)
    
    print(f"📊 Analyzed {len(weekly_data)} weeks of data")
    print(f"🔍 Found {len(patterns)} 3WI patterns")
    
    if patterns:
        pattern = patterns[0]
        print(f"\n📈 Pattern Details:")
        print(f"   Mother High: ₹{pattern['mother_high']:.2f}")
        print(f"   Mother Low: ₹{pattern['mother_low']:.2f}")
        print(f"   Inside Weeks: {pattern['inside_weeks']}")
        print(f"   Week Start: {pattern['week_start']}")
        
        # Calculate breakout strength
        strength = calculate_breakout_strength(weekly_data, pattern)
        print(f"\n💪 Breakout Strength:")
        print(f"   Distance to High: {strength.get('distance_to_high_pct', 0):.2f}%")
        print(f"   Volume Ratio: {strength.get('volume_ratio', 0):.2f}x")
        print(f"   ATR %: {strength.get('atr_pct', 0):.2f}%")
    
    return len(patterns) > 0

def demo_technical_indicators():
    """Demonstrate technical indicators."""
    print("\n📊 Demonstrating Technical Indicators")
    print("=" * 50)
    
    from data.indicators import compute
    
    # Create sample data
    np.random.seed(42)
    days = 100
    
    # Create trending data
    trend = np.linspace(100, 120, days)
    noise = np.random.randn(days) * 1
    close_prices = trend + noise
    
    sample_data = pd.DataFrame({
        'open': close_prices - np.random.rand(days),
        'high': close_prices + np.random.rand(days) * 2,
        'low': close_prices - np.random.rand(days) * 2,
        'close': close_prices,
        'volume': 1000000 + np.random.randint(-100000, 100000, days)
    })
    
    # Compute indicators
    result = compute(sample_data)
    
    # Show latest values
    latest = result.iloc[-1]
    
    print(f"📈 Latest Technical Indicators:")
    print(f"   RSI: {latest['RSI']:.2f}")
    print(f"   WMA20: ₹{latest['WMA20']:.2f}")
    print(f"   WMA50: ₹{latest['WMA50']:.2f}")
    print(f"   WMA100: ₹{latest['WMA100']:.2f}")
    print(f"   ATR: ₹{latest['ATR']:.2f}")
    print(f"   ATR %: {latest['ATR_PCT']:.2f}%")
    print(f"   Volume Ratio: {latest['VOL_X20D']:.2f}x")
    
    return True

def demo_filters():
    """Demonstrate trading filters."""
    print("\n🔍 Demonstrating Trading Filters")
    print("=" * 50)
    
    from strategy.filters import filters_ok, get_filter_score
    
    # Create sample stock data
    sample_stock = pd.Series({
        'RSI': 65.5,
        'WMA20': 105.2,
        'WMA50': 103.8,
        'WMA100': 101.5,
        'VOL_X20D': 1.8,
        'ATR_PCT': 0.045,
        'close': 107.5
    })
    
    # Test filters
    passes_basic = filters_ok(sample_stock)
    filter_scores = get_filter_score(sample_stock)
    
    print(f"📊 Sample Stock Data:")
    print(f"   RSI: {sample_stock['RSI']:.1f}")
    print(f"   WMA20: ₹{sample_stock['WMA20']:.2f}")
    print(f"   WMA50: ₹{sample_stock['WMA50']:.2f}")
    print(f"   WMA100: ₹{sample_stock['WMA100']:.2f}")
    print(f"   Volume Ratio: {sample_stock['VOL_X20D']:.1f}x")
    print(f"   ATR %: {sample_stock['ATR_PCT']:.1f}%")
    
    print(f"\n✅ Basic Filters: {'PASS' if passes_basic else 'FAIL'}")
    print(f"📊 Filter Scores:")
    for key, value in filter_scores.items():
        if key != 'overall_score':
            print(f"   {key}: {'✅' if value else '❌'}")
    print(f"   Overall Score: {filter_scores['overall_score']:.1f}%")
    
    return passes_basic

def demo_risk_management():
    """Demonstrate risk management."""
    print("\n💰 Demonstrating Risk Management")
    print("=" * 50)
    
    from core.risk import size_position, calculate_targets, calculate_position_metrics
    
    # Sample parameters
    entry_price = 100.0
    stop_loss = 95.0
    capital = 400000
    risk_pct = 1.5
    plan = 1.0
    
    # Calculate position size
    qty, risk_amount = size_position(entry_price, stop_loss, capital, risk_pct, plan)
    
    # Calculate targets
    atr = 2.0
    t1, t2 = calculate_targets(entry_price, stop_loss, atr)
    
    # Calculate metrics
    current_price = 102.0
    metrics = calculate_position_metrics(entry_price, current_price, stop_loss, qty)
    
    print(f"📊 Position Parameters:")
    print(f"   Entry Price: ₹{entry_price:.2f}")
    print(f"   Stop Loss: ₹{stop_loss:.2f}")
    print(f"   Capital: ₹{capital:,}")
    print(f"   Risk %: {risk_pct}%")
    
    print(f"\n📦 Position Sizing:")
    print(f"   Quantity: {qty} shares")
    print(f"   Risk Amount: ₹{risk_amount:.2f}")
    print(f"   Position Value: ₹{entry_price * qty:,.2f}")
    
    print(f"\n🎯 Targets:")
    print(f"   T1: ₹{t1:.2f} (1.5R)")
    print(f"   T2: ₹{t2:.2f} (3R)")
    
    print(f"\n📈 Current Metrics:")
    print(f"   Current Price: ₹{current_price:.2f}")
    print(f"   Unrealized PnL: ₹{metrics['unrealized_pnl']:.2f}")
    print(f"   PnL %: {metrics['pnl_pct']:.2f}%")
    print(f"   Risk Amount: ₹{metrics['risk_amount']:.2f}")
    
    return True

def demo_database_operations():
    """Demonstrate database operations."""
    print("\n💾 Demonstrating Database Operations")
    print("=" * 50)
    
    from storage.db import get_db_session
    from storage.ledger import log_trade, get_performance_summary
    from sqlalchemy import text
    
    try:
        # Test database connection
        db = get_db_session()
        try:
            # Count instruments
            result = db.execute(text("SELECT COUNT(*) FROM instruments")).fetchone()
            print(f"📊 Database Status:")
            print(f"   Instruments: {result[0]}")
            
            # Test ledger operations
            print(f"\n📝 Testing Ledger Operations:")
            
            # Log a sample trade
            log_trade(
                symbol="RELIANCE",
                opened_ts="2024-01-15T09:30:00",
                closed_ts="2024-01-20T15:30:00",
                pnl=1500.0,
                rr=1.5,
                tag="3WI_SUCCESS"
            )
            print("   ✅ Sample trade logged")
            
            # Get performance summary
            performance = get_performance_summary(days=30)
            print(f"   📊 Performance Summary:")
            print(f"      Total Trades: {performance['total_trades']}")
            print(f"      Win Rate: {performance['win_rate']:.1f}%")
            print(f"      Avg PnL: ₹{performance['avg_pnl']:.2f}")
            print(f"      Avg R:R: {performance['avg_rr']:.2f}")
            
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main demonstration function."""
    print("🚀 Institutional AI Trade Engine - Demonstration")
    print("=" * 60)
    print("This demo showcases the key features of the trading engine.\n")
    
    demos = [
        ("3WI Pattern Detection", demo_3wi_detection),
        ("Technical Indicators", demo_technical_indicators),
        ("Trading Filters", demo_filters),
        ("Risk Management", demo_risk_management),
        ("Database Operations", demo_database_operations)
    ]
    
    passed = 0
    total = len(demos)
    
    for demo_name, demo_func in demos:
        try:
            if demo_func():
                passed += 1
                print(f"✅ {demo_name} completed successfully")
            else:
                print(f"❌ {demo_name} failed")
        except Exception as e:
            print(f"❌ {demo_name} error: {e}")
    
    print(f"\n{'='*60}")
    print(f"DEMO SUMMARY: {passed}/{total} demonstrations completed")
    print('='*60)
    
    if passed == total:
        print("🎉 All demonstrations completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Configure your API credentials in .env file")
        print("2. Test with: python3 -m src.alerts.telegram 'Test message'")
        print("3. Run scanner: python3 -m src.exec.scanner --dry")
        print("4. Start daemon: python3 -m src.daemon")
    else:
        print("⚠️  Some demonstrations failed. Check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())