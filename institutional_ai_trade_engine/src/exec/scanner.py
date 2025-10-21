"""
Scanner module for detecting 3WI setups and breakouts.
"""
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd

try:
    from ..data.fetch import DataFetcher  # type: ignore
    from ..data.indicators import compute  # type: ignore
    from ..strategy.three_week_inside import detect_3wi, breakout, is_near_breakout, calculate_breakout_strength  # type: ignore
    from ..strategy.filters import filters_ok, get_filter_score  # type: ignore
    from ..storage.db import get_db_session  # type: ignore
    from ..storage.ledger import log_trade  # type: ignore
    from ..alerts.telegram import send_trade_alert  # type: ignore
    from ..core.risk import size_position, calculate_targets, check_risk_limits  # type: ignore
    from ..core.config import Config  # type: ignore
    
    # Optional imports that might not be available
    try:
        from ..alerts.sheets import update_master_sheet  # type: ignore
        SHEETS_AVAILABLE = True
    except ImportError:
        SHEETS_AVAILABLE = False
        logger.warning("Google Sheets integration not available - alerts will be skipped")
        
except Exception:
    from src.data.fetch import DataFetcher  # type: ignore
    from src.data.indicators import compute  # type: ignore
    from src.strategy.three_week_inside import detect_3wi, breakout, is_near_breakout, calculate_breakout_strength  # type: ignore
    from src.strategy.filters import filters_ok, get_filter_score  # type: ignore
    from src.storage.db import get_db_session  # type: ignore
    from src.storage.ledger import log_trade  # type: ignore
    from src.alerts.telegram import send_trade_alert  # type: ignore
    from src.core.risk import size_position, calculate_targets, check_risk_limits  # type: ignore
    from src.core.config import Config  # type: ignore
    
    # Optional imports that might not be available
    try:
        from src.alerts.sheets import update_master_sheet  # type: ignore
        SHEETS_AVAILABLE = True
    except ImportError:
        SHEETS_AVAILABLE = False
        logger.warning("Google Sheets integration not available - alerts will be skipped")
from sqlalchemy import text

logger = logging.getLogger(__name__)

class Scanner:
    """Scanner for 3WI setups and breakouts."""
    
    def __init__(self, broker=None):
        try:
            self.fetcher = DataFetcher(broker)
            self.dry_run = False
            logger.info("Scanner initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DataFetcher: {e}")
            raise e
    
    def scan_all_instruments(self) -> List[Dict]:
        """
        Scan all enabled instruments for 3WI setups.
        
        Returns:
            List[Dict]: Detailed scan results with stock information
        """
        try:
            # Get enabled instruments
            logger.info("Fetching enabled instruments...")
            instruments = self.fetcher.get_enabled_instruments()
            if not instruments:
                logger.warning("No enabled instruments found")
                return {
                    "total_instruments": 0,
                    "scanned_instruments": [],
                    "valid_setups": [],
                    "breakouts": [],
                    "errors": [{"error": "No enabled instruments found in database"}]
                }
            
            logger.info(f"Found {len(instruments)} enabled instruments to scan")
            
            scan_results = {
                "total_instruments": len(instruments),
                "scanned_instruments": [],
                "valid_setups": [],
                "breakouts": [],
                "errors": []
            }
            
            for i, instrument in enumerate(instruments):
                try:
                    symbol = instrument['symbol']
                    logger.info(f"Scanning {symbol} ({i+1}/{len(instruments)})...")
                    
                    # Get weekly data
                    weekly_df = self.fetcher.get_weekly_data(symbol, weeks=52)
                    if weekly_df is None:
                        logger.warning(f"No data available for {symbol}")
                        scan_results["errors"].append({
                            "symbol": symbol,
                            "error": "No data available"
                        })
                        continue
                        
                    if not self.fetcher.validate_data_quality(weekly_df):
                        logger.warning(f"Invalid data quality for {symbol}")
                        scan_results["errors"].append({
                            "symbol": symbol,
                            "error": "Invalid data quality"
                        })
                        continue
                    
                    # Compute indicators
                    weekly_df = compute(weekly_df)
                    latest = weekly_df.iloc[-1]
                    
                    # Create instrument scan result
                    instrument_result = {
                        "symbol": symbol,
                        "current_price": float(latest["close"]),
                        "rsi": float(latest.get("RSI", 0)),
                        "wma20": float(latest.get("WMA20", 0)),
                        "wma50": float(latest.get("WMA50", 0)),
                        "wma100": float(latest.get("WMA100", 0)),
                        "volume_ratio": float(latest.get("VOL_X20D", 0)),
                        "atr_pct": float(latest.get("ATR_PCT", 0)),
                        "patterns_found": 0,
                        "filters_passed": 0,
                        "breakout_detected": False,
                        "strategy_status": "No Pattern",
                        "mother_high": None,
                        "mother_low": None,
                        "quality_score": 0,
                        "scanned_at": datetime.now().isoformat()
                    }
                    
                    # Detect 3WI patterns
                    patterns = detect_3wi(weekly_df)
                    instrument_result["patterns_found"] = len(patterns)
                    
                    if patterns:
                        instrument_result["strategy_status"] = "Pattern Detected"
                        
                        # Check each pattern
                        for pattern in patterns:
                            instrument_result["mother_high"] = float(pattern.get("mother_high", 0))
                            instrument_result["mother_low"] = float(pattern.get("mother_low", 0))
                            
                            if self._validate_setup(symbol, pattern, weekly_df):
                                instrument_result["filters_passed"] = 4
                                instrument_result["strategy_status"] = "Valid Setup"
                                instrument_result["quality_score"] = get_filter_score(latest)
                                
                                scan_results["valid_setups"].append({
                                    'symbol': symbol,
                                    'pattern': pattern,
                                    'weekly_data': weekly_df,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                # Check for breakout
                                breakout_direction = breakout(weekly_df, pattern.get("index", 0))
                                if breakout_direction == "up":
                                    instrument_result["breakout_detected"] = True
                                    instrument_result["strategy_status"] = "Breakout Confirmed"
                            else:
                                # Count how many filters passed
                                passed_filters = sum([
                                    latest['RSI'] > 55,
                                    latest['WMA20'] > latest['WMA50'] > latest['WMA100'],
                                    latest['VOL_X20D'] >= 1.5,
                                    latest['ATR_PCT'] < 0.06
                                ])
                                instrument_result["filters_passed"] = passed_filters
                                instrument_result["strategy_status"] = f"Pattern Found - {passed_filters}/4 Filters"
                    
                    scan_results["scanned_instruments"].append(instrument_result)
                
                except Exception as e:
                    logger.error(f"Error scanning {instrument.get('symbol', 'unknown')}: {e}")
                    scan_results["errors"].append({
                        "symbol": instrument.get('symbol', 'unknown'),
                        "error": str(e)
                    })
                    continue
            
            scan_results["valid_setups"] = valid_setups
            logger.info(f"Scan completed: {len(valid_setups)} setups found")
            return scan_results
            
        except Exception as e:
            logger.error(f"Error scanning instruments: {e}")
            return {
                "total_instruments": 0,
                "scanned_instruments": [],
                "valid_setups": [],
                "breakouts": [],
                "errors": [{"error": str(e)}]
            }
    
    def _validate_setup(self, symbol: str, pattern: Dict, weekly_df: pd.DataFrame) -> bool:
        """
        Validate a 3WI setup.
        
        Args:
            symbol: Stock symbol
            pattern: 3WI pattern
            weekly_df: Weekly data
        
        Returns:
            bool: True if setup is valid
        """
        try:
            # Get latest data point
            latest = weekly_df.iloc[-1]
            
            # Apply filters
            if not filters_ok(latest):
                return False
            
            # Check if near breakout
            if not is_near_breakout(weekly_df, pattern):
                return False
            
            # Calculate breakout strength
            strength = calculate_breakout_strength(weekly_df, pattern)
            if not strength:
                return False
            
            # Store setup in database
            self._store_setup(symbol, pattern, latest)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating setup for {symbol}: {e}")
            return False
    
    def _store_setup(self, symbol: str, pattern: Dict, latest: pd.Series):
        """Store setup in database."""
        try:
            db = get_db_session()
            try:
                query = text("""
                    INSERT INTO setups (symbol, week_start, mother_high, mother_low, 
                                      inside_weeks, matched_filters, comment)
                    VALUES (:symbol, :week_start, :mother_high, :mother_low, 
                            :inside_weeks, :matched_filters, :comment)
                """)
                
                db.execute(query, {
                    "symbol": symbol,
                    "week_start": pattern['week_start'],
                    "mother_high": pattern['mother_high'],
                    "mother_low": pattern['mother_low'],
                    "inside_weeks": pattern['inside_weeks'],
                    "matched_filters": 1,
                    "comment": f"3WI setup detected"
                })
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing setup: {e}")
    
    def check_breakouts(self) -> List[Dict]:
        """
        Check for confirmed breakouts in existing setups.
        
        Returns:
            List[Dict]: List of confirmed breakouts
        """
        try:
            # Get all active setups (simplified query without setup_id reference)
            db = get_db_session()
            try:
                query = text("""
                    SELECT * FROM setups 
                    ORDER BY created_at DESC
                """)
                setups = db.execute(query).fetchall()
                
            finally:
                db.close()
            
            confirmed_breakouts = []
            
            for setup in setups:
                symbol = setup.symbol
                
                # Get latest weekly data
                weekly_df = self.fetcher.get_weekly_data(symbol, weeks=52)
                if not self.fetcher.validate_data_quality(weekly_df):
                    continue
                
                # Check for breakout
                pattern_index = setup.id  # Assuming setup ID corresponds to pattern index
                breakout_direction = breakout(weekly_df, pattern_index)
                
                if breakout_direction:
                    # Create position
                    position = self._create_position(symbol, setup, weekly_df, breakout_direction)
                    if position:
                        confirmed_breakouts.append(position)
            
            return confirmed_breakouts
            
        except Exception as e:
            logger.error(f"Error checking breakouts: {e}")
            return []
    
    def _create_position(self, symbol: str, setup: Dict, weekly_df: pd.DataFrame, direction: str) -> Dict:
        """
        Create a new position from confirmed breakout.
        
        Args:
            symbol: Stock symbol
            setup: Setup data
            weekly_df: Weekly data
            direction: Breakout direction ('up' or 'down')
        
        Returns:
            Dict: Position data
        """
        try:
            # Get current price
            current_price = self.fetcher.get_current_price(symbol)
            if not current_price:
                logger.error(f"Could not get current price for {symbol}")
                return None
            
            # Calculate stop loss and targets
            if direction == "up":
                entry = current_price
                stop = setup.mother_low
                t1, t2 = calculate_targets(entry, stop, weekly_df['ATR'].iloc[-1])
            else:
                entry = current_price
                stop = setup.mother_high
                t1, t2 = calculate_targets(entry, stop, weekly_df['ATR'].iloc[-1])
                # For short positions, targets are below entry
                t1 = entry - (entry - stop) * 1.5
                t2 = entry - (entry - stop) * 3.0
            
            # Calculate position size
            qty, risk_amount = size_position(
                entry, stop, Config.PORTFOLIO_CAPITAL, 
                Config.RISK_PCT, Config.POSITION_SIZING_PLAN
            )
            
            # Check risk limits
            if not check_risk_limits([], risk_amount):
                logger.warning(f"Position size exceeds risk limits for {symbol}")
                return None
            
            # Create position record
            position = {
                "symbol": symbol,
                "status": "open",
                "entry_price": entry,
                "stop": stop,
                "t1": t1,
                "t2": t2,
                "qty": qty,
                "capital": Config.PORTFOLIO_CAPITAL,
                "plan_size": Config.POSITION_SIZING_PLAN,
                "opened_ts": datetime.now().isoformat(),
                "direction": direction,
                "risk_amount": risk_amount
            }
            
            # Store in database
            self._store_position(position)
            
            # Send alerts
            if not self.dry_run:
                send_trade_alert(position, "NEW_POSITION")
                if SHEETS_AVAILABLE:
                    update_master_sheet(position, "NEW_POSITION")
                else:
                    logger.info("Skipping Google Sheets update - integration not available")
            
            logger.info(f"Created position for {symbol}: {direction} breakout")
            return position
            
        except Exception as e:
            logger.error(f"Error creating position for {symbol}: {e}")
            return None
    
    def _store_position(self, position: Dict):
        """Store position in database."""
        try:
            db = get_db_session()
            try:
                query = text("""
                    INSERT INTO positions (symbol, status, entry_price, stop, t1, t2, 
                                        qty, capital, plan_size, opened_ts, pnl, rr)
                    VALUES (:symbol, :status, :entry_price, :stop, :t1, :t2, 
                            :qty, :capital, :plan_size, :opened_ts, :pnl, :rr)
                """)
                
                db.execute(query, {
                    "symbol": position["symbol"],
                    "status": position["status"],
                    "entry_price": position["entry_price"],
                    "stop": position["stop"],
                    "t1": position["t1"],
                    "t2": position["t2"],
                    "qty": position["qty"],
                    "capital": position["capital"],
                    "plan_size": position["plan_size"],
                    "opened_ts": position["opened_ts"],
                    "pnl": 0.0,
                    "rr": 0.0
                })
                db.commit()
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error storing position: {e}")
    
    def run(self, dry_run: bool = False):
        """
        Run the scanner.
        
        Args:
            dry_run: If True, don't create actual positions
            
        Returns:
            dict: Scan results with setups and breakouts found
        """
        try:
            self.dry_run = dry_run
            logger.info("Starting scanner run...")
            
            # Scan for new setups
            scan_results = self.scan_all_instruments()
            logger.info(f"Found {len(scan_results.get('valid_setups', []))} new setups")
            
            # Check for breakouts
            breakouts = self.check_breakouts()
            logger.info(f"Found {len(breakouts)} confirmed breakouts")
            
            # Return properly structured results
            results = {
                "total_instruments": scan_results.get("total_instruments", 0),
                "scanned_instruments": scan_results.get("scanned_instruments", []),
                "valid_setups": scan_results.get("valid_setups", []),
                "breakouts": breakouts,
                "errors": scan_results.get("errors", []),
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("Scanner run completed")
            return results
            
        except Exception as e:
            logger.error(f"Error in scanner run: {e}")
            return {
                "total_instruments": 0,
                "scanned_instruments": [],
                "valid_setups": [],
                "breakouts": [],
                "errors": [{"error": str(e)}],
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }

# Global scanner instance
scanner = None

def run(dry_run: bool = False):
    """Wrapper function for scheduler."""
    global scanner
    if scanner is None:
        # Initialize scanner with proper broker
        try:
            try:
                from ..core.config import Settings
                broker = Settings.get_broker()
                logger.info(f"Initializing scanner with broker: {type(broker).__name__}")
            except Exception as e:
                logger.warning(f"Failed to import from relative path: {e}")
                from src.core.config import Settings
                broker = Settings.get_broker()
                logger.info(f"Initialized scanner with broker: {type(broker).__name__}")
            scanner = Scanner(broker)
        except Exception as e:
            logger.error(f"Failed to initialize scanner: {e}")
            # Return error result instead of crashing
            return {
                "total_instruments": 0,
                "scanned_instruments": [],
                "valid_setups": [],
                "breakouts": [],
                "errors": [{"error": f"Scanner initialization failed: {str(e)}"}],
                "dry_run": dry_run,
                "timestamp": datetime.now().isoformat()
            }
    return scanner.run(dry_run)

if __name__ == "__main__":
    import sys
    dry_run = "--dry" in sys.argv
    run(dry_run)