"""
Start AuraQuant API with proper encoding
"""

import sys
import os

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import and run the API
if __name__ == "__main__":
    import uvicorn
    from backend.api.main import app
    
    print("🚀 Starting AuraQuant API...")
    print("📍 API URL: http://localhost:8000")
    print("📊 Docs: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/api/ibkr/ws")
    print("-" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )