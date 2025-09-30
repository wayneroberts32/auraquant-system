#!/usr/bin/env python3
"""
Start AuraQuant Backend API
Simple startup script that works with or without MongoDB
"""

import os
import sys
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

# Load environment variables
load_dotenv()

def main():
    """Start the API server"""
    print("\n" + "="*60)
    print("🚀 STARTING AURAQUANT BACKEND API")
    print("="*60)
    
    # Check environment
    mongodb_uri = os.getenv("MONGODB_URI", "")
    if "localhost" in mongodb_uri:
        print("⚠️  Using local MongoDB (may not be running)")
        print("   The system will work with file storage as fallback")
    elif mongodb_uri:
        print("✅ MongoDB Atlas configured")
    else:
        print("⚠️  No MongoDB configured - using file storage only")
    
    # Get configuration
    port = int(os.getenv("API_PORT", 8000))
    
    print(f"\n📡 Starting API server on port {port}")
    print(f"   Documentation: http://localhost:{port}/docs")
    print(f"   Health check: http://localhost:{port}/health")
    print("\nPress CTRL+C to stop the server\n")
    
    # Start the server
    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure port is not in use")
        print("2. Check that all dependencies are installed")
        print("3. Run: python3.13t -m pip install fastapi uvicorn")

if __name__ == "__main__":
    main()