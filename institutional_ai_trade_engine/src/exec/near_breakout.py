"""
Near-breakout tracker for monitoring setups close to breakout.
"""
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd

from ..data.fetch import DataFetcher
from ..strategy.three_week_inside import is_near_breakout, calculate_breakout_strength
from ..storage.db import get_db_session
from ..alerts.telegram import send_alert
from sqlalchemy import text

logger = logging.getLogger(__name__)

class NearBreakoutTracker:
    """Tracker for near-breakout setups."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def get_near_breakout_setups(self) -> List[Dict]:
        """
        Get all setups that are near breakout.
        
        Returns:
            List[Dict]: List of near-breakout setups
        """
        try:
            # Get all active setups
            db = get_db_session()
            try:
                query = text("""
                    SELECT * FROM setups 
                    WHERE id NOT IN (
                        SELECT DISTINCT setup_id FROM positions 
                        WHERE setup_id IS NOT NULL
                    )
                    ORDER BY week_start DESC
                """)
                setups = db.execute(query).fetchall()
                
            finally:
                db.close()
            
            near_breakouts = []
            
            for setup in setups:
                symbol = setup.symbol
                
                # Get latest weekly data
                weekly_df = self.fetcher.get_weekly_data(symbol, weeks=52)
                if not self.fetcher.validate_data_quality(weekly_df):
                    continue
                
                # Check if near breakout
                pattern = {
                    'mother_high': setup.mother_high,
                    'mother_low': setup.mother_low
                }
                
                if is_near_breakout(weekly_df, pattern, threshold=0.99):
                    # Calculate breakout strength
                    strength = calculate_breakout_strength(weekly_df, pattern)
                    
                    near_breakout = {
                        'symbol': symbol,
                        'setup_id': setup.id,
                        'mother_high': setup.mother_high,
                        'mother_low': setup.mother_low,
                        'current_price': weekly_df.iloc[-1]['close'],
                        'distance_to_high_pct': strength.get('distance_to_high_pct', 0),
                        'distance_to_low_pct': strength.get('distance_to_low_pct', 0),
                        'volume_ratio': strength.get('volume_ratio', 0),
                        'atr_pct': strength.get('atr_pct', 0),
                        'confidence': self._calculate_confidence(strength),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    near_breakouts.append(near_breakout)
            
            return near_breakouts
            
        except Exception as e:
            logger.error(f"Error getting near-breakout setups: {e}")
            return []
    
    def _calculate_confidence(self, strength: Dict) -> float:
        """
        Calculate confidence score for near-breakout setup.
        
        Args:
            strength: Breakout strength metrics
        
        Returns:
            float: Confidence score (0-100)
        """
        try:
            score = 0
            
            # Distance to breakout (closer is better)
            distance_to_high = abs(strength.get('distance_to_high_pct', 100))
            if distance_to_high <= 1:  # Within 1%
                score += 40
            elif distance_to_high <= 2:  # Within 2%
                score += 30
            elif distance_to_high <= 5:  # Within 5%
                score += 20
            
            # Volume confirmation
            volume_ratio = strength.get('volume_ratio', 0)
            if volume_ratio >= 2.0:  # 2x average volume
                score += 30
            elif volume_ratio >= 1.5:  # 1.5x average volume
                score += 20
            elif volume_ratio >= 1.2:  # 1.2x average volume
                score += 10
            
            # ATR (moderate volatility is good)
            atr_pct = strength.get('atr_pct', 0)
            if 2 <= atr_pct <= 6:  # 2-6% ATR
                score += 20
            elif 1 <= atr_pct <= 8:  # 1-8% ATR
                score += 10
            
            # Price action (current price vs mother range)
            current_price = strength.get('current_price', 0)
            mother_high = strength.get('mother_high', 0)
            mother_low = strength.get('mother_low', 0)
            
            if mother_high > mother_low > 0:
                position_in_range = (current_price - mother_low) / (mother_high - mother_low)
                if 0.7 <= position_in_range <= 0.95:  # Upper part of range
                    score += 10
            
            return min(score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0
    
    def check_friday_breakouts(self) -> List[Dict]:
        """
        Check for confirmed breakouts on Friday (promote to full position).
        
        Returns:
            List[Dict]: List of confirmed breakouts
        """
        try:
            # Check if it's Friday
            if datetime.now().weekday() != 4:  # Friday is 4
                return []
            
            # Get near-breakout setups
            near_breakouts = self.get_near_breakout_setups()
            confirmed_breakouts = []
            
            for setup in near_breakouts:
                # Get latest data
                weekly_df = self.fetcher.get_weekly_data(setup['symbol'], weeks=52)
                if not self.fetcher.validate_data_quality(weekly_df):
                    continue
                
                # Check for actual breakout
                current_price = weekly_df.iloc[-1]['close']
                mother_high = setup['mother_high']
                mother_low = setup['mother_low']
                
                # Check for breakout
                if current_price > mother_high:  # Upward breakout
                    confirmed_breakouts.append({
                        'symbol': setup['symbol'],
                        'direction': 'up',
                        'entry_price': current_price,
                        'stop': mother_low,
                        'confidence': setup['confidence']
                    })
                elif current_price < mother_low:  # Downward breakout
                    confirmed_breakouts.append({
                        'symbol': setup['symbol'],
                        'direction': 'down',
                        'entry_price': current_price,
                        'stop': mother_high,
                        'confidence': setup['confidence']
                    })
            
            return confirmed_breakouts
            
        except Exception as e:
            logger.error(f"Error checking Friday breakouts: {e}")
            return []
    
    def send_near_breakout_alerts(self, near_breakouts: List[Dict]):
        """
        Send alerts for near-breakout setups.
        
        Args:
            near_breakouts: List of near-breakout setups
        """
        try:
            if not near_breakouts:
                return
            
            # Group by confidence level
            high_confidence = [s for s in near_breakouts if s['confidence'] >= 80]
            medium_confidence = [s for s in near_breakouts if 60 <= s['confidence'] < 80]
            low_confidence = [s for s in near_breakouts if s['confidence'] < 60]
            
            # Send alerts
            if high_confidence:
                self._send_confidence_alert("HIGH", high_confidence)
            if medium_confidence:
                self._send_confidence_alert("MEDIUM", medium_confidence)
            if low_confidence:
                self._send_confidence_alert("LOW", low_confidence)
                
        except Exception as e:
            logger.error(f"Error sending near-breakout alerts: {e}")
    
    def _send_confidence_alert(self, level: str, setups: List[Dict]):
        """Send alert for specific confidence level."""
        try:
            message = f"🔍 NEAR-BREAKOUT ALERT ({level} CONFIDENCE)\n\n"
            message += f"Found {len(setups)} setups near breakout:\n\n"
            
            for setup in setups:
                message += f"📈 {setup['symbol']}\n"
                message += f"   Price: ₹{setup['current_price']:.2f}\n"
                message += f"   Distance to High: {setup['distance_to_high_pct']:.2f}%\n"
                message += f"   Volume Ratio: {setup['volume_ratio']:.2f}x\n"
                message += f"   Confidence: {setup['confidence']:.1f}%\n\n"
            
            send_alert(message)
            
        except Exception as e:
            logger.error(f"Error sending confidence alert: {e}")
    
    def run(self):
        """Run the near-breakout tracker."""
        try:
            logger.info("Starting near-breakout tracker...")
            
            # Get near-breakout setups
            near_breakouts = self.get_near_breakout_setups()
            logger.info(f"Found {len(near_breakouts)} near-breakout setups")
            
            # Send alerts
            self.send_near_breakout_alerts(near_breakouts)
            
            # Check for Friday breakouts
            if datetime.now().weekday() == 4:  # Friday
                confirmed_breakouts = self.check_friday_breakouts()
                if confirmed_breakouts:
                    logger.info(f"Found {len(confirmed_breakouts)} confirmed Friday breakouts")
                    # These would be promoted to full positions by the scanner
            
            logger.info("Near-breakout tracker completed")
            
        except Exception as e:
            logger.error(f"Error in near-breakout tracker: {e}")

# Global tracker instance
near_breakout_tracker = NearBreakoutTracker()

def run():
    """Wrapper function for scheduler."""
    near_breakout_tracker.run()

if __name__ == "__main__":
    run()