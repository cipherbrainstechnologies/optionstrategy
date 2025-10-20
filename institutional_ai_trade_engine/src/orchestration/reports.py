"""
End-of-day reporting and learning ledger updates.
Runs at 15:25 IST daily.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from ..core.config import Settings, get_settings
from ..storage.db import get_db_session
from ..storage.models import Position, LedgerEntry, Signal
from ..strategy.portfolio_mode import PortfolioMode

try:
    from ..exec.eod_report import run as run_eod  # type: ignore
except Exception:
    from exec.eod_report import run as run_eod  # type: ignore
try:
    from ..core.config import Settings  # type: ignore
except Exception:
    from core.config import Settings  # type: ignore

logger = logging.getLogger(__name__)


def run_eod():
    """
    End-of-day report generation.
    
    1. Summarize open positions
    2. Summarize closed positions (today)
    3. Calculate performance metrics
    4. Update learning ledger
    5. Generate EOD report
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting EOD REPORT")
        logger.info("=" * 60)
        
        # Initialize
        settings = get_settings()
        broker = settings.get_broker()
        db = get_db_session()
        portfolio = PortfolioMode(settings.DATA_DIR)
        
        # Generate report sections
        open_summary = _summarize_open_positions(db, broker)
        closed_summary = _summarize_closed_positions(db)
        performance = _calculate_performance(db)
        risk_metrics = _calculate_risk_metrics(open_summary, settings)
        
        # Print report
        _print_report(open_summary, closed_summary, performance, risk_metrics)
        
        # Send alerts (if configured)
        _send_alerts(open_summary, closed_summary, performance, settings)
        
        db.close()
        
        logger.info("EOD report completed")
        
    except Exception as e:
        logger.error(f"Error in EOD report: {e}", exc_info=True)


def _summarize_open_positions(db, broker) -> Dict:
    """Summarize open positions."""
    positions = db.query(Position).filter(
        Position.status.in_(["OPEN", "PARTIAL"])
    ).all()
    
    if not positions:
        return {
            "count": 0,
            "positions": [],
            "total_unrealized_pnl": 0,
            "total_capital_deployed": 0
        }
    
    positions_data = []
    total_unrealized_pnl = 0
    total_capital_deployed = 0
    
    for pos in positions:
        ltp = broker.get_ltp(pos.symbol) or pos.entry_price
        unrealized_pnl = (ltp - pos.entry_price) * pos.qty
        pnl_pct = ((ltp - pos.entry_price) / pos.entry_price) * 100
        
        days_in_trade = (datetime.utcnow() - pos.opened_ts).days
        
        positions_data.append({
            "symbol": pos.symbol,
            "qty": pos.qty,
            "entry": pos.entry_price,
            "ltp": ltp,
            "stop": pos.stop,
            "t1": pos.t1,
            "t2": pos.t2,
            "unrealized_pnl": unrealized_pnl,
            "pnl_pct": pnl_pct,
            "days_in_trade": days_in_trade,
            "status": pos.status
        })
        
        total_unrealized_pnl += unrealized_pnl
        total_capital_deployed += pos.entry_price * pos.qty
    
    return {
        "count": len(positions),
        "positions": positions_data,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_capital_deployed": total_capital_deployed
    }


def _summarize_closed_positions(db) -> Dict:
    """Summarize positions closed today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    positions = db.query(Position).filter(
        Position.status == "CLOSED",
        Position.closed_ts >= today_start
    ).all()
    
    if not positions:
        return {
            "count": 0,
            "positions": [],
            "total_realized_pnl": 0,
            "wins": 0,
            "losses": 0
        }
    
    positions_data = []
    total_realized_pnl = 0
    wins = 0
    losses = 0
    
    for pos in positions:
        positions_data.append({
            "symbol": pos.symbol,
            "entry": pos.entry_price,
            "exit_reason": pos.exit_reason,
            "pnl": pos.pnl,
            "rr": pos.rr,
            "opened": pos.opened_ts,
            "closed": pos.closed_ts
        })
        
        total_realized_pnl += pos.pnl
        if pos.pnl > 0:
            wins += 1
        else:
            losses += 1
    
    return {
        "count": len(positions),
        "positions": positions_data,
        "total_realized_pnl": total_realized_pnl,
        "wins": wins,
        "losses": losses,
        "win_rate": (wins / len(positions) * 100) if positions else 0
    }


def _calculate_performance(db) -> Dict:
    """Calculate overall performance metrics."""
    # Get all closed positions
    all_closed = db.query(Position).filter(Position.status == "CLOSED").all()
    
    if not all_closed:
        return {
            "total_trades": 0,
            "win_rate": 0,
            "avg_rr": 0,
            "total_pnl": 0,
            "avg_hold_days": 0
        }
    
    wins = sum(1 for p in all_closed if p.pnl > 0)
    total_pnl = sum(p.pnl for p in all_closed)
    avg_rr = sum(p.rr for p in all_closed if p.rr) / len(all_closed)
    
    hold_durations = []
    for p in all_closed:
        if p.opened_ts and p.closed_ts:
            duration = (p.closed_ts - p.opened_ts).total_seconds() / 3600 / 24
            hold_durations.append(duration)
    
    avg_hold_days = sum(hold_durations) / len(hold_durations) if hold_durations else 0
    
    return {
        "total_trades": len(all_closed),
        "win_rate": (wins / len(all_closed) * 100),
        "avg_rr": avg_rr,
        "total_pnl": total_pnl,
        "avg_hold_days": avg_hold_days,
        "wins": wins,
        "losses": len(all_closed) - wins
    }


def _calculate_risk_metrics(open_summary: Dict, settings) -> Dict:
    """Calculate risk metrics."""
    total_capital = settings.PORTFOLIO_CAPITAL
    capital_deployed = open_summary["total_capital_deployed"]
    
    # Calculate total risk (assuming all stops hit)
    # This is a simplified calculation
    open_risk_pct = (open_summary["count"] * settings.RISK_PCT_PER_TRADE)
    
    return {
        "total_capital": total_capital,
        "capital_deployed": capital_deployed,
        "capital_deployed_pct": (capital_deployed / total_capital * 100) if total_capital > 0 else 0,
        "open_risk_pct": open_risk_pct,
        "available_capital": total_capital - capital_deployed,
        "max_risk_pct": settings.MAX_OPEN_RISK_PCT
    }


def _print_report(open_summary: Dict, closed_summary: Dict, performance: Dict, risk_metrics: Dict):
    """Print formatted EOD report."""
    print("\n" + "=" * 60)
    print("END OF DAY REPORT")
    print("=" * 60)
    
    # Open Positions
    print(f"\n📊 OPEN POSITIONS: {open_summary['count']}")
    if open_summary['count'] > 0:
        for pos in open_summary['positions']:
            print(
                f"  • {pos['symbol']}: {pos['qty']} @ {pos['entry']:.2f} → {pos['ltp']:.2f} "
                f"({pos['pnl_pct']:+.2f}%) | SL: {pos['stop']:.2f} | Days: {pos['days_in_trade']}"
            )
        print(f"  Total Unrealized P&L: ₹{open_summary['total_unrealized_pnl']:,.2f}")
    
    # Closed Positions (Today)
    print(f"\n✅ CLOSED TODAY: {closed_summary['count']}")
    if closed_summary['count'] > 0:
        for pos in closed_summary['positions']:
            print(
                f"  • {pos['symbol']}: P&L ₹{pos['pnl']:,.2f} (R:R {pos['rr']:.2f}) | {pos['exit_reason']}"
            )
        print(f"  Total Realized P&L: ₹{closed_summary['total_realized_pnl']:,.2f}")
        print(f"  Win Rate: {closed_summary['win_rate']:.1f}% ({closed_summary['wins']}W / {closed_summary['losses']}L)")
    
    # Performance Metrics
    print(f"\n📈 OVERALL PERFORMANCE")
    print(f"  Total Trades: {performance['total_trades']}")
    print(f"  Win Rate: {performance['win_rate']:.1f}% ({performance['wins']}W / {performance['losses']}L)")
    print(f"  Avg R:R: {performance['avg_rr']:.2f}")
    print(f"  Total P&L: ₹{performance['total_pnl']:,.2f}")
    print(f"  Avg Hold Duration: {performance['avg_hold_days']:.1f} days")
    
    # Risk Metrics
    print(f"\n⚖️ RISK METRICS")
    print(f"  Total Capital: ₹{risk_metrics['total_capital']:,.0f}")
    print(f"  Capital Deployed: ₹{risk_metrics['capital_deployed']:,.0f} ({risk_metrics['capital_deployed_pct']:.1f}%)")
    print(f"  Open Risk: {risk_metrics['open_risk_pct']:.1f}% (Max: {risk_metrics['max_risk_pct']:.1f}%)")
    print(f"  Available Capital: ₹{risk_metrics['available_capital']:,.0f}")
    
    print("\n" + "=" * 60)


def _send_alerts(open_summary: Dict, closed_summary: Dict, performance: Dict, settings):
    """Send EOD report via Telegram (if configured)."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.info("Telegram not configured, skipping alerts")
        return
    
    try:
        from ..alerts.telegram import send_message
        
        message = (
            f"📊 *EOD REPORT*\n\n"
            f"Open Positions: {open_summary['count']}\n"
            f"Unrealized P&L: ₹{open_summary['total_unrealized_pnl']:,.2f}\n\n"
            f"Closed Today: {closed_summary['count']}\n"
            f"Realized P&L: ₹{closed_summary['total_realized_pnl']:,.2f}\n\n"
            f"Overall:\n"
            f"• Total Trades: {performance['total_trades']}\n"
            f"• Win Rate: {performance['win_rate']:.1f}%\n"
            f"• Avg R:R: {performance['avg_rr']:.2f}\n"
            f"• Total P&L: ₹{performance['total_pnl']:,.2f}"
        )
        
        send_message(message)
        logger.info("EOD report sent via Telegram")
        
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    run_eod()
