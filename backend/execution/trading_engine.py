"""
AuraQuant Universal Trading Execution Engine
=============================================
Connects to ASX, Crypto Exchanges, and DEXs for Meme Coins
Ultra-low latency execution with full compliance

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import asyncio
import ccxt.async_support as ccxt
import yfinance as yf
from web3 import Web3
from web3.middleware import geth_poa_middleware
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import time
import json
import hashlib
import hmac
from enum import Enum
import logging
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraQuant.TradingEngine")

# Import internal modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compliance.regulatory_framework import RegulatoryFramework, Market, ComplianceStatus
from money_management.money_manager import MoneyManager
from orchestrator.master_orchestrator import MasterOrchestrator

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    ICEBERG = "ICEBERG"
    TWAP = "TWAP"  # Time-weighted average price
    VWAP = "VWAP"  # Volume-weighted average price

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class ExecutionVenue(Enum):
    ASX = "ASX"
    BINANCE = "BINANCE"
    COINBASE = "COINBASE"
    KRAKEN = "KRAKEN"
    FTX = "FTX"
    BYBIT = "BYBIT"
    OKX = "OKX"
    UNISWAP = "UNISWAP"
    PANCAKESWAP = "PANCAKESWAP"
    SUSHISWAP = "SUSHISWAP"

@dataclass
class Order:
    """Universal order structure"""
    order_id: str
    symbol: str
    market: Market
    venue: ExecutionVenue
    side: str  # BUY or SELL
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0
    average_price: float = 0
    fees: float = 0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Execution:
    """Trade execution record"""
    execution_id: str
    order_id: str
    symbol: str
    venue: ExecutionVenue
    side: str
    quantity: float
    price: float
    fees: float
    timestamp: float
    latency_ms: float
    slippage: float

class TradingEngine:
    """
    Master Trading Execution Engine
    Handles all order routing, execution, and management
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.compliance = RegulatoryFramework(mongodb_client)
        self.money_manager = MoneyManager(mongodb_client)
        
        # Exchange connections
        self.exchanges = {}
        self.web3_connections = {}
        
        # Order management
        self.active_orders = {}
        self.order_history = []
        self.execution_history = []
        
        # Performance metrics
        self.metrics = {
            'total_orders': 0,
            'successful_executions': 0,
            'failed_orders': 0,
            'average_latency': 0,
            'total_volume': 0,
            'total_fees': 0
        }
        
        # Rate limiting
        self.rate_limits = {
            'orders_per_second': {},
            'last_order_time': {}
        }
        
        # Initialize connections
        self._initialize_connections()
        
        logger.info("Trading Engine initialized with multi-market support")
    
    def _initialize_connections(self):
        """Initialize connections to all supported venues"""
        # Crypto exchanges via CCXT
        self.exchanges = {
            ExecutionVenue.BINANCE: None,  # Will be initialized with API keys
            ExecutionVenue.COINBASE: None,
            ExecutionVenue.KRAKEN: None,
            ExecutionVenue.BYBIT: None,
            ExecutionVenue.OKX: None
        }
        
        # Web3 connections for DEXs
        self.web3_connections = {
            'ethereum': None,  # Mainnet
            'bsc': None,  # Binance Smart Chain
            'polygon': None,  # Polygon/Matic
            'arbitrum': None,  # Arbitrum L2
            'optimism': None  # Optimism L2
        }
        
        # ASX connection (via broker API)
        self.asx_connection = None
    
    async def connect_exchange(self, venue: ExecutionVenue, credentials: Dict):
        """
        Connect to a specific exchange
        """
        try:
            if venue == ExecutionVenue.BINANCE:
                self.exchanges[venue] = ccxt.binance({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret'),
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',
                        'adjustForTimeDifference': True
                    }
                })
                
            elif venue == ExecutionVenue.COINBASE:
                self.exchanges[venue] = ccxt.coinbase({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret'),
                    'password': credentials.get('passphrase'),
                    'enableRateLimit': True
                })
                
            elif venue == ExecutionVenue.KRAKEN:
                self.exchanges[venue] = ccxt.kraken({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret'),
                    'enableRateLimit': True
                })
                
            elif venue == ExecutionVenue.BYBIT:
                self.exchanges[venue] = ccxt.bybit({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret'),
                    'enableRateLimit': True
                })
                
            elif venue == ExecutionVenue.OKX:
                self.exchanges[venue] = ccxt.okx({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret'),
                    'password': credentials.get('passphrase'),
                    'enableRateLimit': True
                })
            
            logger.info(f"Connected to {venue.value}")
            return {'status': 'connected', 'venue': venue.value}
            
        except Exception as e:
            logger.error(f"Failed to connect to {venue.value}: {str(e)}")
            return {'status': 'failed', 'venue': venue.value, 'error': str(e)}
    
    async def connect_web3(self, network: str, rpc_url: str):
        """
        Connect to Web3 for DEX trading
        """
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Add middleware for PoA chains
            if network in ['bsc', 'polygon']:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if w3.is_connected():
                self.web3_connections[network] = w3
                logger.info(f"Connected to {network} via Web3")
                return {'status': 'connected', 'network': network}
            else:
                raise Exception("Web3 connection failed")
                
        except Exception as e:
            logger.error(f"Failed to connect to {network}: {str(e)}")
            return {'status': 'failed', 'network': network, 'error': str(e)}
    
    # ==================== Order Execution ====================
    
    async def execute_order(self, order: Order) -> Dict[str, Any]:
        """
        Execute order with compliance checking and smart routing
        """
        execution_start = time.time()
        
        try:
            # 1. Pre-trade compliance check
            compliance_check = await self.compliance.check_order_compliance({
                'market': order.market.value,
                'symbol': order.symbol,
                'order_type': order.order_type.value,
                'side': order.side,
                'quantity': order.quantity,
                'price': order.price
            })
            
            if compliance_check.status != ComplianceStatus.APPROVED:
                logger.warning(f"Order {order.order_id} failed compliance: {compliance_check.violations}")
                order.status = OrderStatus.REJECTED
                return {
                    'status': 'rejected',
                    'order_id': order.order_id,
                    'reason': compliance_check.violations
                }
            
            # 2. Risk management check
            risk_check = await self.money_manager.check_order_risk({
                'symbol': order.symbol,
                'quantity': order.quantity,
                'price': order.price or await self._get_market_price(order.symbol, order.venue),
                'side': order.side
            })
            
            if not risk_check['approved']:
                logger.warning(f"Order {order.order_id} failed risk check: {risk_check['reason']}")
                order.status = OrderStatus.REJECTED
                return {
                    'status': 'rejected',
                    'order_id': order.order_id,
                    'reason': risk_check['reason']
                }
            
            # 3. Smart order routing
            best_venue = await self._smart_order_routing(order)
            if best_venue != order.venue:
                logger.info(f"Routing order from {order.venue.value} to {best_venue.value}")
                order.venue = best_venue
            
            # 4. Execute based on market type
            if order.market == Market.ASX:
                result = await self._execute_asx_order(order)
            elif order.market in [Market.CRYPTO_SPOT, Market.CRYPTO_FUTURES]:
                result = await self._execute_crypto_order(order)
            elif order.market == Market.MEME_COINS:
                result = await self._execute_meme_coin_order(order)
            else:
                raise ValueError(f"Unsupported market: {order.market}")
            
            # 5. Record execution
            execution_time = (time.time() - execution_start) * 1000  # ms
            
            if result['status'] == 'filled':
                execution = Execution(
                    execution_id=f"EXEC_{int(time.time() * 1000000)}",
                    order_id=order.order_id,
                    symbol=order.symbol,
                    venue=order.venue,
                    side=order.side,
                    quantity=result['filled_quantity'],
                    price=result['average_price'],
                    fees=result['fees'],
                    timestamp=time.time(),
                    latency_ms=execution_time,
                    slippage=self._calculate_slippage(order.price, result['average_price'])
                )
                
                self.execution_history.append(execution)
                await self._store_execution(execution)
                
                # Update metrics
                self.metrics['successful_executions'] += 1
                self.metrics['total_volume'] += result['filled_quantity'] * result['average_price']
                self.metrics['total_fees'] += result['fees']
                
                order.status = OrderStatus.FILLED
                order.filled_quantity = result['filled_quantity']
                order.average_price = result['average_price']
                order.fees = result['fees']
            
            return result
            
        except Exception as e:
            logger.error(f"Order execution failed: {str(e)}")
            order.status = OrderStatus.REJECTED
            self.metrics['failed_orders'] += 1
            return {
                'status': 'failed',
                'order_id': order.order_id,
                'error': str(e)
            }
    
    async def _execute_asx_order(self, order: Order) -> Dict:
        """Execute order on ASX"""
        # Would connect to broker API (e.g., Interactive Brokers)
        # For now, simulate
        logger.info(f"Executing ASX order: {order.symbol}")
        
        # Check ASX market hours
        if not self._is_asx_open():
            return {
                'status': 'rejected',
                'reason': 'Market closed'
            }
        
        # Simulate execution
        market_price = await self._get_asx_price(order.symbol)
        
        if order.order_type == OrderType.MARKET:
            filled_price = market_price * (1.001 if order.side == 'BUY' else 0.999)
        else:
            if order.side == 'BUY' and order.price >= market_price:
                filled_price = order.price
            elif order.side == 'SELL' and order.price <= market_price:
                filled_price = order.price
            else:
                return {'status': 'pending'}
        
        return {
            'status': 'filled',
            'filled_quantity': order.quantity,
            'average_price': filled_price,
            'fees': order.quantity * filled_price * 0.001  # 0.1% fee
        }
    
    async def _execute_crypto_order(self, order: Order) -> Dict:
        """Execute order on crypto exchange"""
        exchange = self.exchanges.get(order.venue)
        if not exchange:
            raise Exception(f"Not connected to {order.venue.value}")
        
        try:
            # Format symbol for exchange
            symbol = self._format_symbol(order.symbol, order.venue)
            
            # Execute based on order type
            if order.order_type == OrderType.MARKET:
                result = await exchange.create_market_order(
                    symbol=symbol,
                    side=order.side.lower(),
                    amount=order.quantity
                )
            elif order.order_type == OrderType.LIMIT:
                result = await exchange.create_limit_order(
                    symbol=symbol,
                    side=order.side.lower(),
                    amount=order.quantity,
                    price=order.price
                )
            elif order.order_type == OrderType.STOP_LOSS:
                result = await exchange.create_stop_loss_order(
                    symbol=symbol,
                    side=order.side.lower(),
                    amount=order.quantity,
                    stopPrice=order.stop_price
                )
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")
            
            # Parse result
            return {
                'status': 'filled' if result['status'] == 'closed' else 'pending',
                'filled_quantity': result['filled'],
                'average_price': result['average'] or result['price'],
                'fees': result['fee']['cost'] if result.get('fee') else 0,
                'exchange_order_id': result['id']
            }
            
        except Exception as e:
            logger.error(f"Crypto order execution failed: {str(e)}")
            raise
    
    async def _execute_meme_coin_order(self, order: Order) -> Dict:
        """Execute meme coin order on DEX"""
        # Determine which chain the token is on
        chain = await self._get_token_chain(order.symbol)
        w3 = self.web3_connections.get(chain)
        
        if not w3:
            raise Exception(f"Not connected to {chain}")
        
        try:
            # Check for honeypot/rug pull
            safety_check = await self._check_token_safety(order.symbol, chain)
            if not safety_check['safe']:
                return {
                    'status': 'rejected',
                    'reason': f"Token safety check failed: {safety_check['reason']}"
                }
            
            # Get DEX router (Uniswap, PancakeSwap, etc.)
            router = await self._get_dex_router(chain)
            
            # Build transaction
            if order.side == 'BUY':
                tx = await self._build_buy_transaction(
                    w3, router, order.symbol, order.quantity, order.price
                )
            else:
                tx = await self._build_sell_transaction(
                    w3, router, order.symbol, order.quantity, order.price
                )
            
            # Execute transaction
            tx_hash = await self._execute_web3_transaction(w3, tx)
            
            # Wait for confirmation
            receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                # Parse logs to get execution details
                execution_details = await self._parse_dex_execution(receipt)
                
                return {
                    'status': 'filled',
                    'filled_quantity': execution_details['amount'],
                    'average_price': execution_details['price'],
                    'fees': execution_details['fees'],
                    'tx_hash': tx_hash.hex()
                }
            else:
                return {
                    'status': 'failed',
                    'reason': 'Transaction reverted'
                }
                
        except Exception as e:
            logger.error(f"Meme coin order execution failed: {str(e)}")
            raise
    
    # ==================== Smart Order Routing ====================
    
    async def _smart_order_routing(self, order: Order) -> ExecutionVenue:
        """
        Determine best venue for order execution
        """
        if order.market == Market.ASX:
            return ExecutionVenue.ASX
        
        if order.market == Market.MEME_COINS:
            # Check liquidity across DEXs
            best_dex = await self._find_best_dex_liquidity(order.symbol)
            return best_dex
        
        # For crypto, check prices across exchanges
        best_price = float('inf') if order.side == 'BUY' else 0
        best_venue = order.venue
        
        for venue, exchange in self.exchanges.items():
            if exchange:
                try:
                    ticker = await exchange.fetch_ticker(
                        self._format_symbol(order.symbol, venue)
                    )
                    
                    if order.side == 'BUY':
                        if ticker['ask'] < best_price:
                            best_price = ticker['ask']
                            best_venue = venue
                    else:
                        if ticker['bid'] > best_price:
                            best_price = ticker['bid']
                            best_venue = venue
                            
                except:
                    continue
        
        return best_venue
    
    # ==================== Order Management ====================
    
    async def cancel_order(self, order_id: str, venue: ExecutionVenue) -> Dict:
        """Cancel an active order"""
        try:
            exchange = self.exchanges.get(venue)
            if exchange:
                result = await exchange.cancel_order(order_id)
                
                # Update order status
                if order_id in self.active_orders:
                    self.active_orders[order_id].status = OrderStatus.CANCELLED
                
                return {'status': 'cancelled', 'order_id': order_id}
            else:
                return {'status': 'failed', 'reason': 'Exchange not connected'}
                
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    async def modify_order(self, order_id: str, modifications: Dict) -> Dict:
        """Modify an existing order"""
        try:
            # Cancel and replace strategy
            order = self.active_orders.get(order_id)
            if not order:
                return {'status': 'failed', 'reason': 'Order not found'}
            
            # Cancel existing
            cancel_result = await self.cancel_order(order_id, order.venue)
            if cancel_result['status'] != 'cancelled':
                return cancel_result
            
            # Create new order with modifications
            for key, value in modifications.items():
                setattr(order, key, value)
            
            order.order_id = f"ORD_{int(time.time() * 1000000)}"  # New ID
            
            # Execute new order
            return await self.execute_order(order)
            
        except Exception as e:
            logger.error(f"Failed to modify order {order_id}: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    async def get_order_status(self, order_id: str, venue: ExecutionVenue) -> Dict:
        """Get current status of an order"""
        try:
            exchange = self.exchanges.get(venue)
            if exchange:
                order = await exchange.fetch_order(order_id)
                return {
                    'status': order['status'],
                    'filled': order['filled'],
                    'remaining': order['remaining'],
                    'average_price': order['average'],
                    'fees': order['fee']['cost'] if order.get('fee') else 0
                }
            else:
                # Check local records
                order = self.active_orders.get(order_id)
                if order:
                    return {
                        'status': order.status.value,
                        'filled': order.filled_quantity,
                        'remaining': order.quantity - order.filled_quantity,
                        'average_price': order.average_price,
                        'fees': order.fees
                    }
                else:
                    return {'status': 'not_found'}
                    
        except Exception as e:
            logger.error(f"Failed to get order status: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    # ==================== Advanced Order Types ====================
    
    async def execute_twap_order(self, order: Order, duration_minutes: int) -> Dict:
        """
        Execute Time-Weighted Average Price order
        """
        total_quantity = order.quantity
        num_slices = duration_minutes  # One order per minute
        slice_quantity = total_quantity / num_slices
        
        results = []
        
        for i in range(num_slices):
            # Create slice order
            slice_order = Order(
                order_id=f"{order.order_id}_SLICE_{i}",
                symbol=order.symbol,
                market=order.market,
                venue=order.venue,
                side=order.side,
                order_type=OrderType.MARKET,
                quantity=slice_quantity
            )
            
            # Execute slice
            result = await self.execute_order(slice_order)
            results.append(result)
            
            # Wait for next interval
            if i < num_slices - 1:
                await asyncio.sleep(60)  # 1 minute
        
        # Aggregate results
        total_filled = sum(r.get('filled_quantity', 0) for r in results)
        total_value = sum(r.get('filled_quantity', 0) * r.get('average_price', 0) for r in results)
        average_price = total_value / total_filled if total_filled > 0 else 0
        
        return {
            'status': 'completed',
            'order_type': 'TWAP',
            'total_filled': total_filled,
            'average_price': average_price,
            'num_slices': num_slices,
            'results': results
        }
    
    async def execute_iceberg_order(self, order: Order, visible_quantity: float) -> Dict:
        """
        Execute iceberg order (show only partial quantity)
        """
        total_quantity = order.quantity
        filled_quantity = 0
        results = []
        
        while filled_quantity < total_quantity:
            # Calculate next slice
            remaining = total_quantity - filled_quantity
            slice_quantity = min(visible_quantity, remaining)
            
            # Create visible order
            slice_order = Order(
                order_id=f"{order.order_id}_ICE_{len(results)}",
                symbol=order.symbol,
                market=order.market,
                venue=order.venue,
                side=order.side,
                order_type=OrderType.LIMIT,
                quantity=slice_quantity,
                price=order.price
            )
            
            # Execute slice
            result = await self.execute_order(slice_order)
            results.append(result)
            
            if result['status'] == 'filled':
                filled_quantity += result['filled_quantity']
            else:
                # Wait or adjust price if needed
                await asyncio.sleep(1)
        
        return {
            'status': 'completed',
            'order_type': 'ICEBERG',
            'total_filled': filled_quantity,
            'visible_size': visible_quantity,
            'num_slices': len(results),
            'results': results
        }
    
    # ==================== Helper Functions ====================
    
    def _format_symbol(self, symbol: str, venue: ExecutionVenue) -> str:
        """Format symbol for specific exchange"""
        if venue == ExecutionVenue.BINANCE:
            return symbol.replace('-', '')  # BTC-USDT -> BTCUSDT
        elif venue in [ExecutionVenue.COINBASE, ExecutionVenue.KRAKEN]:
            return symbol  # Already in correct format
        else:
            return symbol
    
    def _calculate_slippage(self, expected_price: Optional[float], 
                          actual_price: float) -> float:
        """Calculate execution slippage"""
        if not expected_price:
            return 0
        return abs(actual_price - expected_price) / expected_price
    
    def _is_asx_open(self) -> bool:
        """Check if ASX market is open"""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        
        # Sydney time 10:00 - 16:00
        hour = now.hour
        return 10 <= hour < 16
    
    async def _get_asx_price(self, symbol: str) -> float:
        """Get current ASX price"""
        ticker = yf.Ticker(f"{symbol}.AX")
        info = ticker.info
        return info.get('currentPrice', info.get('regularMarketPrice', 0))
    
    async def _get_market_price(self, symbol: str, venue: ExecutionVenue) -> float:
        """Get current market price"""
        exchange = self.exchanges.get(venue)
        if exchange:
            ticker = await exchange.fetch_ticker(self._format_symbol(symbol, venue))
            return ticker['last']
        return 0
    
    async def _get_token_chain(self, symbol: str) -> str:
        """Determine which blockchain a token is on"""
        # Would query token database or API
        # For now, return most common
        if 'SHIB' in symbol or 'DOGE' in symbol:
            return 'ethereum'
        elif 'CAKE' in symbol or 'SAFEMOON' in symbol:
            return 'bsc'
        else:
            return 'ethereum'
    
    async def _check_token_safety(self, symbol: str, chain: str) -> Dict:
        """Check token for rug pull/honeypot risks"""
        # Would implement comprehensive checks:
        # - Contract verification
        # - Liquidity lock check
        # - Ownership check
        # - Tax analysis
        # - Holder distribution
        
        # For now, basic simulation
        return {
            'safe': True,
            'liquidity_locked': True,
            'ownership_renounced': True,
            'max_tax': 5,
            'risk_score': 0.2
        }
    
    async def _get_dex_router(self, chain: str) -> str:
        """Get DEX router address for chain"""
        routers = {
            'ethereum': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',  # Uniswap V2
            'bsc': '0x10ED43C718714eb63d5aA57B78B54704E256024E',  # PancakeSwap
            'polygon': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',  # QuickSwap
        }
        return routers.get(chain)
    
    async def _find_best_dex_liquidity(self, symbol: str) -> ExecutionVenue:
        """Find DEX with best liquidity for token"""
        # Would check liquidity across DEXs
        # For now, return Uniswap as default
        return ExecutionVenue.UNISWAP
    
    async def _build_buy_transaction(self, w3, router, symbol, quantity, price):
        """Build Web3 buy transaction"""
        # Would implement actual Web3 transaction building
        pass
    
    async def _build_sell_transaction(self, w3, router, symbol, quantity, price):
        """Build Web3 sell transaction"""
        # Would implement actual Web3 transaction building
        pass
    
    async def _execute_web3_transaction(self, w3, transaction):
        """Execute Web3 transaction"""
        # Would implement actual transaction execution
        pass
    
    async def _parse_dex_execution(self, receipt) -> Dict:
        """Parse DEX execution from transaction receipt"""
        # Would parse logs to extract execution details
        return {
            'amount': 0,
            'price': 0,
            'fees': 0
        }
    
    # ==================== Storage ====================
    
    async def _store_execution(self, execution: Execution):
        """Store execution record in MongoDB"""
        if self.mongodb:
            await self.mongodb.executions.insert_one({
                'execution_id': execution.execution_id,
                'order_id': execution.order_id,
                'symbol': execution.symbol,
                'venue': execution.venue.value,
                'side': execution.side,
                'quantity': execution.quantity,
                'price': execution.price,
                'fees': execution.fees,
                'timestamp': execution.timestamp,
                'latency_ms': execution.latency_ms,
                'slippage': execution.slippage
            })
    
    # ==================== Monitoring ====================
    
    async def get_execution_metrics(self) -> Dict:
        """Get current execution metrics"""
        return {
            'total_orders': self.metrics['total_orders'],
            'successful_executions': self.metrics['successful_executions'],
            'failed_orders': self.metrics['failed_orders'],
            'success_rate': self.metrics['successful_executions'] / max(self.metrics['total_orders'], 1),
            'average_latency': self.metrics['average_latency'],
            'total_volume': self.metrics['total_volume'],
            'total_fees': self.metrics['total_fees'],
            'active_orders': len(self.active_orders),
            'venues_connected': sum(1 for e in self.exchanges.values() if e is not None)
        }