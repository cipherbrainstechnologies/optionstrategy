# 📦 Installation Guide

Complete installation instructions for the Institutional AI Trade Engine.

---

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **Python**: 3.11 or higher
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 500MB for application + data
- **Internet**: Required for FYERS API (not required for MOCK mode)

### Recommended Setup
- **Python**: 3.11+
- **RAM**: 4GB+
- **CPU**: 2+ cores
- **OS**: Linux (Ubuntu 20.04+) or macOS

---

## Step-by-Step Installation

### 1. Verify Python Version

```bash
python3.11 --version
# Should output: Python 3.11.x or higher
```

**If Python 3.11+ not installed**:

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### macOS (Homebrew)
```bash
brew install python@3.11
```

#### Windows
Download from https://www.python.org/downloads/

---

### 2. Clone Repository

```bash
cd ~/projects  # or your preferred directory
git clone <repository-url>
cd institutional_ai_trade_engine
```

---

### 3. Create Virtual Environment

```bash
python3.11 -m venv .venv
```

**Activate virtual environment**:

#### Linux/macOS
```bash
source .venv/bin/activate
```

#### Windows (PowerShell)
```powershell
.venv\Scripts\Activate.ps1
```

#### Windows (CMD)
```cmd
.venv\Scripts\activate.bat
```

**Verify activation**:
```bash
which python  # Should point to .venv/bin/python
python --version  # Should show Python 3.11.x
```

---

### 4. Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output**: All packages install successfully without errors.

**If errors occur**:

#### Common Issues

**Issue**: `error: externally-managed-environment`
**Solution**: Use virtual environment (step 3) - never install system-wide.

**Issue**: `gcc` or `python-dev` missing (Linux)
**Solution**:
```bash
sudo apt install build-essential python3.11-dev
```

**Issue**: Microsoft C++ Build Tools missing (Windows)
**Solution**: Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

### 6. Verify Installation

```bash
python -c "import pandas, sqlalchemy, fyers_apiv3; print('✓ All imports successful')"
```

**Expected output**: `✓ All imports successful`

---

### 7. Create Configuration

```bash
cp .env.example .env
```

**Edit `.env`**:

```bash
nano .env  # or vim, code, etc.
```

**Minimum configuration** (MOCK mode for testing):
```env
BROKER=MOCK
PORTFOLIO_CAPITAL=400000
RISK_PCT_PER_TRADE=1.5
DATA_DIR=./data
```

**FYERS configuration** (paper trading):
```env
BROKER=FYERS
PORTFOLIO_CAPITAL=400000
RISK_PCT_PER_TRADE=1.5

FYERS_CLIENT_ID=your_client_id
FYERS_ACCESS_TOKEN=your_token
FYERS_SANDBOX=true

DATA_DIR=./data
DB_PATH=./data/trade_engine.sqlite
LOG_PATH=./data/engine.log
```

---

### 8. Create Portfolio File

```bash
cp data/portfolio.json.template data/portfolio.json
```

**Edit `data/portfolio.json`**:

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

**Replace** with your actual holdings or keep for testing.

---

### 9. Initialize Database

```bash
python main.py --init
```

**Expected output**:
```
==========================================
🚀 INSTITUTIONAL AI TRADE ENGINE
==========================================
✓ Database initialized
Database initialized at ./data/trade_engine.sqlite
✅ Execution completed successfully
```

---

### 10. First Test Run

```bash
python main.py --daily
```

**Expected output**:
```
==========================================
🚀 INSTITUTIONAL AI TRADE ENGINE - FYERS-FIRST
==========================================
Starting DAILY SCAN
==========================================
Broker: MOCK_EXCHANGE (or FYERS_SANDBOX)
Portfolio mode: 2 holdings
Scanning: RELIANCE
Scanning: TCS
...
Daily scan completed
✅ Execution completed successfully
```

---

## Verification Checklist

After installation, verify:

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list` shows all packages)
- [ ] `.env` file created and configured
- [ ] `data/portfolio.json` created
- [ ] Database initialized (file exists at `./data/trade_engine.sqlite`)
- [ ] Test run successful (`python main.py --daily`)
- [ ] Logs created (`./data/engine.log` exists)

---

## Directory Structure After Installation

```
institutional_ai_trade_engine/
├── .venv/                     # Virtual environment
├── .env                       # Configuration (created)
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── src/                       # Source code
├── data/
│   ├── portfolio.json         # Your holdings (created)
│   ├── trade_engine.sqlite    # Database (created)
│   ├── engine.log             # Logs (created)
│   └── ideas.csv              # Proposals (auto-generated)
└── memory-bank/               # Documentation
```

---

## Troubleshooting Installation

### Python Version Issues

**Problem**: `python3.11` not found

**Solution**:
```bash
# Check available versions
ls /usr/bin/python*

# Use available version (3.11+)
python3.12 -m venv .venv  # or python3.13, etc.
```

### Virtual Environment Issues

**Problem**: Cannot activate virtual environment

**Solution** (Linux/macOS):
```bash
# Ensure script is executable
chmod +x .venv/bin/activate
source .venv/bin/activate
```

**Solution** (Windows - Execution Policy):
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependency Installation Issues

**Problem**: Some packages fail to install

**Solution**:
```bash
# Install one by one to identify issue
pip install pydantic==2.8.2
pip install pandas==2.2.2
# ... etc

# Or update setuptools
pip install --upgrade setuptools wheel
```

### Permission Issues

**Problem**: Permission denied errors

**Solution**:
```bash
# Ensure data directory is writable
chmod 755 data/
chmod 644 data/*.json

# Ensure .env is secure
chmod 600 .env
```

### FYERS API Issues

**Problem**: "Missing FYERS credentials"

**Solution**:
1. Visit https://developers.fyers.in
2. Create app → get Client ID
3. Generate OAuth token → get Access Token
4. Add both to `.env`

**Problem**: "Invalid token" or "Token expired"

**Solution**:
1. Regenerate access token at FYERS portal
2. Update `.env` with new token
3. Tokens typically valid for 24 hours

### Database Issues

**Problem**: "Database locked"

**Solution**:
```bash
# Close any SQLite connections
fuser -k data/trade_engine.sqlite  # Linux

# Or delete and reinitialize (caution: loses data)
rm data/trade_engine.sqlite
python main.py --init
```

---

## Upgrading

To upgrade to a new version:

```bash
# Activate environment
source .venv/bin/activate

# Backup database
cp data/trade_engine.sqlite data/trade_engine.sqlite.backup

# Update code
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations (if any)
python main.py --init
```

---

## Uninstallation

To completely remove:

```bash
# Deactivate virtual environment
deactivate

# Remove directory
cd ..
rm -rf institutional_ai_trade_engine

# (Optional) Remove FYERS app from developers.fyers.in
```

---

## Next Steps

After successful installation:

1. **Test in MOCK mode** (no API required)
   ```bash
   python main.py --daily
   python main.py --hourly
   python main.py --eod
   ```

2. **Configure FYERS paper trading**
   - Get credentials from https://developers.fyers.in
   - Update `.env` with credentials
   - Set `FYERS_SANDBOX=true`

3. **Run paper trading for 2-4 weeks**
   - Monitor all signals
   - Review learning ledger
   - Verify strategy performance

4. **Setup automation** (see QUICKSTART_v2.md)
   - Cron jobs (Linux/Mac)
   - Task Scheduler (Windows)

5. **Consider live trading** (only after thorough testing)
   - Set `FYERS_SANDBOX=false`
   - Start with small capital
   - Monitor closely

---

## Getting Help

If installation fails:

1. Check logs: `cat data/engine.log`
2. Verify Python version: `python --version`
3. Verify packages: `pip list | grep -E "pydantic|pandas|fyers"`
4. Review error messages carefully
5. Check this guide's troubleshooting section

---

**Installation Complete! 🎉**

Proceed to [QUICKSTART_v2.md](QUICKSTART_v2.md) for usage instructions.
