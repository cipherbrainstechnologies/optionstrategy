# Deployment Guide

## Overview

This guide covers deploying the Institutional AI Trade Engine to free hosting platforms:

- **Frontend**: Vercel (Next.js)
- **Backend**: Render or Railway (FastAPI)
- **Database**: Neon (PostgreSQL)

## Prerequisites

1. GitHub repository with your code
2. Accounts on:
   - [Vercel](https://vercel.com) (free)
   - [Render](https://render.com) (free tier) or [Railway](https://railway.app) (free tier)
   - [Neon](https://neon.tech) (free tier)

## Step 1: Database Setup (Neon)

1. Create account at [Neon](https://neon.tech)
2. Create new PostgreSQL database
3. Copy the connection string (starts with `postgresql://`)
4. Save this for Step 2

## Step 2: Backend Deployment (Render)

### Option A: Render (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `trading-engine-api`
   - **Root Directory**: `institutional_ai_trade_engine`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.api.server:app --host 0.0.0.0 --port $PORT`

5. Add Environment Variables:
   ```
   BROKER=FYERS
   PORTFOLIO_CAPITAL=400000
   RISK_PCT_PER_TRADE=1.5
   FYERS_CLIENT_ID=your_client_id
   FYERS_SECRET_KEY=your_secret_key
   FYERS_ACCESS_TOKEN=your_access_token
   FYERS_REDIRECT_URI=https://your-backend-url.render.com/callback
   FYERS_SANDBOX=true
   DATABASE_URL=postgresql://your_neon_connection_string
   ```

6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Note your backend URL (e.g., `https://trading-engine-api.onrender.com`)

### Option B: Railway

1. Go to [Railway](https://railway.app)
2. Connect GitHub repository
3. Select `institutional_ai_trade_engine` folder
4. Railway auto-detects Python and uses `Procfile`
5. Add environment variables in Railway dashboard
6. Deploy

## Step 3: Frontend Deployment (Vercel)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Import Project"
3. Select your GitHub repository
4. Configure:
   - **Root Directory**: `web`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

5. Add Environment Variable:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.render.com
   ```

6. Click "Deploy"
7. Wait for deployment (2-3 minutes)
8. Note your frontend URL (e.g., `https://your-project.vercel.app`)

## Step 4: Post-Deployment Setup

### Database Migration

1. SSH into your backend service or use Render's shell
2. Run database initialization:
   ```bash
   python main.py --init
   ```

### Update Fyers OAuth

1. Go to [Fyers Developer Dashboard](https://myapi.fyers.in/dashboard/)
2. Update your app's redirect URI to: `https://your-backend-url.render.com/callback`
3. Generate new access token using the production URL

### Test Deployment

1. Visit your frontend URL
2. Check if API calls work (should show data from backend)
3. Test manual scan functionality

## Environment Variables Reference

### Backend (.env for Render/Railway)

```bash
# Broker Configuration
BROKER=FYERS
PORTFOLIO_CAPITAL=400000
RISK_PCT_PER_TRADE=1.5

# FYERS Credentials
FYERS_CLIENT_ID=your_client_id
FYERS_SECRET_KEY=your_secret_key
FYERS_ACCESS_TOKEN=your_access_token
FYERS_REDIRECT_URI=https://your-backend-url.render.com/callback
FYERS_SANDBOX=true

# Database
DATABASE_URL=postgresql://your_neon_connection_string

# Optional: Telegram Alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional: Google Sheets
GSHEETS_CREDENTIALS_JSON=your_credentials_json
GSHEETS_MASTER_SHEET=Institutional Portfolio Master Sheet
```

### Frontend (.env.local for Vercel)

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.render.com
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure `FRONTEND_URL` is set in backend environment variables
2. **Database Connection**: Check `DATABASE_URL` format (should start with `postgresql://`)
3. **Fyers Authentication**: Verify redirect URI matches production URL
4. **Build Failures**: Check Python version compatibility (use 3.11)

### Logs and Debugging

- **Render**: Check logs in dashboard under "Logs" tab
- **Railway**: Use Railway CLI or dashboard logs
- **Vercel**: Check function logs in dashboard

### Performance Optimization

1. **Database**: Use connection pooling (already configured)
2. **Caching**: Consider Redis for production
3. **CDN**: Vercel automatically provides CDN
4. **Monitoring**: Add health check endpoints

## Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Rotate Fyers tokens regularly
3. **HTTPS**: All platforms provide HTTPS by default
4. **Rate Limiting**: Consider adding rate limiting for production

## Scaling Considerations

### Free Tier Limits

- **Render**: 750 hours/month, sleeps after 15 min inactivity
- **Railway**: $5 credit monthly
- **Neon**: 0.5GB storage, 3 databases
- **Vercel**: 100GB bandwidth, unlimited static hosting

### Upgrade Path

1. **Render**: Upgrade to paid plan for always-on service
2. **Railway**: Add credits for more resources
3. **Neon**: Upgrade for more storage and connections
4. **Vercel**: Pro plan for advanced features

## Maintenance

### Regular Tasks

1. **Token Refresh**: 
   - **Automatic**: Daily at 08:45 IST (FYERS access token)
   - **Manual**: Once every 30 days (FYERS refresh token)
   - See [TOKEN_REFRESH_GUIDE.md](institutional_ai_trade_engine/TOKEN_REFRESH_GUIDE.md) for details
   
2. **Database Backup**: Neon provides automatic backups

3. **Monitoring**: 
   - Check service health regularly
   - Monitor daily token refresh logs
   - Alert on token refresh failures
   
4. **Updates**: Keep dependencies updated

### Backup Strategy

1. **Code**: GitHub provides version control
2. **Database**: Neon automatic backups
3. **Environment**: Document all environment variables
4. **Configuration**: Keep deployment configs in repository

## Support

- **Render**: [Documentation](https://render.com/docs)
- **Railway**: [Documentation](https://docs.railway.app)
- **Vercel**: [Documentation](https://vercel.com/docs)
- **Neon**: [Documentation](https://neon.tech/docs)

## Next Steps

After successful deployment:

1. Set up monitoring and alerts
2. Configure automated backups
3. Implement CI/CD pipeline
4. Add performance monitoring
5. Set up staging environment
