# ✅ CORRECT Way to Get FYERS Tokens (OAuth Flow)

## ❌ What Doesn't Work
- There's NO "Generate Token" button on FYERS dashboard
- You can't manually create tokens

## ✅ What Does Work
You MUST use the **OAuth authentication flow**. Here are 3 methods:

---

## Method 1: Use Your Deployed App's OAuth Endpoint (Easiest)

### Step 1: Get the Auth URL

Visit your Render app's auth URL endpoint:

**For Sandbox (Paper Trading)**:
```
https://your-app.onrender.com/fyers/auth-url?mode=sandbox
```

**For Live Trading**:
```
https://your-app.onrender.com/fyers/auth-url?mode=live
```

This will return:
```json
{
  "success": true,
  "auth_url": "https://api-t1.fyers.in/api/v3/generate-authcode?client_id=...",
  "mode": "sandbox",
  "message": "Visit this URL to renew your FYERS access token"
}
```

### Step 2: Visit the Auth URL

Copy the `auth_url` and paste it in your browser. You'll be redirected to FYERS login page.

### Step 3: Login and Authorize

1. Login with your FYERS credentials
2. Grant permissions to your app
3. FYERS will redirect to your callback URL

### Step 4: Get the Auth Code

You'll be redirected to:
```
https://your-app.onrender.com/callback?s=ok&auth_code=XXXXX&state=sample
```

The page will show the `auth_code`.

### Step 5: Exchange Auth Code for Both Tokens

**Problem**: Your current callback ONLY shows the auth_code but doesn't exchange it for the refresh token.

**Solution**: Use this Python script to exchange it:

```python
import requests
import hashlib
import json

# Your FYERS credentials
CLIENT_ID = "YOUR_CLIENT_ID"
SECRET_KEY = "YOUR_SECRET_KEY"
AUTH_CODE = "PASTE_AUTH_CODE_FROM_CALLBACK_HERE"

# Generate app ID hash
app_id_hash = hashlib.sha256(f"{CLIENT_ID}:{SECRET_KEY}".encode()).hexdigest()

# Exchange auth code for tokens
url = "https://api-t1.fyers.in/api/v3/validate-authcode"  # Sandbox
# url = "https://api.fyers.in/api/v3/validate-authcode"  # Live

payload = {
    "grant_type": "authorization_code",
    "appIdHash": app_id_hash,
    "code": AUTH_CODE
}

response = requests.post(url, json=payload)
result = response.json()

print("=" * 80)
print("FYERS TOKEN RESPONSE")
print("=" * 80)
print(json.dumps(result, indent=2))

if result.get("s") == "ok":
    print("\n✅ SUCCESS! Copy these tokens:\n")
    print(f"FYERS_ACCESS_TOKEN={result['access_token']}")
    print(f"FYERS_REFRESH_TOKEN={result.get('refresh_token', 'NOT_PROVIDED')}")
else:
    print(f"\n❌ ERROR: {result.get('message')}")
```

### Step 6: Add Tokens to Render

Copy the tokens and add to Render environment variables:
```
FYERS_ACCESS_TOKEN=<access_token_from_response>
FYERS_REFRESH_TOKEN=<refresh_token_from_response>
```

---

## Method 2: Fix Your Callback Endpoint (Better Long-Term)

Update your `/callback` endpoint to automatically exchange the auth_code:

<function_calls>
<invoke name="Read">
<parameter name="path">/workspace/institutional_ai_trade_engine/src/api/server.py