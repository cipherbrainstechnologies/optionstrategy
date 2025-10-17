# 🔄 Idempotency Pattern

## Overview

Idempotency is a core architectural principle of the Institutional AI Trade Engine. It ensures that operations can be safely repeated without causing duplicate entries, alerts, or trades - critical for autonomous systems.

**Definition**: An idempotent operation produces the same result regardless of how many times it's executed with the same inputs.

---

## Why Idempotency Matters

### Problem Without Idempotency
```
Scenario: Scanner runs twice due to system restart

Without idempotency:
1. First run: Detects 3WI pattern for RELIANCE → Creates position
2. Second run: Detects same pattern → Creates DUPLICATE position
Result: Double exposure, risk limit exceeded, capital overdeployed
```

### Solution With Idempotency
```
Scenario: Scanner runs twice with same data

With idempotency:
1. First run: Detects 3WI pattern → Creates position (ID: RELIANCE_2025-01-22)
2. Second run: Detects same pattern → Checks for existing position → Skips
Result: Single position, correct risk exposure, system stable
```

---

## Implementation Patterns

### Pattern 1: Database Constraints

**Use Case**: Prevent duplicate setups and positions

**Implementation**:
```sql
-- Unique constraint on setups table
CREATE TABLE setups(
  id INTEGER PRIMARY KEY,
  symbol TEXT,
  week_start TEXT,
  mother_high REAL,
  mother_low REAL,
  UNIQUE(symbol, week_start)  -- Idempotency key
);

-- Insertion with conflict handling
INSERT INTO setups (symbol, week_start, mother_high, mother_low)
VALUES ('RELIANCE', '2025-01-22', 2520.0, 2430.0)
ON CONFLICT (symbol, week_start) DO NOTHING;
```

**Idempotency Key**: `(symbol, week_start)`
- Same symbol + same week = same setup
- Database enforces uniqueness automatically
- Silent failure on conflict (expected behavior)

**Benefits**:
- ✅ Database-level enforcement (most reliable)
- ✅ No application logic needed
- ✅ Atomic operation
- ✅ Race condition safe

---

### Pattern 2: Pre-Insert Check

**Use Case**: Prevent duplicate positions

**Implementation**:
```python
def create_position(symbol, entry_price, stop, qty):
    """
    Create new position with idempotency check.
    
    Idempotency: Check for existing open position before creating.
    """
    # Idempotency check
    existing = db.query(
        """
        SELECT id FROM positions 
        WHERE symbol = ? 
        AND status = 'open'
        """,
        symbol
    )
    
    if existing:
        logger.warning(f"Position already open for {symbol}, skipping")
        return existing[0]['id']  # Return existing position ID
    
    # Create new position
    position_id = db.insert(
        """
        INSERT INTO positions (
            symbol, status, entry_price, stop, qty, opened_ts
        ) VALUES (?, 'open', ?, ?, ?, ?)
        """,
        symbol, entry_price, stop, qty, datetime.now()
    )
    
    logger.info(f"Created new position {position_id} for {symbol}")
    return position_id
```

**Idempotency Key**: `(symbol, status='open')`
- One open position per symbol at a time
- Check before insert
- Safe for concurrent access (with transaction locks)

**Benefits**:
- ✅ Explicit control in application logic
- ✅ Can return existing ID if needed
- ✅ Clear logging
- ✅ Testable

---

### Pattern 3: Deterministic IDs

**Use Case**: Alert deduplication, operation tracking

**Implementation**:
```python
def generate_alert_id(position_id, hour, action):
    """
    Generate deterministic alert ID.
    
    Idempotency: Same position + hour + action = same ID
    """
    # Deterministic ID from inputs
    alert_id = f"{position_id}_{hour}_{action}"
    return alert_id

def should_send_alert(position_id, hour, action):
    """
    Check if alert already sent this hour.
    
    Idempotency: Only send alert once per hour per action.
    """
    alert_id = generate_alert_id(position_id, hour, action)
    
    # Check in-memory cache (fast)
    if alert_id in alert_cache:
        logger.debug(f"Alert {alert_id} already sent, skipping")
        return False
    
    # Check database (persistent)
    existing = db.query(
        "SELECT id FROM alert_log WHERE alert_id = ?",
        alert_id
    )
    
    if existing:
        # Add to cache for future checks
        alert_cache.add(alert_id)
        return False
    
    # Record alert in database
    db.insert(
        """
        INSERT INTO alert_log (
            alert_id, position_id, hour, action, timestamp
        ) VALUES (?, ?, ?, ?, ?)
        """,
        alert_id, position_id, hour, action, datetime.now()
    )
    
    # Add to cache
    alert_cache.add(alert_id)
    
    return True

# Usage in tracker
if should_send_alert(position_id, current_hour, "stop_to_breakeven"):
    send_telegram_alert(message)
else:
    logger.debug("Alert already sent this hour")
```

**Idempotency Key**: `{position_id}_{hour}_{action}`
- Example: `"123_14_stop_to_breakeven"`
- Deterministic from inputs
- Same inputs always produce same ID

**Benefits**:
- ✅ Fine-grained control
- ✅ Prevents alert spam
- ✅ Works across restarts (database-backed)
- ✅ Fast (in-memory cache)

---

### Pattern 4: Transaction Deduplication

**Use Case**: Ledger entries for partial exits

**Implementation**:
```python
def record_partial_exit(position_id, exit_qty, exit_price, timestamp):
    """
    Record partial exit in ledger with idempotency.
    
    Idempotency: Same exit timestamp + position = same transaction
    """
    # Generate transaction ID
    transaction_id = f"partial_{position_id}_{timestamp.isoformat()}"
    
    # Check if already recorded
    existing = db.query(
        "SELECT id FROM ledger WHERE transaction_id = ?",
        transaction_id
    )
    
    if existing:
        logger.info(f"Partial exit {transaction_id} already recorded")
        return existing[0]['id']
    
    # Record in ledger
    ledger_id = db.insert(
        """
        INSERT INTO ledger (
            transaction_id, symbol, opened_ts, closed_ts,
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        transaction_id, position.symbol, position.opened_ts,
        timestamp, calculate_pnl(exit_qty, exit_price),
        calculate_rr(exit_qty, exit_price), "partial_exit"
    )
    
    return ledger_id
```

**Idempotency Key**: `partial_{position_id}_{timestamp}`
- Timestamp includes milliseconds for uniqueness
- Safe for multiple partial exits on same position
- Different timestamps = different transactions

**Benefits**:
- ✅ Accurate trade history
- ✅ No duplicate ledger entries
- ✅ Supports multiple partials
- ✅ Auditable

---

## Comprehensive Idempotency Strategy

### Scanner Module

```python
def scan_instruments():
    """
    Scan for 3WI patterns and create positions.
    
    Idempotency at multiple levels:
    1. Setup storage: Unique constraint (symbol, week_start)
    2. Position creation: Check for existing open position
    3. Alert sending: Deterministic alert ID
    """
    instruments = get_enabled_instruments()
    
    for instrument in instruments:
        symbol = instrument['symbol']
        
        # Fetch and analyze data
        weekly_df = fetch_weekly_data(symbol)
        patterns = detect_3wi(weekly_df)
        
        for pattern in patterns:
            # Store setup (idempotent via DB constraint)
            try:
                db.insert(
                    """
                    INSERT INTO setups (symbol, week_start, ...)
                    VALUES (?, ?, ...)
                    ON CONFLICT (symbol, week_start) DO NOTHING
                    """,
                    symbol, pattern['week_start'], ...
                )
            except IntegrityError:
                # Already exists, expected
                pass
            
            # Check for breakout
            if breakout_confirmed(pattern):
                # Create position (idempotent via pre-check)
                position_id = create_position_idempotent(
                    symbol, entry, stop, qty
                )
                
                if position_id:  # Only alert if new position created
                    # Send alert (idempotent via alert ID)
                    alert_id = f"position_{symbol}_{datetime.now().date()}"
                    if should_send_alert_by_id(alert_id):
                        send_telegram_alert(...)
```

**Idempotency Layers**:
1. Database constraints (setups)
2. Pre-insert checks (positions)
3. Alert IDs (notifications)

---

### Tracker Module

```python
def track_positions():
    """
    Track open positions and manage exits.
    
    Idempotency:
    1. Position updates: Always safe (UPDATE by ID)
    2. Alerts: Hour-based deduplication
    3. Ledger entries: Transaction ID deduplication
    """
    open_positions = get_open_positions()
    current_hour = datetime.now().hour
    
    for position in open_positions:
        ltp = get_ltp(position.symbol)
        pnl_pct = calculate_pnl_pct(position, ltp)
        
        # Rule: +3% → Move stop to breakeven
        if pnl_pct >= 3.0 and position.stop < position.entry_price:
            # Update position (always safe by ID)
            db.update(
                "UPDATE positions SET stop = ? WHERE id = ?",
                position.entry_price, position.id
            )
            
            # Alert (idempotent via hour + action)
            if should_send_alert(position.id, current_hour, "stop_to_be"):
                send_telegram_alert(...)
        
        # Rule: +6% → Book 25%
        if pnl_pct >= 6.0 and position.status == 'open':
            partial_qty = int(position.qty * 0.25)
            
            # Update position
            db.update(
                "UPDATE positions SET qty = ?, status = 'partial' WHERE id = ?",
                position.qty - partial_qty, position.id
            )
            
            # Record in ledger (idempotent via transaction ID)
            transaction_id = f"partial_{position.id}_{datetime.now().isoformat()}"
            record_ledger_entry_idempotent(transaction_id, ...)
            
            # Alert (idempotent)
            if should_send_alert(position.id, current_hour, "partial_25"):
                send_telegram_alert(...)
```

**Idempotency Layers**:
1. Updates by primary key (always safe)
2. Hour-based alert deduplication
3. Transaction ID for ledger entries

---

## Testing Idempotency

### Test Pattern: Repeated Execution

```python
def test_scanner_idempotency():
    """
    Verify scanner can run multiple times safely.
    """
    # Setup: Same test data
    setup_test_instruments()
    mock_weekly_data()
    
    # First run
    result1 = scanner.run()
    
    # Second run (identical data)
    result2 = scanner.run()
    
    # Assertions
    assert result1 == result2  # Same result
    
    # Check database
    setups = db.query("SELECT * FROM setups")
    assert len(setups) == 3  # Not doubled
    
    positions = db.query("SELECT * FROM positions WHERE status = 'open'")
    assert len(positions) == 1  # Not doubled
    
    alerts = db.query("SELECT * FROM alert_log")
    assert len(alerts) == 1  # Not doubled
```

### Test Pattern: Concurrent Execution

```python
def test_concurrent_position_creation():
    """
    Verify no duplicate positions from concurrent scanner runs.
    """
    import threading
    
    def run_scanner():
        scanner.scan_instrument('RELIANCE')
    
    # Run scanner concurrently
    threads = [threading.Thread(target=run_scanner) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Check only one position created
    positions = db.query(
        "SELECT * FROM positions WHERE symbol = 'RELIANCE' AND status = 'open'"
    )
    assert len(positions) == 1
```

### Test Pattern: Restart Recovery

```python
def test_restart_idempotency():
    """
    Verify system state unchanged after restart.
    """
    # Run scanner
    scanner.run()
    
    # Capture state
    state_before = {
        'setups': db.query("SELECT * FROM setups"),
        'positions': db.query("SELECT * FROM positions"),
        'alerts': db.query("SELECT * FROM alert_log")
    }
    
    # Simulate restart (clear cache)
    alert_cache.clear()
    
    # Run scanner again with same data
    scanner.run()
    
    # Capture state after
    state_after = {
        'setups': db.query("SELECT * FROM setups"),
        'positions': db.query("SELECT * FROM positions"),
        'alerts': db.query("SELECT * FROM alert_log")
    }
    
    # Assert state unchanged
    assert len(state_before['setups']) == len(state_after['setups'])
    assert len(state_before['positions']) == len(state_after['positions'])
    # Alerts might differ due to restart (acceptable)
```

---

## Common Pitfalls

### ❌ Non-Deterministic IDs

**Problem**:
```python
# BAD: Random ID
position_id = uuid.uuid4()  # Different every time
```

**Solution**:
```python
# GOOD: Deterministic ID from inputs
position_id = f"{symbol}_{entry_timestamp.date()}"
```

### ❌ Time-Based Keys Without Resolution

**Problem**:
```python
# BAD: Low resolution timestamp
alert_id = f"{position_id}_{datetime.now().date()}"
# Multiple alerts on same day treated as duplicate
```

**Solution**:
```python
# GOOD: Appropriate resolution for use case
alert_id = f"{position_id}_{datetime.now().hour}_{action}"
# One alert per hour per action
```

### ❌ Missing Idempotency Checks

**Problem**:
```python
# BAD: Direct insert without check
db.insert("INSERT INTO positions (...) VALUES (...)")
# Duplicate positions created
```

**Solution**:
```python
# GOOD: Check before insert
existing = db.query("SELECT id FROM positions WHERE symbol = ? AND status = 'open'", symbol)
if not existing:
    db.insert("INSERT INTO positions (...) VALUES (...)")
```

### ❌ Inconsistent State on Failure

**Problem**:
```python
# BAD: No transaction
db.insert("INSERT INTO positions (...)")
send_alert(...)  # Fails
# Position created but no alert
```

**Solution**:
```python
# GOOD: Use transactions
with db.transaction():
    db.insert("INSERT INTO positions (...)")
    record_alert_intent(...)
send_alert(...)  # Failure is recoverable
```

---

## Benefits of Idempotency

### 1. System Reliability
- Safe restarts after failures
- No corruption from repeated operations
- Predictable behavior

### 2. Testing Confidence
- Tests can run multiple times
- Easy to verify correctness
- Deterministic outcomes

### 3. Operations Safety
- Manual reruns are safe
- Scheduled jobs can overlap
- Recovery procedures simplified

### 4. Auditability
- Clear transaction IDs
- No phantom duplicates
- Accurate history

---

## When to Apply Idempotency

### ✅ Apply To:
- Database inserts (setups, positions, ledger)
- Alert/notification sending
- Order placement (when implemented)
- Scheduled job execution
- API calls with side effects

### ⚠️ Not Required For:
- Read-only operations (SELECT queries)
- Calculations (deterministic by nature)
- Logging (informational, duplicates acceptable)
- Metrics collection

---

## Checklist for Implementing Idempotency

When adding a new operation, ask:

1. ☐ Can this operation be called multiple times?
2. ☐ What makes this operation unique? (Define idempotency key)
3. ☐ How do I detect duplicates?
4. ☐ What happens if I run it twice?
5. ☐ Have I added tests for repeated execution?
6. ☐ Is the database constraint or check in place?
7. ☐ Does it work after system restart?
8. ☐ Is it safe under concurrent execution?

---

## Summary

Idempotency is achieved through:

1. **Database Constraints**: Unique keys, ON CONFLICT handling
2. **Pre-Checks**: Explicit checks before operations
3. **Deterministic IDs**: Keys derived from inputs
4. **Transaction Safety**: Atomic operations
5. **Comprehensive Testing**: Repeated execution tests

**Golden Rule**: *Any operation that modifies state should be idempotent.*
