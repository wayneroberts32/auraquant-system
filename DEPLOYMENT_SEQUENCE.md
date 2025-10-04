# 🚀 AURAQUANT COMPLETE DEPLOYMENT SEQUENCE

## ⚠️ IMPORTANT: Frontend Does NOT Auto-Sync!

The frontend and backend must be deployed separately and then linked together.

---

## 📋 DEPLOYMENT SEQUENCE (2 Steps)

### STEP 1: Deploy Backend to Render ✅
**Status: READY TO DEPLOY**

1. Go to: https://dashboard.render.com
2. Create New → Web Service
3. Select: `wayneroberts32/auraquant-system`
4. Configure:
   - Name: `auraquant-backend`
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python backend/system/system_integration.py`
   - Port: `10000` (already configured)
5. Add Environment Variables:
   ```
   MONGODB_URI = mongodb+srv://auraquantdigital:YNa8J5qGu3vswHQ1@cluster0.csjay.mongodb.net/auraquant?retryWrites=true&w=majority
   PORT = 10000
   PYTHON_VERSION = 3.10
   ```
6. Click "Create Web Service"
7. **WAIT for deployment to complete (5-10 minutes)**
8. **COPY YOUR BACKEND URL** (e.g., `https://auraquant-backend.onrender.com`)

---

### STEP 2: Deploy Frontend to Cloudflare 🔗
**Status: REQUIRES BACKEND URL**

After backend is deployed and running:

**Option A: Use the automated script (Recommended)**
```powershell
# Run this command with your backend URL
powershell -ExecutionPolicy Bypass -File "Scripts\deploy_frontend_cloudflare.ps1" -BackendURL "https://auraquant-backend.onrender.com"
```

**Option B: Manual deployment**
1. Update `frontend/.env.production`:
   ```
   VITE_API_URL=https://auraquant-backend.onrender.com
   REACT_APP_API_URL=https://auraquant-backend.onrender.com
   ```

2. Deploy to Cloudflare:
   ```bash
   cd frontend
   npx wrangler pages deploy . --project-name auraquant-frontend
   ```

---

## 🔗 HOW THE LINKING WORKS

### Current Frontend Configuration:
The frontend has **dynamic API detection** in `frontend/js/config.js`:

```javascript
// Checks in order:
1. Environment variable (API_URL) - Set during Cloudflare deployment
2. URL parameter (?api=...) - For testing
3. localStorage - Saved preference
4. Default to localhost:8000 - For local development
```

### After Deployment:
- **Backend URL:** `https://auraquant-backend.onrender.com`
- **Frontend URL:** `https://auraquant-frontend.pages.dev`
- **API Connection:** Frontend → Backend via HTTPS
- **WebSocket:** Frontend → Backend via WSS

---

## ✅ VERIFICATION CHECKLIST

After both deployments:

1. **Test Backend:**
   ```
   https://auraquant-backend.onrender.com/health
   ```
   Should return: `{"status": "healthy"}`

2. **Test Frontend:**
   ```
   https://auraquant-frontend.pages.dev
   ```
   - Open browser console (F12)
   - Should see: "✅ Backend connection successful"

3. **Check Data Flow:**
   - Login screen should appear
   - Trading dashboard should load
   - Real-time data should stream

---

## 🛠️ TROUBLESHOOTING

### If Frontend Can't Connect to Backend:

1. **Check CORS settings** in backend
2. **Verify backend URL** is correct
3. **Clear browser cache** and reload
4. **Check browser console** for errors

### Quick Fix:
In browser console, manually set backend:
```javascript
window.AuraQuantConfig.setApiUrl('https://auraquant-backend.onrender.com');
location.reload();
```

---

## 📊 SYSTEM STATUS

```
✅ Backend: Ready to deploy (Port 10000)
✅ Frontend: Configured for dynamic API
✅ MongoDB: Atlas Cluster0 connected
✅ Files: 309,684+ intact (NO REBUILD)
⏳ Linking: Requires manual configuration
```

---

## 🎯 SUMMARY

**NO, the frontend does NOT automatically link to the backend.**

You must:
1. Deploy backend first → Get URL
2. Configure frontend with backend URL
3. Deploy frontend to Cloudflare

The system is designed this way for:
- **Security:** No hardcoded production URLs
- **Flexibility:** Can change backends easily
- **Testing:** Can point to different environments

**Total deployment time: ~15-20 minutes**