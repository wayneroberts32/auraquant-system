"""
WebSocket Manager for Real-Time Data Streaming
Handles WebSocket connections and broadcasts IBKR data to frontend
"""

import json
import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and data broadcasting"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        self.market_data_cache: Dict[str, Dict] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send initial connection confirmation
        await self.send_personal_message(websocket, {
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_subscribers(self, symbol: str, data: Dict):
        """Broadcast market data to clients subscribed to specific symbol"""
        message = {
            "type": "market_data",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache the latest data
        self.market_data_cache[symbol] = data
        
        disconnected = []
        for connection, symbols in self.subscriptions.items():
            if symbol in symbols or "*" in symbols:  # "*" means subscribe to all
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to subscriber: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def handle_subscription(self, websocket: WebSocket, symbols: List[str]):
        """Handle symbol subscription request from client"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(symbols)
            
            # Send cached data for subscribed symbols
            for symbol in symbols:
                if symbol in self.market_data_cache:
                    await self.send_personal_message(websocket, {
                        "type": "market_data",
                        "symbol": symbol,
                        "data": self.market_data_cache[symbol],
                        "cached": True,
                        "timestamp": datetime.now().isoformat()
                    })
            
            await self.send_personal_message(websocket, {
                "type": "subscription",
                "status": "confirmed",
                "symbols": list(self.subscriptions[websocket]),
                "timestamp": datetime.now().isoformat()
            })
    
    async def handle_unsubscription(self, websocket: WebSocket, symbols: List[str]):
        """Handle symbol unsubscription request from client"""
        if websocket in self.subscriptions:
            for symbol in symbols:
                self.subscriptions[websocket].discard(symbol)
            
            await self.send_personal_message(websocket, {
                "type": "unsubscription",
                "status": "confirmed",
                "symbols": symbols,
                "remaining": list(self.subscriptions[websocket]),
                "timestamp": datetime.now().isoformat()
            })
    
    async def broadcast_account_update(self, data: Dict):
        """Broadcast account updates to all clients"""
        message = {
            "type": "account_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_position_update(self, data: Dict):
        """Broadcast position updates to all clients"""
        message = {
            "type": "position_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_order_update(self, data: Dict):
        """Broadcast order updates to all clients"""
        message = {
            "type": "order_update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_alert(self, level: str, message: str, details: Dict = None):
        """Broadcast alert/notification to all clients"""
        alert = {
            "type": "alert",
            "level": level,  # info, warning, error, success
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(alert)
    
    async def handle_client_message(self, websocket: WebSocket, message: Dict):
        """Handle incoming messages from clients"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "subscribe":
                symbols = message.get("symbols", [])
                await self.handle_subscription(websocket, symbols)
            
            elif msg_type == "unsubscribe":
                symbols = message.get("symbols", [])
                await self.handle_unsubscription(websocket, symbols)
            
            elif msg_type == "ping":
                await self.send_personal_message(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "request_snapshot":
                # Send current market data snapshot
                symbols = message.get("symbols", list(self.market_data_cache.keys()))
                for symbol in symbols:
                    if symbol in self.market_data_cache:
                        await self.send_personal_message(websocket, {
                            "type": "market_data",
                            "symbol": symbol,
                            "data": self.market_data_cache[symbol],
                            "snapshot": True,
                            "timestamp": datetime.now().isoformat()
                        })
            
            else:
                await self.send_personal_message(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                    "timestamp": datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
            await self.send_personal_message(websocket, {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })


# Global WebSocket manager instance
ws_manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint handler for FastAPI"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            await ws_manager.handle_client_message(websocket, data)
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)