"""
Main daemon for the Institutional AI Trade Engine.
"""
import logging
import sys
import signal
from datetime import datetime

from .core.config import Config
from .core.scheduler import run as run_scheduler
from .alerts.telegram import test_connection as test_telegram
from .storage.db import init_database

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TradingEngineDaemon:
    """Main daemon for the trading engine."""
    
    def __init__(self):
        self.running = False
        self.scheduler = None
        
    def setup(self):
        """Setup the trading engine."""
        try:
            logger.info("Setting up Institutional AI Trade Engine...")
            
            # Validate configuration
            Config.validate()
            logger.info("Configuration validated")
            
            # Initialize database
            init_database()
            logger.info("Database initialized")
            
            # Test Telegram connection
            if test_telegram():
                logger.info("Telegram connection successful")
            else:
                logger.warning("Telegram connection failed")
            
            logger.info("Setup completed successfully")
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            raise
    
    def start(self):
        """Start the trading engine."""
        try:
            logger.info("Starting Institutional AI Trade Engine...")
            
            # Setup signal handlers
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.running = True
            
            # Start scheduler
            logger.info("Starting scheduler...")
            run_scheduler()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting trading engine: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the trading engine."""
        try:
            logger.info("Stopping Institutional AI Trade Engine...")
            self.running = False
            
            if self.scheduler:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped")
            
            logger.info("Trading engine stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading engine: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)
    
    def status(self):
        """Get daemon status."""
        return {
            "running": self.running,
            "timestamp": datetime.now().isoformat(),
            "config": {
                "paper_mode": Config.PAPER_MODE,
                "portfolio_capital": Config.PORTFOLIO_CAPITAL,
                "risk_pct": Config.RISK_PCT,
                "timezone": Config.TIMEZONE
            }
        }

def main():
    """Main entry point."""
    try:
        # Create daemon instance
        daemon = TradingEngineDaemon()
        
        # Setup
        daemon.setup()
        
        # Start
        daemon.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()