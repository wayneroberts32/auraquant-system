"""
Market Data Routes
Handles market data endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import random

router = APIRouter()

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Get current quote for a symbol"""
    # Simulated data - replace with real market data
    base_price = random.uniform(50, 500)
    return {
        "symbol": symbol,
        "price": base_price,
        "bid": base_price - 0.05,
        "ask": base_price + 0.05,
        "volume": random.randint(1000000, 10000000),
        "change": random.uniform(-5, 5),
        "change_percent": random.uniform(-2, 2)
    }

@router.get("/candles/{symbol}")
async def get_candles(symbol: str, interval: str = "1h", limit: int = 100):
    """Get historical candle data"""
    return {
        "symbol": symbol,
        "interval": interval,
        "candles": [
            {
                "timestamp": f"2025-01-{i:02d}T00:00:00Z",
                "open": 100 + i,
                "high": 102 + i,
                "low": 99 + i,
                "close": 101 + i,
                "volume": 1000000 + i * 10000
            } for i in range(1, min(limit + 1, 31))
        ]
    }

@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str):
    """Get technical indicators for a symbol"""
    return {
        "symbol": symbol,
        "rsi": random.uniform(30, 70),
        "macd": {
            "macd": random.uniform(-1, 1),
            "signal": random.uniform(-0.5, 0.5),
            "histogram": random.uniform(-0.2, 0.2)
        },
        "sma_20": random.uniform(95, 105),
        "sma_50": random.uniform(90, 110),
        "bollinger_bands": {
            "upper": random.uniform(105, 115),
            "middle": random.uniform(95, 105),
            "lower": random.uniform(85, 95)
        }
    }