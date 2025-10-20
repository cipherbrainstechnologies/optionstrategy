"""
Telegram alert system for trading notifications.
"""
import logging
from typing import Dict, Optional
import requests
from datetime import datetime

try:
    from ..core.config import Config  # type: ignore
except Exception:
    from core.config import Config  # type: ignore

logger = logging.getLogger(__name__)

class TelegramBot:
    """Telegram bot for sending trading alerts."""
    
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: Message to send
            parse_mode: Message parsing mode
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.bot_token or not self.chat_id:
                logger.warning("Telegram credentials not configured")
                return False
            
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info("Telegram message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_trade_alert(self, position: Dict, alert_type: str) -> bool:
        """
        Send trade alert for position.
        
        Args:
            position: Position data
            alert_type: Type of alert
        
        Returns:
            bool: True if successful
        """
        try:
            message = self._format_trade_alert(position, alert_type)
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending trade alert: {e}")
            return False
    
    def _format_trade_alert(self, position: Dict, alert_type: str) -> str:
        """
        Format trade alert message.
        
        Args:
            position: Position data
            alert_type: Type of alert
        
        Returns:
            str: Formatted message
        """
        try:
            symbol = position.get('symbol', 'N/A')
            entry_price = position.get('entry_price', 0)
            stop = position.get('stop', 0)
            qty = position.get('qty', 0)
            direction = position.get('direction', 'LONG')
            
            # Emoji based on alert type
            emoji_map = {
                'NEW_POSITION': '🚀',
                'BREAKEVEN': '⚖️',
                'PARTIAL_BOOK': '💰',
                'TRAIL': '📈',
                'CAUTION': '⚠️',
                'POSITION_CLOSED': '✅'
            }
            
            emoji = emoji_map.get(alert_type, '📊')
            
            message = f"{emoji} *{alert_type.replace('_', ' ')}*\n\n"
            message += f"📈 *Symbol:* {symbol}\n"
            message += f"📊 *Direction:* {direction}\n"
            message += f"💰 *Entry:* ₹{entry_price:.2f}\n"
            message += f"🛑 *Stop:* ₹{stop:.2f}\n"
            message += f"📦 *Quantity:* {qty}\n"
            
            # Add targets if available
            if 't1' in position and 't2' in position:
                t1 = position.get('t1', 0)
                t2 = position.get('t2', 0)
                message += f"🎯 *T1:* ₹{t1:.2f}\n"
                message += f"🎯 *T2:* ₹{t2:.2f}\n"
            
            # Add current metrics if available
            if 'current_price' in position:
                current_price = position.get('current_price', 0)
                pnl_pct = position.get('pnl_pct', 0)
                message += f"💎 *Current:* ₹{current_price:.2f}\n"
                message += f"📊 *PnL %:* {pnl_pct:+.2f}%\n"
            
            # Add PnL if available
            if 'final_pnl' in position:
                final_pnl = position.get('final_pnl', 0)
                final_rr = position.get('final_rr', 0)
                message += f"💰 *Final PnL:* ₹{final_pnl:,.2f}\n"
                message += f"📈 *R:R:* {final_rr:.2f}\n"
            
            message += f"\n🕐 *Time:* {datetime.now().strftime('%H:%M:%S IST')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting trade alert: {e}")
            return f"Error formatting alert: {e}"
    
    def send_eod_report(self, message: str) -> bool:
        """
        Send end-of-day report.
        
        Args:
            message: EOD report message
        
        Returns:
            bool: True if successful
        """
        try:
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending EOD report: {e}")
            return False
    
    def send_alert(self, message: str) -> bool:
        """
        Send general alert.
        
        Args:
            message: Alert message
        
        Returns:
            bool: True if successful
        """
        try:
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test Telegram connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            message = "🤖 Institutional AI Trade Engine - System Online ✅"
            return self.send_message(message)
            
        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False

# Global bot instance
telegram_bot = TelegramBot()

def send_trade_alert(position: Dict, alert_type: str) -> bool:
    """Wrapper function for sending trade alerts."""
    return telegram_bot.send_trade_alert(position, alert_type)

def send_eod_report(message: str) -> bool:
    """Wrapper function for sending EOD reports."""
    return telegram_bot.send_eod_report(message)

def send_alert(message: str) -> bool:
    """Wrapper function for sending general alerts."""
    return telegram_bot.send_alert(message)

def test_connection() -> bool:
    """Wrapper function for testing connection."""
    return telegram_bot.test_connection()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
        send_alert(message)
    else:
        test_connection()