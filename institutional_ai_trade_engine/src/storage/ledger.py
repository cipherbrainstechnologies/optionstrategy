"""
Learning ledger for tracking trade performance and insights.
"""
from datetime import datetime
from sqlalchemy import text
from .db import get_db_session

def log_trade(symbol, opened_ts, closed_ts, pnl, rr, tag):
    """Log a completed trade to the ledger."""
    db = get_db_session()
    try:
        query = text("""
            INSERT INTO ledger (symbol, opened_ts, closed_ts, pnl, rr, tag)
            VALUES (:symbol, :opened_ts, :closed_ts, :pnl, :rr, :tag)
        """)
        db.execute(query, {
            "symbol": symbol,
            "opened_ts": opened_ts,
            "closed_ts": closed_ts,
            "pnl": pnl,
            "rr": rr,
            "tag": tag
        })
        db.commit()
    finally:
        db.close()

def get_performance_summary(days=30):
    """Get performance summary for the last N days."""
    db = get_db_session()
    try:
        query = text("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                AVG(pnl) as avg_pnl,
                AVG(rr) as avg_rr,
                AVG(julianday(closed_ts) - julianday(opened_ts)) as avg_hold_days
            FROM ledger 
            WHERE closed_ts >= datetime('now', '-{} days')
        """.format(days))
        
        result = db.execute(query).fetchone()
        
        if result and result[0] > 0:
            win_rate = (result[1] / result[0]) * 100
            return {
                "total_trades": result[0],
                "winning_trades": result[1],
                "win_rate": round(win_rate, 2),
                "avg_pnl": round(result[2], 2),
                "avg_rr": round(result[3], 2),
                "avg_hold_days": round(result[4], 2)
            }
        else:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "win_rate": 0,
                "avg_pnl": 0,
                "avg_rr": 0,
                "avg_hold_days": 0
            }
    finally:
        db.close()

def get_recent_trades(limit=10):
    """Get recent trades from ledger."""
    db = get_db_session()
    try:
        query = text("""
            SELECT symbol, opened_ts, closed_ts, pnl, rr, tag
            FROM ledger 
            ORDER BY closed_ts DESC 
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).fetchall()
        return [dict(row._mapping) for row in result]
    finally:
        db.close()