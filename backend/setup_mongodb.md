# MongoDB Atlas Setup Guide for AuraQuant

## 🚀 Quick Setup

### Step 1: Create MongoDB Atlas Account
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign up for a free account (or login if you have one)
3. Create a new cluster (free tier is fine for testing)

### Step 2: Configure Database Access
1. In MongoDB Atlas dashboard, go to **Database Access**
2. Click **Add New Database User**
3. Choose **Password** authentication
4. Set username and password (remember these!)
5. Set **Database User Privileges** to "Read and write to any database"
6. Click **Add User**

### Step 3: Configure Network Access
1. Go to **Network Access**
2. Click **Add IP Address**
3. For development, click **Allow Access from Anywhere** (0.0.0.0/0)
   - Note: For production, use specific IP addresses
4. Click **Confirm**

### Step 4: Get Connection String
1. Go to **Database** → **Connect**
2. Choose **Connect your application**
3. Select **Driver**: Python, **Version**: 3.6 or later
4. Copy the connection string
   - It looks like: `mongodb+srv://username:<password>@cluster.mongodb.net/`

### Step 5: Configure AuraQuant
1. Create a `.env` file in the backend folder:
   ```bash
   cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"
   copy .env.example .env
   ```

2. Edit the `.env` file and add your MongoDB connection:
   ```
   MONGODB_URI=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
   ```
   Replace:
   - `YOUR_USERNAME` with your database username
   - `YOUR_PASSWORD` with your database password
   - `YOUR_CLUSTER` with your cluster name (e.g., cluster0.xxxxx)

## 🧪 Test Your Connection

Run the test script:
```powershell
cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"
python3.13t -c "from config.database import test_connection; test_connection()"
```

## 📊 MongoDB Atlas Features

### Collections Created
- `users` - User accounts and authentication
- `trades` - Trade history and execution logs
- `patterns` - Detected market patterns
- `strategies` - Trading strategies
- `brain_states` - Quantum Brain evolution states
- `market_data` - Market data cache
- `portfolio` - Portfolio holdings and performance

### Indexes
The system automatically creates optimized indexes for:
- User email (unique)
- Trade timestamps and symbols
- Pattern types and timestamps
- Strategy names (unique)
- Brain generation numbers

## 🔒 Security Notes

1. **Never commit `.env` file to git**
   - Add `.env` to your `.gitignore`
   
2. **Use environment-specific connection strings**
   - Development: Can use "Allow from Anywhere"
   - Production: Use specific IP whitelist
   
3. **Rotate credentials regularly**
   - Change passwords periodically
   - Use different credentials for dev/prod

## 🛠️ Troubleshooting

### Connection Timeout
- Check Network Access settings in Atlas
- Ensure your IP is whitelisted
- Check firewall settings

### Authentication Failed
- Verify username and password
- Check database user permissions
- Ensure password is URL-encoded if it contains special characters

### SSL/TLS Errors
- Make sure you're using the `mongodb+srv://` protocol
- Update pymongo: `pip install --upgrade pymongo`

## 📝 Example .env Configuration

```env
# MongoDB Atlas (Production)
MONGODB_URI=mongodb+srv://auraquant_user:SecurePass123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=auraquant

# Or for local development (if running MongoDB locally)
# MONGODB_URI=mongodb://localhost:27017
# MONGODB_DATABASE=auraquant_dev

# Other settings
JWT_SECRET_KEY=your-secret-key-here
API_PORT=8000
NODE_ENV=development
```

## 🎯 Next Steps

After setting up MongoDB:

1. Run the backend API:
   ```powershell
   cd "D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\backend"
   python api/main.py
   ```

2. Test API endpoints:
   - http://localhost:8000/docs - API documentation
   - http://localhost:8000/health - Health check

3. Connect frontend:
   - Update frontend to use http://localhost:8000/api

Need help? Check the logs in the terminal or MongoDB Atlas monitoring dashboard.