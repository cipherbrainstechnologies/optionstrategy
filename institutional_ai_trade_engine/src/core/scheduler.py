"""
Scheduler for running trading engine jobs at specified times.
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .config import Config  # local import safe

def run():
    """Run the trading engine scheduler."""
    # Lazy imports to avoid package-relative import issues during tests
    try:
        from ..exec import scanner, tracker, near_breakout, eod_report  # type: ignore
        from ..data import index_watch  # type: ignore
    except Exception:
        from exec import scanner, tracker, near_breakout, eod_report  # type: ignore
        from data import index_watch  # type: ignore

    tz = timezone(Config.TIMEZONE)
    s = BlockingScheduler(timezone=tz)
    
    # Add scheduled jobs
    s.add_job(
        scanner.run,
        "cron",
        day_of_week="mon-fri",
        hour=9,
        minute=25,
        id="pre_open_scanner"
    )
    
    s.add_job(
        scanner.run,
        "cron",
        day_of_week="mon-fri",
        hour=15,
        minute=10,
        id="close_scanner"
    )
    
    s.add_job(
        tracker.run,
        "cron",
        day_of_week="mon-fri",
        hour="9-15",
        minute=0,
        id="hourly_tracker"
    )
    
    s.add_job(
        near_breakout.run,
        "cron",
        day_of_week="mon-fri",
        hour=15,
        minute=20,
        id="near_breakout_tracker"
    )
    
    s.add_job(
        eod_report.run,
        "cron",
        day_of_week="mon-fri",
        hour=15,
        minute=25,
        id="eod_report"
    )
    
    s.add_job(
        index_watch.monitor,
        "cron",
        day_of_week="mon-fri",
        minute="*/5",
        id="index_watch"
    )
    
    logger.info("Starting trading engine scheduler...")
    try:
        s.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        raise

if __name__ == "__main__":
    run()