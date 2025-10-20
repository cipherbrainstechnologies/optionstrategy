"""
Hourly execution layer for managing open positions and executing signals.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..core.risk import size_position, calculate_position_metrics
from ..storage.models import Position, Signal, Order, Fill, generate_order_id
import json

logger = logging.getLogger(__name__)


class HourlyExecutor:
    """
    Hourly execution and position management.
    
    Responsibilities:
    - Monitor open positions hourly
    - Apply profit/loss management rules
    - Execute partial exits
    - Update stop losses (trailing)
    - Execute new signals on hourly confirmation
    """
    
    def __init__(self, broker, db_session, settings):
        """
        Initialize hourly executor.
        
        Args:
            broker: Broker client instance
            db_session: Database session
            settings: Settings object
        """
        self.broker = broker
        self.db = db_session
        self.settings = settings
        
        # Profit/loss thresholds
        self.BREAKEVEN_PCT = 3.0   # Move SL to BE at +3%
        self.BOOK_25_PCT = 6.0     # Book 25% at +6%
        self.BOOK_50_PCT = 10.0    # Book 50% at +10%
        self.CAUTION_PCT = -3.0    # Caution alert at -3%
        self.EXIT_PCT = -6.0       # Force exit at -6%
        
        logger.info("Hourly executor initialized")
    
    def run(self):
        """Main hourly execution flow."""
        try:
            logger.info("=" * 60)
            logger.info("Starting hourly execution cycle")
            logger.info("=" * 60)
            
            # 1. Manage open positions
            self.manage_positions()
            
            # 2. Check for triggered signals
            self.process_signals()
            
            logger.info("Hourly execution cycle completed")
            
        except Exception as e:
            logger.error(f"Error in hourly execution: {e}", exc_info=True)
    
    def manage_positions(self):
        """Manage all open positions."""
        # Fetch open positions
        positions = self.db.query(Position).filter(
            Position.status.in_(["OPEN", "PARTIAL"])
        ).all()
        
        if not positions:
            logger.info("No open positions to manage")
            return
        
        logger.info(f"Managing {len(positions)} open position(s)")
        
        for pos in positions:
            try:
                self._manage_position(pos)
            except Exception as e:
                logger.error(f"Error managing position {pos.symbol}: {e}")
        
        self.db.commit()
    
    def _manage_position(self, pos: Position):
        """
        Manage a single position.
        
        Args:
            pos: Position object
        """
        # Get current price
        ltp = self.broker.get_ltp(pos.symbol)
        if not ltp:
            logger.warning(f"Could not get LTP for {pos.symbol}")
            return
        
        # Calculate metrics
        metrics = calculate_position_metrics(
            entry=pos.entry_price,
            current_price=ltp,
            stop=pos.stop,
            qty=pos.qty
        )
        
        pnl_pct = metrics["pnl_pct"]
        
        logger.info(
            f"{pos.symbol}: LTP={ltp:.2f}, Entry={pos.entry_price:.2f}, "
            f"P&L={pnl_pct:+.2f}%, SL={pos.stop:.2f}"
        )
        
        # Apply management rules
        
        # 1. Stop loss hit
        if ltp <= pos.stop:
            logger.warning(f"{pos.symbol}: Stop loss hit at {ltp:.2f}")
            self._exit_position(pos, ltp, "STOP_HIT")
            return
        
        # 2. Force exit at -6%
        if pnl_pct <= self.EXIT_PCT:
            logger.warning(f"{pos.symbol}: Force exit at {pnl_pct:.2f}%")
            self._exit_position(pos, ltp, "FORCE_EXIT_LOSS")
            return
        
        # 3. Caution at -3%
        if pnl_pct <= self.CAUTION_PCT:
            logger.warning(f"{pos.symbol}: Caution zone {pnl_pct:.2f}%")
            # Just log, no action
        
        # 4. Breakeven at +3%
        if pnl_pct >= self.BREAKEVEN_PCT and pos.stop < pos.entry_price:
            logger.info(f"{pos.symbol}: Moving SL to breakeven")
            pos.stop = pos.entry_price
            pos.updated_at = datetime.utcnow()
        
        # 5. Book 25% at +6%
        if pnl_pct >= self.BOOK_25_PCT and pos.qty == pos.original_qty:
            logger.info(f"{pos.symbol}: Booking 25% profit at +{pnl_pct:.2f}%")
            self._partial_exit(pos, ltp, 0.25, "BOOK_25_AT_6PCT")
        
        # 6. Book 50% at +10%
        if pnl_pct >= self.BOOK_50_PCT and pos.status == "PARTIAL":
            logger.info(f"{pos.symbol}: Booking 50% more at +{pnl_pct:.2f}%")
            self._partial_exit(pos, ltp, 0.50, "BOOK_50_AT_10PCT")
        
        # 7. Target 1 reached
        if ltp >= pos.t1 and pos.status != "PARTIAL":
            logger.info(f"{pos.symbol}: Target 1 reached at {ltp:.2f}")
            self._partial_exit(pos, ltp, 0.50, "TARGET_1")
            # Lock SL at T1
            pos.stop = pos.t1
        
        # 8. Target 2 reached
        if ltp >= pos.t2:
            logger.info(f"{pos.symbol}: Target 2 reached at {ltp:.2f}")
            self._exit_position(pos, ltp, "TARGET_2")
            return
    
    def _partial_exit(self, pos: Position, exit_price: float, fraction: float, reason: str):
        """
        Execute partial exit.
        
        Args:
            pos: Position object
            exit_price: Exit price
            fraction: Fraction to exit (0.25 = 25%)
            reason: Exit reason
        """
        exit_qty = int(pos.qty * fraction)
        if exit_qty <= 0:
            return
        
        # Place sell order
        result = self.broker.place_order(
            symbol=pos.symbol,
            side="SELL",
            qty=exit_qty,
            order_type="MARKET",
            tag=f"PARTIAL_{reason}"
        )
        
        if result["status"] == "success":
            # Update position
            pos.qty -= exit_qty
            pos.status = "PARTIAL"
            
            # Calculate partial PnL
            partial_pnl = (exit_price - pos.entry_price) * exit_qty
            pos.pnl += partial_pnl
            
            logger.info(
                f"Partial exit: {pos.symbol} {exit_qty} @ {exit_price:.2f}, "
                f"P&L: ₹{partial_pnl:.2f}, Remaining: {pos.qty}"
            )
            
            # Store order in database
            self._record_order(pos, result, exit_qty, exit_price, "SELL", reason)
        else:
            logger.error(f"Partial exit failed: {result['message']}")
    
    def _exit_position(self, pos: Position, exit_price: float, reason: str):
        """
        Exit entire position.
        
        Args:
            pos: Position object
            exit_price: Exit price
            reason: Exit reason
        """
        # Place sell order
        result = self.broker.place_order(
            symbol=pos.symbol,
            side="SELL",
            qty=pos.qty,
            order_type="MARKET",
            tag=f"EXIT_{reason}"
        )
        
        if result["status"] == "success":
            # Calculate final PnL
            final_pnl = (exit_price - pos.entry_price) * pos.qty + pos.pnl
            risk = (pos.entry_price - pos.stop) * pos.original_qty
            rr = final_pnl / risk if risk > 0 else 0
            
            # Update position
            pos.status = "CLOSED"
            pos.closed_ts = datetime.utcnow()
            pos.pnl = final_pnl
            pos.rr = rr
            pos.exit_reason = reason
            
            logger.info(
                f"Position closed: {pos.symbol} {pos.qty} @ {exit_price:.2f}, "
                f"P&L: ₹{final_pnl:.2f}, R:R: {rr:.2f}"
            )
            
            # Store order
            self._record_order(pos, result, pos.qty, exit_price, "SELL", reason)
            
            # Update ledger
            self._update_ledger(pos, exit_price)
        else:
            logger.error(f"Position exit failed: {result['message']}")
    
    def _record_order(self, pos: Position, broker_result: Dict, qty: int, price: float, side: str, tag: str):
        """Record order in database."""
        try:
            order = Order(
                order_id=generate_order_id(pos.symbol, side),
                broker_order_id=broker_result.get("order_id"),
                symbol=pos.symbol,
                side=side,
                qty=qty,
                order_type="MARKET",
                price=price,
                status="FILLED",
                filled_qty=qty,
                avg_fill_price=price,
                tag=tag,
                position_id=pos.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(order)
        except Exception as e:
            logger.error(f"Error recording order: {e}")
    
    def _update_ledger(self, pos: Position, exit_price: float):
        """Update learning ledger with closed trade."""
        from ..storage.ledger import record_trade
        try:
            record_trade(
                db=self.db,
                symbol=pos.symbol,
                opened_ts=pos.opened_ts,
                closed_ts=pos.closed_ts,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                qty=pos.original_qty,
                pnl=pos.pnl,
                rr=pos.rr,
                tag=f"3WI_{pos.exit_reason}"
            )
        except Exception as e:
            logger.error(f"Error updating ledger: {e}")
    
    def process_signals(self):
        """Process pending signals that may need execution."""
        # Fetch pending signals
        signals = self.db.query(Signal).filter(
            Signal.status == "PENDING"
        ).all()
        
        if not signals:
            logger.info("No pending signals to process")
            return
        
        logger.info(f"Processing {len(signals)} pending signal(s)")
        
        for signal in signals:
            try:
                self._process_signal(signal)
            except Exception as e:
                logger.error(f"Error processing signal {signal.symbol}: {e}")
        
        self.db.commit()
    
    def _process_signal(self, signal: Signal):
        """
        Process a single signal.
        
        Check if hourly price confirms trigger, then execute.
        
        Args:
            signal: Signal object
        """
        # Get current price
        ltp = self.broker.get_ltp(signal.symbol)
        if not ltp:
            return
        
        # Check if signal triggered
        if signal.direction == "LONG" and ltp >= signal.trigger_price:
            logger.info(f"Signal triggered: {signal.symbol} @ {ltp:.2f}")
            self._execute_signal(signal, ltp)
        elif signal.direction == "SHORT" and ltp <= signal.trigger_price:
            logger.info(f"Short signal triggered: {signal.symbol} @ {ltp:.2f}")
            # For now, we only trade longs
            signal.status = "EXPIRED"
            signal.updated_at = datetime.utcnow()
    
    def _execute_signal(self, signal: Signal, entry_price: float):
        """
        Execute a signal by creating a position.
        
        Args:
            signal: Signal object
            entry_price: Actual entry price
        """
        # Calculate position size
        qty, risk_amt = size_position(
            entry=entry_price,
            stop=signal.stop_loss,
            capital=self.settings.PORTFOLIO_CAPITAL,
            risk_pct=self.settings.RISK_PCT_PER_TRADE,
            plan=self.settings.POSITION_SIZING_PLAN
        )
        
        if qty <= 0:
            logger.warning(f"Invalid quantity for {signal.symbol}, skipping")
            return
        
        # Place buy order
        result = self.broker.place_order(
            symbol=signal.symbol,
            side="BUY",
            qty=qty,
            order_type="MARKET",
            tag="SIGNAL_EXEC"
        )
        
        if result["status"] == "success":
            # Create position
            position = Position(
                symbol=signal.symbol,
                status="OPEN",
                entry_price=entry_price,
                stop=signal.stop_loss,
                t1=signal.target1,
                t2=signal.target2,
                qty=qty,
                original_qty=qty,
                capital=self.settings.PORTFOLIO_CAPITAL,
                plan_size=self.settings.POSITION_SIZING_PLAN,
                opened_ts=datetime.utcnow(),
                signal_id=signal.signal_id,
                metadata=json.dumps({"pattern": signal.pattern_type, "confidence": signal.confidence})
            )
            
            self.db.add(position)
            
            # Update signal
            signal.status = "TRIGGERED"
            signal.triggered_at = datetime.utcnow()
            signal.updated_at = datetime.utcnow()
            
            logger.info(
                f"Position opened: {signal.symbol} {qty} @ {entry_price:.2f}, "
                f"SL={signal.stop_loss:.2f}, T1={signal.target1:.2f}, T2={signal.target2:.2f}"
            )
        else:
            logger.error(f"Signal execution failed: {result['message']}")
