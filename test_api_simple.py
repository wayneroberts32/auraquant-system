"""
Simple API Test - Without Brain Integration
Tests if FastAPI can start without the complex dependencies
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AuraQuant Quantum Brain API - Test Mode",
    description="Testing API functionality",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - System status"""
    return {
        "message": "AuraQuant Quantum Brain API - Test Mode",
        "status": "online",
        "version": "1.0.0",
        "note": "Running in simplified test mode without brain integration"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "test",
        "api": "functional"
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {
        "message": "API is working!",
        "python_version": "3.13",
        "framework": "FastAPI",
        "ready": True
    }

# Simple trading endpoint for testing
@app.get("/api/trading/test")
async def trading_test():
    """Test trading endpoint"""
    return {
        "symbol": "AAPL",
        "price": 150.00,
        "recommendation": "HOLD",
        "confidence": 0.75
    }

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    print(f"🚀 Starting AuraQuant API in Test Mode on port {port}")
    print(f"📚 Documentation available at: http://localhost:{port}/docs")
    print(f"🧪 This is a simplified version without brain integration")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )