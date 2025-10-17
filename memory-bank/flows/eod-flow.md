# 📾 End-of-Day (EOD) Flow - Daily Summary and Reporting

## Overview

The EOD flow executes at the end of each trading day to summarize all trading activity, calculate performance metrics, update the ledger, and send comprehensive reports via Telegram and Google Sheets.

---

## Execution Schedule

| Time (IST) | Day | Purpose |
|------------|-----|---------|
| 15:25 | Mon-Fri | Daily summary after market close (15:00) |

**Timing Rationale**:
- Market closes at 15:00 IST
- 15:20: Near-breakout scanner completes
- 15:25: All final prices confirmed, ready for daily summary

---

## Detailed Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                   EOD REPORT TRIGGERED                      │
│                      (15:25 IST Daily)                     │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 1: FETCH ALL POSITIONS                                │
│ ─────────────────────────────────────────────────────      │
│ • Open positions: SELECT * WHERE status = 'open'           │
│ • Closed today: SELECT * WHERE DATE(closed_ts) = TODAY     │
│ • Calculate counts and totals                              │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 2: CALCULATE OPEN POSITION METRICS                    │
│ ─────────────────────────────────────────────────────      │
│ FOR EACH open_position:                                    │
│   • Fetch current LTP                                      │
│   • Calculate unrealized P&L                               │
│   • Calculate P&L percentage                               │
│   • Calculate days in trade                                │
│   • Sum total unrealized P&L                               │
│   • Sum total capital deployed                             │
│   • Calculate current risk exposure                        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 3: CALCULATE CLOSED POSITION METRICS                  │
│ ─────────────────────────────────────────────────────      │
│ FOR EACH closed_position (today):                          │
│   • Realized P&L                                           │
│   • R:R ratio achieved                                     │
│   • Hold duration (days)                                   │
│   • Entry/Exit prices                                      │
│   • Classify: Win/Loss                                     │
│   • Sum total realized P&L                                 │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 4: CALCULATE PERFORMANCE METRICS                      │
│ ─────────────────────────────────────────────────────      │
│ • Total P&L: Realized + Unrealized                         │
│ • Win Rate: Wins / Total Trades × 100                      │
│ • Average R:R: Sum(R:R) / Total Trades                     │
│ • Average Hold Duration: Sum(Days) / Total Trades          │
│ • Best Trade: Max P&L today                                │
│ • Worst Trade: Min P&L today                               │
│ • Capital Efficiency: P&L / Capital Deployed               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 5: FETCH HISTORICAL PERFORMANCE                       │
│ ─────────────────────────────────────────────────────      │
│ FROM ledger:                                               │
│   • MTD (Month-to-Date) P&L                                │
│   • Week P&L                                               │
│   • Overall win rate                                       │
│   • Overall average R:R                                    │
│   • Total trades executed                                  │
│   • Consecutive wins/losses streak                         │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 6: GENERATE EOD REPORT                                │
│ ─────────────────────────────────────────────────────      │
│ Create comprehensive report with:                          │
│                                                             │
│ SECTION 1: TODAY'S SUMMARY                                 │
│   • Date and trading day                                   │
│   • New positions entered                                  │
│   • Positions closed                                       │
│   • Today's realized P&L                                   │
│                                                             │
│ SECTION 2: OPEN POSITIONS                                  │
│   • Count and symbols                                      │
│   • Total unrealized P&L                                   │
│   • Average P&L percentage                                 │
│   • Capital deployed                                       │
│   • Current risk exposure                                  │
│   • Individual position details                            │
│                                                             │
│ SECTION 3: CLOSED POSITIONS (TODAY)                        │
│   • Count and symbols                                      │
│   • Total realized P&L                                     │
│   • Individual trade details                               │
│   • Win/Loss classification                                │
│                                                             │
│ SECTION 4: PERFORMANCE METRICS                             │
│   • Today's total P&L                                      │
│   • Today's win rate                                       │
│   • Average R:R today                                      │
│   • Best/Worst trade                                       │
│                                                             │
│ SECTION 5: CUMULATIVE PERFORMANCE                          │
│   • Week P&L                                               │
│   • Month P&L                                              │
│   • Overall win rate                                       │
│   • Overall average R:R                                    │
│   • Total trades                                           │
│                                                             │
│ SECTION 6: RISK METRICS                                    │
│   • Current open risk %                                    │
│   • Available risk capacity                                │
│   • Max drawdown (if any)                                  │
│   • Risk utilization                                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 7: SEND TELEGRAM REPORT                               │
│ ─────────────────────────────────────────────────────      │
│ • Format report for Telegram (markdown)                    │
│ • Send comprehensive daily digest                          │
│ • Include emojis and formatting for readability            │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 8: UPDATE GOOGLE SHEETS                               │
│ ─────────────────────────────────────────────────────      │
│ UPDATE "Performance Dashboard" Tab:                        │
│   • Add today's row with metrics                           │
│   • Update cumulative charts                               │
│   • Update win rate tracker                                │
│                                                             │
│ UPDATE "Trade History" Tab:                                │
│   • Add all closed trades from today                       │
│   • Calculate running statistics                           │
│                                                             │
│ UPDATE "Active Positions" Tab:                             │
│   • Refresh all open positions                             │
│   • Update unrealized P&L                                  │
│   • Sort by performance                                    │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 9: UPDATE LEDGER                                      │
│ ─────────────────────────────────────────────────────      │
│ • Verify all closed trades recorded                        │
│ • Update performance tags                                  │
│ • Calculate running metrics                                │
│ • Store daily summary record                               │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 10: GENERATE INSIGHTS (OPTIONAL)                      │
│ ─────────────────────────────────────────────────────      │
│ • Identify patterns in winning trades                      │
│ • Identify patterns in losing trades                       │
│ • Suggest adjustments if needed                            │
│ • Note any anomalies                                       │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                    EOD REPORT COMPLETE                      │
│                  Next run: Tomorrow 15:25                  │
└────────────────────────────────────────────────────────────┘
```

---

## Report Format Example

### Telegram Report

```
📊 END-OF-DAY REPORT
═══════════════════════════════════════
📅 Date: Friday, 22 Jan 2025
🕒 Market Close: 15:00 IST

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 TODAY'S SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
New Positions: 2
  • RELIANCE (3WI Breakout)
  • TCS (3WI Breakout)

Closed Positions: 1
  • INFY (T2 Target Hit) ✅

Today's Realized P&L: +₹8,450 (+2.1% capital)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💼 OPEN POSITIONS (3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Unrealized P&L: +₹3,240 (+0.81%)
Capital Deployed: ₹1,88,500
Current Risk: 4.5% of portfolio

1. RELIANCE
   Entry: ₹2,510 | LTP: ₹2,545
   P&L: +₹2,625 (+1.39%) | Days: 1
   Stop: ₹2,430 | Status: OPEN 🟢

2. TCS
   Entry: ₹3,850 | LTP: ₹3,858
   P&L: +₹480 (+0.21%) | Days: 1
   Stop: ₹3,780 | Status: OPEN 🟢

3. HDFCBANK
   Entry: ₹1,650 | LTP: ₹1,651
   P&L: +₹135 (+0.08%) | Days: 3
   Stop: ₹1,650 (BE) | Status: OPEN 🟢

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CLOSED POSITIONS TODAY (1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Realized P&L: +₹8,450

1. INFY - T2 TARGET HIT 🎯
   Entry: ₹1,520 | Exit: ₹1,640
   P&L: +₹8,450 (+7.89%) | R:R: +2.8R
   Duration: 5 days | Qty: 75 shares
   Tag: Partial exits at +6%, T1, T2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PERFORMANCE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODAY:
  Total P&L: +₹11,690 (Realized + Unrealized)
  Win Rate: 100% (1/1)
  Avg R:R: +2.8R

WEEK:
  P&L: +₹24,350 (+6.09%)
  Trades: 4 | Wins: 3 | Losses: 1
  Win Rate: 75%

MONTH:
  P&L: +₹68,920 (+17.23%)
  Trades: 15 | Wins: 11 | Losses: 4
  Win Rate: 73.3%
  Avg R:R: +2.1R

OVERALL:
  Total Trades: 47
  Win Rate: 68.1%
  Avg R:R: +1.8R
  Best Trade: +₹18,500 (BHARTIARTL)
  Largest Loss: -₹5,800 (ITC)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 RISK METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Open Risk: 4.5% / 6.0% max
Available Capacity: 1.5% (1 position)
Risk Utilization: 75%

Capital Breakdown:
  Portfolio Capital: ₹4,00,000
  Deployed: ₹1,88,500 (47%)
  Available: ₹2,11,500 (53%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 INSIGHTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Strong momentum today with all open positions in profit
✅ Disciplined exit on INFY at T2 target
✅ Risk management on track (4.5% / 6.0%)
✅ Monthly performance exceeding expectations (+17.23%)

📌 Capacity for 1 more position (1.5% risk available)

═══════════════════════════════════════
✨ Trading Engine v1.0.0
🤖 Autonomous • Idempotent • Institutional-Grade
═══════════════════════════════════════
```

---

## Google Sheets Update Structure

### "Performance Dashboard" Tab

| Date | Open Positions | Closed Trades | Realized P&L | Unrealized P&L | Total P&L | Win Rate | Avg R:R | Risk % |
|------|----------------|---------------|--------------|----------------|-----------|----------|---------|--------|
| 22-Jan-25 | 3 | 1 | 8,450 | 3,240 | 11,690 | 100% | 2.8R | 4.5% |
| 21-Jan-25 | 2 | 0 | 0 | 1,850 | 1,850 | - | - | 3.0% |
| 20-Jan-25 | 2 | 2 | 12,500 | 950 | 13,450 | 100% | 2.3R | 3.0% |

### "Trade History" Tab

| Symbol | Entry Date | Exit Date | Entry Price | Exit Price | Qty | P&L | R:R | Duration | Tag |
|--------|------------|-----------|-------------|------------|-----|-----|-----|----------|-----|
| INFY | 17-Jan-25 | 22-Jan-25 | 1,520 | 1,640 | 75 | 8,450 | 2.8R | 5 days | T2_target_success |
| WIPRO | 20-Jan-25 | 20-Jan-25 | 420 | 418 | 150 | -300 | -0.2R | 0 days | stopped_out |

### "Active Positions" Tab

| Symbol | Entry Date | Entry Price | Stop | T1 | T2 | Qty | Current Price | Unrealized P&L | P&L % | Days | Status |
|--------|------------|-------------|------|----|----|-----|---------------|----------------|-------|------|--------|
| RELIANCE | 22-Jan-25 | 2,510 | 2,430 | 2,630 | 2,750 | 75 | 2,545 | 2,625 | 1.39% | 1 | OPEN |
| TCS | 22-Jan-25 | 3,850 | 3,780 | 4,005 | 4,160 | 60 | 3,858 | 480 | 0.21% | 1 | OPEN |

---

## Metric Calculations

### Win Rate
```python
def calculate_win_rate(closed_trades):
    """Calculate percentage of winning trades."""
    if not closed_trades:
        return 0.0
    
    wins = sum(1 for trade in closed_trades if trade['pnl'] > 0)
    total = len(closed_trades)
    
    return (wins / total) * 100

# Example
closed_trades = [
    {'pnl': 8450},
    {'pnl': -300},
    {'pnl': 4200},
    {'pnl': 1850}
]
win_rate = calculate_win_rate(closed_trades)
# Result: 75% (3 wins out of 4 trades)
```

### Average R:R Ratio
```python
def calculate_avg_rr(closed_trades):
    """Calculate average Risk:Reward ratio."""
    if not closed_trades:
        return 0.0
    
    total_rr = sum(trade['rr'] for trade in closed_trades)
    count = len(closed_trades)
    
    return total_rr / count

# Example
closed_trades = [
    {'rr': 2.8},
    {'rr': -1.0},
    {'rr': 1.5},
    {'rr': 3.0}
]
avg_rr = calculate_avg_rr(closed_trades)
# Result: 1.575R average
```

### Average Hold Duration
```python
def calculate_avg_duration(closed_trades):
    """Calculate average days in trade."""
    if not closed_trades:
        return 0
    
    total_days = sum(trade['duration_days'] for trade in closed_trades)
    count = len(closed_trades)
    
    return total_days / count

# Example
closed_trades = [
    {'duration_days': 5},
    {'duration_days': 1},
    {'duration_days': 7},
    {'duration_days': 3}
]
avg_duration = calculate_avg_duration(closed_trades)
# Result: 4 days average
```

### Capital Efficiency
```python
def calculate_capital_efficiency(total_pnl, capital_deployed):
    """Calculate return on deployed capital."""
    if capital_deployed == 0:
        return 0.0
    
    return (total_pnl / capital_deployed) * 100

# Example
total_pnl = 11690
capital_deployed = 188500
efficiency = calculate_capital_efficiency(total_pnl, capital_deployed)
# Result: 6.2% return on deployed capital
```

### Maximum Drawdown
```python
def calculate_max_drawdown(ledger_data):
    """Calculate maximum drawdown from peak."""
    cumulative_pnl = []
    running_total = 0
    
    for trade in ledger_data:
        running_total += trade['pnl']
        cumulative_pnl.append(running_total)
    
    peak = cumulative_pnl[0]
    max_dd = 0
    
    for value in cumulative_pnl:
        if value > peak:
            peak = value
        
        drawdown = ((peak - value) / peak) * 100
        if drawdown > max_dd:
            max_dd = drawdown
    
    return max_dd

# Example
ledger_data = [
    {'pnl': 5000},   # Cumulative: 5000 (peak)
    {'pnl': -2000},  # Cumulative: 3000 (40% DD from peak)
    {'pnl': 1000},   # Cumulative: 4000
    {'pnl': 3000}    # Cumulative: 7000 (new peak)
]
max_dd = calculate_max_drawdown(ledger_data)
# Result: 40% maximum drawdown
```

---

## Historical Performance Queries

### Month-to-Date P&L
```sql
SELECT SUM(pnl) as mtd_pnl
FROM ledger
WHERE strftime('%Y-%m', closed_ts) = strftime('%Y-%m', 'now');
```

### Week P&L
```sql
SELECT SUM(pnl) as week_pnl
FROM ledger
WHERE DATE(closed_ts) >= DATE('now', '-7 days');
```

### Overall Statistics
```sql
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losses,
    AVG(rr) as avg_rr,
    AVG(julianday(closed_ts) - julianday(opened_ts)) as avg_duration,
    MAX(pnl) as best_trade,
    MIN(pnl) as worst_trade
FROM ledger;
```

---

## Error Handling

### LTP Fetch Failures for Open Positions
```python
try:
    ltp = angel_client.getLTP(symbol)
except APIError:
    # Use entry price if LTP unavailable
    ltp = position.entry_price
    logger.warning(f"Using entry price for {symbol} in EOD report")
```

### Google Sheets Update Failure
```python
try:
    sheets.update_performance_dashboard(metrics)
except SheetsError as e:
    logger.error(f"Sheets update failed: {e}")
    # Continue with Telegram report
    # Retry sheets update in background
```

### Telegram Send Failure
```python
try:
    telegram.send_message(eod_report)
except TelegramError as e:
    logger.error(f"Telegram report failed: {e}")
    # Store report in database for manual retrieval
    db.insert("INSERT INTO report_archive (...) VALUES (...)")
```

---

## Insights Generation

### Pattern Recognition
```python
def generate_insights(closed_trades, open_positions):
    """Generate actionable insights from trading data."""
    insights = []
    
    # Check winning streak
    recent_wins = sum(1 for t in closed_trades[-5:] if t['pnl'] > 0)
    if recent_wins >= 4:
        insights.append("✅ Strong momentum with 4+ wins in last 5 trades")
    
    # Check losing streak
    recent_losses = sum(1 for t in closed_trades[-3:] if t['pnl'] <= 0)
    if recent_losses >= 3:
        insights.append("⚠️ 3 consecutive losses - review strategy")
    
    # Check average win size vs loss size
    wins = [t['pnl'] for t in closed_trades if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in closed_trades if t['pnl'] <= 0]
    
    if wins and losses:
        avg_win = sum(wins) / len(wins)
        avg_loss = sum(losses) / len(losses)
        
        if avg_win > avg_loss * 2:
            insights.append("✅ Excellent win/loss ratio - cutting losses, letting winners run")
    
    # Check risk capacity
    open_risk_pct = calculate_open_risk_pct(open_positions)
    if open_risk_pct < 3.0:
        insights.append(f"📌 Low risk utilization ({open_risk_pct:.1f}%) - capacity for more positions")
    elif open_risk_pct > 5.5:
        insights.append(f"⚠️ High risk utilization ({open_risk_pct:.1f}%) - approaching limit")
    
    # Check hold durations
    durations = [t['duration_days'] for t in closed_trades]
    if durations:
        avg_duration = sum(durations) / len(durations)
        if avg_duration < 2:
            insights.append("💡 Short hold times - consider letting winners run longer")
    
    return insights
```

---

## Testing Strategy

### Unit Tests
```python
def test_win_rate_calculation():
    trades = [
        {'pnl': 1000},
        {'pnl': -500},
        {'pnl': 2000},
        {'pnl': -300}
    ]
    
    win_rate = calculate_win_rate(trades)
    assert win_rate == 50.0  # 2 wins out of 4
```

### Integration Tests
```python
def test_full_eod_flow():
    # Given: Test database with positions
    setup_test_db()
    
    # When: Run EOD report
    eod_report.run()
    
    # Then: Verify report generated
    # Check Telegram sent
    # Check Google Sheets updated
    # Check ledger updated
```

---

## Monitoring and Alerts

### Success Metrics
- Report generation time: < 30 seconds
- All sections populated
- Telegram sent successfully
- Google Sheets updated
- Ledger reconciled

### Alert Conditions
- Report generation > 60 seconds → Performance alert
- No trades for 5+ days → Inactivity alert
- Win rate < 50% (rolling 10 trades) → Strategy review alert
- Drawdown > 15% → Risk alert

---

## Compliance

### Daily Audit
- All closed trades verified
- P&L calculations audited
- Google Sheets reconciled with database
- Performance metrics validated

### Archiving
- Daily reports archived in database
- Trade history maintained indefinitely
- Performance metrics tracked monthly

---

## Future Enhancements

1. **Advanced Analytics**: Sharpe ratio, Sortino ratio, profit factor
2. **Sector Analysis**: Performance by sector/industry
3. **Correlation Analysis**: Portfolio correlation metrics
4. **Benchmark Comparison**: Performance vs Nifty 50
5. **PDF Reports**: Generate PDF for weekly/monthly summaries
6. **Email Integration**: Send reports via email in addition to Telegram
