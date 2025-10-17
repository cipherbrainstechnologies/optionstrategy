"""
Risk management module for position sizing and risk controls.
"""
from .config import Config

def size_position(entry, stop, capital, risk_pct, plan):
    """
    Calculate position size based on risk parameters.
    
    Args:
        entry: Entry price
        stop: Stop loss price
        capital: Available capital
        risk_pct: Risk percentage per trade
        plan: Position sizing plan multiplier
    
    Returns:
        tuple: (quantity, risk_amount)
    """
    risk_rupees = capital * (risk_pct / 100) * plan
    per_share = max(entry - stop, 0.01)
    qty = int(risk_rupees / per_share)
    return max(qty, 1), risk_rupees

def calculate_targets(entry, stop, atr):
    """
    Calculate T1 and T2 targets based on ATR.
    
    Args:
        entry: Entry price
        stop: Stop loss price
        atr: Average True Range
    
    Returns:
        tuple: (t1, t2)
    """
    risk = abs(entry - stop)
    t1 = entry + (risk * 1.5)  # 1.5R target
    t2 = entry + (risk * 3.0)  # 3R target
    return t1, t2

def check_risk_limits(open_positions, new_risk):
    """
    Check if adding new position violates risk limits.
    
    Args:
        open_positions: List of open positions with risk amounts
        new_risk: Risk amount for new position
    
    Returns:
        bool: True if within limits, False otherwise
    """
    total_risk = sum(pos.get('risk_amount', 0) for pos in open_positions)
    max_risk = Config.PORTFOLIO_CAPITAL * (Config.MAX_OPEN_RISK_PCT / 100)
    
    return (total_risk + new_risk) <= max_risk

def calculate_position_metrics(entry, current_price, stop, qty):
    """
    Calculate current position metrics.
    
    Args:
        entry: Entry price
        current_price: Current market price
        stop: Stop loss price
        qty: Position quantity
    
    Returns:
        dict: Position metrics
    """
    unrealized_pnl = (current_price - entry) * qty
    risk_amount = abs(entry - stop) * qty
    pnl_pct = (unrealized_pnl / (entry * qty)) * 100
    
    return {
        "unrealized_pnl": unrealized_pnl,
        "risk_amount": risk_amount,
        "pnl_pct": pnl_pct,
        "current_price": current_price
    }