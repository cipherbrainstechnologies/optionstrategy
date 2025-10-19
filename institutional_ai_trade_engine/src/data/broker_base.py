"""
Broker abstraction layer for trading engine.
Provides a unified interface for different brokers (FYERS, Angel One, Mock).
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import pandas as pd


class BrokerBase(ABC):
    """Abstract base class for all broker implementations."""
    
    @abstractmethod
    def name(self) -> str:
        """Return broker name and mode (e.g., 'FYERS_SANDBOX', 'ANGEL_LIVE')."""
        pass
    
    # ---- Market Data ----
    
    @abstractmethod
    def history(self, symbol: str, resolution: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Args:
            symbol: Trading symbol (e.g., "NSE:RELIANCE-EQ")
            resolution: Time resolution ("60" for 1h, "D" for daily, "W" for weekly)
            start: Start datetime
            end: End datetime
            
        Returns:
            DataFrame with columns: [ts, open, high, low, close, volume]
            Index: ts (datetime with timezone)
        """
        pass
    
    @abstractmethod
    def subscribe_ticks(self, symbols: List[str], on_tick: Callable) -> None:
        """
        Subscribe to real-time tick data (WebSocket).
        
        Args:
            symbols: List of symbols to subscribe
            on_tick: Callback function(symbol, ltp, timestamp)
        """
        pass
    
    @abstractmethod
    def candles(self, symbol: str, tf: str, lookback: int) -> pd.DataFrame:
        """
        Convenience method to fetch recent candles.
        
        Args:
            symbol: Trading symbol
            tf: Timeframe ("1h", "day", "week")
            lookback: Number of periods to fetch
            
        Returns:
            DataFrame with recent candles
        """
        pass
    
    # ---- Orders (paper/live) ----
    
    @abstractmethod
    def place_order(
        self, 
        symbol: str, 
        side: str, 
        qty: int, 
        order_type: str, 
        price: Optional[float] = None, 
        tag: str = ""
    ) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol: Trading symbol
            side: "BUY" or "SELL"
            qty: Quantity (integer)
            order_type: "MARKET" or "LIMIT"
            price: Limit price (required for LIMIT orders)
            tag: Custom tag for tracking (max 15 chars)
            
        Returns:
            Order response dict with keys: order_id, status, message
        """
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """
        Modify an existing order.
        
        Args:
            order_id: Order ID to modify
            **kwargs: Fields to modify (qty, price, etc.)
            
        Returns:
            Response dict
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Response dict
        """
        pass
    
    @abstractmethod
    def positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of position dicts with keys: symbol, qty, avg_price, ltp, pnl
        """
        pass
    
    @abstractmethod
    def orders(self) -> List[Dict[str, Any]]:
        """
        Get order book.
        
        Returns:
            List of order dicts with keys: order_id, symbol, side, qty, price, status
        """
        pass
    
    @abstractmethod
    def get_ltp(self, symbol: str) -> Optional[float]:
        """
        Get Last Traded Price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Last traded price or None
        """
        pass
