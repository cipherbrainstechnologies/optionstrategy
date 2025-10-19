# ⚡ Quick Start Guide - FYERS-First (v2.0)

Get the Institutional AI Trade Engine running in under 10 minutes.

---

## Prerequisites Check

- [ ] Python 3.11 or higher installed
- [ ] FYERS account (or use MOCK mode for testing)
- [ ] 5 minutes of your time

---

## Step 1: Environment Setup (2 minutes)

```bash
# Clone repository
cd institutional_ai_trade_engine

# Create virtual environment
python3.11 -m venv .venv

# Activate
source .venv/bin/activate  # Mac/Linux
# Windows: .venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Expected output**: All packages install successfully.

---

## Step 2: Configuration (3 minutes)

### 2a. Create .env file

```bash
cp .env.example .env
```

### 2b. Edit .env (choose your mode)

#### Option A: FYERS Paper Trading (Recommended)

```env
BROKER=FYERS
PORTFOLIO_CAPITAL=400000
RISK_PCT_PER_TRADE=1.5

FYERS_CLIENT_ID=your_client_id_here
FYERS_ACCESS_TOKEN=your_token_here
FYERS_SANDBOX=true
```

**Get FYERS credentials**:
1. Visit https://developers.fyers.in
2. Create app → Note Client ID
3. Generate OAuth token → Copy Access Token
4. Paste both in `.env`

#### Option B: Mock Mode (Testing, No API needed)

```env
BROKER=MOCK
PORTFOLIO_CAPITAL=400000
RISK_PCT_PER_TRADE=1.5
```

---

## Step 3: Portfolio Setup (2 minutes)

```bash
cp data/portfolio.json.template data/portfolio.json
```

Edit `data/portfolio.json` with your holdings:

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

**Replace** example stocks with your actual holdings.

---

## Step 4: Initialize (1 minute)

```bash
python main.py --init
```

**Expected output**:
```
✓ Database initialized
Database initialized at ./data/trade_engine.sqlite
```

---

## Step 5: First Run (2 minutes)

### Daily Scan

```bash
python main.py --daily
```

**What it does**:
- Loads your portfolio holdings
- Fetches weekly data for each stock
- Detects 3WI patterns
- Checks for breakouts
- Creates signals for confirmed setups
- Proposes new adds to `data/ideas.csv`

**Expected output**:
```
==========================================
Starting DAILY SCAN
==========================================
Broker: FYERS_SANDBOX
Portfolio mode: 2 holdings
Scanning RELIANCE
Scanning TCS
...
Daily scan completed
```

### Hourly Execution (if you have open positions)

```bash
python main.py --hourly
```

**What it does**:
- Fetches open positions
- Gets current prices
- Applies profit/loss rules
- Executes partials/exits

### End-of-Day Report

```bash
python main.py --eod
```

**What it does**:
- Summarizes open positions
- Reports closed trades (today)
- Calculates performance metrics
- Shows risk metrics

---

## Step 6: Review Outputs

### Check Logs

```bash
tail -f data/engine.log
```

### Check Ideas

```bash
cat data/ideas.csv
```

Shows proposed new position adds with:
- Entry price, stop loss, targets
- Position size and R:R
- Confidence score
- Reason

### Check Database

```bash
sqlite3 data/trade_engine.sqlite
.tables
.schema positions
SELECT * FROM positions;
.quit
```

---

## Common Commands

```bash
# Daily scan (run at 09:25 or 15:10 IST)
python main.py --daily

# Hourly execution (run every hour 09:00-15:00)
python main.py --hourly

# End-of-day report (run at 15:25 IST)
python main.py --eod

# Re-initialize database (caution: deletes data)
python main.py --init
```

---

## Next Steps

### 1. Set Up Scheduling

**Linux/Mac (cron)**:
```bash
crontab -e
```

Add:
```cron
25 9 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --daily
10 15 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --daily
0 9-15 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --hourly
25 15 * * 1-5 cd /path/to/engine && .venv/bin/python main.py --eod
```

**Windows (Task Scheduler)**:
Create scheduled tasks for above times.

### 2. Configure Alerts (Optional)

Add to `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Review Strategy

Read [3WI Strategy Guide](memory-bank/flows/scanning-flow.md)

### 4. Understand Outputs

- `data/ideas.csv` - New opportunity proposals
- `data/engine.log` - Detailed execution logs
- `data/trade_engine.sqlite` - All trade data

---

## Troubleshooting

### "Missing FYERS credentials"

**Solution**: Add `FYERS_CLIENT_ID` and `FYERS_ACCESS_TOKEN` to `.env`.

### "No holdings in portfolio"

**Solution**: Edit `data/portfolio.json` with your actual holdings.

### "Database initialization failed"

**Solution**: 
```bash
mkdir -p data
chmod 755 data
python main.py --init
```

### "Import error: fyers-apiv3"

**Solution**:
```bash
pip install fyers-apiv3==3.0.8
```

---

## Testing

### Mock Mode (Offline)

```env
BROKER=MOCK
```

Generates synthetic data, no API needed.

### Paper Trading

```env
BROKER=FYERS
FYERS_SANDBOX=true
```

Real data, simulated execution.

### Live Trading

⚠️ **After thorough testing only**:

```env
BROKER=FYERS
FYERS_SANDBOX=false
```

---

## Quick Reference

| Command | Purpose | When to Run |
|---------|---------|-------------|
| `--daily` | Detect patterns, confirm breakouts | 09:25 or 15:10 IST |
| `--hourly` | Manage positions, execute signals | Every hour 09:00-15:00 |
| `--eod` | Performance report | 15:25 IST |
| `--init` | Initialize database | Once at setup |

---

## What's Happening Under the Hood?

### Daily Scan Flow
1. Load portfolio from `data/portfolio.json`
2. For each holding:
   - Fetch 5 years of weekly data (FYERS)
   - Compute indicators (RSI, WMA, ATR, Volume)
   - Detect 3WI patterns
   - Apply filters (RSI>55, trend alignment, volume≥1.5×)
   - Check for breakout
   - Create signal if confirmed
   - Propose add if near breakout
3. Store results in database
4. Write proposals to `data/ideas.csv`

### Hourly Execution Flow
1. Fetch open positions from database
2. For each position:
   - Get current LTP (FYERS)
   - Calculate P&L %
   - Apply rules:
     - +3%: Move SL to BE
     - +6%: Book 25%
     - +10%: Book 50%
     - -6%: Force exit
   - Execute orders if needed
3. Process pending signals
4. Update database

### EOD Report Flow
1. Summarize open positions (unrealized P&L)
2. Summarize closed positions (today)
3. Calculate performance (win rate, avg R:R)
4. Calculate risk metrics (capital deployed, open risk)
5. Print report
6. Send Telegram alert (if configured)

---

## Need Help?

1. Check logs: `tail -f data/engine.log`
2. Review docs: `memory-bank/`
3. Check database: `sqlite3 data/trade_engine.sqlite`
4. Re-read this guide

---

**You're ready to trade! 🚀**

Start with **mock mode** or **paper trading** to gain confidence before going live.
