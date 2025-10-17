# 🔍 Scanning Flow - New Setup Detection

## Overview

The scanning flow is responsible for detecting new Three-Week Inside (3WI) patterns and confirming breakouts. It runs twice daily at specific market times to identify trading opportunities.

---

## Execution Schedule

| Time (IST) | Purpose |
|------------|---------|
| 09:25 | Pre-open scan - Detect overnight breakouts |
| 15:10 | Close scan - Detect intraday breakouts |

**Rationale**:
- 09:25: After pre-open session, before market opens at 09:30
- 15:10: After market close at 15:00, with final prices confirmed

---

## Detailed Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    SCANNER TRIGGERED                        │
│                    (09:25 or 15:10 IST)                    │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 1: FETCH ENABLED INSTRUMENTS                          │
│ ─────────────────────────────────────────────────────      │
│ • Query database: SELECT * FROM instruments WHERE enabled=1│
│ • Expected count: 50 (Nifty50) or 100/500 based on config │
│ • Error handling: If no instruments, alert and exit        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 2: ITERATE THROUGH INSTRUMENTS                        │
│ ─────────────────────────────────────────────────────      │
│ FOR EACH instrument IN instruments:                        │
│                                                             │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2a. FETCH WEEKLY DATA                           │     │
│   │ ────────────────────────                        │     │
│   │ • API: Angel One SmartAPI                       │     │
│   │ • Timeframe: Weekly (1W)                        │     │
│   │ • Period: Last 52 weeks minimum                 │     │
│   │ • Columns: timestamp, open, high, low, close, vol│    │
│   │ • Error handling: Skip instrument on API failure│     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2b. COMPUTE TECHNICAL INDICATORS                │     │
│   │ ────────────────────────────────                │     │
│   │ • RSI (14-period)                               │     │
│   │ • WMA20, WMA50, WMA100                          │     │
│   │ • ATR (14-period) and ATR_PCT                   │     │
│   │ • Volume ratio (VOL_X20D)                       │     │
│   │ • Result: Enriched DataFrame                    │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2c. DETECT 3WI PATTERNS                         │     │
│   │ ────────────────────────                        │     │
│   │ Algorithm:                                      │     │
│   │   For i in range(2, len(weekly_df)):           │     │
│   │     Mother = week[i-2]                          │     │
│   │     Inside1 = week[i-1]                         │     │
│   │     Inside2 = week[i]                           │     │
│   │                                                  │     │
│   │     If (Inside1.high ≤ Mother.high AND          │     │
│   │         Inside1.low ≥ Mother.low) AND           │     │
│   │        (Inside2.high ≤ Mother.high AND          │     │
│   │         Inside2.low ≥ Mother.low):              │     │
│   │       → Pattern detected                        │     │
│   │                                                  │     │
│   │ • Result: List of detected patterns             │     │
│   │ • If no patterns: Continue to next instrument   │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2d. APPLY TECHNICAL FILTERS                     │     │
│   │ ────────────────────────────                    │     │
│   │ For each detected pattern:                      │     │
│   │   ✓ RSI > 55 (momentum)                         │     │
│   │   ✓ WMA20 > WMA50 > WMA100 (uptrend)            │     │
│   │   ✓ VOL_X20D ≥ 1.5 (volume surge)               │     │
│   │   ✓ ATR_PCT < 0.06 (not too volatile)           │     │
│   │                                                  │     │
│   │ • If ALL filters pass: Mark as valid setup      │     │
│   │ • If ANY filter fails: Discard pattern          │     │
│   │ • Count matched filters for quality score       │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2e. STORE VALID SETUPS                          │     │
│   │ ────────────────────────────                    │     │
│   │ For each valid setup:                           │     │
│   │   INSERT INTO setups (                          │     │
│   │     symbol, week_start,                         │     │
│   │     mother_high, mother_low,                    │     │
│   │     inside_weeks, matched_filters,              │     │
│   │     comment                                     │     │
│   │   )                                             │     │
│   │                                                  │     │
│   │ • Idempotency: Unique constraint on             │     │
│   │   (symbol, week_start)                          │     │
│   │ • Duplicate detection: ON CONFLICT DO NOTHING   │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2f. CHECK FOR BREAKOUT                          │     │
│   │ ────────────────────────                        │     │
│   │ For each valid setup:                           │     │
│   │   current_close = weekly_df.iloc[-1]['close']   │     │
│   │   mother_high = pattern['mother_high']          │     │
│   │   mother_low = pattern['mother_low']            │     │
│   │                                                  │     │
│   │   If current_close > mother_high:               │     │
│   │     → Upward breakout confirmed                 │     │
│   │   Elif current_close < mother_low:              │     │
│   │     → Downward breakout confirmed               │     │
│   │   Else:                                         │     │
│   │     → No breakout yet (skip)                    │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2g. POSITION SIZING (If breakout confirmed)     │     │
│   │ ────────────────────────────────────────────    │     │
│   │ Calculate position parameters:                  │     │
│   │                                                  │     │
│   │ entry_price = current_close                     │     │
│   │ stop_loss = mother_low (for long)               │     │
│   │ capital = Config.PORTFOLIO_CAPITAL               │     │
│   │ risk_pct = Config.RISK_PCT (1.5%)               │     │
│   │                                                  │     │
│   │ qty, risk_amount = size_position(               │     │
│   │   entry=entry_price,                            │     │
│   │   stop=stop_loss,                               │     │
│   │   capital=capital,                              │     │
│   │   risk_pct=risk_pct,                            │     │
│   │   plan=1.0                                      │     │
│   │ )                                               │     │
│   │                                                  │     │
│   │ t1, t2 = calculate_targets(                     │     │
│   │   entry=entry_price,                            │     │
│   │   stop=stop_loss,                               │     │
│   │   atr=current_atr                               │     │
│   │ )                                               │     │
│   │                                                  │     │
│   │ • T1 = entry + 1.5R (50% exit)                  │     │
│   │ • T2 = entry + 3.0R (remaining)                 │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2h. CHECK RISK LIMITS                           │     │
│   │ ────────────────────────                        │     │
│   │ open_positions = fetch_open_positions()         │     │
│   │ total_current_risk = sum(pos.risk_amount)       │     │
│   │ max_allowed_risk = capital × 6%                 │     │
│   │                                                  │     │
│   │ If (total_current_risk + risk_amount) ≤         │     │
│   │    max_allowed_risk:                            │     │
│   │   → Proceed to create position                  │     │
│   │ Else:                                           │     │
│   │   → Skip entry (risk limit exceeded)            │     │
│   │   → Log warning                                 │     │
│   │   → Send Telegram alert                         │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2i. CREATE POSITION (If risk OK)                │     │
│   │ ────────────────────────────                    │     │
│   │ INSERT INTO positions (                         │     │
│   │   symbol, status='open',                        │     │
│   │   entry_price, stop, t1, t2,                    │     │
│   │   qty, capital, plan_size=1.0,                  │     │
│   │   opened_ts=now()                               │     │
│   │ )                                               │     │
│   │                                                  │     │
│   │ • Unique ID: {symbol}_{opened_ts}               │     │
│   │ • Idempotency: Check for existing open position │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2j. SEND NOTIFICATIONS                          │     │
│   │ ────────────────────────                        │     │
│   │ Telegram Alert:                                 │     │
│   │   🚀 NEW POSITION                               │     │
│   │   Symbol: {symbol}                              │     │
│   │   Entry: ₹{entry_price}                         │     │
│   │   Stop: ₹{stop}                                 │     │
│   │   T1: ₹{t1} (1.5R)                              │     │
│   │   T2: ₹{t2} (3.0R)                              │     │
│   │   Qty: {qty}                                    │     │
│   │   Risk: ₹{risk_amount} ({risk_pct}%)            │     │
│   │   Pattern: 3WI Breakout                         │     │
│   │   Quality: {quality_score}/100                  │     │
│   │                                                  │     │
│   │ Google Sheets Update:                           │     │
│   │   • Add row to "Active Positions" tab           │     │
│   │   • Update "Performance Dashboard"              │     │
│   └─────────────────────────────────────────────────┘     │
│                                                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 3: SUMMARY AND LOGGING                                │
│ ─────────────────────────────────────────────────────      │
│ • Log scan completion                                      │
│ • Summary:                                                 │
│   - Instruments scanned: {count}                           │
│   - Patterns detected: {pattern_count}                     │
│   - Filters passed: {valid_count}                          │
│   - Breakouts confirmed: {breakout_count}                  │
│   - New positions created: {position_count}                │
│   - Positions skipped (risk): {skipped_count}              │
│ • Send summary to Telegram                                 │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                   SCAN COMPLETE                             │
│              Next scan: 09:25 or 15:10 IST                 │
└────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Breakdown

### Step 1: Fetch Enabled Instruments

**Purpose**: Load the trading universe

**SQL Query**:
```sql
SELECT id, symbol, exchange, enabled
FROM instruments
WHERE enabled = 1
ORDER BY symbol;
```

**Expected Output**:
```python
[
    {'id': 1, 'symbol': 'RELIANCE', 'exchange': 'NSE', 'enabled': 1},
    {'id': 2, 'symbol': 'TCS', 'exchange': 'NSE', 'enabled': 1},
    ...
]
```

**Error Handling**:
- If no instruments found: Alert and exit gracefully
- Database error: Retry once, then alert

---

### Step 2a: Fetch Weekly Data

**API Call**: Angel One SmartAPI

**Parameters**:
```python
{
    'exchange': 'NSE',
    'symboltoken': '{symbol_token}',
    'interval': 'ONE_WEEK',
    'fromdate': '{52_weeks_ago}',
    'todate': '{today}'
}
```

**Response Transformation**:
```python
# Raw API response
data = [
    ['2024-01-08T00:00:00', 2450, 2520, 2430, 2510, 15000000],
    ...
]

# Transform to DataFrame
df = pd.DataFrame(data, columns=[
    'timestamp', 'open', 'high', 'low', 'close', 'volume'
])
df['timestamp'] = pd.to_datetime(df['timestamp'])
```

**Error Handling**:
- API timeout (30s): Retry 3 times with exponential backoff
- Invalid symbol: Skip instrument, log warning
- Insufficient data (< 52 weeks): Skip instrument

---

### Step 2b: Compute Technical Indicators

**Function**: `indicators.compute(df)`

**Calculations**:
```python
# RSI (14-period)
df['RSI'] = ta.momentum.RSIIndicator(
    close=df['close'],
    window=14
).rsi()

# Weighted Moving Averages
df['WMA20'] = df['close'].rolling(window=20).mean()
df['WMA50'] = df['close'].rolling(window=50).mean()
df['WMA100'] = df['close'].rolling(window=100).mean()

# Average True Range
df['ATR'] = ta.volatility.AverageTrueRange(
    high=df['high'],
    low=df['low'],
    close=df['close'],
    window=14
).average_true_range()

df['ATR_PCT'] = df['ATR'] / df['close']

# Volume Ratio
df['VOL_X20D'] = df['volume'] / df['volume'].rolling(20).mean()
```

**Output**: Enriched DataFrame with all technical indicators

---

### Step 2c: Detect 3WI Patterns

**Function**: `three_week_inside.detect_3wi(weekly_df)`

**Algorithm**:
```python
patterns = []

for i in range(2, len(weekly_df)):
    mother = weekly_df.iloc[i-2]
    inside1 = weekly_df.iloc[i-1]
    inside2 = weekly_df.iloc[i]
    
    # Check if both weeks are inside mother
    if (inside1['high'] <= mother['high'] and
        inside1['low'] >= mother['low'] and
        inside2['high'] <= mother['high'] and
        inside2['low'] >= mother['low']):
        
        pattern = {
            'mother_high': float(mother['high']),
            'mother_low': float(mother['low']),
            'index': i,
            'week_start': inside2['timestamp'].strftime('%Y-%m-%d'),
            'inside_weeks': 2,
            'mother_range_pct': (
                (mother['high'] - mother['low']) / mother['close'] * 100
            )
        }
        patterns.append(pattern)

return patterns
```

**Example Pattern**:
```python
{
    'mother_high': 2520.0,
    'mother_low': 2430.0,
    'index': 25,
    'week_start': '2024-01-22',
    'inside_weeks': 2,
    'mother_range_pct': 3.58
}
```

---

### Step 2d: Apply Technical Filters

**Function**: `filters.filters_ok(row)`

**Filter Criteria** (ALL must pass):

1. **RSI > 55**
   - Purpose: Momentum confirmation
   - Rationale: Avoid weak or bearish momentum

2. **WMA20 > WMA50 > WMA100**
   - Purpose: Trend alignment
   - Rationale: Trade only in direction of major trend

3. **VOL_X20D ≥ 1.5**
   - Purpose: Volume surge
   - Rationale: Institutional participation

4. **ATR_PCT < 0.06**
   - Purpose: Volatility control
   - Rationale: Avoid overly volatile stocks (max 6%)

**Implementation**:
```python
def filters_ok(row):
    return (
        row['RSI'] > 55 and
        row['WMA20'] > row['WMA50'] > row['WMA100'] and
        row['VOL_X20D'] >= 1.5 and
        row['ATR_PCT'] < 0.06
    )

# Apply to latest row
latest = weekly_df.iloc[-1]
if filters_ok(latest):
    matched_filters = 4  # All passed
else:
    matched_filters = sum([
        latest['RSI'] > 55,
        latest['WMA20'] > latest['WMA50'] > latest['WMA100'],
        latest['VOL_X20D'] >= 1.5,
        latest['ATR_PCT'] < 0.06
    ])
```

---

### Step 2e: Store Valid Setups

**SQL Operation**:
```sql
INSERT INTO setups (
    symbol, week_start, mother_high, mother_low,
    inside_weeks, matched_filters, comment
)
VALUES (
    'RELIANCE', '2024-01-22', 2520.0, 2430.0,
    2, 4, '3WI pattern detected with all filters passed'
)
ON CONFLICT (symbol, week_start) DO NOTHING;
```

**Idempotency**:
- Unique constraint on `(symbol, week_start)`
- Duplicate inserts are silently ignored
- Same scan can run multiple times safely

---

### Step 2f: Check for Breakout

**Function**: `three_week_inside.breakout(weekly_df, pattern_index)`

**Logic**:
```python
current_close = weekly_df.iloc[-1]['close']
mother_high = pattern['mother_high']
mother_low = pattern['mother_low']

if current_close > mother_high:
    return 'up'  # Upward breakout
elif current_close < mother_low:
    return 'down'  # Downward breakout (we trade long only)
else:
    return None  # No breakout yet
```

**Trading Rules**:
- Only trade **upward** breakouts (long positions)
- Downward breakouts are logged but not traded
- Partial breakouts (high touched but close below) = No entry

---

### Step 2g: Position Sizing

**Function**: `risk.size_position(...)`

**Example Calculation**:
```python
# Given
entry_price = 2510.0
stop_loss = 2430.0  # Mother low
capital = 400000.0
risk_pct = 1.5
plan = 1.0

# Calculate
risk_rupees = capital * (risk_pct / 100) * plan
            = 400000 * 0.015 * 1.0
            = 6000.0

per_share_risk = entry_price - stop_loss
               = 2510 - 2430
               = 80.0

qty = int(risk_rupees / per_share_risk)
    = int(6000 / 80)
    = 75 shares

# Targets
risk = 80.0
t1 = entry_price + (risk * 1.5) = 2510 + 120 = 2630.0
t2 = entry_price + (risk * 3.0) = 2510 + 240 = 2750.0
```

**Result**:
```python
{
    'qty': 75,
    'risk_amount': 6000.0,
    'entry': 2510.0,
    'stop': 2430.0,
    't1': 2630.0,  # 1.5R target
    't2': 2750.0   # 3.0R target
}
```

---

### Step 2h: Check Risk Limits

**Function**: `risk.check_risk_limits(open_positions, new_risk)`

**Example**:
```python
# Current open positions
open_positions = [
    {'symbol': 'TCS', 'risk_amount': 5500},
    {'symbol': 'INFY', 'risk_amount': 4800},
]

total_current_risk = 5500 + 4800 = 10300
new_risk = 6000
total_risk_after = 10300 + 6000 = 16300

max_allowed_risk = 400000 * 0.06 = 24000

# Check
if 16300 <= 24000:
    return True  # OK to enter
else:
    return False  # Risk limit exceeded
```

**Risk Management**:
- Maximum total open risk: 6% of capital
- This translates to approximately 4 positions at 1.5% each
- Conservative approach: Better to miss trades than overleverage

---

### Step 2i: Create Position

**SQL Operation**:
```sql
INSERT INTO positions (
    symbol, status, entry_price, stop, t1, t2,
    qty, capital, plan_size, opened_ts
)
VALUES (
    'RELIANCE', 'open', 2510.0, 2430.0, 2630.0, 2750.0,
    75, 400000.0, 1.0, '2024-01-22T09:30:00'
);
```

**Idempotency Check**:
```python
# Before inserting, check for existing open position
existing = db.query(
    "SELECT id FROM positions "
    "WHERE symbol = ? AND status = 'open'",
    symbol
)

if existing:
    logger.warning(f"Position already open for {symbol}")
    return  # Skip duplicate entry
```

---

### Step 2j: Send Notifications

**Telegram Alert**:
```
🚀 NEW POSITION ENTERED
─────────────────────
Symbol: RELIANCE
Entry: ₹2,510.00
Stop: ₹2,430.00
Risk per share: ₹80.00

Targets:
T1: ₹2,630.00 (1.5R) - Book 50%
T2: ₹2,750.00 (3.0R) - Full exit

Position Size:
Qty: 75 shares
Capital: ₹1,88,250
Risk: ₹6,000 (1.5% of portfolio)

Pattern: 3WI Breakout
Quality Score: 87/100
─────────────────────
Matched Filters:
✓ RSI: 62.4 (> 55)
✓ Trend: WMA20 > WMA50 > WMA100
✓ Volume: 1.8x (≥ 1.5x)
✓ ATR: 3.2% (< 6%)
─────────────────────
⏰ 22 Jan 2024, 09:30 IST
```

**Google Sheets Update**:
```
Tab: "Active Positions"
Row: [RELIANCE, 2510, 2430, 2630, 2750, 75, 0, 0%, 22-Jan-2024, OPEN]
```

---

## Error Handling

### API Failures

**Scenario**: Angel One API timeout or error

**Handling**:
```python
for attempt in range(3):
    try:
        data = angel_client.get_historical(symbol, 'WEEKLY')
        break
    except APITimeout:
        if attempt < 2:
            time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
        else:
            logger.error(f"API failed for {symbol} after 3 attempts")
            send_telegram_alert(f"⚠️ API failure for {symbol}")
            continue  # Skip this instrument
```

### Database Errors

**Scenario**: Database connection lost

**Handling**:
```python
try:
    db.insert(setup)
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    db.rollback()
    db.reconnect()
    # Retry once
    try:
        db.insert(setup)
    except:
        logger.critical("Database insertion failed after retry")
        send_telegram_alert("🚨 DATABASE ERROR")
```

### Invalid Data

**Scenario**: Insufficient historical data

**Handling**:
```python
if len(weekly_df) < 52:
    logger.warning(f"{symbol}: Insufficient data ({len(weekly_df)} weeks)")
    continue  # Skip instrument
```

---

## Performance Metrics

### Expected Execution Time
- Single instrument scan: 2-5 seconds
- Full Nifty50 scan: 2-5 minutes
- Full Nifty500 scan: 20-40 minutes

### Optimization Strategies
1. **Parallel Processing**: Scan instruments concurrently (future enhancement)
2. **Caching**: Cache indicator calculations for frequently scanned stocks
3. **Incremental Updates**: Only update changed data

---

## Testing Strategy

### Unit Tests
```python
def test_3wi_detection():
    # Given: Sample weekly data with known 3WI pattern
    df = create_sample_data_with_3wi()
    
    # When: Detect patterns
    patterns = detect_3wi(df)
    
    # Then: Expect 1 pattern detected
    assert len(patterns) == 1
    assert patterns[0]['mother_high'] == 100.0
    assert patterns[0]['inside_weeks'] == 2
```

### Integration Tests
```python
def test_full_scan_flow():
    # Given: Test database with sample instruments
    setup_test_db()
    
    # When: Run scanner
    scanner.run()
    
    # Then: Verify setups stored
    setups = db.query("SELECT * FROM setups")
    assert len(setups) > 0
```

### Paper Trading
- Run scanner in paper mode daily
- Verify no duplicate positions
- Check notification delivery
- Validate risk calculations

---

## Monitoring and Alerts

### Success Metrics
- Instruments scanned: 50 (Nifty50)
- Scan duration: < 5 minutes
- Patterns detected: 5-15 (typical)
- Valid setups (filters passed): 2-5 (typical)
- Breakouts confirmed: 0-2 (typical)

### Alert Conditions
- Scan duration > 10 minutes → Performance alert
- Zero patterns detected → Data quality alert
- API failures > 3 → Critical alert
- Risk limit exceeded → Warning alert

---

## Compliance

### Audit Trail
Every scan execution logs:
- Timestamp (start and end)
- Instruments scanned (count and list)
- Patterns detected (count and details)
- Positions created (count and details)
- Errors encountered (count and types)

### Idempotency Verification
- Re-running same scan produces same results
- No duplicate positions created
- Setup table constraints enforce uniqueness
- Position table checks for existing open positions

---

## Future Enhancements

1. **Machine Learning**: Pattern quality prediction
2. **Parallel Scanning**: Multi-threaded instrument processing
3. **Advanced Filters**: Sector rotation, relative strength
4. **Dynamic Risk**: Adjust risk based on market volatility
5. **Options Integration**: Trade options on indices (BankNifty/Nifty)
