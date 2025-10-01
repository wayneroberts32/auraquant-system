"""
Trading Routes
Handles all trading-related API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

router = APIRouter()

# Pydantic models for request/response
class TradeSignal(BaseModel):
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float
    strategy: str
    timestamp: Optional[datetime] = None

class TradeRequest(BaseModel):
    symbol: str
    action: str
    quantity: float
    order_type: str = "MARKET"  # MARKET, LIMIT, STOP
    price: Optional[float] = None
    
class TradeResponse(BaseModel):
    success: bool
    trade_id: str
    symbol: str
    action: str
    quantity: float
    price: float
    timestamp: datetime
    message: str

class MarketAnalysis(BaseModel):
    symbol: str
    current_price: float
    trend: str
    momentum: float
    volatility: float
    support_levels: List[float]
    resistance_levels: List[float]
    recommendation: str
    confidence: float

# Trading endpoints
@router.get("/signals", response_model=List[TradeSignal])
async def get_trading_signals(symbols: Optional[str] = None):
    """
    Get current trading signals from the Quantum Brain
    
    Args:
        symbols: Comma-separated list of symbols to analyze
    """
    try:
        from api.main import quantum_brain
        
        if not quantum_brain:
            raise HTTPException(status_code=503, detail="Quantum Brain not initialized")
        
        # Get recommendations from brain
        if symbols:
            symbol_list = symbols.split(",")
            recommendations = await quantum_brain.get_trading_recommendations(symbol_list)
        else:
            recommendations = await quantum_brain.get_all_recommendations()
        
        # Convert to TradeSignal format
        signals = []
        for rec in recommendations:
            signal = TradeSignal(
                symbol=rec.get("symbol"),
                action=rec.get("action", "HOLD"),
                quantity=rec.get("quantity", 1.0),
                price=rec.get("price"),
                stop_loss=rec.get("stop_loss"),
                take_profit=rec.get("take_profit"),
                confidence=rec.get("confidence", 0.5),
                strategy=rec.get("strategy", "quantum_analysis"),
                timestamp=datetime.now()
            )
            signals.append(signal)
        
        return signals
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest):
    """
    Execute a trade based on the request
    
    Args:
        trade: Trade request details
    """
    try:
        from api.main import quantum_brain, memory_manager
        
        if not quantum_brain:
            raise HTTPException(status_code=503, detail="Quantum Brain not initialized")
        
        # Validate trade with quantum brain
        validation = await quantum_brain.validate_trade(
            symbol=trade.symbol,
            action=trade.action,
            quantity=trade.quantity
        )
        
        if not validation.get("valid", False):
            raise HTTPException(status_code=400, detail=validation.get("reason", "Trade validation failed"))
        
        # Execute trade (simulation for now)
        trade_result = {
            "trade_id": f"TRADE_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "symbol": trade.symbol,
            "action": trade.action,
            "quantity": trade.quantity,
            "price": trade.price or validation.get("market_price", 0),
            "timestamp": datetime.now(),
            "status": "EXECUTED"
        }
        
        # Save to memory
        if memory_manager:
            await memory_manager.save_trade(trade_result)
        
        # Update quantum brain with trade result
        await quantum_brain.update_with_trade(trade_result)
        
        return TradeResponse(
            success=True,
            trade_id=trade_result["trade_id"],
            symbol=trade_result["symbol"],
            action=trade_result["action"],
            quantity=trade_result["quantity"],
            price=trade_result["price"],
            timestamp=trade_result["timestamp"],
            message="Trade executed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{symbol}", response_model=MarketAnalysis)
async def get_market_analysis(symbol: str):
    """
    Get detailed market analysis for a symbol
    
    Args:
        symbol: Trading symbol to analyze
    """
    try:
        from api.main import quantum_brain
        
        if not quantum_brain:
            raise HTTPException(status_code=503, detail="Quantum Brain not initialized")
        
        # Get analysis from quantum brain
        analysis = await quantum_brain.analyze_market(symbol)
        
        return MarketAnalysis(
            symbol=symbol,
            current_price=analysis.get("price", 0),
            trend=analysis.get("trend", "NEUTRAL"),
            momentum=analysis.get("momentum", 0),
            volatility=analysis.get("volatility", 0),
            support_levels=analysis.get("support", []),
            resistance_levels=analysis.get("resistance", []),
            recommendation=analysis.get("recommendation", "HOLD"),
            confidence=analysis.get("confidence", 0.5)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_portfolio():
    """Get current portfolio status"""
    try:
        from api.main import memory_manager
        
        if not memory_manager:
            raise HTTPException(status_code=503, detail="Memory Manager not initialized")
        
        # Get portfolio from memory
        portfolio = await memory_manager.get_portfolio()
        
        return {
            "holdings": portfolio.get("holdings", []),
            "total_value": portfolio.get("total_value", 0),
            "cash_balance": portfolio.get("cash_balance", 10000),
            "profit_loss": portfolio.get("profit_loss", 0),
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_trade_history(limit: int = 100):
    """
    Get trade history
    
    Args:
        limit: Maximum number of trades to return
    """
    try:
        from api.main import memory_manager
        
        if not memory_manager:
            raise HTTPException(status_code=503, detail="Memory Manager not initialized")
        
        # Get trade history from memory
        history = await memory_manager.get_trade_history(limit=limit)
        
        return {
            "trades": history,
            "count": len(history),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest")
async def run_backtest(
    symbol: str,
    strategy: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Run a backtest for a strategy
    
    Args:
        symbol: Symbol to backtest
        strategy: Strategy name
        start_date: Start date for backtest
        end_date: End date for backtest
    """
    try:
        from api.main import quantum_brain
        
        if not quantum_brain:
            raise HTTPException(status_code=503, detail="Quantum Brain not initialized")
        
        # Run backtest
        results = await quantum_brain.backtest_strategy(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "symbol": symbol,
            "strategy": strategy,
            "total_trades": results.get("total_trades", 0),
            "winning_trades": results.get("winning_trades", 0),
            "losing_trades": results.get("losing_trades", 0),
            "win_rate": results.get("win_rate", 0),
            "total_return": results.get("total_return", 0),
            "sharpe_ratio": results.get("sharpe_ratio", 0),
            "max_drawdown": results.get("max_drawdown", 0),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-loss/{trade_id}")
async def set_stop_loss(trade_id: str, stop_loss: float):
    """Set or update stop loss for a trade"""
    try:
        from api.main import memory_manager
        
        if not memory_manager:
            raise HTTPException(status_code=503, detail="Memory Manager not initialized")
        
        # Update stop loss
        success = await memory_manager.update_stop_loss(trade_id, stop_loss)
        
        if success:
            return {"message": f"Stop loss set to {stop_loss} for trade {trade_id}"}
        else:
            raise HTTPException(status_code=404, detail="Trade not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))