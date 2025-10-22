# 🔑 How to Get FYERS Refresh Token - Complete Guide

## 🎯 The Two Issues You're Facing

### Issue 1: Where to Get `FYERS_REFRESH_TOKEN`?
The current OAuth callback only returns the **access_token** (auth_code), but you need **both** access_token AND refresh_token.

### Issue 2: Sandbox/Live Toggle Not Working
Your toggle switch in the frontend doesn't work because `FYERS_SANDBOX=true` is hardcoded in Render environment variables, which overrides the toggle.

---

## 📋 Solution for Issue 1: Getting the Refresh Token

### Option A: Use FYERS Developer Portal (Easiest)

**Step 1**: Visit https://myapi.fyers.in/dashboard/

**Step 2**: Go to "Access Token" section

**Step 3**: Click "Generate Access Token"

**Step 4**: Complete authentication flow

**Step 5**: You'll see a response like this:
```json
{
  "s": "ok",
  "code": 200,
  "access_token": "eyJ0eXAiOiJKV1Qi...",
  "refresh_token": "ABC123XYZ456..."
}
```

**Step 6**: Copy **BOTH** tokens:
- `access_token` → Use for `FYERS_ACCESS_TOKEN`
- `refresh_token` → Use for `FYERS_REFRESH_TOKEN` ✨

---

### Option B: Fix Your Callback Endpoint (Recommended for Production)

The current callback endpoint needs to be updated to extract the refresh_token.

**Problem**: Current callback only shows `auth_code` (access token)

**Solution**: Update callback to exchange auth_code for both tokens

Here's what needs to happen:

#### Current Flow (Incomplete):
```
1. User clicks auth URL
2. FYERS redirects to /callback?auth_code=XXX
3. Callback returns auth_code
4. User manually copies access_token
❌ No refresh_token!
```

#### Correct Flow (Complete):
```
1. User clicks auth URL
2. FYERS redirects to /callback?auth_code=XXX
3. Backend exchanges auth_code for tokens via API call
4. FYERS returns BOTH access_token + refresh_token
5. Backend automatically updates .env or returns both
✅ Both tokens available!
```

---

### Option C: Manual API Call (For Understanding)

You can manually exchange the auth_code for both tokens:

```bash
# Step 1: Get auth_code from current callback
# Step 2: Call FYERS token exchange API

curl -X POST 'https://api-t1.fyers.in/api/v3/validate-authcode' \
  -H 'Content-Type: application/json' \
  -d '{
    "grant_type": "authorization_code",
    "appIdHash": "<SHA256_of_ClientID:SecretKey>",
    "code": "<your_auth_code_here>"
  }'

# Response will include BOTH tokens:
{
  "s": "ok",
  "access_token": "eyJ0eXAiOiJKV1Qi...",
  "refresh_token": "ABC123XYZ..."
}
```

---

## 🔧 Solution for Issue 2: Fix Sandbox/Live Toggle

### The Problem

**Current Situation**:
```python
# In server.py line 86
"mode": "SANDBOX" if os.getenv("FYERS_SANDBOX", "true").lower() == "true" else "LIVE"

# In Render environment variables
FYERS_SANDBOX=true  ← Hardcoded!
```

**Result**: No matter what you toggle in frontend, backend always uses sandbox mode.

---

### The Fix: Make Environment Variable Respect Toggle

You have 3 options:

#### **Option 1: Remove FYERS_SANDBOX from Render (Simplest)**

**In Render Dashboard**:
1. Go to Environment variables
2. **Delete** `FYERS_SANDBOX` variable
3. Restart service

**Result**: 
- Default will be sandbox (from code default "true")
- Toggle will now control the mode dynamically

---

#### **Option 2: Use Session-Based Mode (Better)**

Update your backend to store mode in memory/database instead of reading from env:

```python
# Add to server.py
current_trading_mode = {"mode": "sandbox"}  # Global variable

@app.post("/trading-mode")
async def update_trading_mode(payload: dict):
    """Update trading mode (sandbox/live) for FYERS broker."""
    mode = payload.get("mode")
    if mode not in ["sandbox", "live"]:
        return {"success": False, "message": "Invalid mode"}
    
    # Update global mode
    current_trading_mode["mode"] = mode
    
    return {
        "success": True,
        "mode": mode,
        "message": f"Trading mode updated to {mode}"
    }

# Then use current_trading_mode["mode"] instead of FYERS_SANDBOX everywhere
```

---

#### **Option 3: Dynamic Environment Variable (Most Flexible)**

Use a database or Redis to store the current mode, so it persists across restarts:

```python
# Store in database
@app.post("/trading-mode")
async def update_trading_mode(payload: dict):
    mode = payload.get("mode")
    
    # Save to database
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('trading_mode', :mode)"
        ), {"mode": mode})
        conn.commit()
    
    return {"success": True, "mode": mode}

# Read from database
def get_current_mode():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT value FROM settings WHERE key = 'trading_mode'"
        ))
        row = result.first()
        return row.value if row else "sandbox"
```

---

## 🚀 Complete Setup Process (After Merging to Main)

### Step 1: Merge Your Code
```bash
git checkout main
git merge cursor/automate-fyers-token-refresh-34e3
git push origin main
```

### Step 2: Get BOTH Tokens

**Option A - Developer Portal** (5 minutes):
1. Visit: https://myapi.fyers.in/dashboard/
2. Generate Access Token (for sandbox OR live)
3. Copy both `access_token` and `refresh_token`

**Option B - Your App's OAuth** (if you fix the callback):
1. Visit your app's `/fyers/auth-url?mode=sandbox` endpoint
2. Complete OAuth flow
3. Backend automatically extracts both tokens

### Step 3: Update Render Environment Variables

Go to Render Dashboard → Environment:

```env
# For Sandbox (Paper Trading)
FYERS_SANDBOX=true
FYERS_ACCESS_TOKEN=<sandbox_access_token>
FYERS_REFRESH_TOKEN=<sandbox_refresh_token>

# OR for Live Trading
FYERS_SANDBOX=false
FYERS_ACCESS_TOKEN=<live_access_token>
FYERS_REFRESH_TOKEN=<live_refresh_token>
```

**Important**: Sandbox and Live have **separate** tokens. You can't use a sandbox token for live mode or vice versa.

### Step 4: Fix Toggle Issue

**Quick Fix**:
1. In Render, delete `FYERS_SANDBOX` variable
2. Toggle will now work dynamically

**OR**

Keep environment variable for initial mode, but implement session-based override (Option 2 above).

---

## 🎯 Recommended Approach

### For Your Current Situation:

**Sandbox Trading** (Testing):
```env
FYERS_SANDBOX=true  ← Keep this
FYERS_ACCESS_TOKEN=<get from developer portal>
FYERS_REFRESH_TOKEN=<get from developer portal>
```

**Live Trading** (Production):
```env
FYERS_SANDBOX=false  ← Change to false
FYERS_ACCESS_TOKEN=<get from developer portal - LIVE mode>
FYERS_REFRESH_TOKEN=<get from developer portal - LIVE mode>
```

### Toggle Behavior:

**Current**: Toggle doesn't work (env variable overrides)

**Fix**: 
1. Use environment variable to set **initial** mode
2. Allow toggle to **override** for current session
3. Restart resets to environment variable mode

---

## 📊 Token Types Comparison

| Token Type | Where to Get | Validity | Use Case |
|------------|--------------|----------|----------|
| **Sandbox Access Token** | Developer Portal (Sandbox) | 12 hours | Paper trading |
| **Sandbox Refresh Token** | Developer Portal (Sandbox) | 30 days | Auto-refresh sandbox |
| **Live Access Token** | Developer Portal (Live) | 12 hours | Real trading |
| **Live Refresh Token** | Developer Portal (Live) | 30 days | Auto-refresh live |

**Important**: Sandbox and Live tokens are completely separate. Generate both sets if you want to toggle between modes.

---

## ⚠️ Important Notes

### 1. Toggle vs Environment Variable Priority

**Current Code Behavior**:
```python
# Environment variable ALWAYS wins
mode = os.getenv("FYERS_SANDBOX", "true")  # Always reads from env
```

**Fixed Code Behavior** (after implementing Option 2):
```python
# Session/database mode can override
mode = current_trading_mode.get("mode", os.getenv("FYERS_SANDBOX", "true"))
```

### 2. Separate Token Sets

You need **TWO sets of tokens** if you want to toggle:

```env
# Sandbox tokens
FYERS_ACCESS_TOKEN_SANDBOX=<sandbox_access>
FYERS_REFRESH_TOKEN_SANDBOX=<sandbox_refresh>

# Live tokens
FYERS_ACCESS_TOKEN_LIVE=<live_access>
FYERS_REFRESH_TOKEN_LIVE=<live_refresh>

# Current mode
FYERS_SANDBOX=true  # or false
```

Then your code loads the appropriate token set based on mode.

### 3. Auto-Refresh Applies to BOTH Modes

The automatic token refresh (Step 2) works for **both** sandbox and live:
- Sandbox mode: Refreshes sandbox tokens
- Live mode: Refreshes live tokens
- Each runs independently with their own refresh tokens

---

## 🔧 Quick Fix Code

Here's updated code to fix the toggle issue:

```python
# Add to server.py (top of file)
import json
from pathlib import Path

# Store current mode in a file (persists across restarts)
MODE_FILE = Path("data/trading_mode.json")

def get_current_mode():
    """Get current trading mode (respects toggle)."""
    try:
        if MODE_FILE.exists():
            data = json.loads(MODE_FILE.read_text())
            return data.get("mode", "sandbox")
    except:
        pass
    # Fallback to environment variable
    return "sandbox" if os.getenv("FYERS_SANDBOX", "true").lower() == "true" else "live"

def set_current_mode(mode: str):
    """Set current trading mode."""
    MODE_FILE.parent.mkdir(exist_ok=True)
    MODE_FILE.write_text(json.dumps({"mode": mode}))

# Update the /trading-mode endpoint
@app.post("/trading-mode")
async def update_trading_mode(payload: dict):
    mode = payload.get("mode")
    if mode not in ["sandbox", "live"]:
        return {"success": False, "message": "Invalid mode"}
    
    set_current_mode(mode)
    
    return {
        "success": True,
        "mode": mode,
        "message": f"Trading mode updated to {mode}. Changes take effect immediately."
    }

# Update root endpoint to use get_current_mode()
@app.get("/")
def root():
    return {
        "name": "Institutional AI Trade Engine API",
        "version": "2.0.0",
        "status": "running",
        "broker": os.getenv("BROKER", "FYERS"),
        "mode": get_current_mode().upper(),  # ← Use dynamic mode
        "endpoints": {...}
    }
```

---

## ✅ Action Items Summary

### Immediate (Today):

1. **Get refresh tokens**:
   - Visit: https://myapi.fyers.in/dashboard/
   - Generate tokens for sandbox mode
   - Copy both access_token AND refresh_token

2. **Add to Render**:
   ```
   FYERS_REFRESH_TOKEN=<paste_refresh_token_here>
   ```

3. **Restart Render service**

### Soon (This Week):

1. **Fix toggle issue**:
   - Implement session-based mode storage (code above)
   - OR remove FYERS_SANDBOX from Render env variables

2. **Get live tokens** (when ready for real trading):
   - Generate separate token set for live mode
   - Store in Render with FYERS_SANDBOX=false

3. **Test auto-refresh**:
   - Wait for tomorrow 08:45 IST
   - Check Render logs for successful refresh

---

## 🎉 Final Result

After these fixes:
- ✅ Automatic token refresh working (30 days autonomous)
- ✅ Toggle switch working (sandbox ↔ live)
- ✅ Both modes have their own token sets
- ✅ Production-ready deployment

---

**Questions? Check the logs or ask for help!**
