# MongoDB Atlas Setup for AuraQuant Trading System

## ✅ Connection Status
MongoDB Atlas is successfully configured and connected!

## Connection Details
- **Cluster**: cluster0.qcg7f4h.mongodb.net
- **Database**: auraquant
- **Username**: auraquant
- **Password**: Zeke29@72@22 (contains special characters)

## Environment Configuration

### 1. Environment Variables (.env file)
The following environment variables are configured in your `.env` file:
```
MONGO_URI=mongodb+srv://auraquant:Zeke29@72@22@cluster0.qcg7f4h.mongodb.net/?retryWrites=true&w=majority
MONGODB_URI=mongodb+srv://auraquant:Zeke29@72@22@cluster0.qcg7f4h.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=auraquant
```

### 2. Security Configuration
- **`.gitignore`**: Created to prevent `.env` file from being committed to version control
- **Password Encoding**: Special characters in the password are automatically handled by the database configuration

## Available Databases
Your MongoDB Atlas cluster currently has the following databases:
- `auraquant` (main application database)
- `sample_mflix` (MongoDB sample database)
- `admin` (system database)
- `local` (system database)

## Collections Structure
The application expects the following collections in the `auraquant` database:
- `users` - User authentication and profiles
- `trades` - Trading history and transactions
- `patterns` - Market patterns detected by the AI
- `strategies` - Trading strategies configuration
- `brain_states` - Quantum brain AI states
- `market_data` - Historical market data
- `portfolio` - User portfolio information

## Testing the Connection

### Quick Test
```bash
py -c "from config.database import test_connection; test_connection()"
```

### Detailed Test
```bash
py test_mongo_connection.py
```

## Required Python Packages
The following packages are installed and required:
- `pymongo` - MongoDB driver for Python
- `motor` - Async MongoDB driver
- `python-dotenv` - Environment variable management
- `dnspython` - Required for MongoDB+srv connections

## Important Notes

### 1. IP Whitelisting
Make sure your IP address is whitelisted in MongoDB Atlas:
1. Go to MongoDB Atlas Dashboard
2. Navigate to Network Access
3. Add your current IP or use 0.0.0.0/0 for development (not recommended for production)

### 2. User Permissions
The `auraquant` user should have read/write permissions on the `auraquant` database.

### 3. Connection String Format
Due to special characters in the password (@ symbols), the connection string requires proper URL encoding:
- Raw password: `Zeke29@72@22`
- Encoded: `Zeke29%4072%4022`

### 4. Local vs Cloud Detection
The system automatically detects whether to use MongoDB Atlas based on:
- Presence of `mongodb+srv` in the URI
- NODE_ENV environment variable (production = cloud)

## Troubleshooting

### Authentication Failed
- Verify username and password are correct
- Check IP address is whitelisted
- Ensure user has proper database permissions

### Connection Timeout
- Check internet connectivity
- Verify cluster address is correct
- Ensure firewall isn't blocking outbound connections

### Module Not Found
Install required packages:
```bash
py -m pip install pymongo motor python-dotenv dnspython
```

## Backup Recommendations
1. Enable automatic backups in MongoDB Atlas
2. Set up point-in-time recovery
3. Consider implementing local backup scripts for critical data

## Next Steps
1. ✅ MongoDB connection established
2. ✅ Environment variables configured
3. ✅ Security measures in place (.gitignore)
4. Ready to start the application with `py api/main.py` or `py run_api_no_reload.py`

---
*Last updated: 2025-01-30*
*Engineer: AuraQuant System Setup*