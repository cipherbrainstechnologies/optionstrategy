"""
Index watch module for monitoring BankNifty and Nifty indices.
Supports FYERS, Angel One, and Mock brokers via broker abstraction.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from ..core.config import Settings
from .broker_base import get_broker

logger = logging.getLogger(__name__)

class IndexWatch:
    """Index monitoring and analysis."""
    
    def __init__(self):
        settings = Settings()
        self.client = get_broker(settings)
        self.nifty_symbol = Settings.NIFTY_SYMBOL
        self.banknifty_symbol = Settings.BANKNIFTY_SYMBOL
        
    def get_index_snapshot(self) -> Dict:
        """
        Get current snapshot of index data.
        
        Returns:
            Dict: Index data with LTP, changes, and strike information
        """
        try:
            # Get Nifty data
            nifty_ltp = self.client.get_ltp(self.nifty_symbol)
            banknifty_ltp = self.client.get_ltp(self.banknifty_symbol)
            
            if not nifty_ltp or not banknifty_ltp:
                logger.warning("Failed to get index LTP data")
                return {}
            
            # Calculate strikes (nearest OTM ±100 points)
            nifty_strikes = self._calculate_strikes(nifty_ltp, 100)
            banknifty_strikes = self._calculate_strikes(banknifty_ltp, 100)
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "nifty": {
                    "ltp": nifty_ltp,
                    "strikes": nifty_strikes
                },
                "banknifty": {
                    "ltp": banknifty_ltp,
                    "strikes": banknifty_strikes
                }
            }
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Error getting index snapshot: {e}")
            return {}
    
    def _calculate_strikes(self, ltp: float, step: int) -> Dict:
        """
        Calculate nearest OTM strikes around LTP.
        
        Args:
            ltp: Last traded price
            step: Strike step size
        
        Returns:
            Dict: Strike information
        """
        # Round LTP to nearest step
        base_strike = round(ltp / step) * step
        
        strikes = {
            "ce_strikes": [base_strike + (i * step) for i in range(1, 6)],  # +100, +200, etc.
            "pe_strikes": [base_strike - (i * step) for i in range(1, 6)],  # -100, -200, etc.
            "atm": base_strike
        }
        
        return strikes
    
    def get_volatility_metrics(self, symbol: str, days: int = 20) -> Optional[Dict]:
        """
        Calculate volatility metrics for an index.
        
        Args:
            symbol: Index symbol
            days: Number of days for calculation
        
        Returns:
            Dict: Volatility metrics
        """
        try:
            # Get historical data
            hist_data = self.client.get_historical_data(
                symbol, 
                interval="1DAY",
                from_date=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            )
            
            if not hist_data:
                return None
            
            # Convert to DataFrame for calculations
            import pandas as pd
            df = pd.DataFrame(hist_data)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            df['close'] = pd.to_numeric(df['close'])
            
            # Calculate daily returns
            df['returns'] = df['close'].pct_change()
            
            # Volatility metrics
            volatility = df['returns'].std() * (252 ** 0.5)  # Annualized volatility
            avg_range = ((df['high'] - df['low']) / df['close']).mean() * 100
            
            return {
                "annualized_volatility": round(volatility * 100, 2),
                "avg_daily_range": round(avg_range, 2),
                "current_ltp": df['close'].iloc[-1],
                "period_high": df['high'].max(),
                "period_low": df['low'].min()
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return None
    
    def monitor(self):
        """
        Monitor indices and log data.
        This function is called by the scheduler every 5 minutes.
        """
        try:
            snapshot = self.get_index_snapshot()
            if snapshot:
                logger.info(f"Index snapshot: {snapshot}")
                
                # Get volatility metrics
                nifty_vol = self.get_volatility_metrics(self.nifty_symbol)
                banknifty_vol = self.get_volatility_metrics(self.banknifty_symbol)
                
                if nifty_vol:
                    logger.info(f"Nifty volatility: {nifty_vol}")
                if banknifty_vol:
                    logger.info(f"BankNifty volatility: {banknifty_vol}")
                    
        except Exception as e:
            logger.error(f"Error in index monitoring: {e}")

# Global instance for scheduler
index_watch = IndexWatch()

def monitor():
    """Wrapper function for scheduler."""
    index_watch.monitor()