"""
IBKR Trading Routes
API endpoints for IBKR broker operations
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

# Import broker
from brokers.ibkr_integration import get_ibkr_broker
from api.websocket_manager import ws_manager

router = APIRouter(prefix="/api/ibkr", tags=["IBKR Trading"])
logger = logging.getLogger(__name__)

# Request/Response models
class OrderRequest(BaseModel):
    symbol: str
    action: str  # BUY or SELL
    quantity: int
    order_type: str = "MARKET"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

class MarketDataRequest(BaseModel):
    symbols: List[str]
    subscribe: bool = True

@router.get("/status")
async def get_broker_status():
    """Get IBKR broker connection status"""
    broker = get_ibkr_broker()
    return {
        "connected": broker.connected,
        "host": broker.host,
        "port": broker.port,
        "client_id": broker.client_id
    }

@router.post("/connect")
async def connect_broker():
    """Connect to IBKR Gateway"""
    broker = get_ibkr_broker()
    if broker.connected:
        return {"status": "already_connected"}
    
    success = await broker.connect()
    if success:
        return {"status": "connected"}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to IBKR")

@router.post("/disconnect")
async def disconnect_broker():
    """Disconnect from IBKR Gateway"""
    broker = get_ibkr_broker()
    await broker.disconnect()
    return {"status": "disconnected"}

@router.get("/account")
async def get_account_info():
    """Get account information"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    account_info = await broker.refresh_account_info()
    return account_info

@router.get("/balance")
async def get_account_balance():
    """Get account balance"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    balance = await broker.get_account_balance()
    
    # Broadcast to WebSocket clients
    if ws_manager:
        await ws_manager.broadcast_account_update(balance)
    
    return balance

@router.get("/positions")
async def get_positions():
    """Get current positions"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    positions = await broker.get_positions()
    
    # Broadcast to WebSocket clients
    if ws_manager:
        await ws_manager.broadcast_position_update({"positions": positions})
    
    return positions

@router.post("/order")
async def place_order(order: OrderRequest):
    """Place a trading order"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    result = await broker.place_order(
        symbol=order.symbol,
        action=order.action,
        quantity=order.quantity,
        order_type=order.order_type,
        limit_price=order.limit_price,
        stop_price=order.stop_price
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Broadcast to WebSocket clients
    if ws_manager:
        await ws_manager.broadcast_order_update(result)
        await ws_manager.broadcast_alert("success", f"Order placed: {order.action} {order.quantity} {order.symbol}")
    
    return result

@router.delete("/order/{order_id}")
async def cancel_order(order_id: int):
    """Cancel an order"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    success = await broker.cancel_order(order_id)
    
    if success:
        if ws_manager:
            await ws_manager.broadcast_alert("info", f"Order {order_id} cancelled")
        return {"status": "cancelled", "order_id": order_id}
    else:
        raise HTTPException(status_code=404, detail="Order not found")

@router.get("/market-data/{symbol}")
async def get_market_data(symbol: str):
    """Get current market data for a symbol"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    data = await broker.get_market_data(symbol)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol}")
    
    return data

@router.post("/market-data/stream")
async def manage_market_data_stream(request: MarketDataRequest):
    """Start or stop market data streaming for symbols"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    results = {}
    
    for symbol in request.symbols:
        if request.subscribe:
            # Define callback for this symbol
            async def market_data_callback(data):
                if ws_manager:
                    await ws_manager.broadcast_to_subscribers(data['symbol'], data)
            
            await broker.stream_market_data(symbol, market_data_callback)
            results[symbol] = "streaming"
        else:
            await broker.stop_market_data_stream(symbol)
            results[symbol] = "stopped"
    
    return {"status": "success", "symbols": results}

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    duration: str = "1 D",
    bar_size: str = "1 min"
):
    """Get historical data for a symbol"""
    broker = get_ibkr_broker()
    if not broker.connected:
        raise HTTPException(status_code=503, detail="Not connected to IBKR")
    
    df = await broker.get_historical_data(symbol, duration, bar_size)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No historical data available for {symbol}")
    
    # Convert DataFrame to dict for JSON response
    return {
        "symbol": symbol,
        "data": df.reset_index().to_dict(orient="records")
    }

@router.websocket("/ws")
async def websocket_ibkr_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time IBKR data"""
    if not ws_manager:
        await websocket.close(code=1003, reason="WebSocket manager not available")
        return
    
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive and handle messages
            data = await websocket.receive_json()
            
            # Handle subscription requests
            if data.get("type") == "subscribe":
                symbols = data.get("symbols", [])
                broker = get_ibkr_broker()
                
                if broker.connected:
                    for symbol in symbols:
                        # Start streaming for this symbol
                        async def callback(market_data):
                            await ws_manager.broadcast_to_subscribers(
                                market_data['symbol'], 
                                market_data
                            )
                        
                        await broker.stream_market_data(symbol, callback)
                
                await ws_manager.handle_subscription(websocket, symbols)
            
            else:
                await ws_manager.handle_client_message(websocket, data)
    
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)