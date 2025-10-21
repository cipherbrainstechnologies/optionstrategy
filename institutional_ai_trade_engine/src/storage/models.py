"""
Pydantic models and SQLAlchemy ORM models for the trading engine.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ==================== Pydantic Models ====================

class SignalCreate(BaseModel):
    """Signal creation model."""
    symbol: str
    timeframe: str  # "weekly", "hourly"
    direction: str  # "LONG", "SHORT"
    trigger_price: float
    stop_loss: float
    target1: float
    target2: float
    confidence: float  # 0-100
    pattern_type: str  # "3WI_BREAKOUT", etc.
    trigger_ts: datetime
    metadata: Optional[dict] = None


class OrderCreate(BaseModel):
    """Order creation model."""
    symbol: str
    side: str  # "BUY", "SELL"
    qty: int
    order_type: str  # "MARKET", "LIMIT"
    price: Optional[float] = None
    tag: str = ""


class PositionMetrics(BaseModel):
    """Position metrics calculation."""
    entry: float
    current_price: float
    stop: float
    qty: int
    unrealized_pnl: float
    pnl_pct: float
    risk_amount: float


# ==================== SQLAlchemy ORM Models ====================

class Signal(Base):
    """Trading signals table."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(100), unique=True, nullable=False)  # {symbol}_{tf}_{date}
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    trigger_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target1 = Column(Float, nullable=False)
    target2 = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    pattern_type = Column(String(50), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, TRIGGERED, EXPIRED
    trigger_ts = Column(DateTime, nullable=False, index=True)
    triggered_at = Column(DateTime)
    meta_data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Order(Base):
    """Orders table."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(100), unique=True, nullable=False)
    broker_order_id = Column(String(100), index=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    qty = Column(Integer, nullable=False)
    order_type = Column(String(20), nullable=False)
    price = Column(Float)
    status = Column(String(20), nullable=False, index=True)  # PENDING, FILLED, CANCELLED, REJECTED
    filled_qty = Column(Integer, default=0)
    avg_fill_price = Column(Float, default=0.0)
    tag = Column(String(50))
    signal_id = Column(String(100), index=True)  # Link to signal
    position_id = Column(Integer, index=True)  # Link to position
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text)


class Fill(Base):
    """Order fills table."""
    __tablename__ = "fills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fill_id = Column(String(100), unique=True, nullable=False)
    order_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    filled_at = Column(DateTime, default=datetime.utcnow, index=True)


class Position(Base):
    """Positions table (enhanced from existing)."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # OPEN, PARTIAL, CLOSED
    entry_price = Column(Float, nullable=False)
    stop = Column(Float, nullable=False)
    t1 = Column(Float, nullable=False)
    t2 = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    original_qty = Column(Integer, nullable=False)  # Track original qty for partials
    capital = Column(Float, nullable=False)
    plan_size = Column(Float, nullable=False)
    opened_ts = Column(DateTime, nullable=False, index=True)
    closed_ts = Column(DateTime, index=True)
    pnl = Column(Float, default=0.0)
    rr = Column(Float, default=0.0)
    exit_reason = Column(String(100))  # "STOP_HIT", "TARGET_1", "TARGET_2", "MANUAL"
    signal_id = Column(String(100), index=True)  # Link to signal that created this
    meta_data = Column(Text)  # JSON for additional info


class Instrument(Base):
    """Instruments/universe table (existing, kept for compatibility)."""
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), unique=True, nullable=False)
    exchange = Column(String(20), default="NSE")
    enabled = Column(Integer, default=1)  # 1 = True, 0 = False for PostgreSQL compatibility
    in_portfolio = Column(Integer, default=0)  # 1 = True, 0 = False for PostgreSQL compatibility
    avg_portfolio_price = Column(Float)  # If already held
    portfolio_qty = Column(Integer)  # If already held


class Setup(Base):
    """Setups table (existing 3WI patterns)."""
    __tablename__ = "setups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    week_start = Column(String(20), nullable=False)
    mother_high = Column(Float, nullable=False)
    mother_low = Column(Float, nullable=False)
    inside_weeks = Column(Integer, default=2)
    matched_filters = Column(Integer, default=0)  # 1 = True, 0 = False for PostgreSQL compatibility
    quality_score = Column(Float)  # 0-100
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class LedgerEntry(Base):
    """Ledger table for closed trades (existing)."""
    __tablename__ = "ledger"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(50), nullable=False, index=True)
    opened_ts = Column(DateTime, nullable=False)
    closed_ts = Column(DateTime, nullable=False, index=True)
    pnl = Column(Float, nullable=False)
    rr = Column(Float, nullable=False)
    tag = Column(String(100), index=True)
    entry_price = Column(Float)
    exit_price = Column(Float)
    qty = Column(Integer)
    hold_duration_hours = Column(Float)
    meta_data = Column(Text)  # JSON


# Helper function to generate unique IDs
def generate_signal_id(symbol: str, timeframe: str, trigger_ts: datetime) -> str:
    """Generate unique signal ID."""
    date_str = trigger_ts.strftime("%Y%m%d")
    return f"{symbol}_{timeframe}_{date_str}"


def generate_order_id(symbol: str, side: str) -> str:
    """Generate unique order ID."""
    import uuid
    return f"{symbol}_{side}_{uuid.uuid4().hex[:8]}"
