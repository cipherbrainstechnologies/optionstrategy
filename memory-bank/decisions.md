# 🧭 Decision Evolution Log

## Overview

This document tracks all critical architectural, design, and implementation decisions for the Institutional AI Trade Engine. The engine has been rebuilt as a FYERS-first implementation with full broker abstraction.

---

## Recent Major Decisions (v2.0 - FYERS-First Rebuild)

### Decision #009 – FYERS as Primary Broker

- **Date**: 2025-10-19
- **Author**: System Architect
- **Status**: ✅ Active
- **Summary**: Migrate from Angel One to FYERS as primary broker with full abstraction layer

**Context**:
- Original implementation was Angel One-specific
- Need for broker-agnostic architecture
- FYERS provides unified paper/live trading API
- Requirement for offline testing capability

**Decision**:
- Implement broker abstraction layer (`BrokerBase`)
- FYERS as primary broker (paper + live modes via single API)
- Angel One supported as future option
- Mock Exchange for offline testing
- Broker selection via environment variable

**Rationale**:
1. **Unified API**: FYERS sandbox and live use identical endpoints
2. **Paper Trading**: Native paper trading support without separate infrastructure
3. **Historical Data**: FYERS provides 5+ years of OHLCV data
4. **Future-Proof**: Abstraction allows easy broker switching
5. **Testing**: Mock exchange enables offline development

**Alternatives Considered**:
1. **Keep Angel One Only**: Rejected - want FYERS paper trading
2. **Dual Implementation**: Rejected - maintainability issues
3. **Abstraction Layer**: ✅ Chosen - flexibility and maintainability

**Affected Modules**:
- `src/data/broker_base.py` - Abstraction interface
- `src/data/fyers_client.py` - FYERS implementation
- `src/data/angel_client.py` - Angel One (legacy support)
- `src/data/mock_exchange.py` - Offline testing
- `src/core/config.py` - Broker selection logic

**Consequences**:
- ✅ Benefits:
  - Single codebase supports 3 brokers
  - Easy paper-to-live transition (env var change)
  - Offline testing capability
  - Future broker additions simple
  
- ⚠️ Considerations:
  - Initial migration effort
  - Need to maintain broker interfaces
  - Testing across multiple brokers

**Reversal Conditions**:
- If FYERS API proves unreliable
- If broker abstraction adds significant overhead
- If single-broker approach is sufficient

---

### Decision #010 – Portfolio-Only Mode

- **Date**: 2025-10-19
- **Author**: Strategy Lead
- **Status**: ✅ Active
- **Summary**: Trade only holdings in portfolio, propose new adds per strategy

**Context**:
- Original design scanned entire Nifty universe
- Users want to focus on existing holdings
- Need mechanism to propose new positions
- Capital management for actual portfolio

**Decision**:
- Implement `PortfolioMode` class
- Load holdings from `data/portfolio.json`
- Scan ONLY portfolio stocks for 3WI patterns
- Propose new adds to `data/ideas.csv` when strategy confirms
- Track actual holdings and P&L

**Rationale**:
1. **Focus**: Manage what you own, not theoretical universe
2. **Capital Accuracy**: Size positions based on actual capital
3. **Opportunity Discovery**: Still find new opportunities via ideas.csv
4. **Risk Management**: Better control of total exposure

**Implementation**:
```json
// data/portfolio.json
{
  "holdings": {
    "RELIANCE": {"qty": 10, "avg_price": 2450.50},
    "TCS": {"qty": 5, "avg_price": 3600.00}
  }
}
```

**Affected Modules**:
- `src/strategy/portfolio_mode.py` - Portfolio management
- `src/orchestration/run_daily.py` - Uses portfolio filter
- `data/portfolio.json` - Holdings configuration
- `data/ideas.csv` - Proposed adds output

**Consequences**:
- ✅ Benefits:
  - Focused scanning (faster)
  - Realistic capital management
  - Clear opportunity pipeline
  - Actual vs theoretical alignment
  
- ⚠️ Considerations:
  - Manual portfolio file maintenance
  - Might miss opportunities outside portfolio
  - Requires discipline to review ideas.csv

**Reversal Conditions**:
- If full universe scanning preferred
- If portfolio tracking becomes burdensome

---

### Decision #011 – Hourly Execution Layer

- **Date**: 2025-10-19
- **Author**: Strategy Lead
- **Status**: ✅ Active
- **Summary**: Separate hourly execution from daily scanning

**Context**:
- Original design mixed scanning and execution
- Need clearer separation of concerns
- Hourly position management distinct from daily pattern detection
- Pre-breakout half-size entries on hourly confirmation

**Decision**:
- Create `HourlyExecutor` class
- Run hourly during market hours (09:00-15:00)
- Manage open positions (profit/loss rules)
- Execute pending signals on hourly confirmation
- Support pre-breakout entries (half size)

**Workflow**:
```
Hourly Cycle:
1. Fetch open positions
2. Get current LTP for each
3. Apply profit/loss rules:
   - +3%: Move SL to BE
   - +6%: Book 25%
   - +10%: Book 50%
   - -3%: Caution alert
   - -6%: Force exit
4. Process pending signals
5. Execute triggered signals
```

**Affected Modules**:
- `src/strategy/execution_hourly.py` - Hourly executor
- `src/orchestration/run_hourly.py` - Orchestration
- `main.py` - Entry point with --hourly flag

**Consequences**:
- ✅ Benefits:
  - Clean separation: scan vs execute
  - Hourly position monitoring
  - Pre-breakout entry support
  - Systematic profit management
  
- ⚠️ Considerations:
  - Hourly frequency may miss intra-hour moves
  - Requires scheduler or manual runs

**Reversal Conditions**:
- If real-time tick-by-tick monitoring needed
- If hourly frequency insufficient for strategy

---

### Decision #012 – Main.py Entry Point

- **Date**: 2025-10-19
- **Author**: System Architect
- **Status**: ✅ Active
- **Summary**: Single entry point with CLI arguments for all operations

**Context**:
- Original design used daemon with scheduler
- Need simpler execution model
- Want explicit control over when operations run
- OS schedulers (cron, Task Scheduler) can handle timing

**Decision**:
- Create `main.py` as single entry point
- Use argparse for command selection
- Support: `--daily`, `--hourly`, `--eod`, `--init`
- Let OS handle scheduling (cron/Task Scheduler)

**Usage**:
```bash
# Daily scan
python main.py --daily

# Hourly execution
python main.py --hourly

# End of day report
python main.py --eod

# Initialize database
python main.py --init
```

**Rationale**:
1. **Simplicity**: One command, clear intent
2. **Debuggability**: Easy to run specific flows
3. **Flexibility**: OS schedulers more reliable
4. **Idempotency**: Safe to re-run commands

**Alternatives Considered**:
1. **Daemon with APScheduler**: Rejected - complexity, debugging harder
2. **Separate scripts**: Rejected - maintenance burden
3. **Single entry point**: ✅ Chosen - simplicity and clarity

**Affected Modules**:
- `main.py` - Entry point
- `src/orchestration/` - All flows callable independently

**Consequences**:
- ✅ Benefits:
  - Simple execution model
  - Easy testing of individual flows
  - Clear logging per run
  - OS-level scheduling control
  
- ⚠️ Considerations:
  - User must set up scheduler
  - No built-in scheduling
  - Multiple process management if needed

**Reversal Conditions**:
- If integrated scheduler strongly preferred
- If process management becomes issue

---

### Decision #013 – Pydantic + SQLAlchemy Models

- **Date**: 2025-10-19
- **Author**: Data Architect
- **Status**: ✅ Active
- **Summary**: Use Pydantic for validation, SQLAlchemy for ORM

**Context**:
- Need data validation for API inputs
- Need ORM for database operations
- Want type safety and IDE support

**Decision**:
- Pydantic models for:
  - Configuration (Settings)
  - API requests/responses
  - Data validation
- SQLAlchemy models for:
  - Database tables
  - ORM operations
  - Relationships

**Key Models**:
- `Signal` - Trading signals
- `Order` - Order tracking
- `Fill` - Execution records
- `Position` - Open/closed trades
- `Instrument` - Trading universe
- `Setup` - 3WI patterns
- `LedgerEntry` - Learning ledger

**Affected Modules**:
- `src/storage/models.py` - All models
- `src/storage/schema.sql` - Database schema
- `src/core/config.py` - Settings validation

**Consequences**:
- ✅ Benefits:
  - Type safety
  - Automatic validation
  - IDE autocomplete
  - Clear data contracts
  
- ⚠️ Considerations:
  - Dual model system (Pydantic + SQLAlchemy)
  - Conversion between types when needed

---

## Active Decisions (v1.0 - Original)

### Decision #001 – SQLite as Primary Database
*(Preserved from v1.0)*

- **Date**: 2025-01-15
- **Status**: ✅ Active
- **Summary**: Use SQLite with PostgreSQL migration path

**Rationale**:
- Zero configuration
- Single file database
- Sufficient for 500 instruments
- Easy backups and portability

**Status**: Still active in v2.0

---

### Decision #002 – Risk-Based Position Sizing
*(Preserved from v1.0)*

- **Date**: 2025-01-15
- **Status**: ✅ Active
- **Summary**: Size positions based on 1.5% risk, not fixed capital

**Formula**: `qty = (capital × risk%) / (entry - stop)`

**Status**: Still active in v2.0

---

### Decision #003 – Hourly Tracking Frequency
*(Enhanced in v2.0)*

- **Date**: 2025-01-16
- **Status**: ✅ Active (Enhanced)
- **Summary**: Track positions hourly, not continuously

**Enhancement in v2.0**:
- Separate hourly execution layer
- Pre-breakout support
- Explicit signal processing

**Status**: Enhanced and active in v2.0

---

### Decision #004 – Long-Only Strategy
*(Preserved from v1.0)*

- **Date**: 2025-01-16
- **Status**: ✅ Active
- **Summary**: Trade only long positions, not shorts

**Status**: Still active in v2.0

---

### Decision #005 – Telegram as Primary Alert Channel
*(Preserved from v1.0)*

- **Date**: 2025-01-16
- **Status**: ✅ Active
- **Summary**: Use Telegram for real-time alerts

**Status**: Still active in v2.0 (optional)

---

### Decision #006 – 6% Maximum Open Risk Limit
*(Preserved from v1.0)*

- **Date**: 2025-01-17
- **Status**: ✅ Active
- **Summary**: Limit total open risk to 6% (≈4 positions @ 1.5% each)

**Status**: Still active in v2.0

---

### Decision #007 – APScheduler for Job Scheduling
*(Replaced in v2.0)*

- **Date**: 2025-01-17
- **Status**: ❌ Deprecated (Replaced by Decision #012)
- **Summary**: Originally used APScheduler, now use OS schedulers

**Replacement**: main.py with CLI + OS scheduler (cron/Task Scheduler)

---

### Decision #008 – Partial Profit Booking Strategy
*(Preserved from v1.0)*

- **Date**: 2025-01-17
- **Status**: ✅ Active
- **Summary**: Book 25% @ +6%, 50% @ T1, remainder @ T2

**Status**: Still active in v2.0, implemented in HourlyExecutor

---

## Summary Statistics (v2.0)

**Total Decisions**: 13 (8 preserved, 5 new, 1 deprecated)

**By Category**:
- Architecture: 3 (SQLite, Broker Abstraction, Entry Point)
- Risk Management: 3 (Position sizing, 6% limit, Partials)
- Strategy: 3 (Long-only, Hourly exec, Portfolio-only)
- Integration: 1 (Telegram)
- Data Models: 1 (Pydantic + SQLAlchemy)
- Execution: 2 (Hourly layer, Main entry)

**Version History**:
- v1.0 (Jan 2025): Angel One-specific, daemon-based
- v2.0 (Oct 2025): FYERS-first, broker abstraction, portfolio-only

---

## References

### Internal
- `memory-bank/architecture.md` - Updated architecture
- `memory-bank/patterns/` - Implementation patterns
- `src/data/broker_base.py` - Broker abstraction
- `src/strategy/portfolio_mode.py` - Portfolio management

### External
- FYERS API: https://developers.fyers.in
- "Trade Your Way to Financial Freedom" - Van Tharp
- SQLAlchemy documentation
- Pydantic documentation

---

## Change Log

| Date | Change | By |
|------|--------|-----|
| 2025-01-20 | Initial decision log created | System Architect |
| 2025-10-19 | v2.0 rebuild - FYERS-first architecture | System Architect |
| 2025-10-19 | Added 5 new decisions (#009-#013) | Multiple authors |
| 2025-10-19 | Deprecated APScheduler decision | System Architect |

---

**Note**: This is a living document. All significant decisions MUST be logged here before implementation.
