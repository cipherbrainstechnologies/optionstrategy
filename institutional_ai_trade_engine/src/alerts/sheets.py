"""
Google Sheets integration for portfolio tracking.
"""
import logging
from typing import Dict, List, Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

try:
    from ..core.config import Config  # type: ignore
except Exception:
    from core.config import Config  # type: ignore

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Google Sheets manager for portfolio tracking."""
    
    def __init__(self):
        self.credentials_path = Config.GSHEETS_CREDENTIALS_JSON
        self.master_sheet_name = Config.GSHEETS_MASTER_SHEET
        self.client = None
        self.master_sheet = None
        
    def _authenticate(self) -> bool:
        """
        Authenticate with Google Sheets API.
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.credentials_path:
                logger.warning("Google Sheets credentials not configured")
                return False
            
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, scope
            )
            
            # Authorize and create client
            self.client = gspread.authorize(creds)
            
            # Open the master sheet
            self.master_sheet = self.client.open(self.master_sheet_name).sheet1
            
            logger.info("Google Sheets authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Sheets: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we're authenticated with Google Sheets."""
        if not self.client or not self.master_sheet:
            if not self._authenticate():
                raise Exception("Failed to authenticate with Google Sheets")
    
    def update_master_sheet(self, position: Dict, action: str) -> bool:
        """
        Update master sheet with position data.
        
        Args:
            position: Position data
            action: Action taken
        
        Returns:
            bool: True if successful
        """
        try:
            self._ensure_authenticated()
            
            # Prepare row data
            row_data = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                position.get('symbol', 'N/A'),
                action,
                position.get('direction', 'LONG'),
                position.get('entry_price', 0),
                position.get('stop', 0),
                position.get('t1', 0),
                position.get('t2', 0),
                position.get('qty', 0),
                position.get('current_price', position.get('entry_price', 0)),
                position.get('pnl', 0),
                position.get('pnl_pct', 0),
                position.get('rr', 0),
                position.get('opened_ts', ''),
                position.get('closed_ts', ''),
                position.get('status', 'open')
            ]
            
            # Append row to sheet
            self.master_sheet.append_row(row_data)
            
            logger.info(f"Updated master sheet for {position.get('symbol')} - {action}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating master sheet: {e}")
            return False
    
    def update_eod_summary(self, summary: Dict) -> bool:
        """
        Update EOD summary in Google Sheets.
        
        Args:
            summary: EOD summary data
        
        Returns:
            bool: True if successful
        """
        try:
            self._ensure_authenticated()
            
            # Create or find EOD summary sheet
            try:
                eod_sheet = self.client.open(self.master_sheet_name).worksheet("EOD Summary")
            except gspread.WorksheetNotFound:
                eod_sheet = self.client.open(self.master_sheet_name).add_worksheet(
                    title="EOD Summary", rows=1000, cols=20
                )
                # Add headers
                headers = [
                    "Date", "Open Positions", "Closed Today", "Daily PnL", 
                    "Open PnL", "Total PnL", "Win Rate", "Total Trades"
                ]
                eod_sheet.append_row(headers)
            
            # Prepare EOD data
            perf = summary.get('performance', {})
            eod_data = [
                summary.get('date', ''),
                summary.get('open_positions', 0),
                summary.get('closed_today', 0),
                summary.get('daily_pnl', 0),
                summary.get('open_pnl', 0),
                summary.get('total_pnl', 0),
                perf.get('win_rate', 0),
                perf.get('total_trades', 0)
            ]
            
            # Append EOD data
            eod_sheet.append_row(eod_data)
            
            logger.info("Updated EOD summary in Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error updating EOD summary: {e}")
            return False
    
    def get_portfolio_summary(self) -> Optional[Dict]:
        """
        Get current portfolio summary from Google Sheets.
        
        Returns:
            Dict: Portfolio summary data
        """
        try:
            self._ensure_authenticated()
            
            # Get all data from master sheet
            records = self.master_sheet.get_all_records()
            
            if not records:
                return None
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(records)
            
            # Calculate summary metrics
            open_positions = df[df['Status'] == 'open']
            closed_positions = df[df['Status'] == 'closed']
            
            summary = {
                'total_positions': len(df),
                'open_positions': len(open_positions),
                'closed_positions': len(closed_positions),
                'total_pnl': df['PnL'].sum() if 'PnL' in df.columns else 0,
                'win_rate': self._calculate_win_rate(closed_positions),
                'avg_rr': closed_positions['R:R'].mean() if 'R:R' in closed_positions.columns else 0
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return None
    
    def _calculate_win_rate(self, closed_positions: pd.DataFrame) -> float:
        """
        Calculate win rate from closed positions.
        
        Args:
            closed_positions: DataFrame of closed positions
        
        Returns:
            float: Win rate percentage
        """
        try:
            if closed_positions.empty or 'PnL' not in closed_positions.columns:
                return 0.0
            
            winning_trades = len(closed_positions[closed_positions['PnL'] > 0])
            total_trades = len(closed_positions)
            
            return (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating win rate: {e}")
            return 0.0
    
    def export_positions_to_csv(self, filename: str = None) -> bool:
        """
        Export positions to CSV file.
        
        Args:
            filename: Output filename
        
        Returns:
            bool: True if successful
        """
        try:
            self._ensure_authenticated()
            
            # Get all data
            records = self.master_sheet.get_all_records()
            
            if not records:
                logger.warning("No data to export")
                return False
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"portfolio_export_{timestamp}.csv"
            
            # Export to CSV
            df.to_csv(filename, index=False)
            
            logger.info(f"Exported positions to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting positions: {e}")
            return False

# Global sheets manager instance
sheets_manager = GoogleSheetsManager()

def update_master_sheet(position: Dict, action: str) -> bool:
    """Wrapper function for updating master sheet."""
    return sheets_manager.update_master_sheet(position, action)

def update_eod_summary(summary: Dict) -> bool:
    """Wrapper function for updating EOD summary."""
    return sheets_manager.update_eod_summary(summary)

def get_portfolio_summary() -> Optional[Dict]:
    """Wrapper function for getting portfolio summary."""
    return sheets_manager.get_portfolio_summary()

def export_positions_to_csv(filename: str = None) -> bool:
    """Wrapper function for exporting positions."""
    return sheets_manager.export_positions_to_csv(filename)

if __name__ == "__main__":
    # Test Google Sheets connection
    if sheets_manager._authenticate():
        print("Google Sheets connection successful")
        summary = get_portfolio_summary()
        if summary:
            print(f"Portfolio summary: {summary}")
    else:
        print("Google Sheets connection failed")