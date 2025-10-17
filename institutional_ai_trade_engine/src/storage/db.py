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

# Database configuration
DB_PATH = os.getenv("DB_PATH", "trading_engine.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Initialize database with schema."""
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