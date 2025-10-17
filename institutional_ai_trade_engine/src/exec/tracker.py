"""
Position tracker for managing open trades.
"""
import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd

from ..data.fetch import DataFetcher
from ..core.risk import calculate_position_metrics
from ..storage.db import get_db_session
from ..storage.ledger import log_trade
from ..alerts.telegram import send_trade_alert
from ..alerts.sheets import update_master_sheet
from sqlalchemy import text

logger = logging.getLogger(__name__)

class Tracker:
    """Position tracker for managing open trades."""
    
    def __init__(self):
        self.fetcher = DataFetcher()
    
    def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions from database.
        
        Returns:
            List[Dict]: List of open positions
        """
        try:
            db = get_db_session()
            try:
                query = text("""
                    SELECT * FROM positions 
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
    
    def update_position(self, position: Dict, current_price: float) -> Dict:
        """
        Update position with current market data.
        
        Args:
            position: Position data
            current_price: Current market price
        
        Returns:
            Dict: Updated position data
        """
        try:
            # Calculate current metrics
            metrics = calculate_position_metrics(
                position['entry_price'],
                current_price,
                position['stop'],
                position['qty']
            )
            
            # Update position data
            position.update(metrics)
            
            # Determine action based on price movement
            action = self._determine_action(position)
            
            if action:
                position['action'] = action
                self._execute_action(position, action)
            
            return position
            
        except Exception as e:
            logger.error(f"Error updating position {position['symbol']}: {e}")
            return position
    
    def _determine_action(self, position: Dict) -> str:
        """
        Determine what action to take based on position metrics.
        
        Args:
            position: Position data with current metrics
        
        Returns:
            str: Action to take ('BE', 'BOOK_25', 'BOOK_50', 'TRAIL', 'CAUTION', 'EXIT')
        """
        try:
            pnl_pct = position.get('pnl_pct', 0)
            current_price = position.get('current_price', 0)
            stop = position.get('stop', 0)
            
            # Check for stop loss hit
            if current_price <= stop:
                return 'EXIT'
            
            # Check for profit targets
            if pnl_pct >= 10:  # +10% - Book 50% and trail remainder
                return 'BOOK_50_TRAIL'
            elif pnl_pct >= 6:  # +6% - Book 25%
                return 'BOOK_25'
            elif pnl_pct >= 3:  # +3% - Move stop to breakeven
                return 'BE'
            elif pnl_pct <= -6:  # -6% - Exit
                return 'EXIT'
            elif pnl_pct <= -3:  # -3% - Caution
                return 'CAUTION'
            
            return None
            
        except Exception as e:
            logger.error(f"Error determining action: {e}")
            return None
    
    def _execute_action(self, position: Dict, action: str):
        """
        Execute the determined action.
        
        Args:
            position: Position data
            action: Action to execute
        """
        try:
            if action == 'BE':
                self._move_to_breakeven(position)
            elif action == 'BOOK_25':
                self._book_partial(position, 0.25)
            elif action == 'BOOK_50':
                self._book_partial(position, 0.50)
            elif action == 'BOOK_50_TRAIL':
                self._book_partial(position, 0.50)
                self._start_trailing(position)
            elif action == 'TRAIL':
                self._update_trailing_stop(position)
            elif action == 'CAUTION':
                self._send_caution_alert(position)
            elif action == 'EXIT':
                self._close_position(position)
                
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
    
    def _move_to_breakeven(self, position: Dict):
        """Move stop loss to breakeven."""
        try:
            # Update stop to entry price
            db = get_db_session()
            try:
                query = text("""
                    UPDATE positions 
                    SET stop = :entry_price
                    WHERE id = :position_id
                """)
                db.execute(query, {
                    "entry_price": position['entry_price'],
                    "position_id": position['id']
                })
                db.commit()
                
                # Send alert
                send_trade_alert(position, "BREAKEVEN")
                update_master_sheet(position, "BREAKEVEN")
                
                logger.info(f"Moved {position['symbol']} to breakeven")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error moving to breakeven: {e}")
    
    def _book_partial(self, position: Dict, percentage: float):
        """Book partial profits."""
        try:
            # Calculate quantity to book
            book_qty = int(position['qty'] * percentage)
            remaining_qty = position['qty'] - book_qty
            
            if book_qty <= 0:
                return
            
            # Calculate PnL for booked portion
            booked_pnl = (position['current_price'] - position['entry_price']) * book_qty
            booked_rr = booked_pnl / (position['entry_price'] * book_qty) if position['entry_price'] > 0 else 0
            
            # Update position
            db = get_db_session()
            try:
                query = text("""
                    UPDATE positions 
                    SET qty = :remaining_qty, pnl = :booked_pnl, rr = :booked_rr
                    WHERE id = :position_id
                """)
                db.execute(query, {
                    "remaining_qty": remaining_qty,
                    "booked_pnl": booked_pnl,
                    "booked_rr": booked_rr,
                    "position_id": position['id']
                })
                db.commit()
                
                # Log partial booking
                log_trade(
                    position['symbol'],
                    position['opened_ts'],
                    datetime.now().isoformat(),
                    booked_pnl,
                    booked_rr,
                    f"PARTIAL_BOOK_{int(percentage*100)}%"
                )
                
                # Send alert
                position['action'] = f"BOOK_{int(percentage*100)}%"
                send_trade_alert(position, "PARTIAL_BOOK")
                update_master_sheet(position, "PARTIAL_BOOK")
                
                logger.info(f"Booked {percentage*100}% of {position['symbol']}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error booking partial: {e}")
    
    def _start_trailing(self, position: Dict):
        """Start trailing stop."""
        try:
            # Set trailing stop at 2% below current price
            trailing_stop = position['current_price'] * 0.98
            
            db = get_db_session()
            try:
                query = text("""
                    UPDATE positions 
                    SET stop = :trailing_stop
                    WHERE id = :position_id
                """)
                db.execute(query, {
                    "trailing_stop": trailing_stop,
                    "position_id": position['id']
                })
                db.commit()
                
                logger.info(f"Started trailing stop for {position['symbol']} at {trailing_stop}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error starting trailing: {e}")
    
    def _update_trailing_stop(self, position: Dict):
        """Update trailing stop if price moves favorably."""
        try:
            current_price = position['current_price']
            current_stop = position['stop']
            
            # New trailing stop should be 2% below current price
            new_trailing_stop = current_price * 0.98
            
            # Only update if new stop is higher than current
            if new_trailing_stop > current_stop:
                db = get_db_session()
                try:
                    query = text("""
                        UPDATE positions 
                        SET stop = :new_stop
                        WHERE id = :position_id
                    """)
                    db.execute(query, {
                        "new_stop": new_trailing_stop,
                        "position_id": position['id']
                    })
                    db.commit()
                    
                    logger.info(f"Updated trailing stop for {position['symbol']} to {new_trailing_stop}")
                    
                finally:
                    db.close()
                    
        except Exception as e:
            logger.error(f"Error updating trailing stop: {e}")
    
    def _send_caution_alert(self, position: Dict):
        """Send caution alert for position."""
        try:
            position['action'] = 'CAUTION'
            send_trade_alert(position, "CAUTION")
            update_master_sheet(position, "CAUTION")
            
            logger.info(f"Sent caution alert for {position['symbol']}")
            
        except Exception as e:
            logger.error(f"Error sending caution alert: {e}")
    
    def _close_position(self, position: Dict):
        """Close position completely."""
        try:
            # Calculate final PnL
            final_pnl = (position['current_price'] - position['entry_price']) * position['qty']
            final_rr = final_pnl / (position['entry_price'] * position['qty']) if position['entry_price'] > 0 else 0
            
            # Update position status
            db = get_db_session()
            try:
                query = text("""
                    UPDATE positions 
                    SET status = 'closed', closed_ts = :closed_ts, pnl = :final_pnl, rr = :final_rr
                    WHERE id = :position_id
                """)
                db.execute(query, {
                    "closed_ts": datetime.now().isoformat(),
                    "final_pnl": final_pnl,
                    "final_rr": final_rr,
                    "position_id": position['id']
                })
                db.commit()
                
                # Log trade
                log_trade(
                    position['symbol'],
                    position['opened_ts'],
                    datetime.now().isoformat(),
                    final_pnl,
                    final_rr,
                    "POSITION_CLOSED"
                )
                
                # Send alert
                position['action'] = 'CLOSED'
                position['final_pnl'] = final_pnl
                position['final_rr'] = final_rr
                send_trade_alert(position, "POSITION_CLOSED")
                update_master_sheet(position, "POSITION_CLOSED")
                
                logger.info(f"Closed position {position['symbol']} with PnL: {final_pnl}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    def run(self):
        """Run the position tracker."""
        try:
            logger.info("Starting position tracker...")
            
            # Get all open positions
            positions = self.get_open_positions()
            if not positions:
                logger.info("No open positions to track")
                return
            
            logger.info(f"Tracking {len(positions)} open positions")
            
            # Update each position
            for position in positions:
                try:
                    # Get current price
                    current_price = self.fetcher.get_current_price(position['symbol'])
                    if not current_price:
                        logger.warning(f"Could not get current price for {position['symbol']}")
                        continue
                    
                    # Update position
                    updated_position = self.update_position(position, current_price)
                    
                except Exception as e:
                    logger.error(f"Error tracking position {position['symbol']}: {e}")
                    continue
            
            logger.info("Position tracker completed")
            
        except Exception as e:
            logger.error(f"Error in position tracker: {e}")

# Global tracker instance
tracker = Tracker()

def run():
    """Wrapper function for scheduler."""
    tracker.run()

if __name__ == "__main__":
    run()