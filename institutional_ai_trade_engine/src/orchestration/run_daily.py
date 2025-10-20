"""
Daily scan orchestration.
Runs at 09:25 IST (pre-open) and 15:10 IST (close).
"""
import logging
from datetime import datetime, timedelta
from ..core.config import Settings, get_settings
from ..storage.db import get_db_session
from ..strategy.three_week_inside import detect_3wi, get_pattern_quality_score, is_near_breakout, breakout
from ..strategy.filters import filters_ok
from ..strategy.portfolio_mode import PortfolioMode
from ..data.indicators import compute
from ..storage.models import Signal, Setup, Instrument, generate_signal_id
import json

try:
    from ..exec.scanner import run as run_scanner  # type: ignore
except Exception:
    from exec.scanner import run as run_scanner  # type: ignore
try:
    from ..core.config import Settings  # type: ignore
except Exception:
    from core.config import Settings  # type: ignore

logger = logging.getLogger(__name__)


def run_daily():
    """
    Daily scanning flow.
    
    1. Load portfolio holdings
    2. Fetch weekly data for holdings
    3. Detect 3WI patterns
    4. Apply filters
    5. Check for breakouts
    6. Create signals for confirmed breakouts
    7. Propose new adds for high-quality setups
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting DAILY SCAN")
        logger.info("=" * 60)
        
        # Initialize
        settings = get_settings()
        broker = settings.get_broker()
        db = get_db_session()
        portfolio = PortfolioMode(settings.DATA_DIR)
        
        logger.info(f"Broker: {broker.name()}")
        logger.info(f"Portfolio mode: {len(portfolio.get_holdings())} holdings")
        
        # Get holdings to scan
        holdings = portfolio.get_holdings()
        if not holdings:
            logger.warning("No holdings in portfolio. Add holdings to data/portfolio.json")
            return
        
        logger.info(f"Scanning {len(holdings)} holdings for 3WI patterns")
        
        # Scan each holding
        for symbol in holdings:
            try:
                _scan_symbol(broker, db, portfolio, settings, symbol)
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
        
        db.commit()
        db.close()
        
        logger.info("Daily scan completed")
        
    except Exception as e:
        logger.error(f"Error in daily scan: {e}", exc_info=True)


def _scan_symbol(broker, db, portfolio, settings, symbol: str):
    """
    Scan a single symbol for 3WI patterns.
    
    Args:
        broker: Broker client
        db: Database session
        portfolio: Portfolio mode instance
        settings: Settings object
        symbol: Symbol to scan
    """
    logger.info(f"\nScanning: {symbol}")
    
    # Fetch weekly data (5 years)
    end = datetime.now()
    start = end - timedelta(days=365 * 5)
    
    df_weekly = broker.history(symbol, "W", start, end)
    
    if df_weekly.empty:
        logger.warning(f"No weekly data for {symbol}")
        return
    
    # Rename columns for indicators
    df_weekly = df_weekly.rename(columns={"ts": "timestamp"})
    
    # Compute indicators
    df_weekly = compute(df_weekly)
    
    if df_weekly.empty or len(df_weekly) < 50:
        logger.warning(f"Insufficient data for {symbol}")
        return
    
    # Detect 3WI patterns
    patterns = detect_3wi(df_weekly)
    
    if not patterns:
        logger.info(f"No 3WI patterns found for {symbol}")
        return
    
    logger.info(f"Found {len(patterns)} 3WI pattern(s) for {symbol}")
    
    # Check latest pattern
    latest_pattern = patterns[-1]
    pattern_idx = latest_pattern["index"]
    
    # Get quality score
    quality_score = get_pattern_quality_score(latest_pattern, df_weekly)
    
    logger.info(f"Pattern quality score: {quality_score:.0f}/100")
    
    # Check if filters pass
    latest_row = df_weekly.iloc[pattern_idx]
    
    if not filters_ok(latest_row):
        logger.info(f"Filters not met for {symbol}")
        # Store setup anyway for tracking
        _store_setup(db, symbol, latest_pattern, quality_score, matched_filters=False)
        return
    
    logger.info(f"✓ Filters passed for {symbol}")
    
    # Store setup
    setup = _store_setup(db, symbol, latest_pattern, quality_score, matched_filters=True)
    
    # Check for breakout
    breakout_dir = breakout(df_weekly, pattern_idx)
    
    if breakout_dir == "up":
        logger.info(f"🚀 BREAKOUT CONFIRMED: {symbol} (upward)")
        
        # Create signal for this breakout
        _create_signal(
            db=db,
            symbol=symbol,
            pattern=latest_pattern,
            latest_row=latest_row,
            quality_score=quality_score,
            settings=settings
        )
    
    elif is_near_breakout(df_weekly, latest_pattern, threshold=0.99):
        logger.info(f"⚡ NEAR BREAKOUT: {symbol} (99% of mother high)")
        
        # Propose as potential add
        _propose_add(portfolio, symbol, latest_pattern, latest_row, quality_score, settings)
    
    else:
        logger.info(f"Pattern not yet broken out for {symbol}")


def _store_setup(db, symbol: str, pattern: dict, quality_score: float, matched_filters: bool) -> Setup:
    """Store 3WI setup in database."""
    setup = Setup(
        symbol=symbol,
        week_start=pattern["week_start"],
        mother_high=pattern["mother_high"],
        mother_low=pattern["mother_low"],
        inside_weeks=pattern["inside_weeks"],
        matched_filters=matched_filters,
        quality_score=quality_score,
        comment=f"Range: {pattern['mother_range_pct']:.2f}%",
        created_at=datetime.utcnow()
    )
    
    db.add(setup)
    return setup


def _create_signal(db, symbol: str, pattern: dict, latest_row, quality_score: float, settings):
    """Create trading signal for breakout."""
    entry = pattern["mother_high"]
    stop = pattern["mother_low"]
    
    # Calculate targets (1.5R and 3R)
    risk = entry - stop
    target1 = entry + (risk * 1.5)
    target2 = entry + (risk * 3.0)
    
    # Generate unique signal ID
    trigger_ts = datetime.utcnow()
    signal_id = generate_signal_id(symbol, "weekly", trigger_ts)
    
    # Check if signal already exists
    existing = db.query(Signal).filter(Signal.signal_id == signal_id).first()
    if existing:
        logger.info(f"Signal already exists: {signal_id}")
        return
    
    signal = Signal(
        signal_id=signal_id,
        symbol=symbol,
        timeframe="weekly",
        direction="LONG",
        trigger_price=entry,
        stop_loss=stop,
        target1=target1,
        target2=target2,
        confidence=quality_score,
        pattern_type="3WI_BREAKOUT",
        status="PENDING",
        trigger_ts=trigger_ts,
        metadata=json.dumps({
            "mother_high": pattern["mother_high"],
            "mother_low": pattern["mother_low"],
            "mother_range_pct": pattern["mother_range_pct"],
            "rsi": float(latest_row.get("RSI", 0))
        }),
        created_at=datetime.utcnow()
    )
    
    db.add(signal)
    
    logger.info(
        f"Signal created: {symbol} LONG @ {entry:.2f}, "
        f"SL={stop:.2f}, T1={target1:.2f}, T2={target2:.2f}"
    )


def _propose_add(portfolio, symbol: str, pattern: dict, latest_row, quality_score: float, settings):
    """Propose new stock add to portfolio."""
    from ..core.risk import size_position
    
    entry = pattern["mother_high"]
    stop = pattern["mother_low"]
    risk = entry - stop
    target1 = entry + (risk * 1.5)
    target2 = entry + (risk * 3.0)
    
    # Calculate position size
    qty, _ = size_position(
        entry=entry,
        stop=stop,
        capital=settings.PORTFOLIO_CAPITAL,
        risk_pct=settings.RISK_PCT_PER_TRADE,
        plan=settings.POSITION_SIZING_PLAN
    )
    
    portfolio.propose_add(
        symbol=symbol,
        entry=entry,
        stop=stop,
        t1=target1,
        t2=target2,
        qty=qty,
        confidence=quality_score,
        pattern="3WI_NEAR_BREAKOUT",
        reason=f"Near breakout, RSI={latest_row.get('RSI', 0):.0f}, Quality={quality_score:.0f}"
    )
