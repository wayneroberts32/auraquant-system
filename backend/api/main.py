"""
AuraQuant Quantum Brain API
Main FastAPI Application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional
import asyncio

# Add parent directory to path to import brain modules
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))  # Add project root for packages

# Load environment variables
load_dotenv()

# Import IBKR integration and WebSocket manager
try:
    from brokers.ibkr_integration import get_ibkr_broker, IBKRBroker
    from api.websocket_manager import ws_manager, websocket_endpoint
    HAS_IBKR = True
except ImportError as e:
    print(f"⚠️ IBKR integration not available: {e}")
    HAS_IBKR = False
    get_ibkr_broker = None
    IBKRBroker = None
    ws_manager = None

# Import routers
from api.routes import trading, strategies, market_data, auth, scanner
try:
    from api.routes import profile, journal
    HAS_PROFILE_JOURNAL = True
except ImportError:
    print("⚠️ Profile and Journal routes not available")
    HAS_PROFILE_JOURNAL = False
    profile = None
    journal = None

try:
    from api.routes.ibkr_routes import router as ibkr_router
    HAS_IBKR_ROUTES = True
except ImportError:
    print("⚠️ IBKR routes not available")
    HAS_IBKR_ROUTES = False
    ibkr_router = None

# Import brain modules with fallbacks
try:
    from brain.quantum_brain_fixed import QuantumBrain, get_brain
    HAS_BRAIN = True
except ImportError:
    print("⚠️ Using fallback brain imports")
    try:
        from brain.quantum_brain_local import QuantumBrain
        HAS_BRAIN = True
        get_brain = None
    except ImportError:
        print("❌ No Quantum Brain available")
        HAS_BRAIN = False
        QuantumBrain = None
        get_brain = None

try:
    from brain.dashboard_scanner import DashboardScanner
    HAS_SCANNER = True
except ImportError:
    print("⚠️ Dashboard Scanner not available")
    HAS_SCANNER = False
    DashboardScanner = None

try:
    from brain.local_memory_manager import LocalMemoryManager
    HAS_MEMORY = True
except ImportError:
    print("⚠️ Memory Manager not available")
    HAS_MEMORY = False
    LocalMemoryManager = None

# Initialize FastAPI app
app = FastAPI(
    title="AuraQuant Quantum Brain API",
    description="Advanced AI-powered trading system with quantum computing simulation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
quantum_brain = None
dashboard_scanner = None
memory_manager = None
websocket_connections: List[WebSocket] = []
ibkr_broker: Optional[IBKRBroker] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the Quantum Brain and related services on startup"""
    global quantum_brain, dashboard_scanner, memory_manager, ibkr_broker
    
    print("🚀 Initializing AuraQuant Quantum Brain System...")
    
    try:
        # Initialize components
        memory_path = os.getenv("MEMORY_PATH", "D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\Memory")
        dashboard_path = os.getenv("DASHBOARD_PATH", "D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\frontend\\pages\\main-trading-dashboard.html")
        
        # Initialize brain
        if HAS_BRAIN:
            if get_brain:
                quantum_brain = get_brain()  # Use singleton
            else:
                quantum_brain = QuantumBrain(memory_path=memory_path)
            print("✅ Quantum Brain initialized")
        else:
            print("⚠️ Quantum Brain not available")
        
        # Initialize memory manager
        if HAS_MEMORY:
            memory_manager = LocalMemoryManager(base_path=memory_path)
            print("✅ Memory Manager initialized")
        else:
            print("⚠️ Memory Manager not available")
        
        # Initialize dashboard scanner
        if HAS_SCANNER and quantum_brain:
            dashboard_scanner = DashboardScanner(
                dashboard_path=dashboard_path,
                memory_path=memory_path,
                brain=quantum_brain
            )
            print("✅ Dashboard Scanner initialized")
        else:
            print("⚠️ Dashboard Scanner not available")
        
        # Initialize IBKR broker
        if HAS_IBKR:
            ibkr_broker = get_ibkr_broker()
            connected = await ibkr_broker.connect()
            if connected:
                print("✅ IBKR Broker connected")
                
                # Set up IBKR callbacks for WebSocket broadcasting
                if ws_manager:
                    async def on_market_data_update(data):
                        await ws_manager.broadcast_to_subscribers(data['symbol'], data)
                    
                    async def on_order_update(trade):
                        await ws_manager.broadcast_order_update({
                            'order_id': trade.order.orderId,
                            'status': trade.orderStatus.status,
                            'symbol': trade.contract.symbol
                        })
                    
                    async def on_position_update(position):
                        await ws_manager.broadcast_position_update({
                            'symbol': position.contract.symbol,
                            'quantity': position.position,
                            'avg_cost': position.avgCost
                        })
                    
                    ibkr_broker.register_callback('order_status', on_order_update)
                    ibkr_broker.register_callback('position', on_position_update)
            else:
                print("⚠️ Failed to connect to IBKR")
        else:
            print("⚠️ IBKR integration not available")
        
        # Sync strategies and risk metrics to MongoDB
        try:
            from trading_lib.strategies import StrategyRegistry
            from trading_lib.risk import RiskMetricsRegistry
            await StrategyRegistry.sync_all()
            await RiskMetricsRegistry.sync_all()
            print("✅ Trading strategies and risk metrics synced to MongoDB")
        except Exception as e:
            print(f"⚠️ Could not sync strategies/metrics: {e}")
        
        print("🎯 System ready for trading!")
        
    except Exception as e:
        print(f"❌ Error during startup: {str(e)}")
        # System can still run with limited functionality

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down Quantum Brain System...")
    
    # Close all websocket connections
    for ws in websocket_connections:
        await ws.close()
    
    # Save brain state
    if quantum_brain:
        await quantum_brain.save_state()
    
    print("✅ Shutdown complete")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - System status"""
    return {
        "message": "AuraQuant Quantum Brain API",
        "status": "online",
        "version": "1.0.0",
        "brain_status": "initialized" if quantum_brain else "not initialized",
        "scanner_status": "initialized" if dashboard_scanner else "not initialized"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "quantum_brain": quantum_brain is not None,
        "memory_manager": memory_manager is not None,
        "dashboard_scanner": dashboard_scanner is not None,
        "ibkr_broker": ibkr_broker is not None and ibkr_broker.connected,
        "websocket_connections": len(websocket_connections)
    }

# System info endpoint
@app.get("/api/system/info")
async def system_info():
    """Get system information"""
    return {
        "brain": {
            "initialized": quantum_brain is not None,
            "qubits": 16,
            "evolution_generation": quantum_brain.generation if quantum_brain else 0
        },
        "memory": {
            "path": os.getenv("MEMORY_PATH"),
            "initialized": memory_manager is not None
        },
        "scanner": {
            "initialized": dashboard_scanner is not None,
            "dashboard_path": os.getenv("DASHBOARD_PATH")
        },
        "api": {
            "version": "1.0.0",
            "port": os.getenv("API_PORT", 8000)
        }
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()
            
            # Process commands
            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                status = {
                    "brain_active": quantum_brain is not None,
                    "scanner_active": dashboard_scanner is not None,
                    "connections": len(websocket_connections)
                }
                await websocket.send_json(status)
            else:
                # Echo back unknown commands
                await websocket.send_text(f"Unknown command: {data}")
                
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        print(f"Client disconnected. Active connections: {len(websocket_connections)}")

# Broadcast function for WebSocket updates
async def broadcast_update(message: dict):
    """Broadcast updates to all connected WebSocket clients"""
    for connection in websocket_connections:
        try:
            await connection.send_json(message)
        except:
            # Remove dead connections
            websocket_connections.remove(connection)

# Include routers (with prefix)
app.include_router(trading.router, prefix="/api/trading", tags=["Trading"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(market_data.router, prefix="/api/market", tags=["Market Data"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

# Include profile and journal routers if available
if HAS_PROFILE_JOURNAL:
    if profile:
        app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
    if journal:
        app.include_router(journal.router, prefix="/api/journal", tags=["Journal"])

# Include IBKR router if available
if HAS_IBKR_ROUTES and ibkr_router:
    app.include_router(ibkr_router)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Main entry point
if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )