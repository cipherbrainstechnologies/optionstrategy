# ⚡ Quick Start: Online Token Manager

## 🎯 What You Asked For

You wanted to generate FYERS tokens **from anywhere in the world** and **automatically update Render environment variables**. 

**✅ Done!** I've created a fully online web-based solution.

---

## 🚀 Setup (5 Minutes)

### 1. Get Render API Credentials

**Get API Key**:
- Visit: https://dashboard.render.com/account
- Scroll to "API Keys"
- Click "Create API Key"
- Name: `Token Manager`
- Copy the key

**Get Service ID**:
- Go to your service: https://dashboard.render.com
- Look at URL: `https://dashboard.render.com/web/srv-XXXXX`
- Copy the `srv-XXXXX` part

### 2. Add to Render Environment Variables

Go to your Render service → Environment → Add:

```env
RENDER_API_KEY=rnd_your_api_key_here
RENDER_SERVICE_ID=srv_your_service_id_here
```

### 3. Deploy

```bash
git add .
git commit -m "feat: online token manager"
git push origin main
```

Render will auto-deploy in ~2 minutes.

---

## 🌍 Using It (Anywhere, Anytime)

### Desktop, Mobile, or Tablet:

1. **Visit**: `https://your-app.onrender.com/token-manager`

2. **Select Mode**:
   - Sandbox (paper trading) ← Start here
   - Live (real trading)

3. **Click**: "Generate FYERS Tokens"

4. **Login** to FYERS and authorize

5. **Done!** Tokens auto-generated and auto-updated in Render

6. **Restart** your Render service

---

## 🎉 What You Get

### ✅ Fully Online
- No Python scripts to run
- No terminal commands
- Works from ANY device

### ✅ Auto-Updates Render
- Tokens automatically sent to Render
- Environment variables auto-updated
- Just restart service to apply

### ✅ Beautiful Interface
- Modern, responsive design
- Clear instructions
- Status indicators
- Mobile-friendly

### ✅ Use Anywhere
- From your laptop
- From your phone
- From a tablet
- Even when traveling!

---

## 📱 Monthly Renewal (2 Minutes)

Every 30 days:

1. Open browser (desktop OR mobile)
2. Visit: `https://your-app.onrender.com/token-manager`
3. Click "Generate Tokens"
4. Login to FYERS
5. Restart Render service
6. Done!

**That's it!** No scripts, no commands, no hassle.

---

## 🔄 Complete Flow

```
┌─────────────────────────────────────────┐
│  You (anywhere in the world)            │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Visit: /token-manager                  │
│  Click: "Generate Tokens"               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  FYERS Login Page                       │
│  (You authorize the app)                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Backend:                               │
│  ✓ Exchanges auth_code for tokens      │
│  ✓ Calls Render API                    │
│  ✓ Updates environment variables       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Success Page:                          │
│  ✓ Shows tokens                         │
│  ✓ Confirms auto-update                │
│  ✓ Shows restart instructions          │
└─────────────────────────────────────────┘
```

---

## 🎯 Files Created

### Backend:
- `src/api/token_manager.py` - Token generation & Render API integration
- `src/api/server.py` - Updated callback endpoint
- `src/api/templates/token_manager.html` - Beautiful web interface

### Documentation:
- `ONLINE_TOKEN_MANAGER_SETUP.md` - Complete setup guide
- `QUICK_START_ONLINE_TOKENS.md` - This file (quick reference)

---

## ✅ Setup Checklist

- [ ] Get Render API key
- [ ] Get Render Service ID  
- [ ] Add both to environment variables
- [ ] Push code to main branch
- [ ] Wait for Render deployment
- [ ] Visit `/token-manager` to test
- [ ] Generate sandbox tokens
- [ ] Verify auto-update worked
- [ ] Bookmark the URL

---

## 📖 Full Documentation

For detailed information, see: `ONLINE_TOKEN_MANAGER_SETUP.md`

---

## 🎊 That's It!

You can now:
- ✅ Generate tokens from anywhere
- ✅ Update Render automatically
- ✅ Use any device (phone, laptop, tablet)
- ✅ No scripts, no terminal, no hassle

**Bookmark this URL**: `https://your-app.onrender.com/token-manager`

Use it monthly when your refresh token expires!

---

**Questions? Check `ONLINE_TOKEN_MANAGER_SETUP.md` for troubleshooting and details.** 🚀
