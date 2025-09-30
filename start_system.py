#!/usr/bin/env python
"""
AuraQuant Cloud Startup Script
For Render deployment
"""

import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import system integration
from system.system_integration import SystemIntegration
from agents.swarm_config import initialize_global_swarm, get_swarm_instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraQuant.CloudStartup")

# Create FastAPI app for health checks and API
app = FastAPI(title="AuraQuant Trading System")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://auraquant-frontend.pages.dev",
        "https://ai-auraquant.com",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system instance
auraquant_system = None
swarm_orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize AuraQuant system on startup"""
    global auraquant_system
    
    logger.info("Starting AuraQuant Trading System...")
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv('MONGODB_URI')
    
    if not mongodb_uri:
        logger.warning("MongoDB URI not found - running in demo mode")
    
    # Initialize system
    auraquant_system = SystemIntegration(mongodb_uri)
    
    # Start system initialization in background
    asyncio.create_task(initialize_system())

async def initialize_system():
    """Initialize system components"""
    global auraquant_system, swarm_orchestrator
    
    try:
        # Initialize multi-agent swarm
        logger.info("Initializing Multi-Agent Swarm Orchestrator...")
        swarm_orchestrator = await initialize_global_swarm()
        logger.info(f"✅ Swarm initialized with {len(swarm_orchestrator.agents)} agents")
        
        # Initialize all components
        result = await auraquant_system.initialize_system()
        
        if result['status'] == 'initialized':
            logger.info("✅ AuraQuant System initialized successfully")
            
            # Start the trading system
            await auraquant_system.start_system()
            logger.info("✅ Trading system started")
        else:
            logger.error("System initialization failed")
            
    except Exception as e:
        logger.error(f"System startup error: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "system": "AuraQuant",
        "version": "1.0.0",
        "status": "RUNNING",
        "description": "The Infinity Money Synthetic Intelligence System"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    global auraquant_system
    
    if auraquant_system:
        try:
            health = await auraquant_system.perform_health_check()
            return {
                "status": "healthy",
                "system_health": health['overall_health'],
                "components": health['components'],
                "timestamp": health['timestamp']
            }
        except:
            return {"status": "degraded"}
    else:
        return {"status": "initializing"}

@app.get("/api/status")
async def get_status():
    """Get system status"""
    global auraquant_system
    
    if not auraquant_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    return {
        "trading_enabled": auraquant_system.system_status.trading_enabled,
        "compliance_active": auraquant_system.system_status.compliance_active,
        "risk_management_active": auraquant_system.system_status.risk_management_active,
        "mongodb_connected": auraquant_system.system_status.mongodb_connected,
        "system_health": auraquant_system.system_status.system_health
    }

@app.get("/api/swarm/status")
async def get_swarm_status():
    """Get multi-agent swarm status"""
    global swarm_orchestrator
    
    if not swarm_orchestrator:
        return {"status": "not_initialized", "message": "Swarm not yet initialized"}
    
    return swarm_orchestrator.get_swarm_status()

@app.get("/api/agents")
async def get_agents():
    """Get all agent information"""
    global swarm_orchestrator
    
    if not swarm_orchestrator:
        return {"agents": [], "total": 0}
    
    agents_info = []
    for agent in swarm_orchestrator.agents.values():
        agents_info.append({
            "id": agent.agent_id,
            "type": agent.agent_type.value,
            "status": agent.status,
            "tasks_completed": agent.tasks_completed,
            "errors": agent.errors,
            "last_heartbeat": agent.last_heartbeat
        })
    
    return {"agents": agents_info, "total": len(agents_info)}

@app.get("/api/markets")
async def get_markets():
    """Get supported markets"""
    return {
        "markets": [
            {
                "name": "ASX",
                "status": "ACTIVE",
                "hours": "10:00-16:00 Sydney"
            },
            {
                "name": "Crypto Spot",
                "status": "ACTIVE",
                "hours": "24/7"
            },
            {
                "name": "Crypto Futures",
                "status": "ACTIVE",
                "hours": "24/7",
                "max_leverage": 20
            },
            {
                "name": "Meme Coins",
                "status": "ACTIVE",
                "hours": "24/7",
                "safety_features": ["Rug pull detection", "Honeypot detection"]
            }
        ]
    }

@app.post("/api/emergency/killswitch")
async def activate_killswitch(reason: str = "Manual activation"):
    """Emergency kill switch activation"""
    global auraquant_system
    
    if not auraquant_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    if auraquant_system.components.get('compliance'):
        result = auraquant_system.components['compliance'].activate_kill_switch(reason)
        return {"status": "activated", "result": result}
    else:
        raise HTTPException(status_code=503, detail="Compliance system not available")

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown the system"""
    global auraquant_system, swarm_orchestrator
    
    if swarm_orchestrator:
        logger.info("Shutting down Multi-Agent Swarm...")
        await swarm_orchestrator.shutdown_swarm()
        logger.info("Swarm shutdown complete")
    
    if auraquant_system:
        logger.info("Shutting down AuraQuant system...")
        await auraquant_system.shutdown_system()
        logger.info("System shutdown complete")

if __name__ == "__main__":
    # Get port from environment variable (Render sets this)
    port = int(os.getenv("PORT", 10000))
    
    # Run the FastAPI app
    uvicorn.run(
        "start_system:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )