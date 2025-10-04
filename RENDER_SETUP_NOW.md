# 🚀 RENDER BACKEND SETUP - DO THIS NOW!

## Step 1: Click "Deploy a Web Service" in Render

## Step 2: Connect Your GitHub
1. Select **"Build and deploy from a Git repository"**
2. Click **"Connect GitHub"**
3. Authorize Render to access your GitHub
4. Search for: **auraquant-system**
5. Select your repository

## Step 3: Configure Your Service
Fill in these EXACT settings:

**Name**: `auraquant-api`

**Region**: Select closest to you

**Branch**: `cloudflare-production`

**Runtime**: `Python 3`

**Build Command**:
```
pip install -r requirements.txt
```

**Start Command**:
```
cd backend && python main.py
```

## Step 4: Environment Variables
Click "Advanced" and add these:

```
MONGODB_URI=mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/auraquant_production?retryWrites=true&w=majority
PORT=8000
NODE_ENV=production
SECRET_KEY=xz05NToBe3GdVwsQOFYE89vHDZKI4Apq
JWT_SECRET=iPHVMkpe14mljBKJEhU5L3G7yCcAzdru
CORS_ORIGIN=https://e4cd0ae1.auraquant.pages.dev,https://b0c81dec.auraquant-mobile.pages.dev
PYTHON_VERSION=3.11
```

## Step 5: Deploy
1. Select **Free** instance type
2. Click **"Create Web Service"**
3. Wait 5-10 minutes for deployment

## Your Backend URL Will Be:
```
https://auraquant-api.onrender.com
```

---

# AFTER BACKEND IS DEPLOYED, DO THIS:

## Connect Frontend to Backend:
Once your backend is live, we need to update the frontend to point to it.