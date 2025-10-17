# 🏗️ Institutional AI Trade Engine - Architecture

## Overview

The Institutional AI Trade Engine is a fully autonomous, rule-based trading system designed for institutional-grade equity trading. It implements the "Three-Week Inside" (3WI) strategy across Nifty 50/100/500 stocks with complete automation, idempotency, and recoverability.

**Core Principles:**
- **100% Autonomous**: No human discretion required
- **Idempotent**: Deterministic outputs - same input always produces same signal
- **Modular**: Clean separation of concerns for maintainability
- **Recoverable**: Robust error handling and state persistence
- **Auditable**: Complete audit trail in database and Google Sheets

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Trading Engine Daemon                     │
│                         (Orchestrator)                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
┌──────────┐         ┌──────────┐
│ Scheduler│         │  Config  │
│ (APScheduler)      │ Manager  │
└──────────┘         └──────────┘
      │
      ├─────────────────────────────────────────┐
      │                                         │
      ▼                                         ▼
┌─────────────────┐                    ┌─────────────────┐
│  Data Layer     │                    │ Execution Layer │
│  ─────────────  │                    │  ─────────────  │
│ • Angel Client  │                    │ • Scanner       │
│ • Indicators    │◄───────────────────│ • Tracker       │
│ • Index Watch   │                    │ • Near Breakout │
│ • Data Fetch    │                    │ • EOD Report    │
└─────────────────┘                    └─────────────────┘
      │                                         │
      │                                         │
      ▼                                         ▼
┌─────────────────┐                    ┌─────────────────┐
│ Strategy Layer  │                    │  Alert System   │
│  ─────────────  │                    │  ─────────────  │
│ • 3WI Detection │                    │ • Telegram      │
│ • Filters       │                    │ • Google Sheets │
│ • Risk Model    │                    └─────────────────┘
└─────────────────┘
      │
      │
      ▼
┌─────────────────┐
│ Storage Layer   │
│  ─────────────  │
│ • Database      │
│ • Ledger        │
│ • Schema        │
└─────────────────┘
```

---

## Module Architecture

### 1. Core Layer (`src/core/`)

**Purpose**: Foundational system configuration and orchestration

#### `config.py`
- **Responsibility**: Centralized configuration management
- **Pattern**: Singleton-like class with class methods
- **Key Features**:
  - Environment variable loading via dotenv
  - Validation of required credentials
  - Default value management
  - Type conversion and validation

**Configuration Categories**:
```python
# API Credentials
- Angel One API (key, client code, secret, TOTP)
- Telegram (bot token, chat ID)
- Google Sheets (credentials JSON path)

# Trading Parameters
- Portfolio capital (default: 400,000 INR)
- Risk percentage per trade (default: 1.5%)
- Paper mode flag (default: true)
- Timezone (default: Asia/Kolkata)

# Risk Controls
- Maximum open risk: 6% of capital
- Position sizing plan: 1.0 multiplier

# Timing Configuration
- Pre-open scan: 09:25 IST
- Close scan: 15:10 IST
- EOD report: 15:25 IST
- Near-breakout check: 15:20 IST
```

#### `scheduler.py`
- **Responsibility**: Job scheduling and timing control
- **Technology**: APScheduler with BlockingScheduler
- **Timezone**: Asia/Kolkata (IST)
- **Schedule**:

| Job | Frequency | Time (IST) | Purpose |
|-----|-----------|------------|---------|
| Scanner | Mon-Fri | 09:25, 15:10 | Detect new setups & breakouts |
| Tracker | Mon-Fri | Hourly 09:00-15:00 | Manage open positions |
| Near Breakout | Mon-Fri | 15:20 | Flag near-breakout setups |
| EOD Report | Mon-Fri | 15:25 | Daily summary |
| Index Watch | Mon-Fri | Every 5 min | Monitor indices |

**Features**:
- Cron-based scheduling
- Market hours enforcement
- Graceful shutdown handling
- Error recovery on restart

#### `risk.py`
- **Responsibility**: Position sizing and risk calculations
- **Key Functions**:

```python
size_position(entry, stop, capital, risk_pct, plan)
    → Returns: (quantity, risk_amount)
    → Algorithm: Risk-based position sizing
    → Formula: qty = (capital × risk% × plan) / (entry - stop)

calculate_targets(entry, stop, atr)
    → Returns: (t1, t2)
    → T1 = entry + 1.5R (first profit target)
    → T2 = entry + 3.0R (second profit target)

check_risk_limits(open_positions, new_risk)
    → Returns: bool (True if within limits)
    → Validates: Total open risk ≤ 6% of capital

calculate_position_metrics(entry, current_price, stop, qty)
    → Returns: Dict with unrealized PnL, risk amount, PnL %
    → Real-time position evaluation
```

---

### 2. Data Layer (`src/data/`)

**Purpose**: Market data acquisition and processing

#### `angel_client.py`
- **Responsibility**: Angel One SmartAPI integration
- **Key Features**:
  - TOTP-based authentication
  - Session token management
  - Historical data fetching (weekly/daily/hourly)
  - Real-time LTP (Last Traded Price) retrieval
  - Index data for BankNifty and Nifty50

**Authentication Flow**:
```
1. Generate TOTP token from secret
2. Login with API credentials + TOTP
3. Store session token
4. Auto-refresh on expiry
5. Error handling for invalid credentials
```

#### `fetch.py`
- **Responsibility**: Data fetching utilities
- **Features**:
  - Timeframe-specific data retrieval
  - Data validation and cleaning
  - Timestamp handling for IST timezone
  - Retry logic for API failures

#### `indicators.py`
- **Responsibility**: Technical indicator computation
- **Library**: ta (Technical Analysis library)

**Computed Indicators**:
```python
compute(df) → Returns enriched DataFrame with:
    - RSI (Relative Strength Index): 14-period momentum
    - WMA20, WMA50, WMA100: Weighted Moving Averages
    - ATR (Average True Range): Volatility measure
    - ATR_PCT: ATR as percentage of price
    - VOL_X20D: Volume relative to 20-day average
```

**Usage Pattern**:
- Input: Raw OHLCV DataFrame
- Output: DataFrame with added indicator columns
- Idempotent: Same input always produces same output

#### `index_watch.py`
- **Responsibility**: Real-time index monitoring
- **Purpose**: Contextual awareness for market conditions
- **Monitored Indices**: BankNifty, Nifty50

**Data Collected**:
- Current LTP (Last Traded Price)
- 1-minute and 5-minute % change
- Nearest OTM strikes (±100 points)
- Strike LTPs for CE/PE options
- Implied volatility (when available)

**Note**: This module does NOT execute trades - it only provides market context for future enhancements.

---

### 3. Strategy Layer (`src/strategy/`)

**Purpose**: Trading strategy logic and filters

#### `three_week_inside.py`
- **Responsibility**: 3WI pattern detection and analysis

**Core Algorithm**:
```python
detect_3wi(weekly_df):
    For each 3-week window:
        Mother = week[i-2]
        Inside1 = week[i-1]  
        Inside2 = week[i]
        
        If (Inside1.high ≤ Mother.high AND Inside1.low ≥ Mother.low) AND
           (Inside2.high ≤ Mother.high AND Inside2.low ≥ Mother.low):
            → Pattern detected
            → Store: mother_high, mother_low, index, week_start
```

**Pattern Quality Scoring** (0-100):
- **30 points**: Mother range quality (2-8% ideal)
- **25 points**: Volume confirmation (≥1.5x average)
- **25 points**: Trend alignment (price > SMA20 > SMA50)
- **20 points**: RSI momentum (55-75 range)

**Breakout Detection**:
```python
breakout(weekly_df, pattern_index):
    If close > mother_high: return "up"
    If close < mother_low: return "down"
    Else: return None
```

**Near-Breakout Detection**:
- Threshold: 99% of mother high
- Used for early alerts
- Friday 15:28 IST: Auto-promote to full position

**Breakout Strength Metrics**:
- Distance to breakout levels (%)
- Volume ratio vs 20-day average
- ATR percentage
- Current price relative to mother range

#### `filters.py`
- **Responsibility**: Multi-level trade filters
- **Purpose**: Quality control for trade entries

**Filter Criteria**:
```python
filters_ok(row):
    ✓ RSI > 55 (momentum confirmation)
    ✓ WMA20 > WMA50 > WMA100 (uptrend alignment)
    ✓ VOL_X20D ≥ 1.5 (volume surge)
    ✓ ATR_PCT < 0.06 (not too volatile - max 6%)
    
    ALL conditions must be TRUE
```

**Filter Philosophy**:
- Conservative approach: Better to miss trades than take bad ones
- Trend-following: Only trade in direction of major trend
- Volume confirmation: Ensure institutional participation
- Volatility control: Avoid overly volatile stocks

---

### 4. Execution Layer (`src/exec/`)

**Purpose**: Trade execution and management

#### `scanner.py`
- **Responsibility**: New setup detection and trade entry
- **Execution Times**: 09:25 IST (pre-open), 15:10 IST (close)

**Workflow**:
```
1. Fetch all enabled instruments from database
2. For each instrument:
   a. Fetch weekly data
   b. Compute technical indicators
   c. Detect 3WI patterns
   d. Apply technical filters
   e. Check for breakout confirmation
3. For valid setups:
   a. Calculate position size using risk model
   b. Check risk limits
   c. Store setup in database
   d. If breakout confirmed:
      - Create new position
      - Send Telegram alert
      - Update Google Sheet
4. Log all actions for auditability
```

**Idempotency Mechanism**:
- Unique ID: `{symbol}_{timeframe}_{date}`
- Duplicate entries automatically suppressed
- Database constraints prevent duplicates

#### `tracker.py`
- **Responsibility**: Live position management
- **Execution**: Every hour from 09:00 to 15:00 IST

**Position Management Rules**:
```
Profit Management:
- +3%  → Move stop loss to breakeven (BE)
- +6%  → Book 25% profit, trail stop
- +10% → Book 50% profit, trail remaining
- +15% → Trail aggressively (2 × ATR)

Loss Management:
- -3%  → Caution alert (watch closely)
- -6%  → Exit immediately
- LTP ≤ Stop Loss → Exit immediately

Exit Conditions:
- Stop loss hit
- Target reached
- Trailing stop hit
- Risk management override
```

**Workflow**:
```
1. Fetch all open positions
2. For each position:
   a. Get current LTP
   b. Calculate unrealized PnL
   c. Evaluate profit/loss rules
   d. Update stop loss if needed
   e. Execute partial/full exits
   f. Update database
   g. Send alerts
3. Update Google Sheet with current state
4. Log all actions
```

**Idempotency**:
- Alert hash: `{position_id}_{hour}_{action}`
- Prevents duplicate alerts for same hour

#### `near_breakout.py`
- **Responsibility**: Near-breakout monitoring and alerts
- **Execution**: Daily at 15:20 IST

**Workflow**:
```
1. Fetch all active 3WI setups (not yet broken out)
2. For each setup:
   a. Get current LTP
   b. Calculate distance to mother high
   c. If LTP ≥ 99% of mother high:
      - Flag as near breakout
      - Calculate quality score
      - Send Telegram alert
3. Special Friday Logic (15:28 IST):
   - Check if breakout confirmed
   - Auto-promote to full position
   - Send trade confirmation
```

**Alert Format**:
- Symbol and current price
- Distance to breakout (%)
- Mother high/low levels
- Pattern quality score
- Volume and momentum metrics

#### `eod_report.py`
- **Responsibility**: End-of-day summary and performance tracking
- **Execution**: Daily at 15:25 IST

**Report Contents**:
```
Open Positions:
- Count and symbols
- Unrealized PnL (total and per position)
- Current P&L percentage
- Days in trade

Closed Positions (Today):
- Count and symbols
- Realized PnL
- R:R ratio achieved
- Win/loss classification

Performance Metrics:
- Total PnL (realized + unrealized)
- Win rate (%)
- Average R:R ratio
- Average hold duration
- Best/worst trades

Risk Metrics:
- Total capital deployed
- Current open risk %
- Available capital
- Risk capacity remaining
```

**Ledger Update**:
- All closed trades recorded
- Performance tags applied
- Historical data for backtesting

---

### 5. Alert System (`src/alerts/`)

**Purpose**: Notification and reporting

#### `telegram.py`
- **Responsibility**: Real-time notifications via Telegram
- **Library**: python-telegram-bot

**Alert Types**:
1. **System Alerts**:
   - Engine start/stop
   - Error notifications
   - Configuration warnings

2. **Trade Alerts**:
   - New position entry
   - Stop loss hits
   - Profit booking
   - Position exits
   - Near-breakout notifications

3. **Daily Reports**:
   - EOD summary
   - Performance metrics
   - Risk status

**Alert Format**:
```
🚀 NEW POSITION
─────────────
Symbol: RELIANCE
Entry: ₹2,450.00
Stop: ₹2,380.00
T1: ₹2,555.00 (1.5R)
T2: ₹2,660.00 (3.0R)
Qty: 50
Risk: ₹6,000 (1.5%)
─────────────
Pattern: 3WI Breakout
Quality: 87/100
```

#### `sheets.py`
- **Responsibility**: Google Sheets integration for portfolio tracking
- **Library**: gspread, oauth2client

**Sheet Structure**:
```
Master Sheet: "Institutional Portfolio Master Sheet"

Tabs:
1. Active Positions
   - Symbol, Entry, Stop, Targets, Qty
   - Current Price, Unrealized PnL
   - Days in trade, Status

2. Trade History
   - All closed trades
   - Entry/Exit prices and timestamps
   - PnL, R:R ratio
   - Tags and notes

3. Performance Dashboard
   - Daily/Weekly/Monthly PnL
   - Win rate and average R:R
   - Drawdown tracking
   - Risk metrics

4. Setup Watch List
   - Active 3WI patterns
   - Near-breakout candidates
   - Quality scores
```

**Update Frequency**:
- Real-time: Trade entries/exits
- Hourly: Position updates
- Daily: Performance summary

---

### 6. Storage Layer (`src/storage/`)

**Purpose**: Data persistence and audit trail

#### `db.py`
- **Responsibility**: Database operations
- **Technology**: SQLAlchemy (SQLite default, PostgreSQL ready)

**Key Features**:
- Connection pooling
- Transaction management
- Error handling and rollback
- Migration support

**Operations**:
```python
init_database()       # Create schema
get_session()         # Get DB session
insert()              # Add records
update()              # Modify records
query()               # Fetch records
delete()              # Remove records (soft delete preferred)
```

#### `schema.sql`
- **Responsibility**: Database schema definition

**Tables**:

1. **instruments**
   - Purpose: Trading universe
   - Fields: id, symbol, exchange, enabled
   - Constraints: Unique symbol

2. **setups**
   - Purpose: Detected 3WI patterns
   - Fields: id, symbol, week_start, mother_high, mother_low, inside_weeks, matched_filters, comment
   - Indexing: symbol, week_start

3. **positions**
   - Purpose: Open and closed trades
   - Fields: id, symbol, status, entry_price, stop, t1, t2, qty, capital, plan_size, opened_ts, closed_ts, pnl, rr
   - Status values: 'open', 'partial', 'closed'
   - Indexing: symbol, status, opened_ts

4. **ledger**
   - Purpose: Historical performance tracking
   - Fields: id, symbol, opened_ts, closed_ts, pnl, rr, tag
   - Indexing: closed_ts, tag
   - Tags: "3WI success", "false breakout", "stopped out", etc.

**Design Principles**:
- Normalized for efficiency
- Timestamps in ISO format
- Support for soft deletes
- Audit trail via ledger

#### `ledger.py`
- **Responsibility**: Trade performance tracking and analysis

**Key Functions**:
```python
record_trade(position)
    → Appends closed trade to ledger
    → Classifies outcome (success/failure)
    → Tags for analysis

get_performance_summary(start_date, end_date)
    → Returns: win rate, avg R, avg duration
    → Filters by date range and tags
    → Calculates aggregate metrics

get_best_worst_trades(n=10)
    → Top/bottom performers
    → Used for strategy refinement

calculate_drawdown()
    → Maximum drawdown
    → Current drawdown
    → Recovery metrics
```

---

### 7. Daemon (`src/daemon.py`)

**Purpose**: Main orchestrator and entry point

**Responsibilities**:
- System initialization
- Configuration validation
- Database setup
- Scheduler management
- Signal handling (SIGINT, SIGTERM)
- Graceful shutdown
- Error recovery

**Startup Sequence**:
```
1. Load configuration from environment
2. Validate required credentials
3. Initialize database (create schema if needed)
4. Test external connections:
   - Angel One API
   - Telegram bot
   - Google Sheets (optional)
5. Setup logging (file + console)
6. Register signal handlers
7. Start scheduler with all jobs
8. Enter main loop
```

**Shutdown Sequence**:
```
1. Receive signal (SIGINT/SIGTERM)
2. Stop accepting new jobs
3. Wait for active jobs to complete (timeout: 30s)
4. Close database connections
5. Send shutdown notification
6. Exit gracefully
```

**Error Handling**:
- Missing credentials → Pause and prompt user
- API failure → Retry with exponential backoff
- Database error → Log and continue (skip iteration)
- Critical error → Alert and safe shutdown

---

## Data Flow

### 1. Scanning Flow (New Setup Detection)

```
[Scheduler] → [Scanner]
                ↓
    [Angel API: Fetch Weekly Data]
                ↓
    [Indicators: Compute RSI/WMA/ATR/Volume]
                ↓
    [3WI Strategy: Detect Patterns]
                ↓
    [Filters: Apply Quality Checks]
                ↓
    ┌──────────┴──────────┐
    ↓                     ↓
[Store Setup]      [Breakout Check]
    ↓                     ↓
[Database]        [Create Position]
                          ↓
                  ┌───────┴───────┐
                  ↓               ↓
            [Telegram]      [Google Sheets]
```

### 2. Tracking Flow (Position Management)

```
[Scheduler] → [Tracker]
                ↓
    [Database: Fetch Open Positions]
                ↓
    [Angel API: Get Current LTP]
                ↓
    [Risk: Calculate Metrics]
                ↓
    [Evaluate Rules: +3%, +6%, +10%, -3%, -6%]
                ↓
    ┌──────────┴──────────┐
    ↓                     ↓
[Update Position]   [Execute Exit/Partial]
    ↓                     ↓
[Database]        ┌───────┴───────┐
                  ↓               ↓
            [Telegram]      [Google Sheets]
```

### 3. EOD Flow (Daily Summary)

```
[Scheduler] → [EOD Report]
                ↓
    [Database: Fetch All Positions]
                ↓
    [Ledger: Get Performance Metrics]
                ↓
    [Calculate: Win Rate, Avg R:R, PnL]
                ↓
    [Generate Summary Report]
                ↓
    ┌──────────┴──────────┐
    ↓                     ↓
  [Telegram]      [Google Sheets]
                          ↓
                  [Ledger Update]
```

---

## Technology Stack

### Core Technologies
- **Python**: 3.10+ (type hints, modern syntax)
- **Scheduler**: APScheduler (cron-based job scheduling)
- **Database**: SQLAlchemy (ORM for SQLite/PostgreSQL)
- **Data Processing**: pandas, numpy

### External APIs
- **Angel One SmartAPI**: Market data and order execution
- **Telegram Bot API**: Real-time notifications
- **Google Sheets API**: Portfolio tracking and reporting

### Technical Analysis
- **ta Library**: RSI, ATR, moving averages
- **Custom Indicators**: Volume ratios, trend metrics

### Deployment
- **Environment**: python-dotenv for configuration
- **Logging**: Python logging module (file + console)
- **Process Management**: systemd (Linux) or supervisor

---

## Deployment Architecture

### Development Environment
```
local_machine/
├── .env                    # Local credentials
├── trading_engine.db       # SQLite database
├── trading_engine.log      # Application logs
└── institutional_ai_trade_engine/
    └── src/                # Source code
```

### Production Environment (Recommended)
```
production_server/
├── /opt/trading-engine/
│   ├── .env               # Production credentials
│   ├── src/               # Source code
│   └── venv/              # Virtual environment
├── /var/log/trading-engine/
│   └── trading_engine.log
└── /var/lib/trading-engine/
    └── trading_engine.db  # Database (or PostgreSQL)
```

**Process Management**:
```systemd
[Unit]
Description=Institutional AI Trade Engine
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading-engine
ExecStart=/opt/trading-engine/venv/bin/python -m src.daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Security Considerations

### 1. Credentials Management
- ✅ Environment variables (never hardcode)
- ✅ Restricted file permissions (600 for .env)
- ✅ No credentials in version control
- ✅ Separate dev/prod credentials

### 2. API Security
- ✅ TOTP-based authentication for Angel One
- ✅ Token refresh mechanism
- ✅ Rate limiting compliance
- ✅ Error handling for invalid tokens

### 3. Database Security
- ✅ Parameterized queries (SQLAlchemy)
- ✅ No SQL injection vulnerabilities
- ✅ Regular backups
- ✅ Access control

### 4. Process Security
- ✅ Run as non-root user
- ✅ Limited file system access
- ✅ Graceful signal handling
- ✅ Secure logging (no sensitive data)

---

## Monitoring and Observability

### 1. Logging Levels
```python
DEBUG:   Detailed diagnostic information
INFO:    General operational messages
WARNING: Unusual events (API delays, missing data)
ERROR:   Errors that don't stop execution
CRITICAL: Fatal errors requiring immediate attention
```

### 2. Key Metrics to Monitor
- **System Health**:
  - Daemon uptime
  - Job execution success rate
  - API connection status
  
- **Trading Metrics**:
  - Number of open positions
  - Total capital deployed
  - Current open risk %
  - Daily PnL
  
- **Performance Metrics**:
  - Win rate
  - Average R:R ratio
  - Maximum drawdown
  - Sharpe ratio

### 3. Alert Thresholds
- Open risk > 5.5% → Warning
- Open risk > 6.0% → Critical
- Daily loss > 3% → Alert
- API failures > 3 consecutive → Critical

---

## Scalability Considerations

### Current Capacity
- Instruments: 500 stocks (Nifty 500)
- Concurrent positions: 10-15 (based on 6% total risk)
- Data storage: Grows ~1MB per month
- API calls: ~500 per day (within limits)

### Future Enhancements
1. **Database Migration**: SQLite → PostgreSQL for production
2. **Caching**: Redis for real-time data
3. **Message Queue**: RabbitMQ/Celery for async processing
4. **Load Balancing**: Multiple scanner instances
5. **Microservices**: Split into scanner/tracker/alert services

---

## Testing Strategy

### 1. Unit Tests
- Individual function testing
- Mock external APIs
- Test edge cases

### 2. Integration Tests
- Database operations
- API interactions
- End-to-end flows

### 3. Paper Trading
- Live market data
- No real orders
- Full system validation

### 4. Backtesting
- Historical data
- Strategy validation
- Performance metrics

---

## Disaster Recovery

### 1. Database Backups
- Frequency: Daily
- Retention: 30 days
- Storage: Offsite backup

### 2. State Recovery
- Positions persist in database
- Resume tracking on restart
- No duplicate entries (idempotency)

### 3. Emergency Shutdown
- Close all positions at market
- Send alert notifications
- Log final state
- Wait for manual intervention

---

## Performance Optimization

### 1. Data Fetching
- Batch API calls where possible
- Cache technical indicators
- Avoid redundant calculations

### 2. Database
- Indexed queries (symbol, status, timestamp)
- Connection pooling
- Prepared statements

### 3. Computation
- Vectorized operations (pandas)
- Minimize loops
- Lazy evaluation where possible

---

## Compliance and Audit

### 1. Audit Trail
- All trades logged in ledger
- Timestamps in ISO format
- Immutable records

### 2. Regulatory Compliance
- Position limits enforced
- Risk limits enforced
- Paper mode for testing
- Real-time reporting

### 3. Trade Reconciliation
- Daily position verification
- PnL calculation audit
- Discrepancy alerts

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | January 2025 | Initial implementation - Full autonomous trading engine |

---

## References

### Internal Documentation
- See `memory-bank/flows/` for detailed operational flows
- See `memory-bank/patterns/` for implementation patterns
- See `memory-bank/decisions.md` for architectural decisions

### External Resources
- Angel One SmartAPI: https://smartapi.angelbroking.com
- Technical Analysis Library: https://technical-analysis-library-in-python.readthedocs.io
- APScheduler: https://apscheduler.readthedocs.io
