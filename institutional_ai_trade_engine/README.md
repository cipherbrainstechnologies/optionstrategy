# 🤓 Institutional AI Trade Engine

> **Purpose**: A fully autonomous, rule-based institutional-grade trading system that scans, enters, manages, and exits equity trades per the "Three-Week Inside" (3WI) strategy — for all stocks in Nifty 50 / Nifty 100 / Nifty 500.

**Key Features:**
- 🚀 **100% Autonomous**: No human discretion required
- 🔄 **Idempotent**: Deterministic outputs, same input → same signal
- 🏗️ **Modular**: Clean, maintainable architecture
- 🔒 **Recoverable**: Robust error handling and state management
- 📊 **Real-time**: Live market data and position tracking
- 📱 **Alerts**: Telegram notifications and Google Sheets integration




---

⚙️ CORE OBJECTIVES

1. Automated stock scanning: 3WI pattern + RSI/WMA/ATR/Volume filters.


2. Live portfolio tracking: Hourly risk & exit management.


3. Index watch (BankNifty/Nifty): Real-time tracking of index LTP, implied volatility, and strike derivation; dynamically selects best strike (nearest OTM) for observation, not trading until enabled later.


4. EOD summary + learning ledger: Logs all trades, R:R, PnL, and insights.


5. Full reproducibility: Deterministic outputs; same input → same signal.


6. Strict time gating: 09:25 IST (pre-open) and 15:10 IST (close) for scans; hourly tracking during market hours.


7. Autonomous operations: Cursor IDE executes, pauses only when manual credentials, dependencies, or new libraries are required.




---

🧬 PROJECT STRUCTURE

institutional_ai_trade_engine/
 ├─ pyproject.toml
 ├─ .env.example
 ├─ README.md
 └─ src/
     ├─ core/
     │   ├─ config.py
     │   ├─ scheduler.py
     │   └─ risk.py
     ├─ data/
     │   ├─ angel_client.py
     │   ├─ fetch.py
     │   ├─ indicators.py
     │   ├─ index_watch.py
     ├─ strategy/
     │   ├─ three_week_inside.py
     │   └─ filters.py
     ├─ exec/
     │   ├─ scanner.py
     │   ├─ tracker.py
     │   ├─ near_breakout.py
     │   ├─ eod_report.py
     ├─ alerts/
     │   ├─ telegram.py
     │   └─ sheets.py
     ├─ storage/
     │   ├─ db.py
     │   ├─ schema.sql
     │   └─ ledger.py
     └─ daemon.py


---

🤱 ENVIRONMENT SETUP

pyproject.toml

[project]
name = "institutional-ai-trade-engine"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
  "pandas>=2.2",
  "numpy>=1.26",
  "python-telegram-bot>=21.4",
  "requests",
  "SQLAlchemy>=2.0",
  "apscheduler>=3.10",
  "ta>=0.11.0",
  "python-dotenv",
  "pytz",
  "gspread",
  "oauth2client"
]

.env.example

ANGEL_API_KEY=
ANGEL_CLIENT_CODE=
ANGEL_API_SECRET=
ANGEL_TOTP_SECRET=

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

GSHEETS_CREDENTIALS_JSON=/abs/path/to/creds.json
GSHEETS_MASTER_SHEET="Institutional Portfolio Master Sheet"

PORTFOLIO_CAPITAL=400000
RISK_PCT=1.5
TIMEZONE=Asia/Kolkata
PAPER_MODE=true

Cursor IDE will pause and prompt whenever these credentials are missing or need refresh.


---

🤩 DATABASE SCHEMA (SQLite → PostgreSQL Ready)

src/storage/schema.sql

CREATE TABLE instruments(
  id INTEGER PRIMARY KEY,
  symbol TEXT UNIQUE,
  exchange TEXT DEFAULT 'NSE',
  enabled INTEGER DEFAULT 1
);

CREATE TABLE setups(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  week_start TEXT,
  mother_high REAL,
  mother_low REAL,
  inside_weeks INTEGER,
  matched_filters INTEGER,
  comment TEXT
);

CREATE TABLE positions(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  status TEXT,
  entry_price REAL,
  stop REAL,
  t1 REAL,
  t2 REAL,
  qty INTEGER,
  capital REAL,
  plan_size REAL,
  opened_ts TEXT,
  closed_ts TEXT,
  pnl REAL,
  rr REAL
);

CREATE TABLE ledger(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  opened_ts TEXT,
  closed_ts TEXT,
  pnl REAL,
  rr REAL,
  tag TEXT
);


---

📊 DATA LAYER

src/data/angel_client.py

Handles Angel One SmartAPI for:

Authentication

Historical OHLCV (weekly/daily/hourly)

LTP retrieval (for stocks & indices)

Index module uses BankNifty and Nifty50 symbol tokens.


src/data/index_watch.py

Continuously monitors BankNifty/Nifty index prices:

def get_index_snapshot():
    # Fetch live index LTP, 1m % change, implied vol (if available)
    # Determine nearest OTM strikes (±100 points from LTP)
    # Return dict with current index, strikes, and LTPs

This module does not trade options yet.
It logs and computes volatility zones for later model calibration.


---

📈 INDICATORS

src/data/indicators.py

def compute(df):
    df["RSI"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["WMA20"] = df["close"].rolling(20).mean()
    df["WMA50"] = df["close"].rolling(50).mean()
    df["WMA100"] = df["close"].rolling(100).mean()
    df["ATR"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"]).average_true_range()
    df["ATR_PCT"] = df["ATR"]/df["close"]
    df["VOL_X20D"] = df["volume"]/df["volume"].rolling(20).mean()
    return df


---

🔏 FILTERS

src/strategy/filters.py

def filters_ok(row):
    return (
        row.RSI > 55 and
        row.WMA20 > row.WMA50 > row.WMA100 and
        row.VOL_X20D >= 1.5 and
        row.ATR_PCT < 0.06
    )


---

🔍 THREE-WEEK INSIDE STRATEGY

src/strategy/three_week_inside.py

def detect_3wi(weekly_df):
    res=[]
    for i in range(2,len(weekly_df)):
        m=weekly_df.iloc[i-2]; w1=weekly_df.iloc[i-1]; w2=weekly_df.iloc[i]
        if w1.high<=m.high and w1.low>=m.low and w2.high<=m.high and w2.low>=m.low:
            res.append({"mother_high":m.high,"mother_low":m.low,"index":i})
    return res

def breakout(weekly_df,i):
    m=weekly_df.iloc[i-2]; w2=weekly_df.iloc[i]
    up=w2.close>m.high; down=w2.close<m.low
    return "up" if up else ("down" if down else None)


---

💰 RISK MODEL

src/core/risk.py

def size_position(entry, stop, capital, risk_pct, plan):
    risk_rupees=capital*(risk_pct/100)*plan
    per_share=max(entry-stop,0.01)
    qty=int(risk_rupees/per_share)
    return max(qty,1), risk_rupees


---

🤠 SCANNER (A + E Combined)

src/exec/scanner.py

Runs only at 09:25 and 15:10 IST.

Fetches all enabled instruments.

Detects 3WI patterns, applies filters.

For valid setups:

Store in setups

If breakout confirmed → create new position with computed targets & qty

Send Telegram trade card

Append to Master Sheet




---

⏱ HOURLY TRACKER (B + F)

src/exec/tracker.py

Every hour (minute == 00)

For all live positions:

Fetch LTP

Evaluate:

+3% → SL = BE

+6% → Book 25%

+10% → Book 50%, trail remainder

−3% → Caution

−6% or LTP ≤ SL → Exit


Update Google Sheet & Ledger


Idempotent (duplicate alerts suppressed by position_id + hour hash).



---

📡 NEAR-BREAKOUT TRACKER (E)

src/exec/near_breakout.py

Daily at 15:20 IST.

Scans weekly 3WI setups with LTP ≥ 99% of mother-high.

Lists distance %, highs/lows, close, and confidence.

Friday 15:28 IST → promote any confirmed breakout to full position.



---

📾 EOD SUMMARY (D)

src/exec/eod_report.py

At 15:25 IST.

Summarizes all open/closed trades.

Calculates total PnL, R:R, win rate.

Sends Telegram digest + updates Google Sheet ledger.



---

🕰 SCHEDULER

src/core/scheduler.py

from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
from ..exec import scanner, tracker, near_breakout, eod_report
from ..data import index_watch

def run():
    tz=timezone("Asia/Kolkata")
    s=BlockingScheduler(timezone=tz)
    s.add_job(scanner.run,"cron",day_of_week="mon-fri",hour=9,minute=25)
    s.add_job(scanner.run,"cron",day_of_week="mon-fri",hour=15,minute=10)
    s.add_job(tracker.run,"cron",day_of_week="mon-fri",hour="9-15",minute=0)
    s.add_job(near_breakout.run,"cron",day_of_week="mon-fri",hour=15,minute=20)
    s.add_job(eod_report.run,"cron",day_of_week="mon-fri",hour=15,minute=25)
    s.add_job(index_watch.monitor,"cron",day_of_week="mon-fri",minute="*/5")
    s.start()


---

🧮 INDEX WATCH ENGINE

src/data/index_watch.py

def monitor():
    """
    Fetches live BankNifty/Nifty index data every 5 minutes.
    Logs:
    - current LTP
    - 1m, 5m % change
    - nearest CE/PE strikes (+/-100)
    - corresponding strike LTPs
    Output stored in memory/db for contextual awareness.
    """

No trades are executed — this module provides context only for volatility and breadth awareness.


---

🗾 LEARNING LEDGER

src/storage/ledger.py

Every closed trade appends:

symbol, open/close timestamps

pnl, rr, outcome tag ("3WI success", "false breakout")


Summary function computes:

win rate, avg R, avg hold duration




---

🛠 DEPLOYMENT FLOW (Cursor must pause where manual input needed)

1. Create .venv → install dependencies.


2. Copy .env.example → .env, fill API keys.


3. Initialize DB:

python -m src.storage.db


4. Seed instruments (Nifty 50):

python scripts/seed_instruments.py --list nifty50


5. Test Telegram:

python -m src.alerts.telegram "System online ✅"


6. Dry run scanner:

python -m src.exec.scanner --dry


7. Launch daemon:

python -m src.daemon



Cursor must stop whenever:

A new library is not installed,

API credentials missing/invalid,

Google Sheet auth fails,

Angel One token expired.


Each stop includes a short instruction for manual completion before resuming.


---

🤔 OPERATIONAL PRINCIPLES

Idempotency: Every signal or order carries a deterministic ID (symbol + timeframe + date).

Re-entry safety: Duplicate entries or alerts suppressed.

Auditability: Every trade, alert, and metric logged in DB + Sheet.

Risk caps: Total open risk ≤ 6 % of capital.

Error recovery: On restart, unfinished jobs resume from last DB state.



---

📦 MODULE EXECUTION MAP

Module	Frequency	Purpose

scanner.py	09:25 & 15:10 IST	Detect new setups & confirm breakouts
tracker.py	Hourly (09–15)	Manage open trades, update risk
near_breakout.py	Daily 15:20	Flag near-breakouts
eod_report.py	Daily 15:25	Summary & ledger
index_watch.py	Every 5 min	Monitor index LTP & strikes
daemon.py	Continuous	Runs all jobs



---

✅ FINAL OUTCOME

100% autonomous institutional trading engine.

Scans Nifty universe per defined 3WI strategy.

Enters, manages, and exits trades per risk protocol.

Logs every action in DB + Master Sheet.

Dynamically watches BankNifty/Nifty index context.

Cursor IDE remains deterministic, self-instructed, and safe.

