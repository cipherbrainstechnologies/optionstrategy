"""
Scanner module for detecting 3WI setups and breakouts.
"""
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd

try:
    from ..data.fetch import DataFetcher  # type: ignore
    from ..strategy.three_week_inside import detect_3wi, breakout, is_near_breakout, calculate_breakout_strength  # type: ignore
    from ..strategy.filters import filters_ok, get_filter_score  # type: ignore
    from ..storage.db import get_db_session  # type: ignore
    from ..storage.ledger import log_trade  # type: ignore
    from ..alerts.telegram import send_trade_alert  # type: ignore
    from ..alerts.sheets import update_master_sheet  # type: ignore
    from ..core.risk import size_position, calculate_targets, check_risk_limits  # type: ignore
    from ..core.config import Config  # type: ignore
except Exception:
    from data.fetch import DataFetcher  # type: ignore
    from strategy.three_week_inside import detect_3wi, breakout, is_near_breakout, calculate_breakout_strength  # type: ignore
    from strategy.filters import filters_ok, get_filter_score  # type: ignore
    from storage.db import get_db_session  # type: ignore
    from storage.ledger import log_trade  # type: ignore
    from alerts.telegram import send_trade_alert  # type: ignore
    from alerts.sheets import update_master_sheet  # type: ignore
    from core.risk import size_position, calculate_targets, check_risk_limits  # type: ignore
    from core.config import Config  # type: ignore
from sqlalchemy import text

logger = logging.getLogger(__name__)

class Scanner:
    """Scanner for 3WI setups and breakouts."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.dry_run = False
    
    def scan_all_instruments(self) -> List[Dict]:
        """
        Scan all enabled instruments for 3WI setups.
        
        Returns:
            List[Dict]: List of valid setups found
        """
        try:
            # Get enabled instruments
            instruments = self.fetcher.get_enabled_instruments()
            if not instruments:
                logger.warning("No enabled instruments found")
                return []
            
            valid_setups = []
            
            for instrument in instruments:
                symbol = instrument['symbol']
                logger.info(f"Scanning {symbol}...")
                
                # Get weekly data
                weekly_df = self.fetcher.get_weekly_data(symbol, weeks=52)
                if not self.fetcher.validate_data_quality(weekly_df):
                    logger.warning(f"Invalid data quality for {symbol}")
                    continue
                
                # Detect 3WI patterns
                patterns = detect_3wi(weekly_df)
                if not patterns:
                    continue
                
                # Check each pattern
                for pattern in patterns:
                    if self._validate_setup(symbol, pattern, weekly_df):
                        valid_setups.append({
                            'symbol': symbol,
                            'pattern': pattern,
                            'weekly_data': weekly_df,
                            'timestamp': datetime.now().isoformat()
                        })
            
            logger.info(f"Found {len(valid_setups)} valid setups")
            return valid_setups
            
        except Exception as e:
            logger.error(f"Error scanning instruments: {e}")
            return []
    
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
            # Get all active setups
            db = get_db_session()
            try:
                query = text("""
                    SELECT * FROM setups 
                    WHERE id NOT IN (
                        SELECT DISTINCT setup_id FROM positions 
                        WHERE setup_id IS NOT NULL
                    )
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
                update_master_sheet(position, "NEW_POSITION")
            
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
        """
        try:
            self.dry_run = dry_run
            logger.info("Starting scanner run...")
            
            # Scan for new setups
            setups = self.scan_all_instruments()
            logger.info(f"Found {len(setups)} new setups")
            
            # Check for breakouts
            breakouts = self.check_breakouts()
            logger.info(f"Found {len(breakouts)} confirmed breakouts")
            
            logger.info("Scanner run completed")
            
        except Exception as e:
            logger.error(f"Error in scanner run: {e}")

# Global scanner instance
scanner = Scanner()

def run(dry_run: bool = False):
    """Wrapper function for scheduler."""
    scanner.run(dry_run)

if __name__ == "__main__":
    import sys
    dry_run = "--dry" in sys.argv
    run(dry_run)