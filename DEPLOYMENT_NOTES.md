# AuraQuant Deployment Notes

## Quick Start Deployment Guide

### Prerequisites
- Node.js 16+ installed
- MongoDB 5.0+ running
- Git installed
- PM2 (optional, for production)

---

## 🚀 Deployment Steps

### 1. Environment Configuration

Create `.env` file in `auraquant-backend/` with:

```env
# Server Configuration
PORT=5000
NODE_ENV=production

# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/auraquant?retryWrites=true&w=majority

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this
JWT_EXPIRE=7d

# API Keys (Add as needed)
ALPHA_VANTAGE_API_KEY=your-key-here
IEX_CLOUD_API_KEY=your-key-here
TRADINGVIEW_API_KEY=your-key-here

# Broker APIs (Optional)
IB_CLIENT_ID=your-client-id
IB_CLIENT_SECRET=your-client-secret
ALPACA_KEY_ID=your-key-id
ALPACA_SECRET_KEY=your-secret-key

# AI Workers (Optional)
OPENAI_API_KEY=your-openai-key
CLAUDE_API_KEY=your-claude-key

# WebSocket
WS_PORT=5000
WS_CORS_ORIGIN=*

# Rate Limiting
RATE_LIMIT_WINDOW=15
RATE_LIMIT_MAX=100
```

### 2. Install Dependencies

```bash
# Backend dependencies
cd auraquant-backend
npm install

# Install missing packages if needed
npm install axios colors ws mongodb
```

### 3. Database Setup

```bash
# Connect to MongoDB and create indexes
mongo auraquant --eval "
db.users.createIndex({ email: 1 }, { unique: true });
db.trades.createIndex({ timestamp: -1 });
db.strategies.createIndex({ userId: 1, name: 1 });
"
```

### 4. Start Backend Server

#### Development Mode
```bash
cd auraquant-backend
npm run dev
# or
node server.js
```

#### Production Mode (with PM2)
```bash
# Install PM2 globally
npm install -g pm2

# Start with PM2
pm2 start server.js --name auraquant-backend
pm2 save
pm2 startup
```

### 5. Serve Frontend

#### Development Mode
```bash
cd frontend
# Using Python
python -m http.server 3000

# Or using Node.js http-server
npx http-server -p 3000
```

#### Production Mode (Nginx example)
```nginx
server {
    listen 80;
    server_name auraquant.yourdomain.com;
    
    root /var/www/auraquant/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /ws {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 6. Run QA/QC Checks

```bash
# From project root
node qa-qc-check.js
```

Expected output:
```
✅ All critical checks passed!
🎉 SYSTEM READY FOR DEPLOYMENT
```

---

## 🔧 Configuration Details

### Backend Routes Registration

Ensure `server.js` includes the new features routes:

```javascript
// Add to server.js or app.js
const featuresRouter = require('./routes/features');
app.use('/api', featuresRouter);

// WebSocket setup
const WebSocketHandler = require('./services/websocket-handler');
const wsHandler = new WebSocketHandler(io);
```

### Frontend Access Points

Main entry: `http://localhost:3000/frontend/pages/main-trading-dashboard.html`

All features accessible via the menu button (☰) in left sidebar.

### Admin Access

Set user role to 'admin' in MongoDB:
```javascript
db.users.updateOne(
  { email: "admin@auraquant.com" },
  { $set: { role: "admin" } }
)
```

Admin-only pages:
- Bot Status
- Deployment Verification
- Performance Monitor
- Unified Dashboard

---

## 📊 Monitoring

### Health Check Endpoints

- System Status: `GET /api/deployment/verify`
- WebSocket Health: Connect to `ws://localhost:5000`
- Database Health: `GET /api/health/db`

### Logs

```bash
# View PM2 logs
pm2 logs auraquant-backend

# View error logs
pm2 logs auraquant-backend --err
```

---

## 🚨 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if port 5000 is open
   - Verify CORS settings in backend
   - Ensure socket.io is installed

2. **MongoDB Connection Error**
   - Verify connection string in .env
   - Check network access in MongoDB Atlas
   - Ensure database user has proper permissions

3. **Frontend 404 Errors**
   - Verify file paths are correct
   - Check that workspace-manager.js is loaded
   - Ensure Logo folder exists with images

4. **Admin Features Not Accessible**
   - Check user role in database
   - Verify JWT token includes role claim
   - Check browser localStorage for auth token

---

## 🌐 Cloud Deployment

### Render.com Deployment

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `cd auraquant-backend && npm install`
4. Set start command: `cd auraquant-backend && node server.js`
5. Add environment variables from .env
6. Deploy

### Cloudflare Pages (Frontend)

1. Connect GitHub repository
2. Set build command: `echo "No build required"`
3. Set publish directory: `frontend`
4. Deploy

### MongoDB Atlas

1. Create free cluster
2. Add IP whitelist (0.0.0.0/0 for any)
3. Create database user
4. Get connection string
5. Update MONGODB_URI in .env

---

## ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] MongoDB connection tested
- [ ] Backend server running
- [ ] Frontend accessible
- [ ] WebSocket connection working
- [ ] Admin access verified
- [ ] QA/QC checks passed
- [ ] SSL certificates installed (production)
- [ ] Backup strategy in place
- [ ] Monitoring configured

---

## 📞 Support

For deployment issues:
1. Check qa-report.json for detailed diagnostics
2. Review server logs for errors
3. Verify all environment variables are set
4. Ensure all dependencies are installed

---

*Deployment Notes v2.1.0 - AuraQuant Trading System*