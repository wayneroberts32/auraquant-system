"""
AuraQuant Backend Configuration
Central configuration file for all backend services
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

class Config:
    """Main configuration class"""
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv(
        'MONGODB_URI',
        'mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/?retryWrites=true&w=majority'
    )
    MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'auraquant')
    
    # Alternative MongoDB URI (for backward compatibility)
    MONGO_URI = os.getenv(
        'MONGO_URI',
        'mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/?retryWrites=true&w=majority'
    )
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'auraquant-secret-key-2025')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    # API Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    NODE_ENV = os.getenv('NODE_ENV', 'development')
    DEBUG = NODE_ENV == 'development'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5000,http://127.0.0.1:5500,file://'
    ).split(',')
    
    # Admin Configuration
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'wayneroberts32@outlook.com.au')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # Trading Configuration
    STRATEGY_CONFIDENCE_MIN = float(os.getenv('STRATEGY_CONFIDENCE_MIN', '0.6'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '10000'))
    RISK_TOLERANCE = float(os.getenv('RISK_TOLERANCE', '0.05'))
    
    # File Paths
    MEMORY_PATH = os.getenv(
        'MEMORY_PATH',
        'D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\backend\\Memory'
    )
    DASHBOARD_PATH = os.getenv(
        'DASHBOARD_PATH',
        'D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\frontend\\pages\\main-trading-dashboard.html'
    )
    
    # Alert System Configuration (for multi-channel notifications)
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Discord
    DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')
    
    # Email (SMTP)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL = os.getenv('SMTP_FROM_EMAIL', 'alerts@auraquant.com')
    
    # SMS (Twilio)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '')
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', '60'))  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'backend/logs/auraquant.log')
    
    @classmethod
    def get_mongodb_uri(cls):
        """Get MongoDB URI with proper encoding"""
        return cls.MONGODB_URI
    
    @classmethod
    def get_database_name(cls):
        """Get MongoDB database name"""
        return cls.MONGODB_DATABASE
    
    @classmethod
    def validate_config(cls):
        """Validate critical configuration"""
        errors = []
        
        if not cls.MONGODB_URI:
            errors.append("MongoDB URI is not configured")
        
        if not cls.JWT_SECRET_KEY or cls.JWT_SECRET_KEY == 'auraquant-secret-key-2025':
            errors.append("JWT_SECRET_KEY should be changed for production")
        
        if cls.NODE_ENV == 'production' and cls.DEBUG:
            errors.append("DEBUG should be False in production")
        
        if errors:
            for error in errors:
                print(f"Configuration Warning: {error}")
        
        return len(errors) == 0

# Create config instance
config = Config()

# Validate configuration on import
if __name__ == "__main__":
    if config.validate_config():
        print("✅ Configuration validated successfully")
        print(f"📦 MongoDB URI: {config.MONGODB_URI[:50]}...")
        print(f"📦 Database: {config.MONGODB_DATABASE}")
        print(f"🔐 JWT configured: Yes")
        print(f"🌍 Environment: {config.NODE_ENV}")
        print(f"🚀 API Port: {config.API_PORT}")
    else:
        print("⚠️ Configuration has warnings. Please review above messages.")