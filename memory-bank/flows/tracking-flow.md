# ⏱️ Tracking Flow - Live Position Management

## Overview

The tracking flow is responsible for real-time management of open trading positions. It runs hourly during market hours to monitor profit/loss, update stop losses, execute partial exits, and enforce risk management rules.

---

## Execution Schedule

| Time (IST) | Action |
|------------|--------|
| 09:00 - 15:00 | Run every hour (09:00, 10:00, 11:00, 12:00, 13:00, 14:00, 15:00) |
| Mon - Fri | Trading days only |

**Frequency**: 7 times per trading day

**Rationale**:
- Hourly checks provide balance between responsiveness and API efficiency
- Allows time for market moves to develop
- Prevents over-trading and noise

---

## Detailed Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                   TRACKER TRIGGERED                         │
│                   (Every hour 09:00-15:00)                 │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 1: FETCH OPEN POSITIONS                               │
│ ─────────────────────────────────────────────────────      │
│ SQL: SELECT * FROM positions WHERE status = 'open'         │
│ Expected: 0-10 positions (based on 6% max risk)            │
│ If empty: Log "No open positions" and exit                 │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 2: ITERATE THROUGH POSITIONS                          │
│ ─────────────────────────────────────────────────────      │
│ FOR EACH position IN open_positions:                       │
│                                                             │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2a. FETCH CURRENT LTP                           │     │
│   │ ────────────────────────                        │     │
│   │ • API: Angel One SmartAPI                       │     │
│   │ • Method: getLTP(exchange, symboltoken)         │     │
│   │ • Response: Last Traded Price                   │     │
│   │ • Fallback: If LTP unavailable, use last close  │     │
│   │ • Error handling: Retry 3 times, skip if failed │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2b. CALCULATE POSITION METRICS                  │     │
│   │ ────────────────────────────────                │     │
│   │ unrealized_pnl = (ltp - entry) × qty            │     │
│   │ risk_amount = |entry - stop| × qty              │     │
│   │ pnl_pct = unrealized_pnl / (entry × qty) × 100  │     │
│   │ days_in_trade = today - opened_date             │     │
│   │                                                  │     │
│   │ Current state:                                  │     │
│   │ • LTP: {ltp}                                    │     │
│   │ • Unrealized P&L: ₹{unrealized_pnl}             │     │
│   │ • P&L %: {pnl_pct}%                             │     │
│   │ • Days: {days_in_trade}                         │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2c. EVALUATE PROFIT MANAGEMENT RULES            │     │
│   │ ────────────────────────────────────────────    │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 1: +3% → MOVE STOP TO BREAKEVEN   │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If pnl_pct >= 3.0:                     │     │     │
│   │ │   new_stop = entry_price               │     │     │
│   │ │   UPDATE positions                      │     │     │
│   │ │   SET stop = new_stop                   │     │     │
│   │ │   WHERE id = position_id               │     │     │
│   │ │                                         │     │     │
│   │ │   Alert: "🔒 Stop moved to breakeven"  │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 2: +6% → BOOK 25% PROFIT          │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If pnl_pct >= 6.0 AND status != 'partial':│  │     │
│   │ │   partial_qty = int(qty × 0.25)        │     │     │
│   │ │   remaining_qty = qty - partial_qty     │     │     │
│   │ │   partial_pnl = (ltp - entry) × partial_qty││     │
│   │ │                                         │     │     │
│   │ │   UPDATE positions                      │     │     │
│   │ │   SET qty = remaining_qty,              │     │     │
│   │ │       status = 'partial'                │     │     │
│   │ │   WHERE id = position_id               │     │     │
│   │ │                                         │     │     │
│   │ │   Record in ledger:                     │     │     │
│   │ │   INSERT INTO ledger (partial exit)     │     │     │
│   │ │                                         │     │     │
│   │ │   Alert: "💰 Booked 25% at +6%"        │     │     │
│   │ │                                         │     │     │
│   │ │   Trail remaining:                      │     │     │
│   │ │   new_stop = entry + (0.5 × (ltp - entry))│ │     │
│   │ └────────────────────────────────────────┘     │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 3: +10% → BOOK 50% PROFIT         │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If pnl_pct >= 10.0:                    │     │     │
│   │ │   partial_qty = int(qty × 0.5)         │     │     │
│   │ │   remaining_qty = qty - partial_qty     │     │     │
│   │ │   partial_pnl = (ltp - entry) × partial_qty││     │
│   │ │                                         │     │     │
│   │ │   UPDATE positions                      │     │     │
│   │ │   SET qty = remaining_qty               │     │     │
│   │ │   WHERE id = position_id               │     │     │
│   │ │                                         │     │     │
│   │ │   Record partial exit in ledger         │     │     │
│   │ │                                         │     │     │
│   │ │   Alert: "💰 Booked 50% at +10%"       │     │     │
│   │ │                                         │     │     │
│   │ │   Trail remaining aggressively:         │     │     │
│   │ │   new_stop = ltp - (2 × ATR)            │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 4: TARGET 1 (T1) REACHED          │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If ltp >= t1:                          │     │     │
│   │ │   Book 50% at T1                        │     │     │
│   │ │   Trail remaining to T2                 │     │     │
│   │ │   new_stop = t1 (lock in T1 profit)     │     │     │
│   │ │                                         │     │     │
│   │ │   Alert: "🎯 T1 reached, booked 50%"   │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 5: TARGET 2 (T2) REACHED          │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If ltp >= t2:                          │     │     │
│   │ │   Exit remaining 50%                    │     │     │
│   │ │   Close position completely             │     │     │
│   │ │                                         │     │     │
│   │ │   UPDATE positions                      │     │     │
│   │ │   SET status = 'closed',                │     │     │
│   │ │       closed_ts = now(),                │     │     │
│   │ │       pnl = total_pnl,                  │     │     │
│   │ │       rr = achieved_rr                  │     │     │
│   │ │   WHERE id = position_id               │     │     │
│   │ │                                         │     │     │
│   │ │   Record in ledger with tag "T2 success"│    │     │
│   │ │                                         │     │     │
│   │ │   Alert: "🎉 T2 reached, full exit"    │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2d. EVALUATE LOSS MANAGEMENT RULES              │     │
│   │ ────────────────────────────────────────────    │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 6: -3% → CAUTION ALERT            │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If pnl_pct <= -3.0:                    │     │     │
│   │ │   Alert: "⚠️ Position down 3%"         │     │     │
│   │ │   Additional info:                      │     │     │
│   │ │   - Distance to stop: {distance}       │     │     │
│   │ │   - Current LTP: {ltp}                 │     │     │
│   │ │   - Stop loss: {stop}                  │     │     │
│   │ │                                         │     │     │
│   │ │   No action taken (watch closely)       │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 7: -6% → IMMEDIATE EXIT           │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If pnl_pct <= -6.0:                    │     │     │
│   │ │   Exit entire position immediately      │     │     │
│   │ │   (Risk management override)            │     │     │
│   │ │                                         │     │     │
│   │ │   UPDATE positions                      │     │     │
│   │ │   SET status = 'closed',                │     │     │
│   │ │       closed_ts = now(),                │     │     │
│   │ │       pnl = realized_loss,              │     │     │
│   │ │       rr = -4.0  # Lost 4x intended risk│    │     │
│   │ │   WHERE id = position_id               │     │     │
│   │ │                                         │     │     │
│   │ │   Record in ledger with tag "risk override"│ │     │
│   │ │                                         │     │     │
│   │ │   Alert: "🚨 -6% exit, risk override"  │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   │                                                  │     │
│   │ ┌────────────────────────────────────────┐     │     │
│   │ │ RULE 8: STOP LOSS HIT                  │     │     │
│   │ │ ───────────────────────────────────────│     │     │
│   │ │ If ltp <= stop:                        │     │     │
│   │ │   Exit entire position                  │     │     │
│   │ │                                         │     │     │
│   │ │   UPDATE positions                      │     │     │
│   │ │   SET status = 'closed',                │     │     │
│   │ │       closed_ts = now(),                │     │     │
│   │ │       pnl = (stop - entry) × qty,       │     │     │
│   │ │       rr = -1.0  # Lost 1R as intended  │     │     │
│   │ │   WHERE id = position_id               │     │     │
│   │ │                                         │     │     │
│   │ │   Record in ledger with tag "stopped out"│   │     │
│   │ │                                         │     │     │
│   │ │   Alert: "🛑 Stop loss hit"            │     │     │
│   │ └────────────────────────────────────────┘     │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2e. UPDATE DATABASE                             │     │
│   │ ────────────────────────                        │     │
│   │ • Update position record with new values        │     │
│   │ • If closed: Set closed_ts, final pnl, rr       │     │
│   │ • If partial: Update qty, maintain 'open' status│     │
│   │ • Commit transaction                            │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2f. SEND ALERTS                                 │     │
│   │ ────────────────────────                        │     │
│   │ Telegram:                                       │     │
│   │ • Position update alert (if rule triggered)     │     │
│   │ • Current metrics (LTP, P&L, days in trade)     │     │
│   │                                                  │     │
│   │ Google Sheets:                                  │     │
│   │ • Update "Active Positions" tab                 │     │
│   │ • If closed: Move to "Trade History" tab        │     │
│   └─────────────────────────────────────────────────┘     │
│                          ↓                                 │
│   ┌─────────────────────────────────────────────────┐     │
│   │ 2g. IDEMPOTENCY CHECK                           │     │
│   │ ────────────────────────                        │     │
│   │ • Hash: {position_id}_{hour}_{action}           │     │
│   │ • Check if alert already sent this hour         │     │
│   │ • Skip duplicate alerts (same position, hour)    │     │
│   │ • Prevents spam if tracker runs multiple times  │     │
│   └─────────────────────────────────────────────────┘     │
│                                                             │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 3: UPDATE MASTER SHEET                                │
│ ─────────────────────────────────────────────────────      │
│ • Batch update all open positions in Google Sheet          │
│ • Update current price, unrealized P&L, P&L %              │
│ • Update days in trade                                     │
│ • Sort by P&L % (best to worst)                            │
│ • Add summary row with totals                              │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ STEP 4: SUMMARY AND LOGGING                                │
│ ─────────────────────────────────────────────────────      │
│ • Log tracking completion                                  │
│ • Summary:                                                 │
│   - Positions tracked: {count}                             │
│   - Stop moves: {stop_move_count}                          │
│   - Partial exits: {partial_exit_count}                    │
│   - Full exits: {full_exit_count}                          │
│   - Alerts sent: {alert_count}                             │
│   - Total unrealized P&L: ₹{total_pnl}                     │
│ • Send summary to Telegram (if significant changes)        │
└────────────────────┬───────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│                  TRACKING COMPLETE                          │
│                Next run: Next hour                         │
└────────────────────────────────────────────────────────────┘
```

---

## Position Management Rules - Detailed

### Rule 1: +3% → Move Stop to Breakeven

**Trigger**: `pnl_pct >= 3.0`

**Action**:
```python
if pnl_pct >= 3.0 and current_stop < entry_price:
    new_stop = entry_price
    
    db.update(
        "UPDATE positions SET stop = ? WHERE id = ?",
        new_stop, position_id
    )
    
    send_telegram_alert(f"""
    🔒 STOP MOVED TO BREAKEVEN
    ─────────────────────
    Symbol: {symbol}
    Entry: ₹{entry_price}
    New Stop: ₹{new_stop}
    Current LTP: ₹{ltp}
    Profit: +{pnl_pct:.1f}%
    ─────────────────────
    Position now risk-free!
    """)
```

**Rationale**:
- Protect capital after initial profit
- Ensure no loss on profitable trades
- Psychological benefit: stress-free holding

**Example**:
```
Entry: ₹2,510
Original Stop: ₹2,430
Current LTP: ₹2,585 (+2.99% = no action)
Current LTP: ₹2,586 (+3.03% = move stop to ₹2,510)
```

---

### Rule 2: +6% → Book 25% Profit

**Trigger**: `pnl_pct >= 6.0 AND status != 'partial'`

**Action**:
```python
if pnl_pct >= 6.0 and position.status == 'open':
    # Calculate partial exit
    original_qty = position.qty
    partial_qty = int(original_qty * 0.25)  # 25%
    remaining_qty = original_qty - partial_qty
    partial_pnl = (ltp - entry_price) * partial_qty
    
    # Update position
    db.update("""
        UPDATE positions 
        SET qty = ?, status = 'partial'
        WHERE id = ?
    """, remaining_qty, position_id)
    
    # Record partial exit in ledger
    db.insert("""
        INSERT INTO ledger (
            symbol, opened_ts, closed_ts, 
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, symbol, opened_ts, now(), partial_pnl, 4.0, "partial_25%_at_+6%")
    
    # Trail remaining stop
    trail_distance = (ltp - entry_price) * 0.5
    new_stop = entry_price + trail_distance
    
    db.update(
        "UPDATE positions SET stop = ? WHERE id = ?",
        new_stop, position_id
    )
    
    send_telegram_alert(f"""
    💰 25% PROFIT BOOKED
    ─────────────────────
    Symbol: {symbol}
    Exit Price: ₹{ltp}
    Qty Sold: {partial_qty}
    Profit: ₹{partial_pnl:.2f}
    ─────────────────────
    Remaining: {remaining_qty} shares
    New Stop: ₹{new_stop:.2f} (trailing)
    """)
```

**Rationale**:
- Lock in partial profits
- Reduce risk exposure
- Let winners run with protection

**Example**:
```
Entry: ₹2,510, Qty: 100
LTP: ₹2,660 (+5.98% = no action)
LTP: ₹2,661 (+6.01%)

Action:
- Sell 25 shares at ₹2,661
- Profit on 25 shares: (2,661 - 2,510) × 25 = ₹3,775
- Remaining: 75 shares
- Trail stop to: 2,510 + (2,661 - 2,510) × 0.5 = ₹2,585.50
```

---

### Rule 3: +10% → Book 50% Profit

**Trigger**: `pnl_pct >= 10.0`

**Action**:
```python
if pnl_pct >= 10.0:
    # Calculate partial exit
    current_qty = position.qty  # May already be reduced
    partial_qty = int(current_qty * 0.5)
    remaining_qty = current_qty - partial_qty
    partial_pnl = (ltp - entry_price) * partial_qty
    
    # Update position
    db.update("""
        UPDATE positions 
        SET qty = ?
        WHERE id = ?
    """, remaining_qty, position_id)
    
    # Record partial exit
    db.insert("""
        INSERT INTO ledger (
            symbol, opened_ts, closed_ts, 
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, symbol, opened_ts, now(), partial_pnl, 6.67, "partial_50%_at_+10%")
    
    # Aggressive trailing stop
    atr = get_atr(symbol)
    new_stop = ltp - (2 * atr)  # 2 ATR below current price
    
    db.update(
        "UPDATE positions SET stop = ? WHERE id = ?",
        new_stop, position_id
    )
    
    send_telegram_alert(f"""
    💰💰 50% PROFIT BOOKED
    ─────────────────────
    Symbol: {symbol}
    Exit Price: ₹{ltp}
    Qty Sold: {partial_qty}
    Profit: ₹{partial_pnl:.2f}
    ─────────────────────
    Remaining: {remaining_qty} shares
    New Stop: ₹{new_stop:.2f} (2 ATR trail)
    ─────────────────────
    Let the rest ride! 🚀
    """)
```

**Rationale**:
- Significant profit secured
- Very aggressive trail on remaining
- Capture outlier moves

**Example**:
```
Entry: ₹2,510, Original Qty: 100
At +6%: Sold 25, Remaining: 75
LTP: ₹2,761 (+10.0%)

Action:
- Sell 50% of 75 = 38 shares at ₹2,761
- Profit on 38 shares: (2,761 - 2,510) × 38 = ₹9,538
- Remaining: 37 shares
- ATR = ₹60
- Trail stop to: 2,761 - (2 × 60) = ₹2,641
```

---

### Rule 4: Target 1 (T1) Reached

**Trigger**: `ltp >= t1` (T1 = Entry + 1.5R)

**Action**:
```python
if ltp >= position.t1 and position.status != 'partial':
    # Book 50% at T1
    original_qty = position.qty
    exit_qty = int(original_qty * 0.5)
    remaining_qty = original_qty - exit_qty
    partial_pnl = (position.t1 - entry_price) * exit_qty
    
    # Update position
    db.update("""
        UPDATE positions 
        SET qty = ?, status = 'partial', stop = ?
        WHERE id = ?
    """, remaining_qty, position.t1, position_id)  # Lock stop at T1
    
    # Record partial exit
    db.insert("""
        INSERT INTO ledger (
            symbol, opened_ts, closed_ts, 
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, symbol, opened_ts, now(), partial_pnl, 1.5, "T1_target_hit")
    
    send_telegram_alert(f"""
    🎯 TARGET 1 REACHED
    ─────────────────────
    Symbol: {symbol}
    T1: ₹{position.t1}
    LTP: ₹{ltp}
    Qty Sold: {exit_qty} (50%)
    Profit: ₹{partial_pnl:.2f}
    ─────────────────────
    Remaining: {remaining_qty} shares
    Stop locked at T1: ₹{position.t1}
    Targeting T2: ₹{position.t2}
    """)
```

**Rationale**:
- Systematic profit booking at planned target
- Lock in 1.5R profit on 50%
- No risk on remaining (stop at T1)

---

### Rule 5: Target 2 (T2) Reached

**Trigger**: `ltp >= t2` (T2 = Entry + 3R)

**Action**:
```python
if ltp >= position.t2:
    # Exit entire remaining position
    remaining_qty = position.qty
    final_pnl = (position.t2 - entry_price) * remaining_qty
    
    # Calculate total P&L for full position
    total_pnl = calculate_total_pnl(position)  # Includes all partial exits
    
    # Close position
    db.update("""
        UPDATE positions 
        SET status = 'closed',
            closed_ts = ?,
            pnl = ?,
            rr = ?
        WHERE id = ?
    """, now(), total_pnl, 3.0, position_id)
    
    # Record final exit in ledger
    db.insert("""
        INSERT INTO ledger (
            symbol, opened_ts, closed_ts, 
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, symbol, opened_ts, now(), final_pnl, 3.0, "T2_target_success")
    
    send_telegram_alert(f"""
    🎉 TARGET 2 REACHED - FULL EXIT
    ─────────────────────────────
    Symbol: {symbol}
    T2: ₹{position.t2}
    LTP: ₹{ltp}
    Final Qty Sold: {remaining_qty}
    ─────────────────────────────
    TRADE COMPLETE ✅
    Total P&L: ₹{total_pnl:.2f}
    Average R:R: 2.25R
    Days in Trade: {days_in_trade}
    ─────────────────────────────
    Perfect execution! 🚀
    """)
```

**Rationale**:
- Complete exit at planned maximum target
- Typically achieved after: 25% at +6%, 50% at T1, 25% at T2
- Disciplined profit-taking

---

### Rule 6: -3% → Caution Alert

**Trigger**: `pnl_pct <= -3.0`

**Action**:
```python
if pnl_pct <= -3.0:
    distance_to_stop = ((ltp - position.stop) / ltp) * 100
    
    send_telegram_alert(f"""
    ⚠️ POSITION DOWN 3%
    ─────────────────────
    Symbol: {symbol}
    Entry: ₹{entry_price}
    Stop: ₹{position.stop}
    Current LTP: ₹{ltp}
    Loss: -{abs(pnl_pct):.1f}%
    ─────────────────────
    Distance to stop: {distance_to_stop:.1f}%
    Unrealized loss: ₹{abs(unrealized_pnl):.2f}
    ─────────────────────
    Watching closely... 👀
    """)
```

**Rationale**:
- Early warning system
- No action taken (stop loss will protect)
- Informational only

---

### Rule 7: -6% → Immediate Exit (Risk Override)

**Trigger**: `pnl_pct <= -6.0`

**Action**:
```python
if pnl_pct <= -6.0:
    # Emergency exit - risk management override
    full_qty = position.qty
    realized_loss = (ltp - entry_price) * full_qty
    rr_achieved = realized_loss / position.risk_amount
    
    # Close position immediately
    db.update("""
        UPDATE positions 
        SET status = 'closed',
            closed_ts = ?,
            pnl = ?,
            rr = ?
        WHERE id = ?
    """, now(), realized_loss, rr_achieved, position_id)
    
    # Record in ledger with special tag
    db.insert("""
        INSERT INTO ledger (
            symbol, opened_ts, closed_ts, 
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, symbol, opened_ts, now(), realized_loss, rr_achieved, "risk_override_-6%")
    
    send_telegram_alert(f"""
    🚨 RISK OVERRIDE - IMMEDIATE EXIT
    ───────────────────────────────
    Symbol: {symbol}
    Entry: ₹{entry_price}
    Exit: ₹{ltp}
    Loss: -{abs(pnl_pct):.1f}%
    ───────────────────────────────
    Qty Exited: {full_qty}
    Realized Loss: ₹{abs(realized_loss):.2f}
    ───────────────────────────────
    ⚠️ Position exceeded -6% threshold
    Risk management override activated
    """)
```

**Rationale**:
- Prevent catastrophic losses
- Stop loss may not have been hit (gapping, slippage)
- Safety mechanism

---

### Rule 8: Stop Loss Hit

**Trigger**: `ltp <= stop`

**Action**:
```python
if ltp <= position.stop:
    # Exit at stop loss
    full_qty = position.qty
    realized_loss = (position.stop - entry_price) * full_qty
    rr_achieved = -1.0  # Lost exactly 1R as planned
    
    # Close position
    db.update("""
        UPDATE positions 
        SET status = 'closed',
            closed_ts = ?,
            pnl = ?,
            rr = ?
        WHERE id = ?
    """, now(), realized_loss, rr_achieved, position_id)
    
    # Record in ledger
    db.insert("""
        INSERT INTO ledger (
            symbol, opened_ts, closed_ts, 
            pnl, rr, tag
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, symbol, opened_ts, now(), realized_loss, rr_achieved, "stopped_out")
    
    send_telegram_alert(f"""
    🛑 STOP LOSS HIT
    ─────────────────────
    Symbol: {symbol}
    Entry: ₹{entry_price}
    Stop: ₹{position.stop}
    Exit LTP: ₹{ltp}
    ─────────────────────
    Qty Exited: {full_qty}
    Realized Loss: ₹{abs(realized_loss):.2f}
    R:R: -1.0R
    ─────────────────────
    Risk management working as designed ✅
    Move on to next opportunity.
    """)
```

**Rationale**:
- Disciplined loss-taking
- Exactly 1R loss as intended
- Part of the system

---

## Error Handling

### LTP Fetch Failure

**Scenario**: Angel One API returns error or timeout

**Handling**:
```python
for attempt in range(3):
    try:
        ltp = angel_client.getLTP(symbol)
        break
    except (APITimeout, APIError) as e:
        if attempt < 2:
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            logger.error(f"LTP fetch failed for {symbol} after 3 attempts")
            # Use last known close price
            ltp = db.query(
                "SELECT close FROM historical_data "
                "WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
                symbol
            )[0]['close']
            logger.warning(f"Using last close for {symbol}: {ltp}")
```

### Database Update Failure

**Scenario**: Database connection lost during update

**Handling**:
```python
try:
    db.update(position)
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    db.rollback()
    db.reconnect()
    # Retry once
    try:
        db.update(position)
    except:
        logger.critical(f"Position update failed for {symbol}")
        send_telegram_alert(f"🚨 DATABASE ERROR - Position {symbol}")
```

### Alert Send Failure

**Scenario**: Telegram API error

**Handling**:
```python
try:
    send_telegram_alert(message)
except TelegramError as e:
    logger.error(f"Telegram alert failed: {e}")
    # Store failed alert in queue for retry
    alert_queue.append({
        'message': message,
        'timestamp': now(),
        'retry_count': 0
    })
    # Continue processing (don't block on alert failure)
```

---

## Performance Metrics

### Expected Execution Time
- Single position update: 1-2 seconds
- Full tracking cycle (10 positions): 10-20 seconds

### Optimization Strategies
1. **Batch LTP Fetching**: Fetch all LTPs in one API call
2. **Database Connection Pooling**: Reuse connections
3. **Async Processing**: Update positions concurrently (future enhancement)

---

## Idempotency

### Alert Deduplication

**Mechanism**:
```python
def should_send_alert(position_id, hour, action):
    """Check if alert already sent this hour for this action."""
    alert_hash = f"{position_id}_{hour}_{action}"
    
    # Check in-memory cache
    if alert_hash in alert_cache:
        return False
    
    # Add to cache
    alert_cache.add(alert_hash)
    
    # Persist to database
    db.insert("""
        INSERT INTO alert_log (
            position_id, hour, action, timestamp
        ) VALUES (?, ?, ?, ?)
    """, position_id, hour, action, now())
    
    return True

# Usage
if should_send_alert(position_id, current_hour, "stop_to_breakeven"):
    send_telegram_alert(message)
else:
    logger.info(f"Alert already sent this hour for {symbol}")
```

---

## Testing Strategy

### Unit Tests
```python
def test_profit_management_3_percent():
    # Given: Position with +3% profit
    position = create_test_position(entry=100, stop=95, qty=100)
    ltp = 103  # +3%
    
    # When: Evaluate rules
    new_stop = evaluate_profit_rules(position, ltp)
    
    # Then: Stop should move to breakeven
    assert new_stop == 100
```

### Integration Tests
```python
def test_full_tracking_flow():
    # Given: Test database with open positions
    setup_test_db()
    
    # When: Run tracker
    tracker.run()
    
    # Then: Verify positions updated
    positions = db.query("SELECT * FROM positions WHERE status = 'open'")
    # Check metrics calculated
    # Check alerts sent
```

---

## Monitoring and Alerts

### Success Metrics
- Positions tracked: 0-10 (typical)
- Tracking duration: < 30 seconds
- Stop moves: 0-2 per hour (typical)
- Partial exits: 0-1 per hour (typical)
- Full exits: 0-1 per hour (typical)

### Alert Conditions
- Tracking duration > 60 seconds → Performance alert
- LTP fetch failures > 3 → Critical alert
- No positions for > 5 days → Inactivity alert
- Total unrealized loss > 5% → Risk alert

---

## Compliance

### Audit Trail
Every tracking execution logs:
- Timestamp
- Positions tracked (count and symbols)
- Rules triggered (count and types)
- Exits executed (count and types)
- Errors encountered

### Trade Reconciliation
- Daily verification of position counts
- Daily P&L calculation audit
- Discrepancy alerts

---

## Future Enhancements

1. **Dynamic Trailing**: Adjust trail distance based on volatility
2. **Time-Based Exits**: Exit if no progress after N days
3. **Correlation Analysis**: Reduce correlated positions
4. **Market Context**: Adjust rules based on index behavior
5. **Machine Learning**: Optimize exit timing based on historical data
