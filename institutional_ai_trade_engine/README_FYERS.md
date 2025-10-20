# 🚀 Institutional AI Trade Engine - FYERS-First (v2.0)

> **A fully autonomous, rule-based trading system with broker abstraction, portfolio-only mode, and three-week inside candle strategy.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-brightgreen.svg)]()

---

## 🎯 What's New in v2.0

- **FYERS-First**: Native FYERS integration with unified paper/live API
- **Broker Abstraction**: Support for FYERS, Angel One, and Mock Exchange
- **Portfolio-Only Mode**: Trade only your holdings, get new add proposals
- **Hourly Execution**: Separate hourly position management layer
- **Simplified Entry**: Single `main.py` with CLI arguments
- **5-Year Historical Data**: FYERS provides extensive historical data for backtesting

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Clone and setup
git clone <repo>
cd institutional_ai_trade_engine

# 2. Create environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -U pip
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your FYERS credentials

cp data/portfolio.json.template data/portfolio.json
# Edit data/portfolio.json with your holdings

# 5. Initialize
python main.py --init

# 6. Run
python main.py --daily    # Daily scan
python main.py --hourly   # Hourly execution
python main.py --eod      # End-of-day report
```

---

## 📋 Features

### Core Capabilities

- ✅ **100% Autonomous**: No human discretion required
- ✅ **Idempotent**: Deterministic outputs, safe re-runs
- ✅ **Broker Agnostic**: FYERS (paper/live), Angel One, or Mock
- ✅ **Portfolio-Only**: Trade only your holdings
- ✅ **Historical Data**: 5+ years via FYERS API
- ✅ **Paper Trading**: FYERS sandbox with identical API
- ✅ **3WI Strategy**: Three-week inside candle pattern
- ✅ **Risk Management**: 1.5% risk per trade, 6% total cap
- ✅ **Hourly Execution**: Automated position management
- ✅ **Learning Ledger**: Performance tracking and analysis

### Strategy

**Three-Week Inside Candle (3WI)**
- Detect mother bar + 2 inside weeks
- Confirm breakout with volume (≥1.5× average)
- RSI momentum filter (>55 for longs)
- Entry at mother bar high, SL at mother bar low
- Targets: 1.5R and 3.0R

**Position Management**
- +3%: Move SL to breakeven
- +6%: Book 25%, trail stop
- +10%: Book 50%, trail remainder
- -3%: Caution alert
- -6%: Force exit

---

## 🏗️ Architecture

```
institutional_ai_trade_engine/
├── main.py                    # Single entry point
├── .env                       # Configuration (create from .env.example)
├── requirements.txt           # Dependencies
│
├── src/
│   ├── core/
│   │   ├── config.py         # Settings & broker selection
│   │   └── risk.py           # Position sizing & risk management
│   │
│   ├── data/
│   │   ├── broker_base.py    # Broker abstraction interface
│   │   ├── fyers_client.py   # FYERS implementation
│   │   ├── angel_client.py   # Angel One (legacy)
│   │   ├── mock_exchange.py  # Offline testing
│   │   └── indicators.py     # Technical indicators (RSI, WMA, ATR)
│   │
│   ├── strategy/
│   │   ├── three_week_inside.py  # 3WI pattern detection
│   │   ├── filters.py            # Entry filters
│   │   ├── portfolio_mode.py     # Portfolio management
│   │   └── execution_hourly.py   # Hourly executor
│   │
│   ├── orchestration/
│   │   ├── run_daily.py      # Daily scan flow
│   │   ├── run_hourly.py     # Hourly execution flow
│   │   └── reports.py        # EOD reports
│   │
│   ├── storage/
│   │   ├── db.py             # Database operations
│   │   ├── schema.sql        # Database schema
│   │   ├── models.py         # Pydantic & SQLAlchemy models
│   │   └── ledger.py         # Learning ledger
│   │
│   └── alerts/
│       ├── telegram.py       # Telegram notifications
│       └── sheets.py         # Google Sheets integration
│
└── data/
    ├── portfolio.json        # Your holdings (create from template)
    ├── triggers.yaml         # Custom triggers (optional)
    ├── ideas.csv             # Proposed new adds (auto-generated)
    ├── trade_engine.sqlite   # Main database (auto-created)
    └── engine.log            # Application logs (auto-created)
```

---

## 🔧 Setup

### 1. Prerequisites

- **Python 3.11+**
- FYERS account (or Mock mode for testing)
- (Optional) Telegram bot for alerts

### 2. Environment Setup

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

#### .env File

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Broker: FYERS | ANGEL | MOCK
BROKER=FYERS

# Capital & Risk
PORTFOLIO_CAPITAL=400000
RISK_PCT_PER_TRADE=1.5

# FYERS Credentials
FYERS_CLIENT_ID=your_client_id
FYERS_ACCESS_TOKEN=your_access_token
FYERS_SANDBOX=true  # true for paper, false for live

# Paths
DATA_DIR=./data
DB_PATH=./data/trade_engine.sqlite
LOG_PATH=./data/engine.log
```

**FYERS Setup**:
1. Visit https://developers.fyers.in
2. Create an app, note Client ID
3. Generate OAuth access token
4. Add to `.env` file

#### Portfolio Configuration

```bash
cp data/portfolio.json.template data/portfolio.json
```

Edit `data/portfolio.json`:

```json
{
  "holdings": {
    "RELIANCE": {
      "qty": 10,
      "avg_price": 2450.50,
      "notes": "Energy sector"
    },
    "TCS": {
      "qty": 5,
      "avg_price": 3600.00,
      "notes": "IT sector"
    }
  }
}
```

**Important**: Engine scans ONLY stocks in `portfolio.json`.

### 4. Initialize Database

```bash
python main.py --init
```

---

## 🚀 Usage

### Daily Scan

Detect 3WI patterns and confirm breakouts:

```bash
python main.py --daily
```

**When to run**: 09:25 IST (pre-open) or 15:10 IST (close)

### Hourly Execution

Manage open positions and execute signals:

```bash
python main.py --hourly
```

**When to run**: Every hour 09:00-15:00 IST

### End-of-Day Report

Performance summary and learning ledger:

```bash
python main.py --eod
```

**When to run**: 15:25 IST (after market close)

### Scheduling (Recommended)

#### Linux/Mac (cron)

```cron
# Daily scans
25 9 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --daily
10 15 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --daily

# Hourly execution
0 9-15 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --hourly

# EOD report
25 15 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --eod
```

#### Windows (Task Scheduler)

Create tasks for:
- Daily scan: 09:25 and 15:10, Mon-Fri
- Hourly exec: Every hour 09:00-15:00, Mon-Fri
- EOD report: 15:25, Mon-Fri

---

## 📊 Outputs

### ideas.csv

Proposed new position adds:

```csv
timestamp,symbol,entry,stop,t1,t2,qty,risk_r,r_r,confidence,pattern,reason
2025-10-19T10:30:00,RELIANCE,2500.00,2380.00,2680.00,2860.00,16,120.00,1.50,87.5,3WI_NEAR_BREAKOUT,Near breakout RSI=68
```

### trade_engine.sqlite

SQLite database with tables:
- `instruments` - Trading universe
- `setups` - Detected 3WI patterns
- `signals` - Trade signals
- `orders` - Order history
- `fills` - Execution records
- `positions` - Open/closed trades
- `ledger` - Learning ledger

### engine.log

Application logs with timestamps and execution details.

---

## 🧪 Testing

### Mock Mode (Offline)

Test without broker connection:

```env
BROKER=MOCK
```

Mock exchange generates synthetic data and simulates order execution.

### Paper Trading (FYERS Sandbox)

Test with real market data, simulated execution:

```env
BROKER=FYERS
FYERS_SANDBOX=true
```

### Live Trading

⚠️ **Use with caution**:

```env
BROKER=FYERS
FYERS_SANDBOX=false
```

---

## 📈 Strategy Details

### Three-Week Inside (3WI) Pattern

**Definition**:
- Week t-2: Mother bar (reference candle)
- Week t-1: Inside bar (high ≤ mother high, low ≥ mother low)
- Week t: Inside bar (high ≤ mother high, low ≥ mother low)

**Entry Trigger**:
- Weekly close > mother bar high (long)
- Weekly close < mother bar low (short, not implemented yet)

**Confirmation**:
- Volume ≥ 1.5× 20-week average
- RSI(14) > 55 for longs
- Price > WMA20 > WMA50 > WMA100 (trend alignment)
- ATR% < 6% (volatility control)

**Position Sizing**:
```python
qty = (capital × risk%) / (entry - stop)
# Example: (400,000 × 1.5%) / (2500 - 2380) = 50 shares
```

**Targets**:
- T1 = Entry + 1.5R (50% exit)
- T2 = Entry + 3.0R (remaining 50% exit)

---

## 🔐 Security

- ✅ Environment variables for credentials (never hardcode)
- ✅ `.env` file permissions: 600 (owner read/write only)
- ✅ No credentials in version control
- ✅ Parameterized SQL queries (SQLAlchemy ORM)
- ✅ Separate paper/live credentials

---

## 🛠️ Troubleshooting

### Missing FYERS credentials

```
[SETUP REQUIRED] Missing FYERS credentials: FYERS_CLIENT_ID, FYERS_ACCESS_TOKEN
```

**Solution**: Add credentials to `.env` file.

### No holdings in portfolio

```
No holdings in portfolio. Add holdings to data/portfolio.json
```

**Solution**: Edit `data/portfolio.json` with your actual holdings.

### Database initialization failed

```
Database initialization failed: ...
```

**Solution**: Ensure `data/` directory exists and is writable.

### FYERS API errors

Check:
- Token expiry (regenerate if needed)
- API rate limits
- Network connectivity
- FYERS service status

---

## 📚 Documentation

- [Architecture Overview](memory-bank/architecture.md)
- [Decision Log](memory-bank/decisions.md)
- [Implementation Patterns](memory-bank/patterns/)
- [Data Flows](memory-bank/flows/)

---

## 🤝 Contributing

This is a personal trading system. Fork and customize for your needs.

---

## ⚠️ Disclaimer

**This software is for educational purposes only.**

- Past performance ≠ future results
- Trading involves risk of capital loss
- Test thoroughly in paper mode before live trading
- Use at your own risk
- No warranty or guarantees provided

---

## 📝 License

MIT License - See LICENSE file

---

## 🎯 Roadmap

- [ ] Options trading support (BankNifty/Nifty)
- [ ] Multi-timeframe analysis
- [ ] Machine learning pattern quality scoring
- [ ] Web dashboard (FastAPI)
- [ ] Real-time WebSocket execution
- [ ] Backtesting framework
- [ ] Portfolio optimization

---

## 📞 Support

- Issues: GitHub Issues
- Docs: `memory-bank/` directory
- Logs: `data/engine.log`

---

**Happy Trading! 🚀**
