"""
End-of-day report generator.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

from ..storage.db import get_db_session
from ..storage.ledger import get_performance_summary, get_recent_trades
from ..alerts.telegram import send_eod_report
from ..alerts.sheets import update_eod_summary
from sqlalchemy import text

logger = logging.getLogger(__name__)

class EODReport:
    """End-of-day report generator."""
    
    def __init__(self):
        pass
    
    def generate_daily_summary(self) -> Dict:
        """
        Generate daily trading summary.
        
        Returns:
            Dict: Daily summary data
        """
        try:
            # Get today's date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get open positions
            open_positions = self._get_open_positions()
            
            # Get closed positions today
            closed_today = self._get_closed_positions_today()
            
            # Get performance summary
            performance = get_performance_summary(days=1)  # Today only
            
            # Calculate daily PnL
            daily_pnl = sum(pos.get('pnl', 0) for pos in closed_today)
            
            # Calculate open PnL
            open_pnl = sum(pos.get('unrealized_pnl', 0) for pos in open_positions)
            
            summary = {
                'date': today,
                'open_positions': len(open_positions),
                'closed_today': len(closed_today),
                'daily_pnl': round(daily_pnl, 2),
                'open_pnl': round(open_pnl, 2),
                'total_pnl': round(daily_pnl + open_pnl, 2),
                'performance': performance,
                'open_positions_list': open_positions,
                'closed_positions_list': closed_today
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            return {}
    
    def _get_open_positions(self) -> List[Dict]:
        """Get all open positions."""
        try:
            db = get_db_session()
            try:
                query = text("""
                    SELECT symbol, entry_price, stop, t1, t2, qty, opened_ts, pnl, rr
                    FROM positions 
                    WHERE status = 'open'
                    ORDER BY opened_ts DESC
                """)
                positions = db.execute(query).fetchall()
                return [dict(row._mapping) for row in positions]
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def _get_closed_positions_today(self) -> List[Dict]:
        """Get positions closed today."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            db = get_db_session()
            try:
                query = text("""
                    SELECT symbol, entry_price, closed_ts, pnl, rr
                    FROM positions 
                    WHERE status = 'closed' 
                    AND DATE(closed_ts) = :today
                    ORDER BY closed_ts DESC
                """)
                positions = db.execute(query, {"today": today}).fetchall()
                return [dict(row._mapping) for row in positions]
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error getting closed positions today: {e}")
            return []
    
    def generate_weekly_summary(self) -> Dict:
        """
        Generate weekly trading summary.
        
        Returns:
            Dict: Weekly summary data
        """
        try:
            # Get this week's date range
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Get weekly performance
            performance = get_performance_summary(days=7)
            
            # Get recent trades
            recent_trades = get_recent_trades(limit=20)
            
            # Calculate weekly metrics
            weekly_pnl = sum(trade.get('pnl', 0) for trade in recent_trades 
                           if datetime.fromisoformat(trade['closed_ts'].replace('Z', '+00:00')).date() >= week_start.date())
            
            summary = {
                'week_start': week_start.strftime('%Y-%m-%d'),
                'week_end': week_end.strftime('%Y-%m-%d'),
                'weekly_pnl': round(weekly_pnl, 2),
                'performance': performance,
                'recent_trades': recent_trades[:10]  # Last 10 trades
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return {}
    
    def generate_monthly_summary(self) -> Dict:
        """
        Generate monthly trading summary.
        
        Returns:
            Dict: Monthly summary data
        """
        try:
            # Get this month's performance
            performance = get_performance_summary(days=30)
            
            # Get monthly trades
            recent_trades = get_recent_trades(limit=50)
            
            # Calculate monthly metrics
            monthly_pnl = sum(trade.get('pnl', 0) for trade in recent_trades)
            
            summary = {
                'month': datetime.now().strftime('%Y-%m'),
                'monthly_pnl': round(monthly_pnl, 2),
                'performance': performance,
                'total_trades': len(recent_trades)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating monthly summary: {e}")
            return {}
    
    def format_telegram_report(self, summary: Dict) -> str:
        """
        Format summary for Telegram message.
        
        Args:
            summary: Summary data
        
        Returns:
            str: Formatted message
        """
        try:
            message = "📊 EOD TRADING REPORT\n"
            message += "=" * 30 + "\n\n"
            
            # Date
            message += f"📅 Date: {summary.get('date', 'N/A')}\n\n"
            
            # Position summary
            message += f"📈 Open Positions: {summary.get('open_positions', 0)}\n"
            message += f"📉 Closed Today: {summary.get('closed_today', 0)}\n\n"
            
            # PnL summary
            daily_pnl = summary.get('daily_pnl', 0)
            open_pnl = summary.get('open_pnl', 0)
            total_pnl = summary.get('total_pnl', 0)
            
            message += f"💰 Daily PnL: ₹{daily_pnl:,.2f}\n"
            message += f"💎 Open PnL: ₹{open_pnl:,.2f}\n"
            message += f"🎯 Total PnL: ₹{total_pnl:,.2f}\n\n"
            
            # Performance metrics
            perf = summary.get('performance', {})
            if perf:
                message += "📊 Performance Metrics:\n"
                message += f"   Win Rate: {perf.get('win_rate', 0):.1f}%\n"
                message += f"   Avg PnL: ₹{perf.get('avg_pnl', 0):,.2f}\n"
                message += f"   Avg R:R: {perf.get('avg_rr', 0):.2f}\n"
                message += f"   Total Trades: {perf.get('total_trades', 0)}\n\n"
            
            # Open positions
            open_positions = summary.get('open_positions_list', [])
            if open_positions:
                message += "🔍 Open Positions:\n"
                for pos in open_positions[:5]:  # Show first 5
                    pnl_pct = (pos.get('pnl', 0) / (pos.get('entry_price', 1) * pos.get('qty', 1))) * 100
                    message += f"   {pos.get('symbol', 'N/A')}: ₹{pos.get('pnl', 0):,.2f} ({pnl_pct:+.1f}%)\n"
                if len(open_positions) > 5:
                    message += f"   ... and {len(open_positions) - 5} more\n"
                message += "\n"
            
            # Closed positions today
            closed_today = summary.get('closed_positions_list', [])
            if closed_today:
                message += "✅ Closed Today:\n"
                for pos in closed_today[:5]:  # Show first 5
                    pnl_pct = (pos.get('pnl', 0) / (pos.get('entry_price', 1) * pos.get('qty', 1))) * 100
                    message += f"   {pos.get('symbol', 'N/A')}: ₹{pos.get('pnl', 0):,.2f} ({pnl_pct:+.1f}%)\n"
                if len(closed_today) > 5:
                    message += f"   ... and {len(closed_today) - 5} more\n"
                message += "\n"
            
            message += "🤖 Generated by Institutional AI Trade Engine"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting Telegram report: {e}")
            return "Error generating report"
    
    def run(self):
        """Run the EOD report generator."""
        try:
            logger.info("Starting EOD report generation...")
            
            # Generate daily summary
            daily_summary = self.generate_daily_summary()
            if not daily_summary:
                logger.warning("Failed to generate daily summary")
                return
            
            # Send Telegram report
            telegram_message = self.format_telegram_report(daily_summary)
            send_eod_report(telegram_message)
            
            # Update Google Sheets
            update_eod_summary(daily_summary)
            
            # Generate weekly summary (on Friday)
            if datetime.now().weekday() == 4:  # Friday
                weekly_summary = self.generate_weekly_summary()
                logger.info(f"Weekly summary: {weekly_summary}")
            
            # Generate monthly summary (on last day of month)
            if datetime.now().day >= 28:  # Approximate last week of month
                monthly_summary = self.generate_monthly_summary()
                logger.info(f"Monthly summary: {monthly_summary}")
            
            logger.info("EOD report generation completed")
            
        except Exception as e:
            logger.error(f"Error in EOD report generation: {e}")

# Global report generator instance
eod_report = EODReport()

def run():
    """Wrapper function for scheduler."""
    eod_report.run()

if __name__ == "__main__":
    run()