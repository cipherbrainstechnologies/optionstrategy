from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List

from src.storage.db import init_database, engine
from sqlalchemy import text

app = FastAPI(title="Institutional AI Trade Engine API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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

@app.on_event("startup")
def startup_event():
    try:
        init_database()
    except Exception:
        pass

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
    return {
        "engineStatus": "Running",
        "paperMode": paper_mode,
        "lastScan": "--:--",
        "capital": capital,
        "openRiskPct": 0.0,
        "pnlDay": 0.0,
        "positions": positions_count,
        "signals": 0,
        "winRate": 0,
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
