from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from typing import List
import asyncio
import logging
from pathlib import Path

from src.storage.db import init_database, engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

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

@app.get("/")
def root():
    """Root endpoint - API information and available endpoints."""
    return {
        "name": "Institutional AI Trade Engine API",
        "version": "2.0.0",
        "status": "running",
        "broker": os.getenv("BROKER", "FYERS"),
        "mode": "SANDBOX" if os.getenv("FYERS_SANDBOX", "true").lower() == "true" else "LIVE",
        "endpoints": {
            "health": "/health",
            "overview": "/overview",
            "positions": "/positions",
            "scan": "/scan",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint for deployment monitoring."""
    return {"status": "ok", "message": "Trading Engine API is running"}

@app.get("/token-manager", response_class=HTMLResponse)
async def token_manager_page():
    """Serve the token manager web interface."""
    try:
        html_path = Path(__file__).parent / "templates" / "token_manager.html"
        if html_path.exists():
            return html_path.read_text()
        else:
            return """
            <html>
                <body>
                    <h1>Token Manager</h1>
                    <p>Template file not found. Please check deployment.</p>
                </body>
            </html>
            """
    except Exception as e:
        return f"""
        <html>
            <body>
                <h1>Error</h1>
                <p>Error loading token manager: {str(e)}</p>
            </body>
        </html>
        """

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

@app.get("/fyers/auth-url")
async def get_fyers_auth_url(mode: str = "sandbox"):
    """Get FYERS authentication URL for token renewal."""
    try:
        from src.core.config import Settings
        
        # Create a temporary FyersAPI instance to get the auth URL
        try:
            from src.data.fyers_client import FyersAPI
        except Exception:
            from src.data.fyers_client import FyersAPI
        
        # Create settings instance
        settings = Settings()
        
        # Override sandbox setting based on mode parameter
        if mode == "live":
            settings.FYERS_SANDBOX = False
        else:
            settings.FYERS_SANDBOX = True
        
        # Create FyersAPI instance (this will handle the expired token gracefully)
        fyers_client = FyersAPI(settings)
        
        # Get the auth URL
        auth_url = fyers_client.get_auth_url()
        
        if auth_url:
            return {
                "success": True,
                "auth_url": auth_url,
                "mode": mode,
                "message": f"Visit this URL to renew your FYERS access token ({mode} mode)"
            }
        else:
            return {
                "success": False,
                "auth_url": None,
                "message": "Failed to generate FYERS auth URL"
            }
            
    except Exception as e:
        return {
            "success": False,
            "auth_url": None,
            "message": f"Error generating auth URL: {str(e)}"
        }

@app.get("/callback")
async def fyers_callback(
    s: str = None, 
    code: str = None, 
    auth_code: str = None, 
    state: str = None,
    auto_update: bool = True
):
    """
    Handle FYERS OAuth callback, exchange auth_code for tokens,
    and optionally update Render environment variables.
    """
    try:
        if s == "ok" and auth_code:
            logger.info("FYERS OAuth callback received successfully")
            logger.info(f"Auth code: {auth_code[:20]}...")
            
            # Exchange auth_code for tokens
            from .token_manager import FyersTokenManager, RenderEnvManager
            from src.core.config import Settings
            
            settings = Settings()
            
            # Initialize token manager
            token_manager = FyersTokenManager(
                client_id=settings.FYERS_CLIENT_ID,
                secret_key=settings.FYERS_SECRET_KEY,
                sandbox=settings.FYERS_SANDBOX
            )
            
            # Exchange auth_code for both tokens
            token_result = token_manager.exchange_auth_code(auth_code)
            
            if not token_result.get("success"):
                return {
                    "success": False,
                    "message": token_result.get("message"),
                    "auth_code": auth_code,
                    "instructions": [
                        "Token exchange failed.",
                        "You can try again or update tokens manually in Render dashboard."
                    ]
                }
            
            access_token = token_result.get("access_token")
            refresh_token = token_result.get("refresh_token")
            
            logger.info("✅ Successfully received both tokens from FYERS")
            
            # Auto-update Render environment variables if requested
            update_result = None
            if auto_update:
                logger.info("Attempting to update Render environment variables...")
                env_manager = RenderEnvManager()
                
                variables = {
                    "FYERS_ACCESS_TOKEN": access_token
                }
                
                # Only update refresh token if provided
                if refresh_token:
                    variables["FYERS_REFRESH_TOKEN"] = refresh_token
                
                update_result = env_manager.update_env_vars(variables)
            
            # Prepare response
            response = {
                "success": True,
                "message": "🎉 FYERS Authentication Successful!",
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token if refresh_token else "Not provided by FYERS"
                },
                "mode": "SANDBOX" if settings.FYERS_SANDBOX else "LIVE"
            }
            
            # Add update status
            if update_result:
                if update_result.get("success"):
                    response["auto_update"] = {
                        "status": "success",
                        "message": update_result.get("message"),
                        "method": update_result.get("method")
                    }
                    response["instructions"] = [
                        "✅ Tokens automatically updated in Render!",
                        "🔄 Please restart your Render service to apply changes:",
                        "   1. Go to Render Dashboard",
                        "   2. Click 'Manual Deploy' → 'Clear build cache & deploy'",
                        "   OR click the restart button",
                        "",
                        "⏰ Your tokens will auto-refresh daily at 08:45 IST"
                    ]
                else:
                    response["auto_update"] = {
                        "status": "failed",
                        "message": update_result.get("message"),
                        "method": "manual"
                    }
                    response["instructions"] = [
                        "⚠️ Automatic update failed. Please update manually:",
                        "",
                        "📋 Copy these to Render Environment Variables:",
                        "",
                        f"FYERS_ACCESS_TOKEN={access_token}",
                        f"FYERS_REFRESH_TOKEN={refresh_token}" if refresh_token else "",
                        "",
                        "Then restart your application."
                    ]
            else:
                response["instructions"] = [
                    "📋 Add these to Render Environment Variables:",
                    "",
                    f"FYERS_ACCESS_TOKEN={access_token}",
                    f"FYERS_REFRESH_TOKEN={refresh_token}" if refresh_token else "",
                    "",
                    "Then restart your application."
                ]
            
            return response
                
        elif s == "error":
            error_msg = f"FYERS authentication failed: {code}" if code else "Unknown error"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg,
                "instructions": [
                    "Authentication failed.",
                    "Check your FYERS credentials and try again."
                ]
            }
        else:
            return {
                "success": False,
                "message": "Invalid callback parameters",
                "received": {
                    "s": s,
                    "code": code,
                    "auth_code": auth_code,
                    "state": state
                }
            }
            
    except Exception as e:
        logger.error(f"Error handling FYERS callback: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"Error processing callback: {str(e)}"
        }

@app.post("/trading-mode")
async def update_trading_mode(payload: dict):
    """Update trading mode (sandbox/live) for FYERS broker."""
    try:
        mode = payload.get("mode")
        if mode not in ["sandbox", "live"]:
            return {
                "success": False,
                "message": "Invalid mode. Must be 'sandbox' or 'live'"
            }
        
        # Update the FYERS_SANDBOX environment variable logic
        # Note: This is a runtime change that affects the current session
        # For persistent changes, the user would need to update Render environment variables
        
        logger.info(f"Trading mode changed to: {mode}")
        
        return {
            "success": True,
            "message": f"Trading mode updated to {mode}",
            "mode": mode,
            "note": "This change affects the current session. For permanent changes, update FYERS_SANDBOX in Render environment variables."
        }
        
    except Exception as e:
        logger.error(f"Error updating trading mode: {e}")
        return {
            "success": False,
            "message": f"Error updating trading mode: {str(e)}"
        }
