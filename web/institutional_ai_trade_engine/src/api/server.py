from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List

from src.storage.db import get_db_session, init_database
from src.storage.models import Position

app = FastAPI(title= Institutional AI Trade Engine API)

origins = [
    http://localhost:3000,
    http://127.0.0.1:3000,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[*],
    allow_headers=[*],
)

class ActionPayload(BaseModel):
    action: str
    symbol: str | None = None

@app.on_event(startup)
def startup_event():
    try:
        init_database()
    except Exception:
        # Database may already be initialized
        pass

@app.get(/overview)
def get_overview():
    db = get_db_session()
    try:
        positions_count = db.query(Position).count()
    except Exception:
        positions_count = 0
    capital = float(os.getenv(PORTFOLIO_CAPITAL, 400000))
    paper_str = os.getenv(PAPER_MODE, true).lower()
    paper_mode = paper_str in (1, true, yes, y)
    return {
        engineStatus: Running,
        paperMode: paper_mode,
        lastScan: --:--,
        capital: capital,
        openRiskPct: 0.0,
        pnlDay: 0.0,
        positions: positions_count,
        signals: 0,
        winRate: 0,
    }

@app.get(/positions)
def get_positions():
    db = get_db_session()
    try:
        rows: List[Position] = db.query(Position).all()
    except Exception as e:
        rows = []
    result = []
    for p in rows:
        result.append({
            symbol: p.symbol,
            entry: p.entry_price,
            stop: p.stop,
            t1: p.t1,
            t2: p.t2,
            ltp: p.entry_price,  # placeholder; ideally fetch live price
            status: p.status,
            pnl: p.pnl if p.pnl is not None else 0.0,
        })
    return result

@app.post(/actions)
def post_actions(payload: ActionPayload):
    # For now, acknowledge action; real implementation would route to orchestration
    return {ok: True, action: payload.action, symbol: payload.symbol}
