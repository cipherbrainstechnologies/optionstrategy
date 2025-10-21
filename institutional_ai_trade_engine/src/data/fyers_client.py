"""
FYERS API client implementation using official v3 API.
Supports both paper trading (sandbox) and live trading.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
import logging

try:
    from fyers_apiv3 import fyersModel
    FYERS_AVAILABLE = True
except ImportError:
    FYERS_AVAILABLE = False
    logging.warning("fyers-apiv3 not installed. Install with: pip install fyers-apiv3")

from .broker_base import BrokerBase

logger = logging.getLogger(__name__)


class FyersAPI(BrokerBase):
    """FYERS API implementation with paper/live support."""
    
    def __init__(self, settings):
        """
        Initialize FYERS client using official v3 API.
        
        Args:
            settings: Settings object with FYERS credentials
        """
        if not FYERS_AVAILABLE:
            raise ImportError("fyers-apiv3 not installed. Run: pip install fyers-apiv3")
        
        self.settings = settings
        self._sandbox = bool(str(settings.FYERS_SANDBOX).lower() == "true")
        
        # Validate required credentials
        missing = []
        for key in ["FYERS_CLIENT_ID", "FYERS_SECRET_KEY"]:
            if not getattr(settings, key, None):
                missing.append(key)
        
        if missing:
            raise ValueError(
                f"Missing FYERS credentials: {missing}\n"
                "1) Visit https://myapi.fyers.in/dashboard/ to create app\n"
                "2) Add CLIENT_ID and SECRET_KEY to .env\n"
                "3) Run with dynamic token generation"
            )
        
        # Check if we have an access token, if not we'll generate one
        self.access_token = getattr(settings, 'FYERS_ACCESS_TOKEN', None)
        
        # Ensure log directory exists
        log_path = getattr(settings, 'LOG_PATH', './data/')
        if not log_path.endswith('/'):
            log_path += '/'
        
        # If LOG_PATH points to a file, use its directory instead
        import os
        if os.path.isfile(log_path.rstrip('/')):
            log_path = os.path.dirname(log_path.rstrip('/')) + '/'
        
        # Ensure the directory exists
        os.makedirs(log_path, exist_ok=True)
        
        logger.info(f"FYERS log path configured: {log_path}")
        
        # Initialize FYERS client using official v3 API
        self.client = fyersModel.FyersModel(
            token=self.access_token,
            is_async=False,
            client_id=settings.FYERS_CLIENT_ID,
            log_path=log_path
        )
        
        logger.info(f"Initialized FYERS client: {self.name()}")
    
    def name(self) -> str:
        """Return broker name with mode."""
        return f"FYERS_{'SANDBOX' if self._sandbox else 'LIVE'}"
    
    def get_auth_url(self) -> str:
        """
        Generate FYERS authentication URL for manual token renewal.
        
        Returns:
            str: Authentication URL
        """
        try:
            from urllib.parse import urlencode
            
            # Generate auth URL
            base_url = "https://api-t1.fyers.in/api/v3" if self._sandbox else "https://api.fyers.in/api/v3"
            
            auth_params = {
                "client_id": self.settings.FYERS_CLIENT_ID,
                "redirect_uri": self.settings.FYERS_REDIRECT_URI,
                "response_type": "code",
                "state": "sample_state"
            }
            
            auth_url = f"{base_url}/generate-authcode?{urlencode(auth_params)}"
            return auth_url
            
        except Exception as e:
            logger.error(f"Failed to generate auth URL: {e}")
            return None
    
    def refresh_token_if_needed(self) -> bool:
        """
        Check if token is valid and provide instructions for renewal if needed.
        
        Returns:
            bool: True if token is valid, False if renewal needed
        """
        try:
            # Test current token
            response = self.client.get_profile()
            
            if response.get('s') == 'ok':
                logger.info("FYERS token is valid")
                return True
            elif response.get('code') in [-16, -17]:  # Authentication errors
                logger.warning("FYERS token expired - manual renewal required")
                
                # Generate auth URL for manual renewal
                auth_url = self.get_auth_url()
                if auth_url:
                    logger.error("=" * 80)
                    logger.error("🔑 FYERS TOKEN RENEWAL REQUIRED 🔑")
                    logger.error("=" * 80)
                    logger.error("❌ Your FYERS access token has expired!")
                    logger.error("")
                    logger.error("🔗 AUTHENTICATION URL:")
                    logger.error(f"   {auth_url}")
                    logger.error("")
                    logger.error("📋 STEPS TO RENEW:")
                    logger.error("   1. Click the URL above to open FYERS login")
                    logger.error("   2. Complete the OAuth authentication")
                    logger.error("   3. Copy the new access token from the response")
                    logger.error("   4. Update FYERS_ACCESS_TOKEN in Render dashboard")
                    logger.error("   5. Restart the application")
                    logger.error("")
                    logger.error("⚠️  The system will continue with MockExchange until token is renewed")
                    logger.error("=" * 80)
                else:
                    logger.error("Failed to generate FYERS auth URL")
                
                return False
            else:
                logger.warning(f"Unexpected FYERS response: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking FYERS token: {e}")
            return False
    
    def _symbol(self, symbol: str) -> str:
        """
        Normalize symbol to FYERS format.
        
        Args:
            symbol: Symbol in any format
            
        Returns:
            FYERS format: "NSE:SYMBOL-EQ"
        """
        if ":" in symbol:
            return symbol
        return f"NSE:{symbol}-EQ"
    
    def history(self, symbol: str, resolution: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from FYERS using official v3 API.
        
        Args:
            symbol: Trading symbol
            resolution: "60" for 1h, "D" for daily, "W" for weekly
            start: Start datetime
            end: End datetime
            
        Returns:
            DataFrame with [ts, open, high, low, close, volume]
        """
        try:
            # Convert datetime to Unix timestamp
            start_timestamp = int(start.timestamp())
            end_timestamp = int(end.timestamp())
            
            payload = {
                "symbol": self._symbol(symbol),
                "resolution": resolution,
                "date_format": "0",  # Unix timestamp format
                "range_from": str(start_timestamp),
                "range_to": str(end_timestamp),
                "cont_flag": "1"  # Continuous data
            }
            
            response = self.client.history(data=payload)
            
            if response.get("s") != "ok":
                logger.error(f"FYERS history error: {response}")
                return pd.DataFrame()
            
            candles = response.get("candles", [])
            if not candles:
                logger.warning(f"No data for {symbol} from {start} to {end}")
                return pd.DataFrame()
            
            # Create DataFrame
            cols = ["ts", "open", "high", "low", "close", "volume"]
            df = pd.DataFrame(candles, columns=cols)
            
            # Convert timestamp to IST
            df["ts"] = pd.to_datetime(df["ts"], unit="s")
            df["ts"] = df["ts"].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
            
            # Set index
            df = df.set_index("ts")
            
            logger.info(f"Fetched {len(df)} candles for {symbol} ({resolution})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {e}")
            return pd.DataFrame()
    
    def candles(self, symbol: str, tf: str, lookback: int) -> pd.DataFrame:
        """
        Convenience method to fetch recent candles.
        
        Args:
            symbol: Trading symbol
            tf: "1h", "day", "week"
            lookback: Number of periods
            
        Returns:
            DataFrame with recent candles
        """
        # Map timeframes
        tf_map = {
            "1h": ("60", timedelta(days=lookback * 2)),  # ~2 days per candle
            "day": ("D", timedelta(days=lookback)),
            "week": ("W", timedelta(weeks=lookback))
        }
        
        if tf not in tf_map:
            logger.error(f"Invalid timeframe: {tf}. Use '1h', 'day', or 'week'")
            return pd.DataFrame()
        
        resolution, delta = tf_map[tf]
        end = datetime.now()
        start = end - delta
        
        return self.history(symbol, resolution, start, end).tail(lookback)
    
    def subscribe_ticks(self, symbols: List[str], on_tick: Callable) -> None:
        """
        Subscribe to real-time ticks via WebSocket.
        Note: FYERS WebSocket implementation would go here.
        For hourly execution, this is not critical.
        """
        logger.warning("WebSocket subscription not implemented. Use get_ltp() for current prices.")
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
        Place order on FYERS (paper or live).
        
        Args:
            symbol: Trading symbol
            side: "BUY" or "SELL"
            qty: Quantity (integer)
            order_type: "MARKET" or "LIMIT"
            price: Limit price
            tag: Custom tag (max 15 chars)
            
        Returns:
            Dict with order_id, status, message
        """
        try:
            data = {
                "symbol": self._symbol(symbol),
                "qty": int(qty),
                "type": 2 if order_type.upper() == "MARKET" else 1,
                "side": 1 if side.upper() == "BUY" else -1,
                "productType": "CNC",  # Cash & Carry (delivery)
                "limitPrice": float(price) if price else 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "stopLoss": 0,
                "takeProfit": 0,
                "tag": tag[:15] if tag else ""
            }
            
            response = self.client.place_order(data=data)
            
            if response.get("s") == "ok":
                order_id = response.get("id", "")
                logger.info(f"Order placed: {symbol} {side} {qty} @ {price or 'MARKET'} (ID: {order_id})")
                return {
                    "order_id": order_id,
                    "status": "success",
                    "message": response.get("message", "Order placed")
                }
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(f"Order failed: {error_msg}")
                return {
                    "order_id": None,
                    "status": "error",
                    "message": error_msg
                }
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                "order_id": None,
                "status": "error",
                "message": str(e)
            }
    
    def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify an existing order."""
        try:
            data = {"id": order_id}
            data.update(kwargs)
            
            response = self.client.modify_order(data=data)
            
            return {
                "status": "success" if response.get("s") == "ok" else "error",
                "message": response.get("message", "")
            }
        except Exception as e:
            logger.error(f"Error modifying order {order_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            response = self.client.cancel_order(data={"id": order_id})
            
            return {
                "status": "success" if response.get("s") == "ok" else "error",
                "message": response.get("message", "")
            }
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def positions(self) -> List[Dict[str, Any]]:
        """Get current positions."""
        try:
            response = self.client.positions()
            
            if response.get("s") != "ok":
                logger.error(f"Error fetching positions: {response.get('message')}")
                return []
            
            positions = response.get("netPositions", [])
            
            # Normalize format
            result = []
            for pos in positions:
                result.append({
                    "symbol": pos.get("symbol", ""),
                    "qty": pos.get("netQty", 0),
                    "avg_price": pos.get("avgPrice", 0),
                    "ltp": pos.get("ltp", 0),
                    "pnl": pos.get("pl", 0)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def orders(self) -> List[Dict[str, Any]]:
        """Get order book."""
        try:
            response = self.client.orderbook()
            
            if response.get("s") != "ok":
                logger.error(f"Error fetching orders: {response.get('message')}")
                return []
            
            orders = response.get("orderBook", [])
            
            # Normalize format
            result = []
            for order in orders:
                result.append({
                    "order_id": order.get("id", ""),
                    "symbol": order.get("symbol", ""),
                    "side": "BUY" if order.get("side") == 1 else "SELL",
                    "qty": order.get("qty", 0),
                    "filled_qty": order.get("filledQty", 0),
                    "price": order.get("limitPrice", 0),
                    "status": order.get("status", ""),
                    "order_type": "MARKET" if order.get("type") == 2 else "LIMIT"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return []
    
    def get_ltp(self, symbol: str) -> Optional[float]:
        """
        Get Last Traded Price using official v3 API.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            LTP or None
        """
        try:
            payload = {
                "symbols": self._symbol(symbol)
            }
            
            response = self.client.quotes(data=payload)
            
            if response.get("s") != "ok":
                logger.error(f"Error fetching LTP: {response.get('message')}")
                return None
            
            data = response.get("d", [])
            if data:
                ltp = data[0].get("v", {}).get("lp", None)
                return float(ltp) if ltp else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching LTP for {symbol}: {e}")
            return None
