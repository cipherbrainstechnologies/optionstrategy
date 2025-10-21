#!/usr/bin/env python3
"""
Script to seed instruments database with Nifty stocks.
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.db import get_db_session, init_database
from src.core.config import Config
from src.storage.models import Instrument
from sqlalchemy import text

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nifty 50 stocks
NIFTY_50 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK",
    "HDFC", "ITC", "LT", "SBIN", "BHARTIARTL", "ASIANPAINT", "AXISBANK", "MARUTI",
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "WIPRO", "NESTLEIND", "ONGC", "POWERGRID",
    "NTPC", "TECHM", "TATAMOTORS", "TATASTEEL", "BAJFINANCE", "HCLTECH", "DRREDDY",
    "JSWSTEEL", "TATACONSUM", "BRITANNIA", "DIVISLAB", "EICHERMOT", "GRASIM",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "INDUSINDBK", "SBILIFE", "SHREECEM",
    "UPL", "APOLLOHOSP", "BAJAJFINSV", "COALINDIA", "CIPLA"
]

# Nifty 100 stocks (additional 50)
NIFTY_100_ADDITIONAL = [
    "ADANIPORTS", "ADANITRANS", "BAJAJ-AUTO", "BAJAJHLDNG", "BANDHANBNK", "BERGEPAINT",
    "BIOCON", "BOSCHLTD", "CADILAHC", "CHOLAFIN", "COLPAL", "CONCOR", "DABUR",
    "DIVISLAB", "DMART", "GAIL", "GODREJCP", "GODREJPROP", "HDFCAMC", "HINDPETRO",
    "ICICIGI", "ICICIPRULI", "IDEA", "INDIGO", "INFIBEAM", "IRCTC", "JINDALSTEL",
    "JUBLFOOD", "LALPATHLAB", "LUPIN", "M&M", "MCDOWELL-N", "MFSL", "MINDTREE",
    "MOTHERSON", "MRF", "MUTHOOTFIN", "NAUKRI", "PEL", "PETRONET", "PIDILITIND",
    "PNB", "PVR", "RBLBANK", "SAIL", "SIEMENS", "SRF", "TATAPOWER", "TORNTPHARM",
    "VEDL", "YESBANK", "ZEEL", "ZOMATO"
]

# Nifty 500 stocks (sample - would need complete list)
NIFTY_500_SAMPLE = [
    "ABB", "ACC", "ADANIGREEN", "ADANIPOWER", "AJANTPHARM", "ALBK", "AMBUJACEM",
    "APOLLOTYRE", "ASHOKLEY", "AUROPHARMA", "BALRAMCHIN", "BANKBARODA", "BATAINDIA",
    "BEL", "BEML", "BHEL", "BPCL", "CANFINHOME", "CENTRALBK", "CESC", "CGPOWER",
    "CHAMBLFERT", "COCHINSHIP", "CUMMINSIND", "DALBHARAT", "DCBBANK",
    "DHFL", "DISHTV", "DLF", "EDELWEISS", "EXIDEIND", "FEDERALBNK", "FORTIS",
    "GLENMARK", "GMRINFRA", "GODREJIND", "GRANULES", "HATHWAY", "HEG", "HEXAWARE",
    "HINDUJAVENT", "HUDCO", "IBREALEST", "IDBI", "IDFCFIRSTB", "IGL", "INDIANB",
    "IOC", "IPCALAB", "JKCEMENT", "JUBLPHARMA", "JUSTDIAL", "KAJARIA", "KANSAINER",
    "L&TFH", "LICHSGFIN", "LTTS", "LUXIND", "MANAPPURAM", "MARICO",
    "NMDC", "OBEROI", "OFSS", "OIL", "PAGEIND", "RECLTD", "RELAXO", "SAIL", "SIEMENS", "SRF",
    "TATAPOWER", "TORNTPHARM", "TRENT", "TVSMOTORS", "UBL", "VEDL", "VOLTAS",
    "YESBANK", "ZEEL", "ZOMATO"
]

def seed_instruments(list_name: str):
    """
    Seed instruments database with specified list.
    
    Args:
        list_name: Name of the list to seed ('nifty50', 'nifty100', 'nifty500')
    """
    try:
        # Initialize database
        init_database()
        
        # Get appropriate stock list
        if list_name.lower() == 'nifty50':
            stocks = NIFTY_50
        elif list_name.lower() == 'nifty100':
            stocks = NIFTY_50 + NIFTY_100_ADDITIONAL
        elif list_name.lower() == 'nifty500':
            stocks = NIFTY_50 + NIFTY_100_ADDITIONAL + NIFTY_500_SAMPLE
        else:
            logger.error(f"Unknown list: {list_name}")
            return False
        
        # Insert stocks into database
        db = get_db_session()
        try:
            # Clear existing instruments
            db.execute(text("DELETE FROM instruments"))
            db.commit()
            
            # Remove duplicates and insert new instruments
            unique_stocks = list(set(stocks))
            for symbol in unique_stocks:
                # Use raw SQL with explicit PostgreSQL handling
                try:
                    db.execute(text("""
                        INSERT INTO instruments (symbol, exchange, enabled, in_portfolio, avg_portfolio_price, portfolio_qty)
                        VALUES (:symbol, :exchange, :enabled, :in_portfolio, :avg_portfolio_price, :portfolio_qty)
                    """), {
                        "symbol": symbol,
                        "exchange": "NSE", 
                        "enabled": 1,
                        "in_portfolio": 0,
                        "avg_portfolio_price": None,
                        "portfolio_qty": None
                    })
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to insert {symbol}: {e}")
                    db.rollback()
                    continue
            logger.info(f"Seeded {len(unique_stocks)} instruments from {list_name}")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error seeding instruments: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Seed instruments database")
    parser.add_argument(
        "--list", 
        choices=["nifty50", "nifty100", "nifty500"],
        default="nifty50",
        help="List of stocks to seed"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Seeding instruments with {args.list}")
    
    if seed_instruments(args.list):
        logger.info("Seeding completed successfully")
        sys.exit(0)
    else:
        logger.error("Seeding failed")
        sys.exit(1)

if __name__ == "__main__":
    main()