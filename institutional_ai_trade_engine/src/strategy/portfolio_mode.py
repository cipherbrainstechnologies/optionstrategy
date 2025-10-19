"""
Portfolio-only mode handler.
Tracks only stocks in portfolio and proposes adds per strategy.
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PortfolioMode:
    """
    Portfolio-only mode manager.
    
    Tracks holdings and proposes new additions based on strategy signals.
    """
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize portfolio mode.
        
        Args:
            data_dir: Directory for portfolio and ideas files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.portfolio_file = self.data_dir / "portfolio.json"
        self.ideas_file = self.data_dir / "ideas.csv"
        
        self.portfolio = self._load_portfolio()
        logger.info(f"Portfolio mode initialized with {len(self.portfolio)} holdings")
    
    def _load_portfolio(self) -> Dict[str, Dict]:
        """
        Load portfolio from JSON file.
        
        Returns:
            Dict: {symbol: {qty, avg_price, notes}}
        """
        if not self.portfolio_file.exists():
            logger.warning(f"Portfolio file not found: {self.portfolio_file}")
            logger.info("Creating empty portfolio.json template")
            self._create_portfolio_template()
            return {}
        
        try:
            with open(self.portfolio_file, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Loaded {len(data.get('holdings', {}))} holdings from portfolio")
            return data.get('holdings', {})
        
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            return {}
    
    def _create_portfolio_template(self):
        """Create portfolio.json template."""
        template = {
            "updated_at": datetime.now().isoformat(),
            "holdings": {
                "RELIANCE": {
                    "qty": 10,
                    "avg_price": 2450.50,
                    "notes": "Example holding"
                },
                "TCS": {
                    "qty": 5,
                    "avg_price": 3600.00,
                    "notes": "Tech sector exposure"
                }
            },
            "notes": "Edit this file to track your actual holdings"
        }
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info(f"Created portfolio template: {self.portfolio_file}")
    
    def get_holdings(self) -> List[str]:
        """
        Get list of symbols in portfolio.
        
        Returns:
            List of symbol strings
        """
        return list(self.portfolio.keys())
    
    def is_in_portfolio(self, symbol: str) -> bool:
        """
        Check if symbol is in portfolio.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if in portfolio
        """
        return symbol in self.portfolio
    
    def get_holding_info(self, symbol: str) -> Optional[Dict]:
        """
        Get holding information.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with qty, avg_price, notes or None
        """
        return self.portfolio.get(symbol)
    
    def propose_add(
        self, 
        symbol: str, 
        entry: float, 
        stop: float, 
        t1: float, 
        t2: float,
        qty: int,
        confidence: float,
        pattern: str,
        reason: str
    ):
        """
        Propose new position add to ideas file.
        
        Args:
            symbol: Stock symbol
            entry: Entry price
            stop: Stop loss
            t1: Target 1
            t2: Target 2
            qty: Proposed quantity
            confidence: Confidence score (0-100)
            pattern: Pattern type
            reason: Reasoning/notes
        """
        # Check if ideas file exists, create with header if not
        if not self.ideas_file.exists():
            header = "timestamp,symbol,entry,stop,t1,t2,qty,risk_r,r_r,confidence,pattern,reason\n"
            with open(self.ideas_file, 'w') as f:
                f.write(header)
        
        # Calculate risk:reward
        risk = entry - stop
        reward1 = t1 - entry
        rr = reward1 / risk if risk > 0 else 0
        
        # Append idea
        timestamp = datetime.now().isoformat()
        line = (
            f"{timestamp},{symbol},{entry:.2f},{stop:.2f},{t1:.2f},{t2:.2f},"
            f"{qty},{risk:.2f},{rr:.2f},{confidence:.1f},{pattern},{reason}\n"
        )
        
        with open(self.ideas_file, 'a') as f:
            f.write(line)
        
        logger.info(f"Proposed add: {symbol} @ {entry} (R:R {rr:.2f}, Confidence {confidence:.0f})")
    
    def add_to_portfolio(self, symbol: str, qty: int, avg_price: float, notes: str = ""):
        """
        Add new holding to portfolio.
        
        Args:
            symbol: Stock symbol
            qty: Quantity
            avg_price: Average purchase price
            notes: Optional notes
        """
        self.portfolio[symbol] = {
            "qty": qty,
            "avg_price": avg_price,
            "notes": notes
        }
        
        self._save_portfolio()
        logger.info(f"Added {symbol} to portfolio: {qty} @ {avg_price}")
    
    def update_holding(self, symbol: str, qty: int, avg_price: float):
        """
        Update existing holding (for partials/adds).
        
        Args:
            symbol: Stock symbol
            qty: New quantity (can be less if partial exit)
            avg_price: Updated average price
        """
        if symbol not in self.portfolio:
            logger.warning(f"Cannot update {symbol} - not in portfolio")
            return
        
        self.portfolio[symbol]["qty"] = qty
        self.portfolio[symbol]["avg_price"] = avg_price
        
        self._save_portfolio()
        logger.info(f"Updated {symbol} holding: {qty} @ {avg_price}")
    
    def remove_from_portfolio(self, symbol: str):
        """
        Remove holding from portfolio (full exit).
        
        Args:
            symbol: Stock symbol
        """
        if symbol in self.portfolio:
            del self.portfolio[symbol]
            self._save_portfolio()
            logger.info(f"Removed {symbol} from portfolio")
    
    def _save_portfolio(self):
        """Save portfolio to JSON file."""
        data = {
            "updated_at": datetime.now().isoformat(),
            "holdings": self.portfolio,
            "notes": "Auto-updated by trading engine"
        }
        
        with open(self.portfolio_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """
        Calculate portfolio value and P&L.
        
        Args:
            current_prices: Dict of {symbol: current_price}
            
        Returns:
            Dict with total_value, total_cost, unrealized_pnl, pnl_pct
        """
        total_cost = 0
        total_value = 0
        
        for symbol, holding in self.portfolio.items():
            qty = holding["qty"]
            avg_price = holding["avg_price"]
            current_price = current_prices.get(symbol, avg_price)
            
            cost = qty * avg_price
            value = qty * current_price
            
            total_cost += cost
            total_value += value
        
        unrealized_pnl = total_value - total_cost
        pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_cost": total_cost,
            "total_value": total_value,
            "unrealized_pnl": unrealized_pnl,
            "pnl_pct": pnl_pct,
            "holdings_count": len(self.portfolio)
        }
    
    def filter_universe(self, all_symbols: List[str]) -> List[str]:
        """
        Filter universe to portfolio-only symbols.
        
        Args:
            all_symbols: List of all available symbols
            
        Returns:
            List of symbols that are in portfolio
        """
        portfolio_symbols = self.get_holdings()
        return [s for s in all_symbols if s in portfolio_symbols]
