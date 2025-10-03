"""
AuraQuant Real-Time Market Data Connector
The Infinity Money Synthetic Intelligence System
Multi-Broker WebSocket & REST API Integration with Failover
"""

import asyncio
import aiohttp
import websockets
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys
from collections import deque
import time

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_db_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Available market data sources"""
    BINANCE = "binance"
    ALPACA = "alpaca"
    POLYGON = "polygon"
    FINNHUB = "finnhub"
    YAHOO_FINANCE = "yahoo_finance"
    TRADINGVIEW = "tradingview"
    IBKR = "ibkr"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    FTX = "ftx"  # If available
    DERIBIT = "deribit"  # Options
    CME = "cme"  # Futures

class MarketType(Enum):
    """Market types"""
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    FUTURES = "futures"
    OPTIONS = "options"
    COMMODITIES = "commodities"
    INDICES = "indices"

@dataclass
class MarketTick:
    """Real-time market tick data"""
    symbol: str
    source: str
    timestamp: datetime
    bid: float
    ask: float
    last: float
    volume: float
    bid_size: float
    ask_size: float
    market_type: str
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'source': self.source,
            'timestamp': self.timestamp,
            'bid': self.bid,
            'ask': self.ask,
            'last': self.last,
            'volume': self.volume,
            'bid_size': self.bid_size,
            'ask_size': self.ask_size,
            'market_type': self.market_type
        }

@dataclass
class OrderBook:
    """Order book snapshot"""
    symbol: str
    timestamp: datetime
    bids: List[Tuple[float, float]]  # [(price, size), ...]
    asks: List[Tuple[float, float]]  # [(price, size), ...]
    
    def get_spread(self) -> float:
        """Get bid-ask spread"""
        if self.bids and self.asks:
            return self.asks[0][0] - self.bids[0][0]
        return 0.0
    
    def get_mid_price(self) -> float:
        """Get mid price"""
        if self.bids and self.asks:
            return (self.asks[0][0] + self.bids[0][0]) / 2
        return 0.0

class RealTimeMarketConnector:
    """
    Real-Time Market Data Connector with:
    - Multi-source WebSocket connections
    - REST API fallback
    - Auto-reconnection and failover
    - Data normalization
    - Latency monitoring
    - Rate limiting
    """
    
    def __init__(self):
        """Initialize the Market Connector"""
        self.db_config = get_db_config()
        self.db = None
        
        # Connection management
        self.connections = {}  # Active WebSocket connections
        self.subscriptions = {}  # Symbol subscriptions by source
        self.callbacks = {}  # Data callbacks
        
        # Data buffers
        self.tick_buffer = deque(maxlen=10000)  # Recent ticks
        self.orderbook_cache = {}  # Latest order books
        
        # Performance tracking
        self.latency_stats = {}
        self.message_counts = {}
        self.error_counts = {}
        
        # Rate limiting
        self.rate_limits = {
            DataSource.BINANCE: {'requests_per_minute': 1200},
            DataSource.ALPACA: {'requests_per_minute': 200},
            DataSource.POLYGON: {'requests_per_second': 100},
            DataSource.FINNHUB: {'requests_per_minute': 60},
            DataSource.COINBASE: {'requests_per_second': 10},
        }
        self.rate_trackers = {}
        
        # Failover configuration
        self.primary_sources = {
            MarketType.CRYPTO: DataSource.BINANCE,
            MarketType.STOCKS: DataSource.ALPACA,
            MarketType.FOREX: DataSource.FINNHUB,
            MarketType.FUTURES: DataSource.CME,
            MarketType.OPTIONS: DataSource.DERIBIT
        }
        
        self.fallback_sources = {
            MarketType.CRYPTO: [DataSource.COINBASE, DataSource.KRAKEN],
            MarketType.STOCKS: [DataSource.POLYGON, DataSource.FINNHUB],
            MarketType.FOREX: [DataSource.ALPACA],
            MarketType.FUTURES: [DataSource.IBKR],
            MarketType.OPTIONS: [DataSource.IBKR]
        }
        
        # WebSocket URLs
        self.ws_urls = {
            DataSource.BINANCE: "wss://stream.binance.com:9443/ws",
            DataSource.ALPACA: "wss://stream.data.alpaca.markets/v2/sip",
            DataSource.POLYGON: "wss://socket.polygon.io/stocks",
            DataSource.FINNHUB: "wss://ws.finnhub.io",
            DataSource.COINBASE: "wss://ws-feed.exchange.coinbase.com",
            DataSource.KRAKEN: "wss://ws.kraken.com",
            DataSource.DERIBIT: "wss://www.deribit.com/ws/api/v2"
        }
        
        # REST endpoints
        self.rest_urls = {
            DataSource.BINANCE: "https://api.binance.com/api/v3",
            DataSource.ALPACA: "https://data.alpaca.markets/v2",
            DataSource.POLYGON: "https://api.polygon.io/v2",
            DataSource.FINNHUB: "https://finnhub.io/api/v1",
            DataSource.COINBASE: "https://api.exchange.coinbase.com",
            DataSource.YAHOO_FINANCE: "https://query1.finance.yahoo.com/v8"
        }
        
        # Connection status
        self.is_running = False
        self.reconnect_delays = {}  # Exponential backoff
        
        logger.info("📡 Real-Time Market Connector initialized")
    
    async def connect(self):
        """Connect to MongoDB and initialize connections"""
        if self.db_config.async_client:
            self.db = self.db_config.async_db
            logger.info("✅ Market Connector connected to MongoDB")
    
    async def start(self):
        """Start all market data connections"""
        self.is_running = True
        
        # Start WebSocket connections for each market type
        tasks = []
        for market_type in MarketType:
            source = self.primary_sources.get(market_type)
            if source:
                task = asyncio.create_task(self._connect_websocket(source))
                tasks.append(task)
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self._monitor_connections())
        tasks.append(monitor_task)
        
        # Start data processor
        processor_task = asyncio.create_task(self._process_data())
        tasks.append(processor_task)
        
        logger.info("🚀 Market data connections starting...")
        
        # Wait for all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(
        self,
        symbols: List[str],
        market_type: MarketType,
        callback: Optional[Callable] = None
    ):
        """
        Subscribe to real-time data for symbols
        
        Args:
            symbols: List of symbols to subscribe
            market_type: Type of market
            callback: Optional callback for data
        """
        
        source = self.primary_sources.get(market_type)
        if not source:
            logger.error(f"No data source for market type: {market_type}")
            return
        
        # Store subscription
        if source not in self.subscriptions:
            self.subscriptions[source] = set()
        
        self.subscriptions[source].update(symbols)
        
        # Store callback if provided
        if callback:
            for symbol in symbols:
                if symbol not in self.callbacks:
                    self.callbacks[symbol] = []
                self.callbacks[symbol].append(callback)
        
        # Send subscription message if connected
        if source in self.connections:
            await self._send_subscription(source, symbols)
        
        logger.info(f"📊 Subscribed to {len(symbols)} symbols on {source.value}")
    
    async def _connect_websocket(self, source: DataSource):
        """Connect to WebSocket data source"""
        
        if source not in self.ws_urls:
            logger.warning(f"No WebSocket URL for {source.value}")
            return
        
        url = self.ws_urls[source]
        retry_count = 0
        max_retries = 5
        
        while self.is_running and retry_count < max_retries:
            try:
                # Get authentication if needed
                headers = await self._get_auth_headers(source)
                
                # Connect to WebSocket
                async with websockets.connect(url, extra_headers=headers) as ws:
                    self.connections[source] = ws
                    logger.info(f"✅ Connected to {source.value} WebSocket")
                    
                    # Reset retry count on successful connection
                    retry_count = 0
                    
                    # Send initial subscriptions
                    if source in self.subscriptions:
                        await self._send_subscription(source, list(self.subscriptions[source]))
                    
                    # Listen for messages
                    await self._listen_websocket(source, ws)
                    
            except Exception as e:
                retry_count += 1
                delay = min(60, 2 ** retry_count)  # Exponential backoff
                logger.error(f"WebSocket error for {source.value}: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                
                # Try fallback source if max retries reached
                if retry_count >= max_retries:
                    await self._activate_fallback(source)
    
    async def _listen_websocket(self, source: DataSource, ws):
        """Listen for WebSocket messages"""
        
        try:
            async for message in ws:
                # Record message receipt time
                receipt_time = time.time()
                
                # Parse message
                data = json.loads(message)
                
                # Process based on source
                tick = await self._parse_tick(source, data)
                
                if tick:
                    # Calculate latency
                    if 'timestamp' in data:
                        latency = receipt_time - (data['timestamp'] / 1000)
                        self._update_latency(source, latency)
                    
                    # Store tick
                    self.tick_buffer.append(tick)
                    
                    # Execute callbacks
                    await self._execute_callbacks(tick)
                    
                    # Store in database
                    await self._store_tick(tick)
                    
                # Update message count
                self.message_counts[source] = self.message_counts.get(source, 0) + 1
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"WebSocket connection closed for {source.value}")
            del self.connections[source]
        except Exception as e:
            logger.error(f"Error processing WebSocket message from {source.value}: {e}")
            self.error_counts[source] = self.error_counts.get(source, 0) + 1
    
    async def _send_subscription(self, source: DataSource, symbols: List[str]):
        """Send subscription message to WebSocket"""
        
        if source not in self.connections:
            return
        
        ws = self.connections[source]
        
        # Format subscription message based on source
        if source == DataSource.BINANCE:
            # Binance stream format
            streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
            message = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": 1
            }
            
        elif source == DataSource.ALPACA:
            # Alpaca format
            message = {
                "action": "subscribe",
                "trades": symbols,
                "quotes": symbols
            }
            
        elif source == DataSource.COINBASE:
            # Coinbase format
            message = {
                "type": "subscribe",
                "product_ids": symbols,
                "channels": ["ticker", "level2"]
            }
            
        elif source == DataSource.POLYGON:
            # Polygon format
            message = {
                "action": "subscribe",
                "params": ",".join([f"T.{s}" for s in symbols])
            }
            
        else:
            logger.warning(f"Subscription format not implemented for {source.value}")
            return
        
        # Send subscription
        await ws.send(json.dumps(message))
        logger.info(f"📤 Sent subscription for {len(symbols)} symbols to {source.value}")
    
    async def _parse_tick(self, source: DataSource, data: Dict) -> Optional[MarketTick]:
        """Parse tick data from different sources"""
        
        try:
            if source == DataSource.BINANCE:
                # Binance ticker format
                if 'e' in data and data['e'] == '24hrTicker':
                    return MarketTick(
                        symbol=data['s'],
                        source=source.value,
                        timestamp=datetime.fromtimestamp(data['E'] / 1000),
                        bid=float(data['b']),
                        ask=float(data['a']),
                        last=float(data['c']),
                        volume=float(data['v']),
                        bid_size=float(data['B']),
                        ask_size=float(data['A']),
                        market_type=MarketType.CRYPTO.value
                    )
                    
            elif source == DataSource.ALPACA:
                # Alpaca format
                if data.get('T') == 'q':  # Quote
                    return MarketTick(
                        symbol=data['S'],
                        source=source.value,
                        timestamp=datetime.fromisoformat(data['t']),
                        bid=float(data['bp']),
                        ask=float(data['ap']),
                        last=float(data.get('p', data['bp'])),
                        volume=0,
                        bid_size=float(data['bs']),
                        ask_size=float(data['as']),
                        market_type=MarketType.STOCKS.value
                    )
                    
            elif source == DataSource.COINBASE:
                # Coinbase format
                if data.get('type') == 'ticker':
                    return MarketTick(
                        symbol=data['product_id'],
                        source=source.value,
                        timestamp=datetime.fromisoformat(data['time'].replace('Z', '+00:00')),
                        bid=float(data['best_bid']),
                        ask=float(data['best_ask']),
                        last=float(data['price']),
                        volume=float(data['volume_24h']),
                        bid_size=float(data.get('best_bid_size', 0)),
                        ask_size=float(data.get('best_ask_size', 0)),
                        market_type=MarketType.CRYPTO.value
                    )
                    
            # Add more source parsers as needed
            
        except Exception as e:
            logger.error(f"Error parsing tick from {source.value}: {e}")
            
        return None
    
    async def get_quote(
        self,
        symbol: str,
        market_type: MarketType
    ) -> Optional[MarketTick]:
        """
        Get latest quote via REST API
        
        Args:
            symbol: Trading symbol
            market_type: Type of market
            
        Returns:
            Latest market tick or None
        """
        
        source = self.primary_sources.get(market_type)
        if not source:
            return None
        
        # Check rate limit
        if not await self._check_rate_limit(source):
            # Try fallback source
            for fallback in self.fallback_sources.get(market_type, []):
                if await self._check_rate_limit(fallback):
                    source = fallback
                    break
            else:
                logger.warning(f"Rate limited on all sources for {market_type.value}")
                return None
        
        try:
            # Make REST API call based on source
            if source == DataSource.BINANCE:
                url = f"{self.rest_urls[source]}/ticker/24hr"
                params = {'symbol': symbol}
                
            elif source == DataSource.ALPACA:
                url = f"{self.rest_urls[source]}/stocks/{symbol}/quotes/latest"
                params = {}
                
            elif source == DataSource.POLYGON:
                url = f"{self.rest_urls[source]}/last/trade/{symbol}"
                params = {'apiKey': os.getenv('POLYGON_API_KEY')}
                
            else:
                logger.warning(f"REST API not implemented for {source.value}")
                return None
            
            # Make request
            headers = await self._get_auth_headers(source)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse response based on source
                        tick = await self._parse_rest_response(source, data, symbol, market_type)
                        
                        # Update rate limit tracker
                        self._update_rate_limit(source)
                        
                        return tick
                    else:
                        logger.error(f"REST API error {response.status} from {source.value}")
                        
        except Exception as e:
            logger.error(f"Error getting quote from {source.value}: {e}")
            
        return None
    
    async def get_orderbook(
        self,
        symbol: str,
        market_type: MarketType,
        depth: int = 10
    ) -> Optional[OrderBook]:
        """
        Get order book snapshot
        
        Args:
            symbol: Trading symbol
            market_type: Type of market
            depth: Order book depth
            
        Returns:
            OrderBook or None
        """
        
        # Check cache first
        cache_key = f"{symbol}:{market_type.value}"
        if cache_key in self.orderbook_cache:
            cached = self.orderbook_cache[cache_key]
            # Return if fresh (< 1 second old)
            if (datetime.now() - cached['timestamp']).total_seconds() < 1:
                return cached['orderbook']
        
        source = self.primary_sources.get(market_type)
        if not source:
            return None
        
        try:
            # Get order book based on source
            if source == DataSource.BINANCE:
                url = f"{self.rest_urls[source]}/depth"
                params = {'symbol': symbol, 'limit': depth}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            orderbook = OrderBook(
                                symbol=symbol,
                                timestamp=datetime.now(),
                                bids=[(float(p), float(q)) for p, q in data['bids']],
                                asks=[(float(p), float(q)) for p, q in data['asks']]
                            )
                            
                            # Cache order book
                            self.orderbook_cache[cache_key] = {
                                'orderbook': orderbook,
                                'timestamp': datetime.now()
                            }
                            
                            return orderbook
                            
        except Exception as e:
            logger.error(f"Error getting order book from {source.value}: {e}")
            
        return None
    
    async def get_historical_data(
        self,
        symbol: str,
        market_type: MarketType,
        interval: str = '1h',
        limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data
        
        Args:
            symbol: Trading symbol
            market_type: Type of market
            interval: Time interval (1m, 5m, 15m, 1h, 1d)
            limit: Number of candles
            
        Returns:
            DataFrame with OHLCV data or None
        """
        
        source = self.primary_sources.get(market_type)
        if not source:
            return None
        
        try:
            if source == DataSource.BINANCE:
                url = f"{self.rest_urls[source]}/klines"
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'limit': limit
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Parse to DataFrame
                            df = pd.DataFrame(data, columns=[
                                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                                'close_time', 'quote_volume', 'trades', 'buy_base',
                                'buy_quote', 'ignore'
                            ])
                            
                            # Convert types
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                            for col in ['open', 'high', 'low', 'close', 'volume']:
                                df[col] = df[col].astype(float)
                            
                            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
                            
        except Exception as e:
            logger.error(f"Error getting historical data from {source.value}: {e}")
            
        return None
    
    async def _monitor_connections(self):
        """Monitor connection health and statistics"""
        
        while self.is_running:
            try:
                # Check connection status
                for source in list(self.connections.keys()):
                    ws = self.connections[source]
                    if ws.closed:
                        logger.warning(f"Connection lost to {source.value}")
                        del self.connections[source]
                        
                        # Attempt reconnection
                        asyncio.create_task(self._connect_websocket(source))
                
                # Log statistics
                stats = {
                    'active_connections': len(self.connections),
                    'message_counts': self.message_counts,
                    'error_counts': self.error_counts,
                    'avg_latencies': {
                        source.value: np.mean(latencies) if latencies else 0
                        for source, latencies in self.latency_stats.items()
                    }
                }
                
                logger.info(f"📊 Market Data Stats: {stats}")
                
                # Store stats in database
                if self.db:
                    await self.db.market_data_stats.insert_one({
                        **stats,
                        'timestamp': datetime.now()
                    })
                
                # Clear old latency data
                for source in self.latency_stats:
                    if len(self.latency_stats[source]) > 1000:
                        self.latency_stats[source] = self.latency_stats[source][-100:]
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(5)
    
    async def _process_data(self):
        """Process incoming market data"""
        
        while self.is_running:
            try:
                # Process tick buffer
                if len(self.tick_buffer) > 0:
                    # Batch process ticks
                    batch_size = min(100, len(self.tick_buffer))
                    batch = []
                    
                    for _ in range(batch_size):
                        if self.tick_buffer:
                            batch.append(self.tick_buffer.popleft())
                    
                    # Analyze batch for anomalies
                    await self._detect_anomalies(batch)
                    
                    # Calculate market metrics
                    await self._calculate_metrics(batch)
                
                await asyncio.sleep(0.1)  # Process every 100ms
                
            except Exception as e:
                logger.error(f"Error in data processor: {e}")
                await asyncio.sleep(1)
    
    async def _detect_anomalies(self, ticks: List[MarketTick]):
        """Detect anomalies in market data"""
        
        for tick in ticks:
            # Check for suspicious spreads
            if tick.ask > 0 and tick.bid > 0:
                spread_pct = (tick.ask - tick.bid) / tick.bid * 100
                
                if spread_pct > 5:  # > 5% spread
                    logger.warning(f"⚠️ Large spread detected: {tick.symbol} - {spread_pct:.2f}%")
                    
                    # Store anomaly
                    if self.db:
                        await self.db.market_anomalies.insert_one({
                            'type': 'large_spread',
                            'symbol': tick.symbol,
                            'spread_pct': spread_pct,
                            'tick': tick.to_dict(),
                            'timestamp': datetime.now()
                        })
    
    async def _calculate_metrics(self, ticks: List[MarketTick]):
        """Calculate market metrics from ticks"""
        
        # Group by symbol
        symbol_ticks = {}
        for tick in ticks:
            if tick.symbol not in symbol_ticks:
                symbol_ticks[tick.symbol] = []
            symbol_ticks[tick.symbol].append(tick)
        
        # Calculate metrics per symbol
        for symbol, symbol_tick_list in symbol_ticks.items():
            if len(symbol_tick_list) > 0:
                # Calculate average spread
                spreads = [(t.ask - t.bid) for t in symbol_tick_list if t.ask > 0 and t.bid > 0]
                avg_spread = np.mean(spreads) if spreads else 0
                
                # Calculate price volatility
                prices = [t.last for t in symbol_tick_list if t.last > 0]
                volatility = np.std(prices) / np.mean(prices) if len(prices) > 1 else 0
                
                # Store metrics
                if self.db:
                    await self.db.market_metrics.insert_one({
                        'symbol': symbol,
                        'avg_spread': avg_spread,
                        'volatility': volatility,
                        'tick_count': len(symbol_tick_list),
                        'timestamp': datetime.now()
                    })
    
    async def _activate_fallback(self, failed_source: DataSource):
        """Activate fallback data source"""
        
        # Find market type for failed source
        market_type = None
        for mt, source in self.primary_sources.items():
            if source == failed_source:
                market_type = mt
                break
        
        if not market_type:
            return
        
        # Try fallback sources
        for fallback in self.fallback_sources.get(market_type, []):
            if fallback not in self.connections:
                logger.info(f"🔄 Activating fallback source: {fallback.value}")
                await self._connect_websocket(fallback)
                
                # Update primary source temporarily
                self.primary_sources[market_type] = fallback
                break
    
    async def _get_auth_headers(self, source: DataSource) -> Dict:
        """Get authentication headers for source"""
        
        headers = {}
        
        if source == DataSource.ALPACA:
            headers = {
                'APCA-API-KEY-ID': os.getenv('ALPACA_API_KEY'),
                'APCA-API-SECRET-KEY': os.getenv('ALPACA_SECRET')
            }
        elif source == DataSource.POLYGON:
            # Polygon uses query params for auth
            pass
        elif source == DataSource.FINNHUB:
            headers = {
                'X-Finnhub-Token': os.getenv('FINNHUB_API_KEY')
            }
        
        return headers
    
    async def _check_rate_limit(self, source: DataSource) -> bool:
        """Check if we're within rate limits"""
        
        if source not in self.rate_limits:
            return True
        
        if source not in self.rate_trackers:
            self.rate_trackers[source] = []
        
        # Clean old entries
        now = time.time()
        limit_config = self.rate_limits[source]
        
        if 'requests_per_minute' in limit_config:
            window = 60
            limit = limit_config['requests_per_minute']
        elif 'requests_per_second' in limit_config:
            window = 1
            limit = limit_config['requests_per_second']
        else:
            return True
        
        # Remove old entries
        self.rate_trackers[source] = [
            t for t in self.rate_trackers[source]
            if now - t < window
        ]
        
        # Check if we can make request
        return len(self.rate_trackers[source]) < limit
    
    def _update_rate_limit(self, source: DataSource):
        """Update rate limit tracker"""
        
        if source not in self.rate_trackers:
            self.rate_trackers[source] = []
        
        self.rate_trackers[source].append(time.time())
    
    def _update_latency(self, source: DataSource, latency: float):
        """Update latency statistics"""
        
        if source not in self.latency_stats:
            self.latency_stats[source] = []
        
        self.latency_stats[source].append(latency)
    
    async def _execute_callbacks(self, tick: MarketTick):
        """Execute callbacks for tick data"""
        
        if tick.symbol in self.callbacks:
            for callback in self.callbacks[tick.symbol]:
                try:
                    await callback(tick)
                except Exception as e:
                    logger.error(f"Error executing callback: {e}")
    
    async def _store_tick(self, tick: MarketTick):
        """Store tick in database"""
        
        if self.db:
            await self.db.market_ticks.insert_one(tick.to_dict())
    
    async def _parse_rest_response(
        self,
        source: DataSource,
        data: Dict,
        symbol: str,
        market_type: MarketType
    ) -> Optional[MarketTick]:
        """Parse REST API response"""
        
        try:
            if source == DataSource.BINANCE:
                return MarketTick(
                    symbol=symbol,
                    source=source.value,
                    timestamp=datetime.now(),
                    bid=float(data['bidPrice']),
                    ask=float(data['askPrice']),
                    last=float(data['lastPrice']),
                    volume=float(data['volume']),
                    bid_size=float(data['bidQty']),
                    ask_size=float(data['askQty']),
                    market_type=market_type.value
                )
            
            # Add more parsers as needed
            
        except Exception as e:
            logger.error(f"Error parsing REST response from {source.value}: {e}")
            
        return None
    
    async def stop(self):
        """Stop all connections"""
        
        self.is_running = False
        
        # Close all WebSocket connections
        for source, ws in self.connections.items():
            await ws.close()
            logger.info(f"Closed connection to {source.value}")
        
        self.connections.clear()
        
        logger.info("🛑 Market data connector stopped")

# Export the connector
market_connector = RealTimeMarketConnector()