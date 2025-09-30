# 🚀 AuraQuant Deployment - EXECUTE NOW

## ⚠️ CRITICAL: Complete These Steps in Order

---

## STEP 1: BACKUP OLD BOT ENVIRONMENT VARIABLES ⚡

### 1A. Backup Render Environment Variables
1. Open: https://dashboard.render.com
2. Login to your account
3. Find your OLD bot service
4. Click on it → Go to "Environment" tab
5. **COPY AND SAVE** all environment variables to a text file:
   - MONGODB_URI
   - Any API keys
   - Any secret keys
   
### 1B. Backup Cloudflare Environment Variables  
1. Open: https://dash.cloudflare.com
2. Go to "Workers & Pages" → Pages
3. Find your OLD bot project
4. Click Settings → Environment Variables
5. **COPY AND SAVE** all variables

---

## STEP 2: DELETE OLD BOT 🗑️

### 2A. Remove from Render
1. In Render dashboard, select your OLD bot service
2. Go to Settings tab
3. Scroll to bottom → Click "Delete Service"
4. Type service name to confirm
5. Click "Delete Service"

### 2B. Remove from Cloudflare Pages
1. In Cloudflare dashboard → Workers & Pages
2. Select your OLD bot project
3. Go to Settings
4. Click "Delete Project"
5. Confirm deletion

---

## STEP 3: PUSH CODE TO GITHUB 📤

### 3A. Create GitHub Repository
1. Go to: https://github.com/new
2. Repository name: `auraquant-system`
3. Set as **Private**
4. Do NOT initialize with README
5. Click "Create repository"

### 3B. Push Your Code
Copy and run these commands in PowerShell:

```powershell
# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/auraquant-system.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**If you get authentication error:**
1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate new token (classic)
3. Select scopes: repo (all)
4. Copy token
5. Use token as password when prompted

---

## STEP 4: DEPLOY BACKEND TO RENDER 🖥️

### 4A. Create Render Service
1. Go to: https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect GitHub account if not connected
4. Select your `auraquant-system` repository
5. Click "Connect"

### 4B. Configure Service
**Fill in these EXACT settings:**

- **Name:** `auraquant-backend`
- **Region:** Select closest to you
- **Branch:** `main`
- **Root Directory:** (leave blank)
- **Runtime:** `Python 3`
- **Build Command:** 
  ```
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```
  python start_system.py
  ```
- **Instance Type:** Select "Starter" ($7/month)

### 4C. Add Environment Variables
Click "Advanced" → Add Environment Variables:

```
MONGODB_URI=mongodb+srv://YOUR_MONGODB_CONNECTION_STRING
PORT=10000
PYTHON_VERSION=3.10
```

**Plus all your backed-up variables from Step 1A**

### 4D. Create Service
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Check Logs tab for any errors

---

## STEP 5: DEPLOY FRONTEND TO CLOUDFLARE 🌐

### 5A. Create Cloudflare Pages Project
1. Go to: https://dash.cloudflare.com
2. Go to "Workers & Pages" → Pages
3. Click "Create a project"
4. Connect to Git → Authorize GitHub
5. Select `auraquant-system` repository

### 5B. Configure Build
**Set these EXACT settings:**

- **Project name:** `auraquant-frontend`
- **Production branch:** `main`
- **Framework preset:** `Create React App`
- **Build command:**
  ```
  cd frontend && npm install && npm run build
  ```
- **Build output directory:**
  ```
  frontend/build
  ```
- **Root directory:**
  ```
  /
  ```

### 5C. Add Environment Variables
Add variable:
```
REACT_APP_API_URL=https://auraquant-backend.onrender.com
```

**Plus any backed-up variables from Step 1B**

### 5D. Deploy
1. Click "Save and Deploy"
2. Wait for build (3-5 minutes)
3. Note your deployment URL (e.g., auraquant-frontend.pages.dev)

---

## STEP 6: VERIFY DEPLOYMENT ✅

### 6A. Check Backend
Open in browser or PowerShell:
```powershell
# Check health
Invoke-WebRequest -Uri "https://auraquant-backend.onrender.com/health" | Select-Object -ExpandProperty Content

# Check swarm status
Invoke-WebRequest -Uri "https://auraquant-backend.onrender.com/api/swarm/status" | Select-Object -ExpandProperty Content
```

### 6B. Check Frontend
1. Open: https://auraquant-frontend.pages.dev
2. Should see login screen with logo
3. Check browser console (F12) for any errors

### 6C. Test Emergency Kill Switch
```powershell
# Test kill switch (BE CAREFUL - this will stop trading)
$body = @{reason="Test activation"} | ConvertTo-Json
Invoke-WebRequest -Method Post -Uri "https://auraquant-backend.onrender.com/api/emergency/killswitch" -Body $body -ContentType "application/json"
```

---

## STEP 7: CONFIGURE CUSTOM DOMAIN (Optional) 🌍

### For Frontend (Cloudflare)
1. In Cloudflare Pages → your project → Custom domains
2. Add your domain (e.g., ai-auraquant.com)
3. Follow DNS configuration instructions

### Update Backend URL in Frontend
1. Go to Cloudflare Pages → Settings → Environment variables
2. Update `REACT_APP_API_URL` to use HTTPS

---

## 🚨 TROUBLESHOOTING

### If Render deployment fails:
- Check Logs tab for errors
- Ensure Python version is 3.10
- Verify all environment variables are set
- Check MongoDB connection string is correct

### If Cloudflare deployment fails:
- Check build logs
- Ensure frontend/package.json exists
- Verify React app builds locally first

### If Frontend can't connect to Backend:
- Check CORS settings in backend
- Ensure REACT_APP_API_URL is correct
- Check if backend is running (health endpoint)

---

## ✅ SUCCESS CHECKLIST

Complete? | Task
---------|------
⬜ | Old bot environment variables backed up
⬜ | Old bot removed from Render
⬜ | Old bot removed from Cloudflare
⬜ | Code pushed to GitHub
⬜ | Backend deployed to Render
⬜ | Frontend deployed to Cloudflare
⬜ | Backend health check passes
⬜ | Swarm shows 13 agents
⬜ | Frontend login page loads
⬜ | No console errors
⬜ | Kill switch tested

---

## 📞 FINAL NOTES

- **System is now LIVE** - Be careful with any changes
- **Monitor costs** - Check Render and Cloudflare billing
- **Keep secrets safe** - Never commit .env files
- **Regular backups** - Export MongoDB data weekly

---

**DEPLOYMENT DATE:** 2025-01-30
**SYSTEM:** AuraQuant Multi-Agent Swarm v1.0
**STATUS:** READY FOR PRODUCTION

---

## Need Help?

If you encounter issues:
1. Check the logs in Render/Cloudflare dashboards
2. Verify all environment variables are set correctly
3. Ensure MongoDB is accessible from Render
4. Check that all required files are in the repository