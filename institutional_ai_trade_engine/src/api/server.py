from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List
import asyncio
import logging

from src.storage.db import init_database, engine
from sqlalchemy import text

app = FastAPI(title="Institutional AI Trade Engine API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.vercel.app",
    os.getenv("FRONTEND_URL", "")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ActionPayload(BaseModel):
    action: str
    symbol: str | None = None

class ScanPayload(BaseModel):
    dry_run: bool = False

# Global variable to track scan status
scan_status = {"running": False, "last_scan": None, "results": None}

def ensure_instruments_seeded():
    """Ensure instruments table has stock symbols."""
    try:
        logging.info("Checking if instruments are already seeded...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM instruments WHERE enabled = 1"))
            row = result.first()
            count = int(row.count) if row and row.count is not None else 0
            
            if count > 0:
                logging.info(f"Instruments already seeded: {count} enabled instruments")
                return
            
            # No instruments, seed with Nifty 500
            logging.info("No instruments found, seeding with Nifty 500...")
            from scripts.seed_instruments import seed_instruments
            if seed_instruments('nifty500'):
                logging.info("Successfully seeded Nifty 500 instruments")
            else:
                logging.error("Failed to seed instruments")
    except Exception as e:
        import traceback
        logging.error(f"Error checking/seeding instruments: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")

@app.on_event("startup")
def startup_event():
    try:
        logging.info("Starting application initialization...")
        init_database()
        logging.info("Database initialized successfully")
        ensure_instruments_seeded()
        logging.info("Application startup completed successfully")
    except Exception as e:
        import traceback
        logging.error(f"Startup error: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        # Don't let startup errors crash the app - continue with limited functionality

@app.get("/health")
def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "ok", "message": "Trading Engine API is running"}

@app.get("/overview")
def get_overview():
    # Avoid ORM import; use SQLAlchemy Core
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(1) AS c FROM positions"))
            row = result.first()
            positions_count = int(row.c) if row and row.c is not None else 0
    except Exception:
        positions_count = 0
    capital = float(os.getenv("PORTFOLIO_CAPITAL", "400000"))
    paper_str = os.getenv("PAPER_MODE", "true").lower()
    paper_mode = paper_str in ("1", "true", "yes", "y")
    
    # Include scan status
    last_scan = scan_status.get("last_scan", "--:--")
    if scan_status.get("running"):
        last_scan = "Scanning..."
    
    return {
        "engineStatus": "Running",
        "paperMode": paper_mode,
        "lastScan": last_scan,
        "capital": capital,
        "openRiskPct": 0.0,
        "pnlDay": 0.0,
        "positions": positions_count,
        "signals": 0,
        "winRate": 0,
        "scanRunning": scan_status.get("running", False),
    }

@app.get("/positions")
def get_positions():
    # Avoid ORM import; use SQLAlchemy Core
    rows: List[dict] = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                """
                SELECT symbol, entry_price AS entry, stop, t1, t2, status,
                       COALESCE(pnl, 0.0) AS pnl
                FROM positions
                ORDER BY id DESC
                """
            ))
            for r in result.mappings():
                rows.append({
                    "symbol": r["symbol"],
                    "entry": r["entry"],
                    "stop": r["stop"],
                    "t1": r["t1"],
                    "t2": r["t2"],
                    "ltp": r["entry"],  # placeholder
                    "status": r["status"],
                    "pnl": r["pnl"],
                })
    except Exception:
        rows = []
    return rows

@app.post("/actions")
def post_actions(payload: ActionPayload):
    return {"ok": True, "action": payload.action, "symbol": payload.symbol}

def run_scanner_background(dry_run: bool = False):
    """Run scanner in background thread."""
    try:
        # Import scanner here to avoid circular imports
        from src.exec.scanner import run as scanner_run
        scan_status["running"] = True
        scan_status["last_scan"] = None
        scan_status["results"] = None
        
        # Run the scanner
        results = scanner_run(dry_run)
        
        # Update status
        from datetime import datetime
        scan_status["running"] = False
        scan_status["last_scan"] = datetime.now().strftime("%H:%M")
        scan_status["results"] = results
        
        logging.info(f"Manual scan completed at {scan_status['last_scan']}")
        
    except Exception as e:
        scan_status["running"] = False
        scan_status["last_scan"] = f"Error: {str(e)}"
        scan_status["results"] = None
        logging.error(f"Manual scan failed: {e}")

@app.post("/scan")
def manual_scan(payload: ScanPayload, background_tasks: BackgroundTasks):
    """Trigger a manual scan."""
    if scan_status.get("running", False):
        return {"ok": False, "message": "Scan already in progress"}
    
    # Start background scan
    background_tasks.add_task(run_scanner_background, payload.dry_run)
    
    return {
        "ok": True, 
        "message": "Manual scan started",
        "dry_run": payload.dry_run
    }

@app.get("/scan/status")
def get_scan_status():
    """Get current scan status."""
    return scan_status

@app.get("/scan/results")
def get_scan_results():
    """Get latest scan results."""
    return scan_status.get("results", {
        "total_instruments": 0,
        "scanned_instruments": [],
        "valid_setups": [],
        "breakouts": [],
        "errors": []
    })
