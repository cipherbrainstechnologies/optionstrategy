"""
Database initialization and connection management.
"""
import os
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    """Get SQLAlchemy engine with cloud-ready configuration."""
    from ..core.config import Settings
    settings = Settings()
    
    db_url = settings.DATABASE_URL
    
    # PostgreSQL configuration for cloud
    if db_url.startswith("postgresql://"):
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
    else:
        # SQLite for local development
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False}
        )
    
    return engine

# Database configuration
DB_PATH = os.getenv("DB_PATH", "trading_engine.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Convert Render's postgres:// to postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database with schema."""
    # Ensure DB directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    # Lightweight migration: add missing columns if needed before indexes
    with engine.connect() as conn:
        # Check instruments table for in_portfolio column
        try:
            result = conn.execute(text("PRAGMA table_info(instruments)"))
            columns = {row[1] for row in result.fetchall()}
            if "in_portfolio" not in columns:
                conn.execute(text("ALTER TABLE instruments ADD COLUMN in_portfolio INTEGER DEFAULT 0"))
            if "avg_portfolio_price" not in columns:
                conn.execute(text("ALTER TABLE instruments ADD COLUMN avg_portfolio_price REAL"))
            if "portfolio_qty" not in columns:
                conn.execute(text("ALTER TABLE instruments ADD COLUMN portfolio_qty INTEGER"))
        except Exception:
            # Table might not exist yet; schema creation below will handle it
            pass

        # Check positions table for newly added columns
        try:
            result = conn.execute(text("PRAGMA table_info(positions)"))
            pos_columns = {row[1] for row in result.fetchall()}
            # Ensure columns used in schema and indexes exist
            if "original_qty" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN original_qty INTEGER"))
            if "plan_size" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN plan_size REAL"))
            if "pnl" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN pnl REAL DEFAULT 0"))
            if "rr" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN rr REAL DEFAULT 0"))
            if "exit_reason" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN exit_reason TEXT"))
            if "signal_id" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN signal_id TEXT"))
            if "metadata" not in pos_columns:
                conn.execute(text("ALTER TABLE positions ADD COLUMN metadata TEXT"))
        except Exception:
            # Table might not exist yet; schema creation below will handle it
            pass

        conn.commit()

    # Read schema file
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Split into individual statements and execute
    statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
    
    with engine.connect() as conn:
        for statement in statements:
            if statement:
                conn.execute(text(statement))
        conn.commit()
    
    print(f"Database initialized at {DB_PATH}")

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session():
    """Get database session directly."""
    return SessionLocal()

if __name__ == "__main__":
    init_database()