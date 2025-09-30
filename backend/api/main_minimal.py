"""
AuraQuant Minimal API for Profile and Journal
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import only working routers
from api.routes import auth, profile, journal

# Initialize FastAPI app
app = FastAPI(
    title="AuraQuant API",
    description="Trading system with Profile and Journal functionality",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - System status"""
    return {
        "message": "AuraQuant API",
        "status": "online",
        "version": "1.0.0",
        "features": ["profile", "journal", "authentication"]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "profile_api": True,
        "journal_api": True,
        "auth_api": True
    }

# System info endpoint
@app.get("/api/system/info")
async def system_info():
    """Get system information"""
    return {
        "api": {
            "version": "1.0.0",
            "port": os.getenv("API_PORT", 8000),
            "database": "MongoDB Atlas"
        },
        "features": {
            "profile_management": True,
            "trading_journal": True,
            "authentication": True,
            "csv_export": True
        }
    }

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(journal.router, prefix="/api/journal", tags=["Journal"])

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("✅ AuraQuant API Started")
    print("📊 Profile and Journal APIs ready")
    print("🔐 Authentication enabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down AuraQuant API...")