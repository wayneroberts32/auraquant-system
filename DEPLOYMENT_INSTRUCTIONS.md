# AuraQuant System Deployment Instructions

## 🚨 IMPORTANT: Cloud-Based System Only
This system is designed to run EXCLUSIVELY on cloud platforms (Render for backend, Cloudflare Pages for frontend).
**DO NOT RUN LOCALLY** - The system is configured for cloud deployment only.

---

## 📋 Pre-Deployment Checklist

### 1. Backup Environment Variables
Before removing the old bot, ensure you have saved all environment variables from both platforms:

**Render Environment Variables to Backup:**
- `MONGODB_URI`
- `API_KEYS` (for exchanges)
- `SECRET_KEYS`
- Any custom configurations

**Cloudflare Pages Environment Variables to Backup:**
- `REACT_APP_API_URL`
- Any frontend-specific configs

### 2. Remove Old Bot

#### Remove from Render:
1. Go to Render Dashboard (https://dashboard.render.com)
2. Select your old bot service
3. Go to Settings
4. **SAVE ALL ENVIRONMENT VARIABLES**
5. Click "Delete Service" at the bottom
6. Confirm deletion

#### Remove from Cloudflare Pages:
1. Go to Cloudflare Dashboard
2. Navigate to Pages
3. Select your old bot project
4. Go to Settings
5. **SAVE ALL ENVIRONMENT VARIABLES**
6. Click "Delete Project"
7. Confirm deletion

---

## 🚀 Deploy New AuraQuant System

### Backend Deployment (Render)

1. **Prepare Repository**
   ```bash
   git add .
   git commit -m "AuraQuant Multi-Agent Swarm System - Production Ready"
   git push origin main
   ```

2. **Create New Render Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your repository
   - Select branch: `main`

3. **Configure Service Settings**
   - **Name:** `auraquant-backend`
   - **Region:** Choose closest to your target market
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python start_system.py`
   - **Plan:** Starter ($7/month minimum for production)

4. **Add Environment Variables**
   Add all backed-up variables plus:
   ```
   MONGODB_URI=<your_mongodb_connection_string>
   PORT=10000
   PYTHON_VERSION=3.10
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Check logs for successful initialization

### Frontend Deployment (Cloudflare Pages)

1. **Prepare Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to Cloudflare Pages**
   - Go to Cloudflare Dashboard → Pages
   - Click "Create a project"
   - Connect to Git
   - Select your repository

3. **Configure Build Settings**
   - **Framework preset:** Create React App
   - **Build command:** `npm run build`
   - **Build output directory:** `build`
   - **Root directory:** `frontend`

4. **Add Environment Variables**
   ```
   REACT_APP_API_URL=https://auraquant-backend.onrender.com
   ```

5. **Deploy**
   - Click "Save and Deploy"
   - Wait for deployment

---

## 🔍 Post-Deployment Verification

### 1. Check Backend Health
```bash
curl https://auraquant-backend.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "system_health": "OPTIMAL"
}
```

### 2. Check Multi-Agent Swarm
```bash
curl https://auraquant-backend.onrender.com/api/swarm/status
```

Should show:
- 13 agents initialized
- Various agent types (INDICATOR, PATTERN, STRATEGY, etc.)
- All agents in IDLE or WORKING state

### 3. Check Frontend
- Navigate to: https://auraquant-frontend.pages.dev
- Verify login screen appears
- Check for company logo
- Ensure no overlays or obstructive elements

---

## 🛡️ Security Reminders

1. **NEVER expose API keys in code**
2. **Use environment variables for all secrets**
3. **Enable 2FA on all platform accounts**
4. **Regularly rotate API keys**
5. **Monitor usage and costs**

---

## 🆘 Emergency Procedures

### Kill Switch Activation
If needed, activate the emergency kill switch:

```bash
curl -X POST https://auraquant-backend.onrender.com/api/emergency/killswitch \
  -H "Content-Type: application/json" \
  -d '{"reason": "Emergency shutdown required"}'
```

### Quick Rollback
If issues occur:
1. Render: Use "Rollback" feature in dashboard
2. Cloudflare: Rollback to previous deployment

---

## 📊 Monitoring

### System Status Endpoints
- Health: `/health`
- Status: `/api/status`
- Markets: `/api/markets`
- Swarm Status: `/api/swarm/status`
- Agents: `/api/agents`

### Logs
- **Render:** Check "Logs" tab in service dashboard
- **Cloudflare:** Check "Functions" logs in Pages dashboard

---

## ✅ Success Criteria

The deployment is successful when:
1. ✅ Backend responds to health checks
2. ✅ Multi-agent swarm shows 13 active agents
3. ✅ MongoDB connection established
4. ✅ Frontend loads with login screen
5. ✅ No console errors in browser
6. ✅ Trading compliance framework active
7. ✅ Emergency kill switch functional

---

## 📝 Notes

- System is configured for ASX, Crypto (Spot/Futures), and Meme Coins
- Compliance framework includes global and market-specific rules
- Multi-agent swarm handles parallel processing
- All changes follow ADD-ONLY policy
- System includes branding and identity locks

---

## 🚨 DO NOT:
- Run the system locally
- Modify core architecture
- Remove safety features
- Disable compliance checks
- Use old/recycled code
- Deploy without testing kill switch

---

**Created:** 2025-01-30
**System:** AuraQuant - The Infinity Money Synthetic Intelligence System
**Status:** PRODUCTION-READY