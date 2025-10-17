# 🚀 Quick Start Guide

## Prerequisites

- Python 3.10 or higher
- Angel One SmartAPI account
- Telegram Bot Token
- Google Sheets API credentials (optional)

## Installation

1. **Clone and setup**:
   ```bash
   cd institutional_ai_trade_engine
   python setup.py
   ```

2. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Test the setup**:
   ```bash
   python test_setup.py
   ```

## Configuration

### Required Environment Variables

```bash
# Angel One API
ANGEL_API_KEY=your_api_key
ANGEL_CLIENT_CODE=your_client_code
ANGEL_API_SECRET=your_api_secret
ANGEL_TOTP_SECRET=your_totp_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Parameters
PORTFOLIO_CAPITAL=400000
RISK_PCT=1.5
PAPER_MODE=true
```

### Optional Configuration

```bash
# Google Sheets (optional)
GSHEETS_CREDENTIALS_JSON=/path/to/credentials.json
GSHEETS_MASTER_SHEET="Institutional Portfolio Master Sheet"

# Advanced Settings
TIMEZONE=Asia/Kolkata
DB_PATH=trading_engine.db
```

## Usage

### 1. Initialize Database
```bash
python -m src.storage.db
```

### 2. Seed Instruments
```bash
python scripts/seed_instruments.py --list nifty50
```

### 3. Test Connections
```bash
# Test Telegram
python -m src.alerts.telegram "System online ✅"

# Test Scanner (dry run)
python -m src.exec.scanner --dry
```

### 4. Start Trading Engine
```bash
python -m src.daemon
```

## Trading Strategy

### Three-Week Inside (3WI) Pattern

The system identifies stocks with:
1. **Mother Candle**: A weekly candle 2 weeks ago
2. **Inside Weeks**: Two consecutive weeks inside the mother candle range
3. **Breakout**: Price breaks above mother high or below mother low

### Filters Applied

- **RSI > 55**: Momentum confirmation
- **WMA Alignment**: WMA20 > WMA50 > WMA100 (uptrend)
- **Volume**: Current volume ≥ 1.5x 20-day average
- **ATR < 6%**: Not too volatile

### Risk Management

- **Position Sizing**: Based on 1.5% risk per trade
- **Stop Loss**: Mother candle low (for long) or high (for short)
- **Targets**: T1 = 1.5R, T2 = 3R
- **Trailing**: Start trailing after 10% profit

## Monitoring

### Real-time Alerts
- New position entries
- Stop loss hits
- Profit booking
- Position closures

### Daily Reports
- Open positions summary
- Daily PnL
- Performance metrics
- Win rate and R:R ratios

## File Structure

```
institutional_ai_trade_engine/
├── src/
│   ├── core/           # Configuration, scheduling, risk
│   ├── data/           # Market data and indicators
│   ├── strategy/       # 3WI pattern and filters
│   ├── exec/           # Scanner, tracker, reports
│   ├── alerts/         # Telegram and Google Sheets
│   ├── storage/        # Database and ledger
│   └── daemon.py       # Main entry point
├── scripts/            # Utility scripts
├── .env.example        # Environment template
├── pyproject.toml      # Dependencies
└── README.md          # This file
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're in the project directory
2. **Database Errors**: Run `python -m src.storage.db` to initialize
3. **API Errors**: Check your credentials in `.env`
4. **Telegram Errors**: Verify bot token and chat ID

### Logs

Check `trading_engine.log` for detailed logs:
```bash
tail -f trading_engine.log
```

### Database

View database with SQLite browser:
```bash
sqlite3 trading_engine.db
```

## Support

For issues and questions:
1. Check the logs first
2. Verify all credentials
3. Test individual components
4. Review the main README.md for detailed documentation

## Disclaimer

This is a trading system for educational purposes. Always test thoroughly in paper mode before live trading. Past performance does not guarantee future results.