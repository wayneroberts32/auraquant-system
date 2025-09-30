"""
Fixed Database Configuration for AuraQuant Trading System
Handles MongoDB connection with proper error handling
"""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import MongoDB clients
HAS_PYMONGO = False
HAS_MOTOR = False

try:
    from pymongo import MongoClient
    HAS_PYMONGO = True
except ImportError:
    logger.warning("pymongo not installed - sync MongoDB not available")
    MongoClient = None

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    HAS_MOTOR = True
except ImportError:
    logger.warning("motor not installed - async MongoDB not available")
    AsyncIOMotorClient = None

class DatabaseConfig:
    """Database configuration with safe fallbacks"""
    
    def __init__(self):
        self.environment = os.getenv("NODE_ENV", "development")
        self.is_cloud = self.environment == "production"
        
        # Determine MongoDB URI
        if self.is_cloud:
            self.mongodb_uri = os.getenv("MONGODB_ATLAS_URI", os.getenv("MONGODB_URI", ""))
            print("🌩️ Using MongoDB Atlas (Cloud)")
        else:
            self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            print("🏠 Using Local MongoDB")
        
        self.database_name = os.getenv("MONGODB_DATABASE", "auraquant")
        
        # Initialize clients
        self.sync_client = None
        self.async_client = None
        self.sync_db = None
        self.async_db = None
        
        # Try to connect
        self._init_sync_client()
        self._init_async_client()
    
    def _init_sync_client(self):
        """Initialize synchronous MongoDB client"""
        if not HAS_PYMONGO or not self.mongodb_uri:
            return
        
        try:
            self.sync_client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            # Test connection
            self.sync_client.admin.command('ping')
            self.sync_db = self.sync_client[self.database_name]
            logger.info(f"✅ Connected to MongoDB: {self.database_name}")
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.sync_client = None
            self.sync_db = None
    
    def _init_async_client(self):
        """Initialize asynchronous MongoDB client"""
        if not HAS_MOTOR or not self.mongodb_uri:
            return
        
        try:
            self.async_client = AsyncIOMotorClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            self.async_db = self.async_client[self.database_name]
            logger.info(f"✅ Async MongoDB client created")
        except Exception as e:
            logger.error(f"❌ Async MongoDB connection failed: {e}")
            self.async_client = None
            self.async_db = None

class Collections:
    """Safe collection accessor that returns None if DB not available"""
    
    def __init__(self, db):
        self._db = db
    
    def __getattr__(self, name):
        """Return collection if DB exists, None otherwise"""
        if self._db is not None:
            return self._db[name]
        return None
    
    @property
    def users(self):
        return self._db.users if self._db is not None else None
    
    @property
    def trades(self):
        return self._db.trades if self._db is not None else None
    
    @property
    def patterns(self):
        return self._db.patterns if self._db is not None else None
    
    @property
    def strategies(self):
        return self._db.strategies if self._db is not None else None
    
    @property
    def brain_states(self):
        return self._db.brain_states if self._db is not None else None
    
    @property
    def market_data(self):
        return self._db.market_data if self._db is not None else None
    
    @property
    def portfolio(self):
        return self._db.portfolio if self._db is not None else None

# Initialize global configuration
_db_config = None

def get_db_config():
    """Get or create database configuration"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config

# Export convenience functions
def get_sync_db():
    """Get synchronous database"""
    config = get_db_config()
    return config.sync_db

def get_async_db():
    """Get asynchronous database"""
    config = get_db_config()
    return config.async_db

def get_sync_collections():
    """Get synchronous collections"""
    db = get_sync_db()
    return Collections(db) if db is not None else None

def get_async_collections():
    """Get asynchronous collections"""
    db = get_async_db()
    return Collections(db) if db is not None else None

# Export for compatibility
sync_db = get_sync_db()
async_db = get_async_db()
sync_collections = get_sync_collections()
async_collections = get_async_collections()

# Test connection
def test_connection():
    """Test MongoDB connection"""
    config = get_db_config()
    if config.sync_client:
        try:
            config.sync_client.admin.command('ping')
            print(f"✅ MongoDB connected: {config.database_name}")
            return True
        except Exception as e:
            print(f"❌ MongoDB test failed: {e}")
            return False
    else:
        print("⚠️ No MongoDB connection available")
        return False

if __name__ == "__main__":
    test_connection()