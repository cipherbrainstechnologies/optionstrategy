"""
Angel One SmartAPI client for market data and trading operations.
"""
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import pyotp

from ..core.config import Config

logger = logging.getLogger(__name__)

class AngelClient:
    """Angel One SmartAPI client."""
    
    def __init__(self):
        self.api_key = Config.ANGEL_API_KEY
        self.client_code = Config.ANGEL_CLIENT_CODE
        self.api_secret = Config.ANGEL_API_SECRET
        self.totp_secret = Config.ANGEL_TOTP_SECRET
        
        self.base_url = "https://apiconnect.angelone.in"
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
    def authenticate(self):
        """Authenticate with Angel One API."""
        try:
            # Generate TOTP
            totp_code = self._generate_totp()
            if not totp_code:
                logger.error("Failed to generate TOTP code")
                return False
            
            # Get access token using MPIN authentication
            auth_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByMpin"
            
            payload = {
                "clientcode": self.client_code,
                "mpin": self.api_secret,
                "totp": totp_code,
                "state": "live"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "192.168.1.1",
                "X-ClientPublicIP": "192.168.1.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            response = self.session.post(auth_url, json=payload, headers=headers)
            logger.debug(f"Auth response status: {response.status_code}")
            logger.debug(f"Auth response text: {response.text}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response.text}")
                return False
            
            if data.get("status"):
                self.access_token = data["data"]["jwtToken"]
                self.refresh_token = data["data"]["refreshToken"]
                self.token_expiry = datetime.now() + timedelta(hours=1)
                logger.info("Successfully authenticated with Angel One API")
                return True
            else:
                logger.error(f"Authentication failed: {data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _generate_totp(self):
        """Generate TOTP for authentication."""
        try:
            if not self.totp_secret:
                logger.error("TOTP secret not configured")
                return None
            
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            return None
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expiry and datetime.now() >= self.token_expiry):
            if not self.authenticate():
                raise Exception("Failed to authenticate with Angel One API")
    
    def get_ltp(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """Get Last Traded Price for a symbol."""
        try:
            self._ensure_authenticated()
            
            url = f"{self.base_url}/rest/secure/angelbroking/market/v1/quote/"
            
            payload = {
                "mode": "FULL",
                "exchangeTokens": {
                    exchange: [symbol]
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "192.168.1.1",
                "X-ClientPublicIP": "192.168.1.1",
                "X-MACAddress": "00:00:00:00:00:00"
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") and data.get("data"):
                return float(data["data"][exchange][symbol]["lastPrice"])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting LTP for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str = "1DAY", 
                          from_date: str = None, to_date: str = None) -> Optional[List[Dict]]:
        """Get historical OHLCV data."""
        try:
            self._ensure_authenticated()
            
            if not from_date:
                from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData"
            
            payload = {
                "exchange": "NSE",
                "symboltoken": symbol,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "192.168.1.1",
                "X-ClientPublicIP": "192.168.1.1",
                "X-MACAddress": "00:00:00:00:00:00"
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") and data.get("data"):
                return data["data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_instruments(self, exchange: str = "NSE") -> Optional[List[Dict]]:
        """Get list of instruments for an exchange."""
        try:
            self._ensure_authenticated()
            
            url = f"{self.base_url}/rest/secure/angelbroking/market/v1/master-contract"
            
            payload = {"exchange": exchange}
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "192.168.1.1",
                "X-ClientPublicIP": "192.168.1.1",
                "X-MACAddress": "00:00:00:00:00:00"
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") and data.get("data"):
                return data["data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting instruments for {exchange}: {e}")
            return None