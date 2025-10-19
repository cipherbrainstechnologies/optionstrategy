"""
Hourly orchestration.
Runs every hour during market hours (09:00-15:00 IST).
"""
import logging
from ..core.config import Settings, get_settings
from ..storage.db import get_db_session
from ..strategy.execution_hourly import HourlyExecutor

logger = logging.getLogger(__name__)


def run_hourly():
    """
    Hourly execution flow.
    
    1. Initialize broker and database
    2. Create hourly executor
    3. Run execution cycle:
       - Manage open positions
       - Process pending signals
       - Apply profit/loss rules
       - Execute partials/exits
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting HOURLY EXECUTION")
        logger.info("=" * 60)
        
        # Initialize
        settings = get_settings()
        broker = settings.get_broker()
        db = get_db_session()
        
        logger.info(f"Broker: {broker.name()}")
        
        # Create executor
        executor = HourlyExecutor(broker, db, settings)
        
        # Run hourly cycle
        executor.run()
        
        db.close()
        
        logger.info("Hourly execution completed")
        
    except Exception as e:
        logger.error(f"Error in hourly execution: {e}", exc_info=True)


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    run_hourly()
