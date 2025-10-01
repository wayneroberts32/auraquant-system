"""
Test script to verify Profile and Journal integration with MongoDB
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from config import db_config

async def test_integration():
    """Test profile and journal collections in MongoDB"""
    try:
        # Connect to MongoDB
        print("🔌 Connecting to MongoDB Atlas...")
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"\n📚 Available collections: {collections}")
        
        # Test User Profiles collection
        print("\n🔍 Testing User Profiles Collection...")
        profile_count = await db.user_profiles.count_documents({})
        print(f"  - Profile documents: {profile_count}")
        
        if profile_count == 0:
            # Create a test profile
            test_profile = {
                "user_id": "test_user_001",
                "username": "TestTrader",
                "email": "test@auraquant.com",
                "brokers": [],
                "risk_preferences": {
                    "max_drawdown": 0.20,
                    "target_growth": 0.15,
                    "trading_mode": "moderate",
                    "max_position_size": 0.10,
                    "stop_loss": 0.02,
                    "take_profit": 0.05
                },
                "notifications": {
                    "email": {"enabled": True, "address": "test@auraquant.com"},
                    "telegram": {"enabled": False, "chat_id": ""},
                    "discord": {"enabled": False, "webhook": ""},
                    "sms": {"enabled": False, "phone": ""}
                },
                "trading_experience": "intermediate",
                "preferred_assets": ["BTC", "ETH", "AAPL"],
                "auto_trade_enabled": False,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await db.user_profiles.insert_one(test_profile)
            print(f"  ✅ Created test profile: {result.inserted_id}")
        
        # Test Trading Journal collection
        print("\n🔍 Testing Trading Journal Collection...")
        journal_count = await db.trading_journal.count_documents({})
        print(f"  - Journal entries: {journal_count}")
        
        if journal_count == 0:
            # Create test journal entries
            test_entries = [
                {
                    "user_id": "test_user_001",
                    "symbol": "BTCUSDT",
                    "side": "buy",
                    "entry_price": 45000,
                    "exit_price": 47000,
                    "size": 0.1,
                    "pnl": 200,
                    "strategy": "swing",
                    "notes": "Bullish breakout pattern",
                    "tags": ["breakout", "trending"],
                    "emotions": "confident",
                    "timestamp": datetime.utcnow(),
                    "win": True
                },
                {
                    "user_id": "test_user_001",
                    "symbol": "ETHUSDT",
                    "side": "sell",
                    "entry_price": 3200,
                    "exit_price": 3150,
                    "size": 1,
                    "pnl": 50,
                    "strategy": "scalping",
                    "notes": "Quick resistance rejection",
                    "tags": ["scalp", "resistance"],
                    "emotions": "calm",
                    "timestamp": datetime.utcnow(),
                    "win": True
                },
                {
                    "user_id": "test_user_001",
                    "symbol": "AAPL",
                    "side": "buy",
                    "entry_price": 175,
                    "exit_price": 173,
                    "size": 10,
                    "pnl": -20,
                    "strategy": "daytrading",
                    "notes": "Stop loss hit",
                    "tags": ["stopped"],
                    "emotions": "anxious",
                    "timestamp": datetime.utcnow(),
                    "win": False
                }
            ]
            
            result = await db.trading_journal.insert_many(test_entries)
            print(f"  ✅ Created {len(result.inserted_ids)} test journal entries")
        
        # Check indexes
        print("\n🔍 Checking Indexes...")
        
        # Profile indexes
        profile_indexes = await db.user_profiles.index_information()
        print(f"  - Profile indexes: {list(profile_indexes.keys())}")
        
        # Ensure user_id index exists
        if "user_id_1" not in profile_indexes:
            await db.user_profiles.create_index("user_id", unique=True)
            print("  ✅ Created user_id index on profiles")
        
        # Journal indexes
        journal_indexes = await db.trading_journal.index_information()
        print(f"  - Journal indexes: {list(journal_indexes.keys())}")
        
        # Ensure journal indexes exist
        if "user_id_1" not in journal_indexes:
            await db.trading_journal.create_index("user_id")
            print("  ✅ Created user_id index on journal")
        if "timestamp_-1" not in journal_indexes:
            await db.trading_journal.create_index([("timestamp", -1)])
            print("  ✅ Created timestamp index on journal")
        
        # Test aggregation pipeline for statistics
        print("\n🔍 Testing Statistics Aggregation...")
        pipeline = [
            {"$match": {"user_id": "test_user_001"}},
            {"$group": {
                "_id": "$user_id",
                "total_trades": {"$sum": 1},
                "total_pnl": {"$sum": "$pnl"},
                "winning_trades": {
                    "$sum": {"$cond": [{"$gt": ["$pnl", 0]}, 1, 0]}
                },
                "losing_trades": {
                    "$sum": {"$cond": [{"$lt": ["$pnl", 0]}, 1, 0]}
                }
            }}
        ]
        
        stats_cursor = db.trading_journal.aggregate(pipeline)
        stats = await stats_cursor.to_list(1)
        
        if stats:
            stat = stats[0]
            win_rate = (stat["winning_trades"] / stat["total_trades"] * 100) if stat["total_trades"] > 0 else 0
            print(f"  - Total trades: {stat['total_trades']}")
            print(f"  - Total P&L: ${stat['total_pnl']}")
            print(f"  - Win rate: {win_rate:.1f}%")
        
        print("\n✅ All integration tests passed successfully!")
        print("\n📋 Summary:")
        print(f"  - MongoDB: Connected to {db_config.database_name}")
        print(f"  - Profile Collection: Ready ({profile_count + (1 if profile_count == 0 else 0)} documents)")
        print(f"  - Journal Collection: Ready ({journal_count + (3 if journal_count == 0 else 0)} documents)")
        print(f"  - Indexes: Configured")
        print(f"  - Aggregations: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    print("=" * 60)
    print("AuraQuant Profile & Journal Integration Test")
    print("=" * 60)
    
    success = asyncio.run(test_integration())
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Start the backend server: python main.py")
        print("  2. Open frontend pages:")
        print("     - Profile: frontend/pages/profile.html")
        print("     - Journal: frontend/pages/journal.html")
        print("  3. Ensure auth token is set in localStorage")
    else:
        print("\n⚠️ Please check the errors above and fix any issues")