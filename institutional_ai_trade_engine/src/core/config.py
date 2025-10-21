"""
Configuration management for the trading engine.
Supports FYERS, Angel One, and Mock brokers.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class Settings:
    """Settings class with validation for broker credentials."""
    
    # Broker selection
    BROKER: str = os.getenv("BROKER", "FYERS")
    
    # Capital & Risk
    PORTFOLIO_CAPITAL: float = float(os.getenv("PORTFOLIO_CAPITAL", 400000))
    RISK_PCT_PER_TRADE: float = float(os.getenv("RISK_PCT_PER_TRADE", 1.5))
    
    # FYERS
    FYERS_CLIENT_ID: Optional[str] = os.getenv("FYERS_CLIENT_ID")
    FYERS_REDIRECT_URI: Optional[str] = os.getenv("FYERS_REDIRECT_URI")
    FYERS_SECRET_KEY: Optional[str] = os.getenv("FYERS_SECRET_KEY")
    FYERS_ACCESS_TOKEN: Optional[str] = os.getenv("FYERS_ACCESS_TOKEN")
    FYERS_SANDBOX: bool = os.getenv("FYERS_SANDBOX", "true").lower() == "true"
    
    # Angel One (future)
    ANGEL_API_KEY: Optional[str] = os.getenv("ANGEL_API_KEY")
    ANGEL_CLIENT_CODE: Optional[str] = os.getenv("ANGEL_CLIENT_CODE")
    ANGEL_API_SECRET: Optional[str] = os.getenv("ANGEL_API_SECRET")
    ANGEL_TOTP_SECRET: Optional[str] = os.getenv("ANGEL_TOTP_SECRET")
    
    # Telegram (optional)
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Google Sheets (optional)
    GSHEETS_CREDENTIALS_JSON: Optional[str] = os.getenv("GSHEETS_CREDENTIALS_JSON")
    GSHEETS_MASTER_SHEET: str = os.getenv("GSHEETS_MASTER_SHEET", "Institutional Portfolio Master Sheet")
    
    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/trade_engine.sqlite")
    
    # Convert Render's postgres:// to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Paths
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    DB_PATH: str = os.getenv("DB_PATH", "./data/trade_engine.sqlite")
    LOG_PATH: str = os.getenv("LOG_PATH", "./data/")
    
    # Timezone
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    # Paper trading mode (legacy compatibility)
    PAPER_MODE: bool = os.getenv("PAPER_MODE", "true").lower() in ("1", "true", "yes", "y")
    
    # Risk management
    MAX_OPEN_RISK_PCT: float = 6.0
    POSITION_SIZING_PLAN: float = 1.0
    
    # Trading hours (IST)
    PRE_OPEN_TIME: str = "09:25"
    CLOSE_TIME: str = "15:10"
    EOD_TIME: str = "15:25"
    NEAR_BREAKOUT_TIME: str = "15:20"
    
    # Index symbols
    NIFTY_SYMBOL: str = "NIFTY 50"
    BANKNIFTY_SYMBOL: str = "NIFTY BANK"
    
    @classmethod
    def validate(cls):
        """Validate required configuration based on broker selection."""
        broker = cls.BROKER.upper()
        
        # Create data directory if it doesn't exist
        Path(cls.DATA_DIR).mkdir(parents=True, exist_ok=True)
        
        if broker == "FYERS":
            # Validate FYERS credentials
            required = {
                "FYERS_CLIENT_ID": cls.FYERS_CLIENT_ID,
                "FYERS_ACCESS_TOKEN": cls.FYERS_ACCESS_TOKEN
            }
            missing = [k for k, v in required.items() if not v]
            
            if missing:
                error_msg = (
                    f"\n{'='*60}\n"
                    f"[SETUP REQUIRED] Missing FYERS credentials: {', '.join(missing)}\n"
                    f"{'='*60}\n\n"
                    f"To configure FYERS:\n"
                    f"1. Visit: https://developers.fyers.in\n"
                    f"2. Create an app and note your Client ID\n"
                    f"3. Generate OAuth access token\n"
                    f"4. Add credentials to .env file:\n"
                    f"   FYERS_CLIENT_ID=your_client_id\n"
                    f"   FYERS_ACCESS_TOKEN=your_token\n"
                    f"   FYERS_SANDBOX=true  # for paper trading\n\n"
                    f"5. Re-run the engine\n"
                    f"{'='*60}\n"
                )
                raise SystemExit(error_msg)
            
            mode = "SANDBOX (Paper)" if cls.FYERS_SANDBOX else "LIVE"
            logger.info(f"✓ FYERS credentials validated - Mode: {mode}")
        
        elif broker == "ANGEL":
            # Validate Angel One credentials
            required = {
                "ANGEL_API_KEY": cls.ANGEL_API_KEY,
                "ANGEL_CLIENT_CODE": cls.ANGEL_CLIENT_CODE,
                "ANGEL_API_SECRET": cls.ANGEL_API_SECRET
            }
            missing = [k for k, v in required.items() if not v]
            
            if missing:
                error_msg = (
                    f"\n{'='*60}\n"
                    f"[SETUP REQUIRED] Missing Angel One credentials: {', '.join(missing)}\n"
                    f"{'='*60}\n\n"
                    f"To configure Angel One:\n"
                    f"1. Visit: https://smartapi.angelbroking.com\n"
                    f"2. Register for API access\n"
                    f"3. Add credentials to .env file\n"
                    f"4. Re-run the engine\n"
                    f"{'='*60}\n"
                )
                raise SystemExit(error_msg)
            
            logger.info("✓ Angel One credentials validated")
        
        elif broker == "MOCK":
            logger.info("✓ Using Mock Exchange (offline mode)")
        
        else:
            raise ValueError(f"Invalid broker: {broker}. Use FYERS, ANGEL, or MOCK")
        
        return True
    
    @classmethod
    def get_broker(cls):
        """
        Get broker client instance based on configuration.
        
        Returns:
            BrokerBase: Initialized broker client
        """
        cls.validate()
        
        broker = cls.BROKER.upper()
        
        if broker == "FYERS":
            try:
                from ..data.fyers_client import FyersAPI  # type: ignore
            except Exception:
                from src.data.fyers_client import FyersAPI  # type: ignore
            
            try:
                fyers_client = FyersAPI(cls)
                # Test authentication by making a simple API call
                test_response = fyers_client.client.get_profile()
                if test_response.get('s') == 'error' and test_response.get('code') == -16:
                    logger.warning("FYERS authentication failed, falling back to MockExchange")
                    return cls._get_mock_broker()
                return fyers_client
            except Exception as e:
                logger.warning(f"FYERS initialization failed: {e}, falling back to MockExchange")
                return cls._get_mock_broker()
        
        elif broker == "ANGEL":
            try:
                from ..data.angel_client import AngelClient  # type: ignore
            except Exception:
                from src.data.angel_client import AngelClient  # type: ignore
            # Note: Will need to update AngelClient to match BrokerBase interface
            logger.warning("Angel One client may need interface updates")
            return AngelClient()
        
        elif broker == "MOCK":
            try:
                from ..data.mock_exchange import MockExchange  # type: ignore
            except Exception:
                from src.data.mock_exchange import MockExchange  # type: ignore
            return MockExchange(cls)
        
        else:
            raise ValueError(f"Unknown broker: {broker}")
    
    @classmethod
    def _get_mock_broker(cls):
        """Helper method to get MockExchange broker."""
        try:
            from ..data.mock_exchange import MockExchange  # type: ignore
        except Exception:
            from src.data.mock_exchange import MockExchange  # type: ignore
        return MockExchange(cls)


# Legacy Config class for backward compatibility
class Config:
    """Legacy configuration class (for backward compatibility)."""
    
    # Map new settings to old format
    PORTFOLIO_CAPITAL = Settings.PORTFOLIO_CAPITAL
    RISK_PCT = Settings.RISK_PCT_PER_TRADE
    DB_PATH = Settings.DB_PATH
    TIMEZONE = Settings.TIMEZONE
    MAX_OPEN_RISK_PCT = Settings.MAX_OPEN_RISK_PCT
    POSITION_SIZING_PLAN = Settings.POSITION_SIZING_PLAN
    # Legacy flag expected by older tests/scripts
    PAPER_MODE = Settings.PAPER_MODE or Settings.FYERS_SANDBOX
    
    # Angel One (existing)
    ANGEL_API_KEY = Settings.ANGEL_API_KEY
    ANGEL_CLIENT_CODE = Settings.ANGEL_CLIENT_CODE
    ANGEL_API_SECRET = Settings.ANGEL_API_SECRET
    ANGEL_TOTP_SECRET = Settings.ANGEL_TOTP_SECRET
    
    # Telegram
    TELEGRAM_BOT_TOKEN = Settings.TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID = Settings.TELEGRAM_CHAT_ID
    
    # Google Sheets
    GSHEETS_CREDENTIALS_JSON = Settings.GSHEETS_CREDENTIALS_JSON
    GSHEETS_MASTER_SHEET = Settings.GSHEETS_MASTER_SHEET
    
    # Trading hours
    PRE_OPEN_TIME = Settings.PRE_OPEN_TIME
    CLOSE_TIME = Settings.CLOSE_TIME
    EOD_TIME = Settings.EOD_TIME
    NEAR_BREAKOUT_TIME = Settings.NEAR_BREAKOUT_TIME
    
    # Index symbols
    NIFTY_SYMBOL = Settings.NIFTY_SYMBOL
    BANKNIFTY_SYMBOL = Settings.BANKNIFTY_SYMBOL
    
    @classmethod
    def validate(cls):
        """Validate configuration (legacy method)."""
        # For existing Angel One setup
        if Settings.BROKER.upper() == "ANGEL":
            required_vars = [
                "ANGEL_API_KEY", "ANGEL_CLIENT_CODE", "ANGEL_API_SECRET"
            ]
            missing = [var for var in required_vars if not getattr(cls, var)]
            if missing:
                raise ValueError(f"Missing required environment variables: {missing}")
        return True


def get_settings() -> Settings:
    """
    Get validated settings instance.
    
    Returns:
        Settings: Validated settings object
    """
    Settings.validate()
    return Settings