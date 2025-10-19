"""
Institutional AI Trade Engine - Main Entry Point
FYERS-First Implementation with Broker Abstraction

Usage:
    python main.py --daily     # Run daily scan (09:25 or 15:10 IST)
    python main.py --hourly    # Run hourly execution (every hour 09:00-15:00)
    python main.py --eod       # Run end-of-day report (15:25 IST)
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging
def setup_logging():
    """Configure logging for the engine."""
    log_dir = Path("./data")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "engine.log"
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger


def print_banner():
    """Print engine banner."""
    print("\n" + "=" * 70)
    print("🚀 INSTITUTIONAL AI TRADE ENGINE - FYERS-FIRST")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("=" * 70 + "\n")


def initialize_database():
    """Initialize database if needed."""
    from src.storage.db import init_database
    try:
        init_database()
        logging.info("✓ Database initialized")
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        raise


def main():
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Institutional AI Trade Engine - FYERS-First",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --daily     # Daily scan
  python main.py --hourly    # Hourly execution
  python main.py --eod       # End-of-day report
  python main.py --init      # Initialize database only
        """
    )
    
    parser.add_argument("--daily", action="store_true", help="Run daily scan")
    parser.add_argument("--hourly", action="store_true", help="Run hourly execution")
    parser.add_argument("--eod", action="store_true", help="Run end-of-day report")
    parser.add_argument("--init", action="store_true", help="Initialize database only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Check if any action specified
    if not any([args.daily, args.hourly, args.eod, args.init]):
        parser.print_help()
        print("\n⚠️  Error: No action specified. Use --daily, --hourly, or --eod\n")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    print_banner()
    
    try:
        # Initialize database
        initialize_database()
        
        # Execute requested action
        if args.init:
            print("\n✓ Database initialized successfully\n")
            return
        
        if args.daily:
            logger.info("Running DAILY SCAN")
            from src.orchestration.run_daily import run_daily
            run_daily()
        
        if args.hourly:
            logger.info("Running HOURLY EXECUTION")
            from src.orchestration.run_hourly import run_hourly
            run_hourly()
        
        if args.eod:
            logger.info("Running EOD REPORT")
            from src.orchestration.reports import run_eod
            run_eod()
        
        print("\n" + "=" * 70)
        print("✅ Execution completed successfully")
        print("=" * 70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user\n")
        sys.exit(1)
    
    except SystemExit as e:
        # Configuration error (missing credentials)
        print(str(e))
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        print("Check logs at ./data/engine.log for details\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
