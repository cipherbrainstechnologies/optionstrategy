"""
Data fetching utilities for historical and real-time data.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from .angel_client import AngelClient
from .indicators import compute, compute_weekly_indicators

logger = logging.getLogger(__name__)

class DataFetcher:
    """Data fetching and processing utilities."""
    
    def __init__(self):
        self.client = AngelClient()
    
    def get_weekly_data(self, symbol: str, weeks: int = 52) -> Optional[pd.DataFrame]:
        """
        Get weekly OHLCV data for a symbol.
        
        Args:
            symbol: Stock symbol
            weeks: Number of weeks of data
        
        Returns:
            DataFrame: Weekly OHLCV data with indicators
        """
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(weeks=weeks)
            
            # Get historical data
            hist_data = self.client.get_historical_data(
                symbol,
                interval="1WEEK",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )
            
            if not hist_data:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(hist_data)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # Convert data types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Compute indicators
            df = compute_weekly_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching weekly data for {symbol}: {e}")
            return None
    
    def get_daily_data(self, symbol: str, days: int = 252) -> Optional[pd.DataFrame]:
        """
        Get daily OHLCV data for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of days of data
        
        Returns:
            DataFrame: Daily OHLCV data with indicators
        """
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Get historical data
            hist_data = self.client.get_historical_data(
                symbol,
                interval="1DAY",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )
            
            if not hist_data:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(hist_data)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # Convert data types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Compute indicators
            df = compute(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return None
    
    def get_hourly_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Get hourly OHLCV data for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of days of data
        
        Returns:
            DataFrame: Hourly OHLCV data with indicators
        """
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)
            
            # Get historical data
            hist_data = self.client.get_historical_data(
                symbol,
                interval="1HOUR",
                from_date=from_date.strftime("%Y-%m-%d"),
                to_date=to_date.strftime("%Y-%m-%d")
            )
            
            if not hist_data:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(hist_data)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # Convert data types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Compute indicators
            df = compute(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching hourly data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current LTP for a symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            float: Current LTP or None if error
        """
        try:
            return self.client.get_ltp(symbol)
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def get_enabled_instruments(self) -> List[Dict]:
        """
        Get list of enabled instruments from database.
        
        Returns:
            List[Dict]: List of enabled instruments
        """
        try:
            from ..storage.db import get_db_session
            from sqlalchemy import text
            
            db = get_db_session()
            try:
                query = text("SELECT symbol, exchange FROM instruments WHERE enabled = 1")
                result = db.execute(query).fetchall()
                return [dict(row._mapping) for row in result]
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting enabled instruments: {e}")
            return []
    
    def validate_data_quality(self, df: pd.DataFrame) -> bool:
        """
        Validate data quality for trading decisions.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            bool: True if data quality is good
        """
        if df is None or df.empty:
            return False
        
        # Check for required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            return False
        
        # Check for sufficient data
        if len(df) < 20:
            return False
        
        # Check for missing values
        if df[required_cols].isnull().any().any():
            return False
        
        # Check for valid price data
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            return False
        
        return True