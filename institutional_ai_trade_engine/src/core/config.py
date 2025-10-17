"""
Configuration management for the trading engine.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the trading engine."""
    
    # Angel One API
    ANGEL_API_KEY = os.getenv("ANGEL_API_KEY")
    ANGEL_CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
    ANGEL_API_SECRET = os.getenv("ANGEL_API_SECRET")
    ANGEL_TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # Google Sheets
    GSHEETS_CREDENTIALS_JSON = os.getenv("GSHEETS_CREDENTIALS_JSON")
    GSHEETS_MASTER_SHEET = os.getenv("GSHEETS_MASTER_SHEET", "Institutional Portfolio Master Sheet")
    
    # Trading parameters
    PORTFOLIO_CAPITAL = float(os.getenv("PORTFOLIO_CAPITAL", 400000))
    RISK_PCT = float(os.getenv("RISK_PCT", 1.5))
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
    PAPER_MODE = os.getenv("PAPER_MODE", "true").lower() == "true"
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "trading_engine.db")
    
    # Risk management
    MAX_OPEN_RISK_PCT = 6.0  # Maximum total open risk as % of capital
    POSITION_SIZING_PLAN = 1.0  # Position sizing multiplier
    
    # Trading hours (IST)
    PRE_OPEN_TIME = "09:25"
    CLOSE_TIME = "15:10"
    EOD_TIME = "15:25"
    NEAR_BREAKOUT_TIME = "15:20"
    
    # Index symbols
    NIFTY_SYMBOL = "NIFTY 50"
    BANKNIFTY_SYMBOL = "NIFTY BANK"
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required_vars = [
            "ANGEL_API_KEY", "ANGEL_CLIENT_CODE", "ANGEL_API_SECRET",
            "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"
        ]
        
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
        
        return True