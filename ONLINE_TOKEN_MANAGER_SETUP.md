# 🌍 Fully Online FYERS Token Manager - Setup Guide

## ✨ What You're Getting

A **fully web-based solution** to generate and update FYERS tokens from **anywhere in the world**:

✅ **No local scripts needed**  
✅ **Beautiful web interface**  
✅ **Automatic Render environment variable updates**  
✅ **Works from any device (phone, tablet, laptop)**  
✅ **One-click token generation and renewal**

---

## 🎯 How It Works

```
You (anywhere) → Visit https://your-app.onrender.com/token-manager
                      ↓
                Click "Generate Tokens"
                      ↓
                Login to FYERS
                      ↓
                Tokens auto-generated
                      ↓
                Render env vars auto-updated
                      ↓
                Restart service
                      ↓
                ✅ Done! Trading engine ready
```

---

## 🚀 Setup (One-Time Configuration)

### Step 1: Get Render API Key

To enable automatic environment variable updates, you need a Render API key:

1. **Login to Render**: https://dashboard.render.com
2. **Go to Account Settings**: Click your profile → Account Settings
3. **API Keys**: Scroll down to "API Keys" section
4. **Create New Key**: 
   - Name: `Token Manager`
   - Click "Create API Key"
5. **Copy the key**: Save it securely (you'll need it next)

### Step 2: Get Render Service ID

1. **Go to your service**: https://dashboard.render.com (click your trading-engine-api service)
2. **Copy Service ID**: Look at the URL:
   ```
   https://dashboard.render.com/web/srv-XXXXXXXXXXXXX
                                       ↑
                                  This is your Service ID
   ```
   Example: `srv-abc123def456`

### Step 3: Add to Render Environment Variables

Go to Render Dashboard → Your Service → Environment:

Add these **two new variables**:

```env
RENDER_API_KEY=<paste_your_api_key_here>
RENDER_SERVICE_ID=srv-<your_service_id_here>
```

Example:
```env
RENDER_API_KEY=rnd_abcdef123456789
RENDER_SERVICE_ID=srv-abc123def456
```

### Step 4: Deploy the Code

```bash
# Commit and push the changes
git add .
git commit -m "feat: add online FYERS token manager with auto-update"
git push origin main

# Render will auto-deploy
```

---

## 🎨 Using the Token Manager

### Access the Web Interface

Visit: `https://your-app.onrender.com/token-manager`

Replace `your-app` with your actual Render URL.

### Generate Tokens (3 Easy Steps)

#### 1. Select Mode
- Click **"Sandbox"** for paper trading (recommended first)
- OR click **"Live"** for real trading (after testing)

#### 2. Click "Generate FYERS Tokens"
- You'll be redirected to FYERS login page
- Login with your FYERS credentials
- Authorize the application

#### 3. Automatic Processing
- ✅ Tokens automatically generated
- ✅ Render environment variables automatically updated
- ✅ Success message displayed

#### 4. Restart Service
- Go to Render Dashboard
- Click "Manual Deploy" → "Clear build cache & deploy"
- OR click the restart button
- Done! Your engine now uses the new tokens

---

## 📱 Use From Anywhere

### Desktop
Visit: `https://your-app.onrender.com/token-manager`

### Mobile
1. Open browser on your phone
2. Visit: `https://your-app.onrender.com/token-manager`
3. Complete the flow
4. Works perfectly on mobile!

### Tablet
Same as desktop - fully responsive interface.

---

## 🔧 What Gets Updated Automatically

When you generate tokens through the web interface:

### Automatic Updates (if Render API configured):
```env
FYERS_ACCESS_TOKEN=<new_access_token>    ← Auto-updated
FYERS_REFRESH_TOKEN=<new_refresh_token>  ← Auto-updated
```

### Manual Fallback (if Render API not configured):
- Page will show the tokens
- Copy and paste manually into Render dashboard
- Still easier than local scripts!

---

## 🎯 Monthly Token Renewal Process

Every 30 days when refresh token expires:

### From Desktop:
1. Visit `https://your-app.onrender.com/token-manager`
2. Click "Generate FYERS Tokens"
3. Login and authorize
4. Restart Render service
5. Done! (2 minutes total)

### From Mobile (on vacation):
1. Open browser on phone
2. Visit the token manager URL
3. Same 3-step process
4. Done! You can manage from the beach! 🏖️

---

## 🛡️ Security Notes

### Render API Key Security
- ✅ Stored as environment variable (secure)
- ✅ Never exposed to frontend
- ✅ Only backend can use it
- ✅ Can be revoked anytime in Render dashboard

### Token Security
- ✅ Tokens transmitted over HTTPS only
- ✅ Not stored in browser
- ✅ Automatically updated in secure Render environment
- ✅ Auto-refresh system keeps tokens fresh

### Best Practices
- 🔒 Keep Render API key private
- 🔒 Don't share your token manager URL publicly
- 🔒 Use strong FYERS password
- 🔒 Enable 2FA on FYERS account

---

## 🐛 Troubleshooting

### Issue: "Automatic update failed"

**Cause**: Render API key or Service ID not configured

**Solution**:
1. Check env vars: `RENDER_API_KEY` and `RENDER_SERVICE_ID`
2. Verify API key is correct (no typos)
3. Verify Service ID matches your service
4. If still failing, tokens will be displayed for manual copy

### Issue: "Token exchange failed"

**Cause**: Invalid auth_code or expired

**Solution**:
1. Try the flow again (auth codes expire in 30 seconds)
2. Make sure you're using correct mode (sandbox vs live)
3. Verify FYERS credentials are correct

### Issue: Page not loading

**Cause**: Template file missing

**Solution**:
1. Ensure you deployed all files
2. Check `src/api/templates/token_manager.html` exists
3. Redeploy if needed

---

## 📊 Monitoring

### Check Auto-Update Status

After generating tokens, check Render logs:

```
✅ Successfully received both tokens from FYERS
✅ Updated FYERS_ACCESS_TOKEN on Render
✅ Updated FYERS_REFRESH_TOKEN on Render
```

### Verify Environment Variables

Go to Render Dashboard → Environment:
- Look for `FYERS_ACCESS_TOKEN` - should be updated
- Look for `FYERS_REFRESH_TOKEN` - should be updated
- Check timestamp to confirm it's recent

---

## 🎉 Benefits of This Solution

### vs Local Scripts:
- ✅ No Python installation needed
- ✅ Works from any device
- ✅ No file downloads
- ✅ No terminal/command line

### vs Manual Process:
- ✅ Auto-updates environment variables
- ✅ Beautiful user interface
- ✅ Clear status messages
- ✅ Less error-prone

### vs FYERS Dashboard:
- ✅ Integrated with your app
- ✅ One-click deployment
- ✅ Automatic variable updates
- ✅ Mobile-friendly

---

## 🔄 Complete Monthly Workflow

**Every 30 days** (or when refresh token expires):

1. **Get notification** (check logs or set calendar reminder)
2. **Open browser** (desktop or mobile)
3. **Visit**: `https://your-app.onrender.com/token-manager`
4. **Select mode**: Sandbox or Live
5. **Click**: "Generate FYERS Tokens"
6. **Login**: FYERS credentials
7. **Authorize**: Grant permissions
8. **Wait**: Automatic updates happen
9. **Restart**: Click restart in Render dashboard
10. **Done**: Back to autonomous operation!

**Total time**: 2-3 minutes  
**From anywhere**: Beach, office, home, travel  
**Any device**: Phone, laptop, tablet

---

## 📱 QR Code Access (Optional)

Generate a QR code for your token manager URL for easy mobile access:

1. Visit: https://www.qr-code-generator.com
2. Enter: `https://your-app.onrender.com/token-manager`
3. Generate QR code
4. Save to phone
5. Scan anytime you need to renew tokens!

---

## ✅ Setup Checklist

- [ ] Step 1: Created Render API key
- [ ] Step 2: Got Render Service ID
- [ ] Step 3: Added both to environment variables
- [ ] Step 4: Deployed code to Render
- [ ] Step 5: Visited `/token-manager` and tested
- [ ] Step 6: Generated sandbox tokens successfully
- [ ] Step 7: Verified auto-update worked
- [ ] Step 8: Restarted service
- [ ] Step 9: Confirmed engine uses new tokens
- [ ] Step 10: Bookmarked URL for future use

---

## 🎯 Next Steps

### Now:
1. Complete the setup checklist above
2. Test token generation in sandbox mode
3. Bookmark the token manager URL

### Monthly:
1. Visit token manager when refresh token expires
2. Generate new tokens (2 minutes)
3. Restart service
4. Continue autonomous trading!

---

## 🌟 Pro Tips

### Tip 1: Bookmark the URL
Save `https://your-app.onrender.com/token-manager` in your browser for quick access.

### Tip 2: Set Calendar Reminder
Add recurring reminder: "Renew FYERS tokens" every 28 days (2 days before expiry).

### Tip 3: Test in Sandbox First
Always test new features in sandbox mode before going live.

### Tip 4: Keep API Key Secure
Store Render API key in password manager, don't share it.

### Tip 5: Mobile Home Screen
Add token manager to phone home screen for instant access.

---

## 📞 Support

### If automatic update fails:
- Tokens will be displayed on screen
- Copy manually to Render dashboard
- Still faster than local scripts!

### If you lose Render API key:
- Go to Render account settings
- Revoke old key
- Create new key
- Update in environment variables

---

**🎉 Congratulations! You now have a fully online, mobile-friendly token manager that works from anywhere in the world!**

No more local scripts, no more terminal commands - just visit a webpage and renew your tokens! 🚀

---

**Last Updated**: 2025-10-21  
**Version**: 2.0.0 with Online Token Manager  
**Status**: ✅ Production Ready
