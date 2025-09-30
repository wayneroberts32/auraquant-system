"""
AuraQuant Real Market Data Manager
===================================
Multi-broker real-time data feeds with failover
Created: 2025-01-30
"""

import asyncio
import websockets
import aiohttp
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json
import time
from collections import deque
from enum import Enum

class DataSource(Enum):
    IBKR = "INTERACTIVE_BROKERS"
    BINANCE = "BINANCE"
    ALPACA = "ALPACA"
    PLUS500 = "PLUS500"
    TRADINGVIEW = "TRADINGVIEW"
    YAHOO = "YAHOO_FINANCE"
    ALPHA_VANTAGE = "ALPHA_VANTAGE"

@dataclass
class MarketTick:
    symbol: str
    timestamp: float
    bid: float
    ask: float
    last: float
    volume: float
    source: DataSource
    latency_ms: float

@dataclass 
class GapEvent:
    symbol: str
    timestamp: float
    gap_size: float
    gap_type: str  # "UP" or "DOWN"
    pre_gap_price: float
    post_gap_price: float

class MarketDataManager:
    """
    Real-time market data management with failover
    Sub-50ms latency processing
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.active_feeds = {}
        self.websocket_connections = {}
        self.data_buffer = defaultdict(lambda: deque(maxlen=10000))
        self.latency_tracker = defaultdict(list)
        self.gap_detector = GapDetector()
        self.repainting_protector = RepaintingProtector()
        
        # Connection configurations
        self.feed_configs = {
            DataSource.BINANCE: {
                'ws_url': 'wss://stream.binance.com:9443/ws',
                'rest_url': 'https://api.binance.com/api/v3',
                'priority': 1
            },
            DataSource.ALPACA: {
                'ws_url': 'wss://stream.data.alpaca.markets/v2/iex',
                'rest_url': 'https://data.alpaca.markets/v2',
                'priority': 2
            },
            DataSource.IBKR: {
                'host': 'localhost',
                'port': 7497,
                'priority': 1
            }
        }
        
        self.failover_sources = [
            DataSource.TRADINGVIEW,
            DataSource.YAHOO,
            DataSource.ALPHA_VANTAGE
        ]
        
        self.target_latency_ms = 50  # Sub-50ms target
        
    async def connect_all_feeds(self):
        """Connect to all primary data feeds"""
        tasks = []
        
        # Connect to primary sources
        for source, config in self.feed_configs.items():
            if 'ws_url' in config:
                tasks.append(self._connect_websocket(source, config))
            else:
                tasks.append(self._connect_api(source, config))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _connect_websocket(self, source: DataSource, config: Dict):
        """Connect to WebSocket feed"""
        try:
            ws = await websockets.connect(config['ws_url'])
            self.websocket_connections[source] = ws
            
            # Start listening
            asyncio.create_task(self._listen_websocket(source, ws))
            
            print(f"✓ Connected to {source.value} WebSocket")
        except Exception as e:
            print(f"✗ Failed to connect {source.value}: {e}")
            await self._activate_failover(source)
    
    async def _listen_websocket(self, source: DataSource, ws):
        """Listen to WebSocket stream"""
        while True:
            try:
                start_time = time.time()
                message = await ws.recv()
                data = json.loads(message)
                
                # Process tick
                tick = self._parse_tick(source, data)
                tick.latency_ms = (time.time() - start_time) * 1000
                
                # Check latency
                if tick.latency_ms > self.target_latency_ms:
                    print(f"⚠ High latency on {source.value}: {tick.latency_ms:.2f}ms")
                
                # Store tick
                await self._process_tick(tick)
                
            except Exception as e:
                print(f"WebSocket error {source.value}: {e}")
                await self._reconnect_websocket(source)
                break
    
    async def _process_tick(self, tick: MarketTick):
        """Process incoming market tick"""
        # Check for gaps
        gap = self.gap_detector.check_gap(tick)
        if gap:
            await self._handle_gap(gap)
        
        # Check for repainting
        if not self.repainting_protector.validate_tick(tick):
            return  # Skip potentially repainting data
        
        # Store in buffer
        self.data_buffer[tick.symbol].append(tick)
        
        # Track latency
        self.latency_tracker[tick.source].append(tick.latency_ms)
        
        # Store in MongoDB if configured
        if self.mongodb:
            await self._store_tick(tick)
    
    async def _activate_failover(self, failed_source: DataSource):
        """Activate failover data source"""
        for fallback in self.failover_sources:
            try:
                if fallback == DataSource.TRADINGVIEW:
                    await self._connect_tradingview_webhook()
                elif fallback == DataSource.YAHOO:
                    await self._connect_yahoo_finance()
                
                print(f"✓ Failover activated: {fallback.value}")
                break
            except:
                continue
    
    async def get_real_time_data(self, symbol: str) -> Optional[MarketTick]:
        """Get latest tick for symbol"""
        if symbol in self.data_buffer and self.data_buffer[symbol]:
            return self.data_buffer[symbol][-1]
        return None
    
    def get_average_latency(self) -> Dict[DataSource, float]:
        """Get average latency per source"""
        return {
            source: np.mean(latencies) if latencies else 0
            for source, latencies in self.latency_tracker.items()
        }
    
    def _parse_tick(self, source: DataSource, data: Dict) -> MarketTick:
        """Parse tick data from different sources"""
        # Simplified parser - would be source-specific in production
        return MarketTick(
            symbol=data.get('s', 'UNKNOWN'),
            timestamp=time.time(),
            bid=float(data.get('b', 0)),
            ask=float(data.get('a', 0)),
            last=float(data.get('p', 0)),
            volume=float(data.get('v', 0)),
            source=source,
            latency_ms=0
        )

class GapDetector:
    """Detect and handle market gaps"""
    
    def __init__(self):
        self.last_prices = {}
        self.gap_threshold = 0.02  # 2% gap threshold
        
    def check_gap(self, tick: MarketTick) -> Optional[GapEvent]:
        """Check for price gaps"""
        if tick.symbol not in self.last_prices:
            self.last_prices[tick.symbol] = tick.last
            return None
        
        last_price = self.last_prices[tick.symbol]
        gap_pct = abs(tick.last - last_price) / last_price
        
        if gap_pct > self.gap_threshold:
            gap = GapEvent(
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                gap_size=gap_pct,
                gap_type="UP" if tick.last > last_price else "DOWN",
                pre_gap_price=last_price,
                post_gap_price=tick.last
            )
            
            self.last_prices[tick.symbol] = tick.last
            return gap
        
        self.last_prices[tick.symbol] = tick.last
        return None

class RepaintingProtector:
    """Protect against repainting indicators"""
    
    def __init__(self):
        self.confirmed_bars = {}
        self.bar_close_only = True
        
    def validate_tick(self, tick: MarketTick) -> bool:
        """Validate tick to prevent repainting"""
        if not self.bar_close_only:
            return True
        
        # Only use bar close prices
        current_minute = int(tick.timestamp / 60)
        
        if tick.symbol not in self.confirmed_bars:
            self.confirmed_bars[tick.symbol] = current_minute
            return False
        
        if current_minute > self.confirmed_bars[tick.symbol]:
            self.confirmed_bars[tick.symbol] = current_minute
            return True
        
        return False