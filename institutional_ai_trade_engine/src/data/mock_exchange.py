"""
Mock exchange for offline testing.
Simulates order execution using SQLite database.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
import logging
import sqlite3
import uuid

from .broker_base import BrokerBase

logger = logging.getLogger(__name__)


class MockExchange(BrokerBase):
    """Mock exchange for offline paper trading."""
    
    def __init__(self, settings):
        """
        Initialize mock exchange.
        
        Args:
            settings: Settings object
        """
        self.settings = settings
        self.db_path = settings.DATA_DIR + "/mock_exchange.db"
        self._init_db()
        
        logger.info("Initialized Mock Exchange (offline mode)")
    
    def _init_db(self):
        """Initialize mock exchange database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_orders (
                order_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty INTEGER NOT NULL,
                order_type TEXT NOT NULL,
                price REAL,
                status TEXT NOT NULL,
                filled_qty INTEGER DEFAULT 0,
                avg_fill_price REAL DEFAULT 0,
                tag TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Fills table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price REAL NOT NULL,
                filled_at TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES mock_orders(order_id)
            )
        """)
        
        # Positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mock_positions (
                symbol TEXT PRIMARY KEY,
                qty INTEGER NOT NULL,
                avg_price REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def name(self) -> str:
        """Return broker name."""
        return "MOCK_EXCHANGE"
    
    def _symbol(self, symbol: str) -> str:
        """Normalize symbol."""
        if ":" in symbol:
            return symbol
        return f"NSE:{symbol}-EQ"
    
    def history(self, symbol: str, resolution: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Generate synthetic historical data for testing.
        """
        logger.warning("Mock exchange: Generating synthetic data")
        
        # Generate random walk data
        periods = (end - start).days
        if resolution == "W":
            periods = periods // 7
        elif resolution == "60":
            periods = periods * 7  # ~7 hours per day
        
        if periods <= 0:
            periods = 100
        
        # Simple random walk
        import numpy as np
        np.random.seed(hash(symbol) % 2**32)  # Deterministic per symbol
        
        dates = pd.date_range(start=start, end=end, periods=periods, tz="Asia/Kolkata")
        base_price = 1000 + (hash(symbol) % 5000)
        
        returns = np.random.normal(0.001, 0.02, periods)
        prices = base_price * (1 + returns).cumprod()
        
        df = pd.DataFrame({
            "ts": dates,
            "open": prices,
            "high": prices * 1.01,
            "low": prices * 0.99,
            "close": prices,
            "volume": np.random.randint(100000, 1000000, periods)
        })
        
        df = df.set_index("ts")
        return df
    
    def candles(self, symbol: str, tf: str, lookback: int) -> pd.DataFrame:
        """Fetch recent candles."""
        tf_map = {
            "1h": ("60", timedelta(days=lookback * 2)),
            "day": ("D", timedelta(days=lookback)),
            "week": ("W", timedelta(weeks=lookback))
        }
        
        if tf not in tf_map:
            return pd.DataFrame()
        
        resolution, delta = tf_map[tf]
        end = datetime.now()
        start = end - delta
        
        return self.history(symbol, resolution, start, end).tail(lookback)
    
    def subscribe_ticks(self, symbols: List[str], on_tick: Callable) -> None:
        """Mock WebSocket - not implemented."""
        logger.warning("Mock exchange: WebSocket not implemented")
        pass
    
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
        Place mock order (simulates instant fill).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            order_id = str(uuid.uuid4())
            symbol = self._symbol(symbol)
            now = datetime.now().isoformat()
            
            # Simulate fill price
            if order_type.upper() == "MARKET":
                # Get current "market price" from synthetic data
                df = self.candles(symbol, "day", 1)
                fill_price = df.iloc[-1]["close"] if not df.empty else (price or 1000)
            else:
                fill_price = price
            
            # Insert order
            cursor.execute("""
                INSERT INTO mock_orders 
                (order_id, symbol, side, qty, order_type, price, status, filled_qty, avg_fill_price, tag, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, symbol, side.upper(), qty, order_type.upper(), price, "FILLED", qty, fill_price, tag, now, now))
            
            # Insert fill
            fill_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO mock_fills
                (fill_id, order_id, symbol, side, qty, price, filled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (fill_id, order_id, symbol, side.upper(), qty, fill_price, now))
            
            # Update position
            cursor.execute("SELECT qty, avg_price FROM mock_positions WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            
            if row:
                existing_qty, existing_avg = row
                if side.upper() == "BUY":
                    new_qty = existing_qty + qty
                    new_avg = ((existing_qty * existing_avg) + (qty * fill_price)) / new_qty
                else:
                    new_qty = existing_qty - qty
                    new_avg = existing_avg if new_qty != 0 else 0
                
                cursor.execute("""
                    UPDATE mock_positions SET qty = ?, avg_price = ?, last_updated = ?
                    WHERE symbol = ?
                """, (new_qty, new_avg, now, symbol))
            else:
                if side.upper() == "BUY":
                    cursor.execute("""
                        INSERT INTO mock_positions (symbol, qty, avg_price, last_updated)
                        VALUES (?, ?, ?, ?)
                    """, (symbol, qty, fill_price, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Mock order filled: {symbol} {side} {qty} @ {fill_price} (ID: {order_id})")
            
            return {
                "order_id": order_id,
                "status": "success",
                "message": f"Mock order filled at {fill_price}"
            }
            
        except Exception as e:
            logger.error(f"Error placing mock order: {e}")
            return {
                "order_id": None,
                "status": "error",
                "message": str(e)
            }
    
    def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify mock order."""
        logger.warning("Mock exchange: Order modification not fully implemented")
        return {"status": "success", "message": "Mock modification"}
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel mock order."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE mock_orders SET status = 'CANCELLED', updated_at = ?
                WHERE order_id = ? AND status = 'PENDING'
            """, (datetime.now().isoformat(), order_id))
            
            conn.commit()
            conn.close()
            
            return {"status": "success", "message": "Order cancelled"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def positions(self) -> List[Dict[str, Any]]:
        """Get mock positions."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT symbol, qty, avg_price FROM mock_positions WHERE qty != 0")
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for symbol, qty, avg_price in rows:
                # Get current LTP
                ltp = self.get_ltp(symbol) or avg_price
                pnl = (ltp - avg_price) * qty
                
                result.append({
                    "symbol": symbol,
                    "qty": qty,
                    "avg_price": avg_price,
                    "ltp": ltp,
                    "pnl": pnl
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching mock positions: {e}")
            return []
    
    def orders(self) -> List[Dict[str, Any]]:
        """Get mock orders."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT order_id, symbol, side, qty, filled_qty, price, status, order_type
                FROM mock_orders
                ORDER BY created_at DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
            conn.close()
            
            result = []
            for row in rows:
                result.append({
                    "order_id": row[0],
                    "symbol": row[1],
                    "side": row[2],
                    "qty": row[3],
                    "filled_qty": row[4],
                    "price": row[5],
                    "status": row[6],
                    "order_type": row[7]
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching mock orders: {e}")
            return []
    
    def get_ltp(self, symbol: str) -> Optional[float]:
        """Get mock LTP from synthetic data."""
        try:
            df = self.candles(symbol, "day", 1)
            if df.empty:
                return None
            return float(df.iloc[-1]["close"])
        except Exception as e:
            logger.error(f"Error fetching mock LTP: {e}")
            return None
