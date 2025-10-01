"""
Test MongoDB Atlas connection with proper credential handling
"""

import os
from urllib.parse import quote_plus
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB Atlas connection with various methods"""
    
    # Method 1: Direct connection string from environment
    print("Testing MongoDB Atlas Connection...")
    print("=" * 50)
    
    # Get the raw URI from environment
    raw_uri = os.getenv("MONGO_URI")
    
    if not raw_uri:
        print("❌ MONGO_URI not found in environment variables")
        return False
    
    print(f"Raw URI found: {raw_uri[:30]}...") # Show only first part for security
    
    # Method 2: Build URI manually with proper encoding
    # The password has multiple special characters including two @ symbols
    username = "auraquant"
    password = "Zeke29@72@22"  # Password with two @ symbols
    cluster = "cluster0.qcg7f4h.mongodb.net"
    
    # Properly encode the password
    encoded_password = quote_plus(password)
    encoded_username = quote_plus(username)
    
    # Build the connection string
    connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster}/?retryWrites=true&w=majority"
    
    print(f"\nAttempting connection with properly encoded credentials...")
    
    try:
        # Try to connect
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        client.admin.command('ping')
        
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # List available databases
        dbs = client.list_database_names()
        print(f"\nAvailable databases: {dbs}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        
        # Try alternative authentication database
        print("\nTrying with authSource=admin...")
        connection_string_admin = f"mongodb+srv://{encoded_username}:{encoded_password}@{cluster}/?retryWrites=true&w=majority&authSource=admin"
        
        try:
            client = MongoClient(connection_string_admin, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("✅ Successfully connected with authSource=admin!")
            client.close()
            return True
        except Exception as e2:
            print(f"❌ Still failed: {e2}")
            
            print("\n⚠️ Please verify:")
            print("1. Username: auraquant")
            print("2. Password: Zeke29@72@22")
            print("3. Cluster: cluster0.qcg7f4h.mongodb.net")
            print("4. Check if IP address is whitelisted in MongoDB Atlas")
            print("5. Ensure the user has proper permissions")
            
            return False

if __name__ == "__main__":
    test_mongodb_connection()