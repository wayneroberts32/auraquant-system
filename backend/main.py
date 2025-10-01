"""
AuraQuant Synthetic Intelligence System - Cloud Deployment Entry Point
The Infinity Money Synthetic Intelligence System
Self-learning, self-evolving, self-upgrading orchestrator of capital
"""

import os
import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the AuraQuant API
from api.main import app
import uvicorn

# Configure for cloud deployment
if __name__ == "__main__":
    # Get port from environment or default to 10000
    port = int(os.environ.get("PORT", 10000))
    host = "0.0.0.0"  # Required for cloud deployment
    
    # AuraQuant Synthetic Intelligence System startup
    print("="*60)
    print("AURAQUANT SYNTHETIC INTELLIGENCE SYSTEM")
    print("The Infinity Money Orchestrator")
    print("Self-evolving | Ultra-safe | Global compliance")
    print("="*60)
    print(f"Starting on {host}:{port}")
    print(f"Trading Mode: {os.environ.get('TRADING_MODE', 'PAPER')}")
    print(f"Currency: {os.environ.get('CURRENCY', 'AUD')}")
    print("="*60)
    
    # Run the orchestrator
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        log_level="info",
        reload=False  # No reload in production
    )