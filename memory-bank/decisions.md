# 🧭 Decision Evolution Log

## Overview

This document tracks all critical architectural, design, and implementation decisions made during the development of the Institutional AI Trade Engine. Each decision is logged with context, rationale, alternatives considered, and current status.

---

## Decision Template

```
### Decision #XXX – [Title]
- **Date**: YYYY-MM-DD
- **Author**: [Name]
- **Status**: [Active | Deprecated | Under Review]
- **Summary**: Brief description
- **Context**: What problem/situation led to this decision
- **Decision**: What was decided
- **Rationale**: Why this decision was made
- **Alternatives Considered**: Other options and why they were rejected
- **Affected Modules**: Which parts of the system are impacted
- **Consequences**: Benefits and drawbacks
- **Reversal Conditions**: Under what conditions should this be reconsidered
- **References**: Links to related discussions, docs, issues
```

---

## Active Decisions

### Decision #001 – SQLite as Primary Database

- **Date**: 2025-01-15
- **Author**: System Architect
- **Status**: ✅ Active
- **Summary**: Use SQLite as the default database with PostgreSQL migration path

**Context**:
- Need simple deployment for single-instance trading engine
- Want easy setup without external database dependencies
- Must support future scaling to PostgreSQL

**Decision**:
- Use SQLite for development and single-server deployment
- Design schema to be PostgreSQL-compatible
- Use SQLAlchemy ORM for database abstraction

**Rationale**:
1. **Simplicity**: Zero configuration, single file database
2. **Portability**: Easy to backup, copy, and restore
3. **Sufficient Performance**: Handles 500 instruments, 50+ trades easily
4. **Migration Ready**: SQLAlchemy makes PostgreSQL migration seamless

**Alternatives Considered**:
1. **PostgreSQL Only**: Rejected - overkill for single instance, complex setup
2. **MongoDB**: Rejected - unnecessary for structured trading data
3. **CSV Files**: Rejected - no ACID guarantees, race conditions

**Affected Modules**:
- `src/storage/db.py` - Database connection and operations
- `src/storage/schema.sql` - Schema definition
- All modules that query database

**Consequences**:
- ✅ Benefits:
  - Fast setup and deployment
  - No external dependencies
  - Easy backups (single file)
  - Sufficient for 95% of use cases
  
- ⚠️ Drawbacks:
  - Limited concurrency (not an issue for single process)
  - Size limit ~140 TB (not a concern for this use case)
  - No built-in replication

**Reversal Conditions**:
- If running multiple scanner instances concurrently
- If database size exceeds 10 GB
- If need distributed deployment
- If require advanced PostgreSQL features (JSON queries, etc.)

**References**:
- SQLAlchemy documentation
- SQLite vs PostgreSQL comparison

---

### Decision #002 – Risk-Based Position Sizing

- **Date**: 2025-01-15
- **Author**: Risk Manager
- **Status**: ✅ Active
- **Summary**: All positions sized based on 1.5% risk, not capital allocation

**Context**:
- Traditional approach: Allocate fixed capital per trade (e.g., ₹50,000)
- Problem: Different stocks have different stop distances
- Result: Inconsistent risk across trades

**Decision**:
- Size every position based on 1.5% risk of total capital
- Formula: `qty = (capital × risk%) / (entry - stop)`
- Independent of stock price or stop distance

**Rationale**:
1. **Consistent Risk**: Every trade risks exactly 1.5% of capital
2. **Predictable Losses**: Maximum loss per trade is known in advance
3. **Portfolio Protection**: No single trade can devastate portfolio
4. **Psychological Benefits**: Same risk across all trades reduces emotion

**Alternatives Considered**:
1. **Fixed Capital Allocation**: Rejected - inconsistent risk
2. **Equal Position Sizes**: Rejected - same issue as fixed capital
3. **Volatility-Based Sizing**: Rejected - overly complex, hard to backtest

**Affected Modules**:
- `src/core/risk.py` - Position sizing calculations
- `src/exec/scanner.py` - Uses risk sizing for entries
- `src/exec/tracker.py` - Tracks risk per position

**Consequences**:
- ✅ Benefits:
  - Consistent risk across all trades
  - Predictable maximum loss
  - Scalable to any capital size
  - Works for any stock price
  
- ⚠️ Drawbacks:
  - Wide stops → smaller position sizes
  - Tight stops → larger position sizes
  - Capital deployment varies

**Reversal Conditions**:
- If risk-adjusted returns underperform fixed allocation
- If psychological preference for equal position sizes
- If regulatory limits on position sizes

**References**:
- Van Tharp's "Trade Your Way to Financial Freedom"
- Risk management best practices

---

### Decision #003 – Hourly Tracking Frequency

- **Date**: 2025-01-16
- **Author**: System Designer
- **Status**: ✅ Active
- **Summary**: Track open positions every hour (09:00-15:00 IST), not continuously

**Context**:
- Need to manage open positions in real-time
- Options: Every minute, every 5 minutes, hourly, daily
- Balance between responsiveness and API efficiency

**Decision**:
- Track positions every hour during market hours
- 7 tracking cycles per day (09:00, 10:00, ..., 15:00)

**Rationale**:
1. **Sufficient Responsiveness**: Hourly checks catch most profit/loss levels
2. **API Efficiency**: 7 calls/day vs 390 calls (per minute)
3. **Reduced Noise**: Hourly timeframe filters market noise
4. **System Stability**: Lower load, fewer errors

**Alternatives Considered**:
1. **Every Minute**: Rejected - too frequent, expensive, noisy
2. **Every 5 Minutes**: Rejected - still too frequent for strategy
3. **Twice Daily**: Rejected - insufficient responsiveness
4. **Real-Time Tick**: Rejected - overkill for swing trading strategy

**Affected Modules**:
- `src/core/scheduler.py` - Job scheduling
- `src/exec/tracker.py` - Position tracking logic

**Consequences**:
- ✅ Benefits:
  - Low API call volume
  - Stable system performance
  - Adequate for 3WI strategy (swing trades)
  - Reduces false signals from noise
  
- ⚠️ Drawbacks:
  - Delayed reaction to price moves (up to 1 hour)
  - Might miss intra-hour stop losses
  - Trailing stops update hourly, not continuously

**Reversal Conditions**:
- If strategy changes to intraday (scalping/day trading)
- If need tighter risk control (immediate stop loss execution)
- If API costs become negligible

**References**:
- Angel One API rate limits
- Trading psychology research on overtrading

---

### Decision #004 – Long-Only Strategy

- **Date**: 2025-01-16
- **Author**: Strategy Designer
- **Status**: ✅ Active
- **Summary**: Trade only long positions (upward breakouts), not short

**Context**:
- 3WI pattern can break out upward or downward
- Need to decide: long only, short only, or both

**Decision**:
- Trade only upward breakouts (long positions)
- Ignore downward breakouts

**Rationale**:
1. **Market Bias**: Indian markets have upward bias long-term
2. **Simplicity**: Easier to manage one direction
3. **Risk Profile**: Longs have unlimited upside, limited downside
4. **Margin Requirements**: Shorts require higher margin

**Alternatives Considered**:
1. **Both Long and Short**: Rejected - complex, requires different filters
2. **Short Only**: Rejected - against market bias, harder psychologically
3. **Market Regime Based**: Rejected - adds complexity, hard to backtest

**Affected Modules**:
- `src/strategy/three_week_inside.py` - Breakout detection
- `src/strategy/filters.py` - Filters favor uptrend
- `src/exec/scanner.py` - Only creates long positions

**Consequences**:
- ✅ Benefits:
  - Simpler system logic
  - Aligned with market bias
  - No short-selling complexities
  - Lower margin requirements
  
- ⚠️ Drawbacks:
  - Misses downward breakout opportunities
  - No hedge during market downturns
  - Fully exposed to market risk

**Reversal Conditions**:
- If market enters sustained bear phase
- If short-selling profitability proven in backtesting
- If need market-neutral strategy

**References**:
- Historical Nifty 50 returns (long-term uptrend)
- Backtesting results of long vs short

---

### Decision #005 – Telegram as Primary Alert Channel

- **Date**: 2025-01-16
- **Author**: Integration Lead
- **Status**: ✅ Active
- **Summary**: Use Telegram for real-time alerts, Google Sheets for historical tracking

**Context**:
- Need real-time notifications for trades, stops, targets
- Options: Email, SMS, Telegram, WhatsApp, Slack
- Need reliable, instant, free solution

**Decision**:
- Telegram Bot API for all real-time alerts
- Google Sheets for portfolio tracking and history
- Email as fallback (future enhancement)

**Rationale**:
1. **Instant Delivery**: Telegram messages arrive instantly
2. **Free**: No per-message costs
3. **Reliable**: 99.9%+ uptime
4. **Rich Formatting**: Markdown support for structured alerts
5. **Easy Setup**: Simple bot creation process

**Alternatives Considered**:
1. **Email**: Rejected - slower, spam filters, less reliable
2. **SMS**: Rejected - cost per message, character limits
3. **WhatsApp**: Rejected - unofficial API, reliability concerns
4. **Slack**: Rejected - overkill, requires workspace setup

**Affected Modules**:
- `src/alerts/telegram.py` - Telegram integration
- All modules that send notifications

**Consequences**:
- ✅ Benefits:
  - Instant notifications on mobile
  - Zero cost
  - Reliable delivery
  - Rich formatting support
  
- ⚠️ Drawbacks:
  - Requires Telegram account
  - API token management
  - No built-in alert history (handled by Google Sheets)

**Reversal Conditions**:
- If Telegram API becomes unreliable
- If cost-effective SMS service available
- If regulatory requirements demand email-only

**References**:
- Telegram Bot API documentation
- Comparison of notification services

---

### Decision #006 – 6% Maximum Open Risk Limit

- **Date**: 2025-01-17
- **Author**: Risk Manager
- **Status**: ✅ Active
- **Summary**: Limit total open risk to 6% of capital (approximately 4 positions)

**Context**:
- Each position risks 1.5% of capital
- Need to prevent overexposure to market
- Balance between diversification and concentration

**Decision**:
- Maximum total open risk: 6% of capital
- Translates to ~4 concurrent positions at 1.5% each
- Hard limit enforced by scanner before entry

**Rationale**:
1. **Controlled Maximum Loss**: Even if all positions stopped out simultaneously, lose only 6%
2. **Reasonable Diversification**: 4 positions provide some diversification
3. **Manageable Tracking**: 4 positions easy to monitor
4. **Recovery Potential**: 6% loss recoverable with 2-3 good trades

**Alternatives Considered**:
1. **10% Limit (6-7 positions)**: Rejected - too many positions, hard to track
2. **3% Limit (2 positions)**: Rejected - too conservative, limited opportunities
3. **No Limit**: Rejected - dangerous, unlimited downside

**Affected Modules**:
- `src/core/config.py` - MAX_OPEN_RISK_PCT configuration
- `src/core/risk.py` - check_risk_limits() function
- `src/exec/scanner.py` - Enforces limit before entry

**Consequences**:
- ✅ Benefits:
  - Maximum drawdown limited to 6% (if all stopped)
  - Forces trade selectivity (only best setups)
  - Manageable number of positions
  - Psychological comfort
  
- ⚠️ Drawbacks:
  - Might miss opportunities when at limit
  - Capital not fully deployed (53% idle typical)
  - Lower absolute returns vs fully deployed capital

**Reversal Conditions**:
- If strategy proves highly reliable (>80% win rate)
- If need higher returns justify higher risk
- If portfolio size grows significantly

**References**:
- Professional trader risk management practices
- Kelly Criterion calculations

---

### Decision #007 – APScheduler for Job Scheduling

- **Date**: 2025-01-17
- **Author**: System Architect
- **Status**: ✅ Active
- **Summary**: Use APScheduler (cron-based) for all time-based job execution

**Context**:
- Need reliable scheduling for: scanner (2x), tracker (7x), EOD, near-breakout
- Options: cron jobs, APScheduler, Celery Beat, custom scheduler
- Need precise timing aligned with IST market hours

**Decision**:
- Use APScheduler with BlockingScheduler
- Cron expressions for all jobs
- Timezone: Asia/Kolkata (IST)

**Rationale**:
1. **Python-Native**: No external dependencies beyond library
2. **Cron Syntax**: Familiar, powerful, well-tested
3. **Timezone Support**: Explicit IST handling
4. **Graceful Shutdown**: Handles SIGTERM/SIGINT properly
5. **Missed Job Handling**: Configurable behavior

**Alternatives Considered**:
1. **System Cron**: Rejected - requires shell scripts, less portable
2. **Celery Beat**: Rejected - overkill, requires message broker
3. **Custom Scheduler**: Rejected - reinventing wheel, error-prone

**Affected Modules**:
- `src/core/scheduler.py` - All job definitions
- `src/daemon.py` - Scheduler initialization

**Consequences**:
- ✅ Benefits:
  - Reliable job execution
  - Precise timing control
  - Easy to add/modify jobs
  - Python-based configuration
  
- ⚠️ Drawbacks:
  - Must keep process running
  - No distributed scheduling (single instance)
  - Jobs must be fast (blocking scheduler)

**Reversal Conditions**:
- If need distributed job execution
- If jobs take >30 minutes (need async)
- If require job persistence across restarts

**References**:
- APScheduler documentation
- Comparison of Python schedulers

---

### Decision #008 – Partial Profit Booking Strategy

- **Date**: 2025-01-17
- **Author**: Strategy Designer
- **Status**: ✅ Active
- **Summary**: Book profits in stages: 25% at +6%, 50% at T1, 50% at T2

**Context**:
- Need to balance: letting winners run vs locking in profits
- Options: all-or-nothing exits, scaling out, trailing only
- Psychological challenge of watching profits evaporate

**Decision**:
- +6%: Book 25% of position, trail remaining
- T1 (+1.5R): Book 50% of remaining, lock stop at T1
- T2 (+3R): Exit remaining 50%

**Rationale**:
1. **Reduces Stress**: Partial profits provide psychological comfort
2. **Captures Outliers**: Remaining position benefits from big moves
3. **Proven Strategy**: Widely used by professional traders
4. **Balanced Approach**: Mix of profit-taking and trend-following

**Alternatives Considered**:
1. **All or Nothing**: Rejected - misses partial wins, high stress
2. **Trail Only**: Rejected - might give back all profits
3. **Equal Thirds**: Rejected - less optimal risk:reward

**Affected Modules**:
- `src/exec/tracker.py` - Partial exit logic
- `src/storage/ledger.py` - Records partial exits
- `src/alerts/telegram.py` - Partial exit alerts

**Consequences**:
- ✅ Benefits:
  - Reduced anxiety watching positions
  - Guaranteed profit on strong moves
  - Captures tail events (rare big winners)
  - Smooth equity curve
  
- ⚠️ Drawbacks:
  - Lower profit on strong trends (vs holding full)
  - More transactions to track
  - Complex exit logic

**Reversal Conditions**:
- If backtesting shows all-or-nothing outperforms
- If system can handle psychological stress of full holds
- If simplicity preferred over optimization

**References**:
- Van Tharp's exit strategies
- Professional trader profit-taking strategies

---

## Deprecated Decisions

### Decision #D01 – Minute-Level Tracking

- **Date**: 2025-01-15 (Created)
- **Deprecated**: 2025-01-16
- **Author**: Initial Designer
- **Status**: ❌ Deprecated (Replaced by Decision #003)
- **Summary**: Originally planned to track positions every minute

**Why Deprecated**:
- Too frequent for swing trading strategy
- High API costs and system load
- Created alert fatigue
- Replaced with hourly tracking (Decision #003)

**Lessons Learned**:
- Match tracking frequency to trading timeframe
- Consider API costs early in design
- Overly frequent updates provide limited value

---

## Under Review

### Decision #R01 – Index Options Integration

- **Date**: 2025-01-20
- **Author**: Strategy Expansion Team
- **Status**: 🔍 Under Review
- **Summary**: Considering adding BankNifty/Nifty options trading alongside equity

**Context**:
- Index watch module already tracks BankNifty/Nifty LTP
- Options provide leverage and defined risk
- Could complement equity strategy

**Proposal**:
- Add options trading for BankNifty weekly expiries
- Use existing 3WI breakout signals for entry timing
- Risk-defined strategies (credit spreads, iron condors)

**Arguments For**:
- Higher returns with less capital
- Defined risk (options can't gap against you)
- Weekly opportunities (52 expiries/year)
- Complement equity positions

**Arguments Against**:
- Increased complexity
- Time decay management required
- Different risk profile than equity
- Regulatory considerations (segment approval)

**Next Steps**:
1. Complete backtesting of options strategies
2. Assess regulatory requirements
3. Design integration with existing system
4. Decision by: 2025-02-15

**References**:
- Options trading research
- Index options historical data

---

## Decision-Making Process

### How We Make Decisions

1. **Identify Problem/Opportunity**: What needs deciding?
2. **Research Options**: What are the alternatives?
3. **Document Tradeoffs**: Pros/cons of each option
4. **Make Decision**: Choose based on project goals
5. **Document Decision**: Record in this file
6. **Implement**: Build based on decision
7. **Review Periodically**: Revisit under "Reversal Conditions"

### When to Revisit a Decision

- **Quarterly Review**: Every 3 months, review all active decisions
- **Performance Issues**: If decision causes problems
- **New Information**: If new alternatives become available
- **Reversal Conditions Met**: As documented in each decision

---

## Summary Statistics

**Total Decisions**: 8 active, 1 deprecated, 1 under review

**By Category**:
- Architecture: 2 (SQLite, APScheduler)
- Risk Management: 3 (Position sizing, 6% limit, Partial exits)
- Strategy: 2 (Long-only, Tracking frequency)
- Integration: 1 (Telegram)
- Under Review: 1 (Options)

**Decision Velocity**:
- January 2025: 10 decisions made
- Review cycle: Quarterly

---

## References

### Internal
- `memory-bank/architecture.md` - System architecture details
- `memory-bank/patterns/` - Implementation patterns

### External
- "Trade Your Way to Financial Freedom" - Van Tharp
- "Professional Trading System Design" - Various authors
- SQLAlchemy documentation
- APScheduler documentation

---

## Change Log

| Date | Change | By |
|------|--------|-----|
| 2025-01-20 | Initial decision log created | System Architect |
| 2025-01-20 | Added 8 active decisions | Multiple authors |
| 2025-01-20 | Added 1 under-review decision | Strategy Team |

---

**Note**: This is a living document. All significant decisions MUST be logged here before implementation.
