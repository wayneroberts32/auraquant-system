"""
Scanner Routes
Dashboard scanner endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

router = APIRouter()

class ScanRequest(BaseModel):
    scan_type: str = "full"  # full, quick, patterns_only
    markets: list = ["stocks", "crypto", "forex"]
    
@router.post("/start")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start dashboard scanning process"""
    try:
        from api.main import dashboard_scanner
        
        if not dashboard_scanner:
            raise HTTPException(status_code=503, detail="Dashboard Scanner not initialized")
        
        # Start scan in background
        background_tasks.add_task(dashboard_scanner.scan_markets, request.markets)
        
        return {
            "status": "started",
            "scan_type": request.scan_type,
            "markets": request.markets,
            "timestamp": datetime.now()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_scan_status():
    """Get current scan status"""
    try:
        from api.main import dashboard_scanner
        
        if not dashboard_scanner:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "last_scan": dashboard_scanner.last_scan_time if hasattr(dashboard_scanner, 'last_scan_time') else None,
            "patterns_found": dashboard_scanner.total_patterns if hasattr(dashboard_scanner, 'total_patterns') else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patterns")
async def get_patterns():
    """Get detected patterns"""
    try:
        from api.main import memory_manager
        
        if not memory_manager:
            raise HTTPException(status_code=503, detail="Memory Manager not initialized")
        
        patterns = await memory_manager.get_patterns()
        return {"patterns": patterns, "count": len(patterns)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))