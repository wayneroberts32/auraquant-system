"""
MongoDB Clean Start and System Memory Push
This script will clean all old data and initialize fresh collections
"""
import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Add parent directory to import config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import db_config

class MongoDBInitializer:
    def __init__(self):
        self.sync_client = None
        self.async_client = None
        self.db_name = db_config.database_name
        self.mongodb_uri = db_config.mongodb_uri
        
    async def clean_database(self):
        """Clean all collections except system ones"""
        print("🗑️ Starting MongoDB cleanup...")
        
        try:
            self.async_client = AsyncIOMotorClient(self.mongodb_uri)
            db = self.async_client[self.db_name]
            
            # List all collections
            collections = await db.list_collection_names()
            
            # Collections to preserve (system collections)
            preserve = ['system.indexes', 'system.users']
            
            # Drop all non-system collections
            for collection in collections:
                if collection not in preserve:
                    await db[collection].drop()
                    print(f"  ✓ Dropped collection: {collection}")
            
            print("✅ Database cleaned successfully!")
            
        except Exception as e:
            print(f"❌ Error cleaning database: {e}")
            
    async def create_collections(self):
        """Create fresh collections with proper indexes"""
        print("\n📦 Creating fresh collections...")
        
        db = self.async_client[self.db_name]
        
        collections_config = {
            # Core Collections
            'users': {
                'indexes': [
                    {'field': 'email', 'unique': True},
                    {'field': 'created_at', 'order': -1}
                ]
            },
            'agents': {
                'indexes': [
                    {'field': 'owner_id', 'order': 1},
                    {'field': 'status', 'order': 1},
                    {'field': 'created_at', 'order': -1}
                ]
            },
            'trades': {
                'indexes': [
                    {'field': 'timestamp', 'order': -1},
                    {'field': 'symbol', 'order': 1},
                    {'field': 'agent_id', 'order': 1}
                ]
            },
            'strategies': {
                'indexes': [
                    {'field': 'name', 'unique': True},
                    {'field': 'type', 'order': 1},
                    {'field': 'auto_registered', 'order': 1},
                    {'field': 'created_at', 'order': -1}
                ]
            },
            'indicators': {
                'indexes': [
                    {'field': 'name', 'unique': True},
                    {'field': 'category', 'order': 1},
                    {'field': 'auto_registered', 'order': 1}
                ]
            },
            'risk_metrics': {
                'indexes': [
                    {'field': 'name', 'unique': True},
                    {'field': 'type', 'order': 1},
                    {'field': 'auto_registered', 'order': 1}
                ]
            },
            'backtest_results': {
                'indexes': [
                    {'field': 'timestamp', 'order': -1},
                    {'field': 'strategy_name', 'order': 1},
                    {'field': 'user_id', 'order': 1}
                ]
            },
            'market_data': {
                'indexes': [
                    {'field': 'timestamp', 'order': -1},
                    {'field': 'symbol', 'order': 1},
                    {'field': 'timeframe', 'order': 1}
                ]
            },
            'brain_states': {
                'indexes': [
                    {'field': 'timestamp', 'order': -1},
                    {'field': 'generation', 'order': -1}
                ]
            },
            'evolution_checkpoints': {
                'indexes': [
                    {'field': 'generation', 'order': -1},
                    {'field': 'fitness_score', 'order': -1}
                ]
            },
            'alerts': {
                'indexes': [
                    {'field': 'timestamp', 'order': -1},
                    {'field': 'priority', 'order': 1},
                    {'field': 'status', 'order': 1}
                ]
            },
            'system_logs': {
                'indexes': [
                    {'field': 'timestamp', 'order': -1},
                    {'field': 'level', 'order': 1},
                    {'field': 'module', 'order': 1}
                ]
            }
        }
        
        for collection_name, config in collections_config.items():
            # Create collection
            try:
                await db.create_collection(collection_name)
                print(f"  ✓ Created collection: {collection_name}")
            except:
                print(f"  ℹ Collection already exists: {collection_name}")
            
            # Create indexes
            collection = db[collection_name]
            for index_config in config.get('indexes', []):
                field = index_config['field']
                order = index_config.get('order', 1)
                unique = index_config.get('unique', False)
                
                await collection.create_index(
                    [(field, order)],
                    unique=unique
                )
            
        print("✅ Collections created successfully!")
        
    async def push_system_memory(self):
        """Push system memory files to MongoDB"""
        print("\n💾 Pushing system memory to MongoDB...")
        
        memory_path = Path("D:/New AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/backend/Memory")
        
        if not memory_path.exists():
            print(f"  ⚠️ Memory path not found: {memory_path}")
            return
            
        db = self.async_client[self.db_name]
        
        # Process different memory types
        memory_types = {
            'strategies': 'strategies',
            'patterns': 'indicators',
            'risk': 'risk_metrics',
            'brain': 'brain_states',
            'evolution': 'evolution_checkpoints'
        }
        
        for memory_type, collection_name in memory_types.items():
            # Look for JSON files in memory
            pattern = f"*{memory_type}*.json"
            files = list(memory_path.glob(pattern))
            
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Add metadata
                    if isinstance(data, dict):
                        data['source_file'] = file_path.name
                        data['imported_at'] = datetime.utcnow()
                        data['auto_registered'] = False
                        
                        # Insert into MongoDB
                        await db[collection_name].insert_one(data)
                        print(f"  ✓ Imported {file_path.name} to {collection_name}")
                        
                    elif isinstance(data, list):
                        # Handle list of items
                        for item in data:
                            if isinstance(item, dict):
                                item['source_file'] = file_path.name
                                item['imported_at'] = datetime.utcnow()
                                item['auto_registered'] = False
                        
                        if data:
                            await db[collection_name].insert_many(data)
                            print(f"  ✓ Imported {len(data)} items from {file_path.name}")
                            
                except Exception as e:
                    print(f"  ⚠️ Error importing {file_path.name}: {e}")
                    
        print("✅ System memory pushed to MongoDB!")
        
    async def register_default_strategies(self):
        """Register default trading strategies"""
        print("\n📊 Registering default strategies...")
        
        db = self.async_client[self.db_name]
        
        default_strategies = [
            {
                'name': 'SMA_Crossover',
                'type': 'trend_following',
                'description': 'Simple Moving Average Crossover Strategy',
                'parameters': {
                    'fast_period': 10,
                    'slow_period': 20
                },
                'auto_registered': True,
                'status': 'active',
                'created_at': datetime.utcnow()
            },
            {
                'name': 'RSI_Oversold_Overbought',
                'type': 'mean_reversion',
                'description': 'RSI based mean reversion strategy',
                'parameters': {
                    'period': 14,
                    'oversold': 30,
                    'overbought': 70
                },
                'auto_registered': True,
                'status': 'active',
                'created_at': datetime.utcnow()
            },
            {
                'name': 'MACD_Signal',
                'type': 'momentum',
                'description': 'MACD histogram and signal line strategy',
                'parameters': {
                    'fast': 12,
                    'slow': 26,
                    'signal': 9
                },
                'auto_registered': True,
                'status': 'active',
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Bollinger_Breakout',
                'type': 'breakout',
                'description': 'Bollinger Bands breakout strategy',
                'parameters': {
                    'period': 20,
                    'std_dev': 2
                },
                'auto_registered': True,
                'status': 'active',
                'created_at': datetime.utcnow()
            },
            {
                'name': 'Volume_Momentum',
                'type': 'volume',
                'description': 'Volume-based momentum strategy',
                'parameters': {
                    'volume_ma': 20,
                    'price_ma': 10
                },
                'auto_registered': True,
                'status': 'experimental',
                'created_at': datetime.utcnow()
            }
        ]
        
        for strategy in default_strategies:
            try:
                await db.strategies.insert_one(strategy)
                print(f"  ✓ Registered strategy: {strategy['name']}")
            except:
                print(f"  ℹ Strategy already exists: {strategy['name']}")
                
        print("✅ Default strategies registered!")
        
    async def register_default_indicators(self):
        """Register default technical indicators"""
        print("\n📈 Registering default indicators...")
        
        db = self.async_client[self.db_name]
        
        default_indicators = [
            {'name': 'SMA', 'category': 'trend', 'description': 'Simple Moving Average'},
            {'name': 'EMA', 'category': 'trend', 'description': 'Exponential Moving Average'},
            {'name': 'WMA', 'category': 'trend', 'description': 'Weighted Moving Average'},
            {'name': 'RSI', 'category': 'momentum', 'description': 'Relative Strength Index'},
            {'name': 'MACD', 'category': 'momentum', 'description': 'Moving Average Convergence Divergence'},
            {'name': 'StochRSI', 'category': 'momentum', 'description': 'Stochastic RSI'},
            {'name': 'BollingerBands', 'category': 'volatility', 'description': 'Bollinger Bands'},
            {'name': 'ATR', 'category': 'volatility', 'description': 'Average True Range'},
            {'name': 'OBV', 'category': 'volume', 'description': 'On Balance Volume'},
            {'name': 'VWAP', 'category': 'volume', 'description': 'Volume Weighted Average Price'},
        ]
        
        for indicator in default_indicators:
            indicator['auto_registered'] = True
            indicator['created_at'] = datetime.utcnow()
            
            try:
                await db.indicators.insert_one(indicator)
                print(f"  ✓ Registered indicator: {indicator['name']}")
            except:
                print(f"  ℹ Indicator already exists: {indicator['name']}")
                
        print("✅ Default indicators registered!")
        
    async def register_default_risk_metrics(self):
        """Register default risk metrics"""
        print("\n⚡ Registering default risk metrics...")
        
        db = self.async_client[self.db_name]
        
        default_metrics = [
            {'name': 'MaxDrawdown', 'type': 'risk', 'description': 'Maximum Drawdown'},
            {'name': 'SharpeRatio', 'type': 'risk_adjusted_return', 'description': 'Sharpe Ratio'},
            {'name': 'SortinoRatio', 'type': 'risk_adjusted_return', 'description': 'Sortino Ratio'},
            {'name': 'ProfitFactor', 'type': 'performance', 'description': 'Profit Factor'},
            {'name': 'WinRate', 'type': 'performance', 'description': 'Win Rate'},
            {'name': 'ExpectedReturn', 'type': 'performance', 'description': 'Expected Return'},
            {'name': 'VaR', 'type': 'risk', 'description': 'Value at Risk'},
            {'name': 'CalmarRatio', 'type': 'risk_adjusted_return', 'description': 'Calmar Ratio'},
        ]
        
        for metric in default_metrics:
            metric['auto_registered'] = True
            metric['created_at'] = datetime.utcnow()
            
            try:
                await db.risk_metrics.insert_one(metric)
                print(f"  ✓ Registered metric: {metric['name']}")
            except:
                print(f"  ℹ Metric already exists: {metric['name']}")
                
        print("✅ Default risk metrics registered!")
        
    async def create_admin_user(self):
        """Create default admin user"""
        print("\n👤 Creating admin user...")
        
        db = self.async_client[self.db_name]
        
        admin_user = {
            'email': 'wayneroberts32@outlook.com.au',
            'username': 'admin',
            'role': 'admin',
            'status': 'active',
            'created_at': datetime.utcnow(),
            'last_login': None,
            'settings': {
                'theme': 'dark',
                'notifications': True,
                'auto_trade': False
            }
        }
        
        try:
            await db.users.insert_one(admin_user)
            print(f"  ✓ Created admin user: {admin_user['email']}")
        except:
            print(f"  ℹ Admin user already exists")
            
        print("✅ Admin user ready!")
        
    async def initialize(self):
        """Run full initialization"""
        print("=" * 60)
        print("🚀 AuraQuant MongoDB Fresh Start Initialization")
        print("=" * 60)
        
        try:
            # Clean database
            await self.clean_database()
            
            # Create fresh collections
            await self.create_collections()
            
            # Push system memory
            await self.push_system_memory()
            
            # Register defaults
            await self.register_default_strategies()
            await self.register_default_indicators()
            await self.register_default_risk_metrics()
            
            # Create admin user
            await self.create_admin_user()
            
            print("\n" + "=" * 60)
            print("✅ MongoDB initialization complete!")
            print("🎯 Database is clean and ready with:")
            print("  • Fresh collections with indexes")
            print("  • System memory imported")
            print("  • Default strategies registered")
            print("  • Default indicators registered")
            print("  • Default risk metrics registered")
            print("  • Admin user created")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            
        finally:
            if self.async_client:
                self.async_client.close()

if __name__ == "__main__":
    initializer = MongoDBInitializer()
    asyncio.run(initializer.initialize())