#!/usr/bin/env python3
"""
Simple API Test - Minimal FastAPI server
"""

from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Create app
app = FastAPI(title="AuraQuant Test API")

@app.get("/")
def read_root():
    return {"message": "AuraQuant API is running!", "status": "OK"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "backend": "Python FastAPI",
        "mongodb": "Not connected (running in test mode)"
    }

@app.get("/api/test")
def test_endpoint():
    return {
        "test": "success",
        "quantum_brain": "Ready",
        "environment": os.getenv("NODE_ENV", "development")
    }

if __name__ == "__main__":
    print("\n🧪 TESTING SIMPLE API SERVER")
    print("=" * 60)
    print("Starting on http://localhost:8000")
    print("Press CTRL+C to stop\n")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n✅ Server stopped")