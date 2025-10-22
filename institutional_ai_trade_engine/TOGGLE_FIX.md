# 🔧 Quick Fix: Sandbox/Live Toggle Not Working

## Problem

Your frontend toggle switch doesn't work because `FYERS_SANDBOX=true` in Render environment variables **always** overrides the toggle.

## Root Cause

```python
# In server.py line 86
"mode": "SANDBOX" if os.getenv("FYERS_SANDBOX", "true").lower() == "true" else "LIVE"
```

Environment variable takes priority over toggle → Toggle has no effect.

## Solution: Implement Dynamic Mode Storage

Copy this code to fix the toggle:

### 1. Add to `src/api/server.py` (at the top after imports):

```python
import json
from pathlib import Path

# File to persist trading mode across restarts
MODE_FILE = Path("data/trading_mode.json")

def get_current_mode():
    """
    Get current trading mode with priority:
    1. User's toggle selection (from file)
    2. Environment variable (initial default)
    """
    try:
        if MODE_FILE.exists():
            data = json.loads(MODE_FILE.read_text())
            mode = data.get("mode", "sandbox")
            logging.info(f"Using trading mode from user preference: {mode}")
            return mode
    except Exception as e:
        logging.warning(f"Could not read mode file: {e}")
    
    # Fallback to environment variable
    env_mode = "sandbox" if os.getenv("FYERS_SANDBOX", "true").lower() == "true" else "live"
    logging.info(f"Using trading mode from environment: {env_mode}")
    return env_mode

def set_current_mode(mode: str):
    """Save trading mode preference."""
    try:
        MODE_FILE.parent.mkdir(exist_ok=True)
        MODE_FILE.write_text(json.dumps({"mode": mode, "updated_at": str(datetime.now())}))
        logging.info(f"Trading mode saved: {mode}")
    except Exception as e:
        logging.error(f"Failed to save trading mode: {e}")
```

### 2. Update the `root()` endpoint (line 78):

```python
@app.get("/")
def root():
    """Root endpoint - API information and available endpoints."""
    return {
        "name": "Institutional AI Trade Engine API",
        "version": "2.0.0",
        "status": "running",
        "broker": os.getenv("BROKER", "FYERS"),
        "mode": get_current_mode().upper(),  # ← Changed: Use dynamic mode
        "endpoints": {
            "health": "/health",
            "overview": "/overview",
            "positions": "/positions",
            "scan": "/scan",
            "docs": "/docs"
        }
    }
```

### 3. Update the `/trading-mode` endpoint (line 361):

```python
@app.post("/trading-mode")
async def update_trading_mode(payload: dict):
    """Update trading mode (sandbox/live) for FYERS broker."""
    try:
        mode = payload.get("mode")
        if mode not in ["sandbox", "live"]:
            return {
                "success": False,
                "message": "Invalid mode. Must be 'sandbox' or 'live'"
            }
        
        # Save the mode preference
        set_current_mode(mode)
        
        # Update in-memory setting (for current session)
        os.environ["FYERS_SANDBOX"] = "true" if mode == "sandbox" else "false"
        
        return {
            "success": True,
            "mode": mode,
            "message": f"Trading mode updated to {mode}. Changes take effect immediately.",
            "note": "Mode preference saved. Will persist across restarts."
        }
        
    except Exception as e:
        logging.error(f"Error updating trading mode: {e}")
        return {
            "success": False,
            "message": f"Failed to update mode: {str(e)}"
        }
```

### 4. Update `get_overview()` to use dynamic mode (line 101):

```python
@app.get("/overview")
def get_overview():
    # ... existing code ...
    
    # Use dynamic mode instead of reading env directly
    current_mode = get_current_mode()
    paper_mode = (current_mode == "sandbox")
    
    return {
        "engineStatus": "Running",
        "paperMode": paper_mode,  # ← Now respects toggle
        # ... rest of response ...
    }
```

## How It Works

### Before (Broken):
```
User clicks toggle → Frontend sends request → Backend ignores it
                                                    ↓
                                            Reads FYERS_SANDBOX env
                                                    ↓
                                            Always returns "sandbox"
```

### After (Fixed):
```
User clicks toggle → Frontend sends request → Backend saves to file
                                                    ↓
                                            Updates os.environ
                                                    ↓
                                            Returns new mode
                                                    ↓
Next request → Reads from file (user preference) → Respects toggle!
```

## Priority Order

1. **User Toggle** (highest priority) - Stored in `data/trading_mode.json`
2. **Environment Variable** (default) - Initial mode on first run

## Testing

### 1. Deploy the fix:
```bash
git add src/api/server.py
git commit -m "fix: make sandbox/live toggle work dynamically"
git push origin main
```

### 2. In Render, create the data directory:
- Render will auto-create `data/trading_mode.json` on first toggle

### 3. Test the toggle:
```bash
# Check current mode
curl https://your-app.onrender.com/

# Toggle to live
curl -X POST https://your-app.onrender.com/trading-mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "live"}'

# Verify mode changed
curl https://your-app.onrender.com/
# Should show "mode": "LIVE"

# Toggle back to sandbox
curl -X POST https://your-app.onrender.com/trading-mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "sandbox"}'
```

## Important Notes

### 1. You Need BOTH Token Sets

To toggle between modes, you need **separate tokens** for each:

```env
# In Render environment variables

# Sandbox tokens
FYERS_ACCESS_TOKEN_SANDBOX=<sandbox_access_token>
FYERS_REFRESH_TOKEN_SANDBOX=<sandbox_refresh_token>

# Live tokens
FYERS_ACCESS_TOKEN_LIVE=<live_access_token>
FYERS_REFRESH_TOKEN_LIVE=<live_refresh_token>
```

Then update your code to load the appropriate tokens:

```python
def get_fyers_tokens():
    """Get FYERS tokens based on current mode."""
    mode = get_current_mode()
    
    if mode == "sandbox":
        return {
            "access_token": os.getenv("FYERS_ACCESS_TOKEN_SANDBOX"),
            "refresh_token": os.getenv("FYERS_REFRESH_TOKEN_SANDBOX")
        }
    else:  # live
        return {
            "access_token": os.getenv("FYERS_ACCESS_TOKEN_LIVE"),
            "refresh_token": os.getenv("FYERS_REFRESH_TOKEN_LIVE")
        }
```

### 2. Current Limitation

Right now you have **one set** of tokens in Render:
- `FYERS_ACCESS_TOKEN`
- `FYERS_REFRESH_TOKEN`

These are either sandbox OR live tokens (not both).

**Recommendation**: 
- Keep `FYERS_SANDBOX=true` in Render for now
- Use sandbox tokens only
- When ready for live trading, change to `FYERS_SANDBOX=false` and update tokens

### 3. Mode Persistence

- **Mode preference**: Saved in `data/trading_mode.json` (persists across restarts)
- **Token selection**: Based on environment variables (requires restart to change)

## Alternative: Simple Fix (No Code Changes)

If you don't want to implement dynamic mode storage:

### Option 1: Remove FYERS_SANDBOX from Render
1. Go to Render → Environment
2. Delete `FYERS_SANDBOX` variable
3. Code will default to "sandbox"
4. Toggle will work (but reset on restart)

### Option 2: Use Separate Deployments
- Deploy two instances on Render:
  - `trading-engine-sandbox` with `FYERS_SANDBOX=true`
  - `trading-engine-live` with `FYERS_SANDBOX=false`
- No toggle needed, just use different URLs

## Recommendation

**For production**: Implement the code fix above. It gives you:
- ✅ Toggle works
- ✅ Preference persists
- ✅ Easy switching between modes
- ✅ Safe default (sandbox) on first run

**For testing now**: Just use sandbox mode with `FYERS_SANDBOX=true` in Render.

---

**Ready to implement? Deploy the fix and your toggle will work!** 🚀
