"""
Test MongoDB Atlas Connection
This script tests the connection to your MongoDB Atlas cluster
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from datetime import datetime
from config import db_config

def test_sync_connection():
    """Test synchronous MongoDB connection"""
    print("\n🔧 Testing SYNCHRONOUS MongoDB connection...")
    print(f"📍 URI: {db_config.mongodb_uri[:50]}...")
    
    try:
        # Create client
        client = MongoClient(db_config.mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database
        db = client[db_config.database_name]
        print(f"📦 Using database: {db_config.database_name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"📋 Collections found: {collections if collections else 'No collections yet'}")
        
        # Test write operation
        test_collection = db['connection_tests']
        test_doc = {
            'test_type': 'sync_connection',
            'timestamp': datetime.utcnow(),
            'status': 'successful',
            'message': 'AuraQuant MongoDB connection test'
        }
        result = test_collection.insert_one(test_doc)
        print(f"✏️ Test document inserted with ID: {result.inserted_id}")
        
        # Test read operation
        found_doc = test_collection.find_one({'_id': result.inserted_id})
        print(f"📖 Test document retrieved: {found_doc['message']}")
        
        # Clean up test document
        test_collection.delete_one({'_id': result.inserted_id})
        print("🗑️ Test document cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

async def test_async_connection():
    """Test asynchronous MongoDB connection (used by backend)"""
    print("\n🔧 Testing ASYNCHRONOUS MongoDB connection...")
    
    try:
        # Create async client
        client = AsyncIOMotorClient(db_config.mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas (async)!")
        
        # Get database
        db = client[db_config.database_name]
        
        # Test async write
        test_collection = db['connection_tests']
        test_doc = {
            'test_type': 'async_connection',
            'timestamp': datetime.utcnow(),
            'status': 'successful',
            'message': 'AuraQuant async MongoDB test'
        }
        result = await test_collection.insert_one(test_doc)
        print(f"✏️ Async test document inserted with ID: {result.inserted_id}")
        
        # Test async read
        found_doc = await test_collection.find_one({'_id': result.inserted_id})
        print(f"📖 Async test document retrieved: {found_doc['message']}")
        
        # Clean up
        await test_collection.delete_one({'_id': result.inserted_id})
        print("🗑️ Async test document cleaned up")
        
        # Test creating collections for AuraQuant
        collections_to_create = [
            'users',
            'agents',
            'trades',
            'market_data',
            'alerts',
            'brain_states',
            'evolution_checkpoints'
        ]
        
        existing_collections = await db.list_collection_names()
        
        for collection_name in collections_to_create:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                print(f"📦 Created collection: {collection_name}")
            else:
                print(f"✓ Collection already exists: {collection_name}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Async connection failed: {str(e)}")
        return False

def main():
    """Run all connection tests"""
    print("=" * 60)
    print("🚀 AuraQuant MongoDB Atlas Connection Test")
    print("=" * 60)
    
    # Test sync connection
    sync_success = test_sync_connection()
    
    # Test async connection
    async_success = asyncio.run(test_async_connection())
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"  Sync Connection:  {'✅ PASSED' if sync_success else '❌ FAILED'}")
    print(f"  Async Connection: {'✅ PASSED' if async_success else '❌ FAILED'}")
    
    if sync_success and async_success:
        print("\n🎉 All tests passed! MongoDB Atlas is properly configured.")
        print("Your AuraQuant backend can now persist data to MongoDB!")
    else:
        print("\n⚠️ Some tests failed. Please check your MongoDB connection string.")
        print("Ensure your IP address is whitelisted in MongoDB Atlas Network Access.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()