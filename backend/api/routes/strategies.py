"""
Strategies Routes
Handles strategy-related endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import sys
import os
import json

# Add parent directory for trading_lib import
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from trading_lib import (
        get_strategy_list, get_indicator_list, get_risk_metrics_list,
        run_strategy, calculate_all_metrics
    )
    TRADING_LIB_AVAILABLE = True
except ImportError:
    TRADING_LIB_AVAILABLE = False
    print("Warning: Trading library not available")

router = APIRouter()

class Strategy(BaseModel):
    name: str
    type: str
    parameters: Dict[str, Any]
    active: bool = True
    
class StrategyPerformance(BaseModel):
    strategy_name: str
    total_trades: int
    win_rate: float
    profit_loss: float
    sharpe_ratio: float
    max_drawdown: float

@router.get("/list")
async def list_strategies():
    """List all available trading strategies"""
    return {
        "strategies": [
            {"name": "momentum", "description": "Momentum-based trading", "active": True},
            {"name": "mean_reversion", "description": "Mean reversion strategy", "active": True},
            {"name": "breakout", "description": "Breakout detection", "active": True},
            {"name": "pairs_trading", "description": "Statistical arbitrage", "active": False},
            {"name": "sentiment", "description": "Sentiment analysis", "active": True},
            {"name": "quantum", "description": "Quantum-inspired strategy", "active": True}
        ]
    }

@router.post("/activate/{strategy_name}")
async def activate_strategy(strategy_name: str):
    """Activate a trading strategy"""
    return {"message": f"Strategy {strategy_name} activated", "active": True}

@router.post("/deactivate/{strategy_name}")
async def deactivate_strategy(strategy_name: str):
    """Deactivate a trading strategy"""
    return {"message": f"Strategy {strategy_name} deactivated", "active": False}

@router.get("/performance/{strategy_name}")
async def get_strategy_performance(strategy_name: str):
    """Get performance metrics for a strategy"""
    # Simulated performance data
    return StrategyPerformance(
        strategy_name=strategy_name,
        total_trades=150,
        win_rate=0.62,
        profit_loss=15000,
        sharpe_ratio=1.8,
        max_drawdown=0.15
    )

# Trading Library Endpoints
@router.get("/strategies/list")
async def get_trading_strategies():
    """Get list of all available trading strategies from trading library"""
    if not TRADING_LIB_AVAILABLE:
        # Return MongoDB strategies if trading lib not available
        from motor.motor_asyncio import AsyncIOMotorClient
        from ...config import db_config
        
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        strategies = await db.strategies.find({}).to_list(100)
        for strategy in strategies:
            strategy['_id'] = str(strategy['_id'])
        
        return {"success": True, "strategies": strategies}
    
    strategies = get_strategy_list()
    return {"success": True, "strategies": strategies}

@router.get("/indicators/list")
async def get_trading_indicators():
    """Get list of all available indicators from trading library"""
    if not TRADING_LIB_AVAILABLE:
        from motor.motor_asyncio import AsyncIOMotorClient
        from ...config import db_config
        
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        indicators = await db.indicators.find({}).to_list(100)
        for indicator in indicators:
            indicator['_id'] = str(indicator['_id'])
        
        return {"success": True, "indicators": indicators}
    
    indicators = get_indicator_list()
    return {"success": True, "indicators": indicators}

@router.get("/risk-metrics/list")
async def get_trading_risk_metrics():
    """Get list of all available risk metrics from trading library"""
    if not TRADING_LIB_AVAILABLE:
        from motor.motor_asyncio import AsyncIOMotorClient
        from ...config import db_config
        
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        metrics = await db.risk_metrics.find({}).to_list(100)
        for metric in metrics:
            metric['_id'] = str(metric['_id'])
        
        return {"success": True, "metrics": metrics}
    
    metrics = get_risk_metrics_list()
    return {"success": True, "metrics": metrics}

class BacktestRequest(BaseModel):
    strategy: str
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    initial_capital: float = 10000
    period_days: int = 30
    parameters: Dict[str, Any] = {}

@router.post("/strategies/backtest")
async def run_backtest(request: BacktestRequest):
    """Run a backtest for a strategy"""
    try:
        # For now, return simulated results
        # In production, this would fetch real data and run actual backtest
        results = {
            "total_return": np.random.uniform(-10, 30),
            "win_rate": np.random.uniform(40, 70),
            "sharpe_ratio": np.random.uniform(0.5, 2.5),
            "max_drawdown": np.random.uniform(-20, -5),
            "total_trades": np.random.randint(20, 100),
            "profit_factor": np.random.uniform(0.8, 2.0)
        }
        
        # Save backtest result to MongoDB
        from motor.motor_asyncio import AsyncIOMotorClient
        from ...config import db_config
        
        client = AsyncIOMotorClient(db_config.mongodb_uri)
        db = client[db_config.database_name]
        
        await db.backtest_results.insert_one({
            "strategy_name": request.strategy,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "initial_capital": request.initial_capital,
            "parameters": request.parameters,
            "results": results,
            "timestamp": datetime.utcnow()
        })
        
        return {"success": True, "results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
