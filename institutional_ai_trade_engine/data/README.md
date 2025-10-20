# Data Directory

This directory contains runtime data files, templates, and the trading database.

## Files

### Templates (Copy and Edit)
- `portfolio.json.template` → Rename to `portfolio.json` and add your holdings
- `triggers.yaml.template` → (Optional) Rename to `triggers.yaml` for custom triggers

### Auto-Generated Files
- `trade_engine.sqlite` - Main database (auto-created)
- `engine.log` - Application logs
- `ideas.csv` - Proposed new position adds
- `mock_exchange.db` - Mock broker database (if using MOCK mode)

## Setup Instructions

### 1. Portfolio Configuration (Required)

```bash
cp portfolio.json.template portfolio.json
```

Edit `portfolio.json` with your actual holdings:

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

**Important**: The engine will scan ONLY stocks listed in `portfolio.json`.

### 2. Custom Triggers (Optional)

```bash
cp triggers.yaml.template triggers.yaml
```

Edit `triggers.yaml` to define specific entry/exit levels:

```yaml
AUROPHARMA:
  pre_breakout: 1110
  stop: 1048
  t1: 1245
  t2: 1320
  notes: "Custom setup"
```

If not provided, the engine calculates levels automatically from 3WI patterns.

## File Descriptions

### portfolio.json
Tracks your current holdings. Engine scans only these symbols for 3WI patterns.

### ideas.csv
Auto-generated file containing proposed new position adds. Columns:
- timestamp
- symbol
- entry, stop, t1, t2
- qty
- risk_r, r_r
- confidence (0-100)
- pattern type
- reason/notes

Review this file to identify new opportunities that meet strategy criteria.

### trade_engine.sqlite
Main SQLite database containing:
- instruments (trading universe)
- setups (detected 3WI patterns)
- signals (trade signals)
- orders (order history)
- fills (execution history)
- positions (open and closed trades)
- ledger (learning ledger for all closed trades)

### engine.log
Application logs with timestamps, levels, and detailed execution info.

## Backup Recommendations

Regular backups recommended for:
- `trade_engine.sqlite` (before any DB schema changes)
- `portfolio.json` (your holdings)
- `ideas.csv` (trade ideas)
- `engine.log` (troubleshooting)

## Directory Structure

```
data/
├── README.md (this file)
├── portfolio.json.template
├── triggers.yaml.template
├── portfolio.json (create from template)
├── triggers.yaml (optional)
├── trade_engine.sqlite (auto-created)
├── engine.log (auto-created)
├── ideas.csv (auto-created)
└── mock_exchange.db (auto-created if using MOCK broker)
```
