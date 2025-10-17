# 💰 Risk Management Pattern

## Overview

Risk management is the cornerstone of the Institutional AI Trade Engine. Every position is sized based on risk, not capital, ensuring consistent risk exposure across all trades regardless of price or volatility.

**Core Principle**: *Risk a fixed percentage of capital on each trade, regardless of stock price, stop distance, or market conditions.*

---

## Risk-Based Position Sizing

### Formula

```
Position Size (Qty) = (Capital × Risk% × Plan) / (Entry Price - Stop Loss)

Where:
- Capital: Total portfolio capital
- Risk%: Percentage of capital to risk per trade (default: 1.5%)
- Plan: Position sizing multiplier (default: 1.0)
- Entry Price: Planned entry price
- Stop Loss: Planned stop loss price
```

### Implementation

```python
def size_position(entry, stop, capital, risk_pct, plan):
    """
    Calculate position size based on risk parameters.
    
    Args:
        entry (float): Entry price
        stop (float): Stop loss price
        capital (float): Available capital
        risk_pct (float): Risk percentage per trade (1.5 = 1.5%)
        plan (float): Position sizing plan multiplier (1.0 = full size)
    
    Returns:
        tuple: (quantity, risk_amount)
    
    Example:
        entry = 2510, stop = 2430, capital = 400000, risk% = 1.5%
        
        risk_rupees = 400000 × 0.015 × 1.0 = 6000
        per_share_risk = 2510 - 2430 = 80
        qty = 6000 / 80 = 75 shares
        
        Returns: (75, 6000.0)
    """
    # Calculate rupees at risk
    risk_rupees = capital * (risk_pct / 100) * plan
    
    # Calculate risk per share
    per_share = max(entry - stop, 0.01)  # Minimum 1 paisa to avoid division by zero
    
    # Calculate quantity
    qty = int(risk_rupees / per_share)
    
    # Ensure minimum quantity of 1
    return max(qty, 1), risk_rupees
```

---

## Risk Examples

### Example 1: High-Priced Stock with Wide Stop

```python
# RELIANCE
entry = 2510.0
stop = 2430.0  # 80 points stop
capital = 400000.0
risk_pct = 1.5

qty, risk = size_position(entry, stop, capital, risk_pct, 1.0)

# Calculations:
risk_amount = 400000 × 0.015 = 6000
per_share_risk = 2510 - 2430 = 80
qty = 6000 / 80 = 75 shares

# Capital deployed: 75 × 2510 = ₹188,250
# Risk: ₹6,000 (1.5% of capital)
# Stop hit = -₹6,000 loss (exactly 1.5%)
```

### Example 2: Low-Priced Stock with Tight Stop

```python
# ITC
entry = 420.0
stop = 410.0  # 10 points stop
capital = 400000.0
risk_pct = 1.5

qty, risk = size_position(entry, stop, capital, risk_pct, 1.0)

# Calculations:
risk_amount = 400000 × 0.015 = 6000
per_share_risk = 420 - 410 = 10
qty = 6000 / 10 = 600 shares

# Capital deployed: 600 × 420 = ₹252,000
# Risk: ₹6,000 (1.5% of capital)
# Stop hit = -₹6,000 loss (exactly 1.5%)
```

### Example 3: Volatile Stock with Very Wide Stop

```python
# ADANIENT (volatile)
entry = 2800.0
stop = 2600.0  # 200 points stop (wide)
capital = 400000.0
risk_pct = 1.5

qty, risk = size_position(entry, stop, capital, risk_pct, 1.0)

# Calculations:
risk_amount = 400000 × 0.015 = 6000
per_share_risk = 2800 - 2600 = 200
qty = 6000 / 200 = 30 shares

# Capital deployed: 30 × 2800 = ₹84,000
# Risk: ₹6,000 (1.5% of capital)
# Stop hit = -₹6,000 loss (exactly 1.5%)
```

**Key Insight**: Regardless of price or stop distance, the risk is always exactly ₹6,000 (1.5% of capital).

---

## Target Calculation

### R-Multiple Targets

```python
def calculate_targets(entry, stop, atr):
    """
    Calculate T1 and T2 targets based on risk (R).
    
    Args:
        entry (float): Entry price
        stop (float): Stop loss price
        atr (float): Average True Range (for context)
    
    Returns:
        tuple: (t1, t2)
    
    R = Risk = Entry - Stop
    T1 = Entry + 1.5R (1.5 times the risk)
    T2 = Entry + 3.0R (3.0 times the risk)
    """
    risk = abs(entry - stop)
    
    # T1: 1.5R target (conservative)
    t1 = entry + (risk * 1.5)
    
    # T2: 3.0R target (aggressive)
    t2 = entry + (risk * 3.0)
    
    return t1, t2
```

### Example: RELIANCE Targets

```python
entry = 2510.0
stop = 2430.0
atr = 60.0  # For context (not used in calculation)

t1, t2 = calculate_targets(entry, stop, atr)

# Calculations:
risk = 2510 - 2430 = 80
t1 = 2510 + (80 × 1.5) = 2510 + 120 = 2630
t2 = 2510 + (80 × 3.0) = 2510 + 240 = 2750

# Exit plan:
# Book 50% at T1 (₹2,630) = +1.5R on half
# Book 50% at T2 (₹2,750) = +3.0R on half
# Average R:R if both hit = (1.5 + 3.0) / 2 = 2.25R
```

**Why R-Multiples?**
- Standardized across all stocks
- Makes performance comparable
- Focuses on risk:reward ratio
- Independent of price

---

## Portfolio Risk Limits

### Maximum Open Risk

```python
# Configuration
MAX_OPEN_RISK_PCT = 6.0  # Maximum total open risk as % of capital

def check_risk_limits(open_positions, new_risk):
    """
    Check if adding new position violates risk limits.
    
    Args:
        open_positions (list): List of open positions with risk_amount
        new_risk (float): Risk amount for new position
    
    Returns:
        bool: True if within limits, False otherwise
    
    Rule: Total open risk ≤ 6% of capital
    """
    # Calculate current total risk
    total_risk = sum(pos.get('risk_amount', 0) for pos in open_positions)
    
    # Calculate maximum allowed risk
    max_risk = Config.PORTFOLIO_CAPITAL * (MAX_OPEN_RISK_PCT / 100)
    
    # Check if new position fits within limit
    return (total_risk + new_risk) <= max_risk
```

### Example: Risk Limit Check

```python
capital = 400000
max_risk_pct = 6.0
max_risk = 400000 × 0.06 = 24000

# Scenario 1: Room for new position
open_positions = [
    {'symbol': 'RELIANCE', 'risk_amount': 6000},
    {'symbol': 'TCS', 'risk_amount': 6000},
    {'symbol': 'INFY', 'risk_amount': 6000}
]
total_current_risk = 18000
new_position_risk = 6000

if (18000 + 6000) <= 24000:  # 24000 <= 24000 ✓
    print("✓ Can enter new position")
    print(f"Risk utilization: {(24000/24000)*100}% (at limit)")

# Scenario 2: Risk limit exceeded
open_positions = [
    {'symbol': 'RELIANCE', 'risk_amount': 6000},
    {'symbol': 'TCS', 'risk_amount': 6000},
    {'symbol': 'INFY', 'risk_amount': 6000},
    {'symbol': 'HDFC', 'risk_amount': 6000}
]
total_current_risk = 24000
new_position_risk = 6000

if (24000 + 6000) <= 24000:  # 30000 <= 24000 ✗
    print("✓ Can enter")
else:
    print("✗ Cannot enter - risk limit exceeded")
    print(f"Would be: {30000/24000*100:.1f}% (over limit)")
```

**Risk Limit Rationale**:
- 6% maximum = 4 positions at 1.5% each
- Conservative approach
- Prevents overexposure
- Allows diversification

---

## Dynamic Risk Adjustment

### Trailing Stop Pattern

```python
def update_trailing_stop(position, ltp, atr):
    """
    Update trailing stop based on profit level.
    
    Trailing Logic:
    - +3%: Move stop to breakeven (no risk)
    - +6%: Trail 50% of profit
    - +10%: Trail aggressively (2 ATR below price)
    """
    entry = position.entry_price
    stop = position.stop
    pnl_pct = ((ltp - entry) / entry) * 100
    
    # Rule 1: +3% → Breakeven
    if pnl_pct >= 3.0 and stop < entry:
        new_stop = entry
        return new_stop
    
    # Rule 2: +6% → Trail 50% of profit
    if pnl_pct >= 6.0:
        profit_distance = ltp - entry
        trail_amount = profit_distance * 0.5
        new_stop = entry + trail_amount
        return new_stop
    
    # Rule 3: +10% → Aggressive trail (2 ATR)
    if pnl_pct >= 10.0:
        new_stop = ltp - (2 * atr)
        return new_stop
    
    # No change
    return stop
```

### Example: Trailing Stop Evolution

```python
# Initial position
entry = 2510
original_stop = 2430
risk = 80 (₹6,000 at 75 shares)

# Scenario 1: LTP = 2585 (+2.99%)
pnl_pct = 2.99%
stop = 2430 (unchanged - below 3% threshold)
risk_exposure = ₹6,000

# Scenario 2: LTP = 2586 (+3.03%)
pnl_pct = 3.03%
stop = 2510 (moved to breakeven)
risk_exposure = ₹0 (risk-free!)

# Scenario 3: LTP = 2660 (+5.98%)
pnl_pct = 5.98%
stop = 2510 (still at breakeven, below 6%)
risk_exposure = ₹0

# Scenario 4: LTP = 2661 (+6.01%)
pnl_pct = 6.01%
profit = 2661 - 2510 = 151
trail_amount = 151 × 0.5 = 75.5
stop = 2510 + 75.5 = 2585.5
locked_profit = (2585.5 - 2510) × 75 = ₹5,662.5

# Scenario 5: LTP = 2761 (+10.0%)
pnl_pct = 10.0%
atr = 60
stop = 2761 - (2 × 60) = 2641
locked_profit = (2641 - 2510) × 75 = ₹9,825
```

**Trailing Benefits**:
- Protects profits
- Lets winners run
- Reduces stress
- Maximizes outliers

---

## Risk-Adjusted Performance Metrics

### R-Multiple Calculation

```python
def calculate_rr_ratio(entry, exit, stop, qty):
    """
    Calculate Risk:Reward (R:R) ratio for a trade.
    
    R = Initial Risk (Entry - Stop)
    Actual P&L in R terms = (Exit - Entry) / R
    
    Args:
        entry (float): Entry price
        exit (float): Exit price
        stop (float): Stop loss price
        qty (int): Position quantity
    
    Returns:
        float: R:R ratio
    """
    risk = abs(entry - stop)
    actual_pnl = exit - entry
    
    # R-multiple
    rr = actual_pnl / risk if risk > 0 else 0
    
    return rr
```

### Example: R-Multiple Calculations

```python
# Winning trade at T2
entry = 2510
stop = 2430
exit = 2750  # T2 target hit
risk = 80

rr = (2750 - 2510) / 80 = 240 / 80 = 3.0R
# Result: +3.0R (perfect T2 exit)

# Losing trade stopped out
entry = 2510
stop = 2430
exit = 2430  # Stop hit
risk = 80

rr = (2430 - 2510) / 80 = -80 / 80 = -1.0R
# Result: -1.0R (controlled loss)

# Partial win at T1
entry = 2510
stop = 2430
exit = 2630  # T1 target hit
risk = 80

rr = (2630 - 2510) / 80 = 120 / 80 = 1.5R
# Result: +1.5R (T1 target)
```

---

## Position Metrics Calculation

```python
def calculate_position_metrics(entry, current_price, stop, qty):
    """
    Calculate current position metrics.
    
    Args:
        entry (float): Entry price
        current_price (float): Current market price
        stop (float): Current stop loss
        qty (int): Position quantity
    
    Returns:
        dict: Position metrics
    """
    # Unrealized P&L
    unrealized_pnl = (current_price - entry) * qty
    
    # Current risk (if stop hit)
    risk_amount = abs(entry - stop) * qty
    
    # P&L percentage
    pnl_pct = (unrealized_pnl / (entry * qty)) * 100
    
    # R-multiple (current)
    initial_risk = abs(entry - stop)
    current_rr = (current_price - entry) / initial_risk if initial_risk > 0 else 0
    
    return {
        "unrealized_pnl": unrealized_pnl,
        "risk_amount": risk_amount,
        "pnl_pct": pnl_pct,
        "current_rr": current_rr,
        "current_price": current_price
    }
```

### Example: Position Metrics

```python
# Position details
entry = 2510
stop = 2430
qty = 75
current_price = 2660

metrics = calculate_position_metrics(entry, current_price, stop, qty)

# Results:
{
    "unrealized_pnl": (2660 - 2510) × 75 = 11,250,
    "risk_amount": (2510 - 2430) × 75 = 6,000,
    "pnl_pct": (11250 / (2510 × 75)) × 100 = 5.98%,
    "current_rr": (2660 - 2510) / 80 = 1.875R,
    "current_price": 2660
}
```

---

## Risk Management Rules Summary

### Entry Rules
1. **Position Size**: Always based on 1.5% risk
2. **Risk Limit**: Total open risk ≤ 6% of capital
3. **One Position**: Maximum one open position per symbol

### Exit Rules
1. **Stop Loss**: -1.0R (controlled loss)
2. **T1 Target**: +1.5R (book 50%)
3. **T2 Target**: +3.0R (book remaining 50%)
4. **Risk Override**: Exit at -6% P&L (safety mechanism)

### Profit Management
1. **+3%**: Move stop to breakeven (risk-free)
2. **+6%**: Book 25%, trail stop
3. **+10%**: Book 50%, aggressive trail

### Risk Limits
1. **Per Trade**: 1.5% of capital
2. **Total Open**: Maximum 6% of capital
3. **Max Positions**: ~4 concurrent positions

---

## Testing Risk Management

```python
def test_position_sizing():
    """Test risk-based position sizing."""
    capital = 400000
    risk_pct = 1.5
    
    # Test 1: High-priced stock
    qty, risk = size_position(2510, 2430, capital, risk_pct, 1.0)
    assert risk == 6000  # Always 1.5% of capital
    assert qty == 75
    
    # Test 2: Low-priced stock
    qty, risk = size_position(420, 410, capital, risk_pct, 1.0)
    assert risk == 6000  # Same risk
    assert qty == 600  # Different qty
    
    # Test 3: Risk consistency
    # Despite different prices, risk is constant
    assert size_position(2510, 2430, capital, risk_pct, 1.0)[1] == \
           size_position(420, 410, capital, risk_pct, 1.0)[1]

def test_risk_limits():
    """Test portfolio risk limits."""
    positions = [
        {'risk_amount': 6000},
        {'risk_amount': 6000},
        {'risk_amount': 6000},
        {'risk_amount': 6000}
    ]
    
    # At limit (24,000 / 24,000)
    assert check_risk_limits(positions, 0) == True
    
    # Over limit (30,000 / 24,000)
    assert check_risk_limits(positions, 6000) == False

def test_rr_calculation():
    """Test R:R ratio calculations."""
    # Win at T2
    rr = calculate_rr_ratio(2510, 2750, 2430, 75)
    assert rr == 3.0  # +3R
    
    # Loss at stop
    rr = calculate_rr_ratio(2510, 2430, 2430, 75)
    assert rr == -1.0  # -1R
```

---

## Benefits of Risk-Based Sizing

### 1. Consistency
- Every trade risks exactly 1.5% of capital
- Losses are predictable and controlled
- No single trade can devastate portfolio

### 2. Adaptability
- Works for any stock price
- Works for any volatility
- Adjusts automatically to stop distance

### 3. Psychology
- Removes emotion from position sizing
- Clear risk on every trade
- Confidence in system

### 4. Performance Tracking
- R-multiples make trades comparable
- Easy to identify what works
- Focus on process, not outcomes

---

## When to Adjust Risk

### Reduce Risk When:
- ❌ Losing streak (3+ consecutive losses)
- ❌ Drawdown > 10%
- ❌ Low confidence in setup
- ❌ Volatile market conditions

### Increase Risk When:
- ✅ Winning streak (5+ consecutive wins)
- ✅ Drawdown < 5%
- ✅ High-quality setups
- ✅ **Never** above 2% per trade (safety limit)

### Risk Adjustment Example

```python
# Normal risk
risk_pct = 1.5

# After 3 losses
risk_pct = 1.0  # Reduce to 1%

# After recovering
risk_pct = 1.5  # Back to normal

# Never
risk_pct = 2.5  # ✗ Too aggressive
```

---

## Key Takeaways

1. **Always size by risk**, not by capital
2. **Keep risk consistent** across all trades
3. **Respect risk limits** (6% total open risk)
4. **Trail stops** to protect profits
5. **Measure performance** in R-multiples
6. **Never risk more than 2%** per trade

**Golden Rule**: *If you can't afford to lose 1.5% of your capital on a trade, don't take the trade.*
