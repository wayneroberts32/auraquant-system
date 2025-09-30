"""
High-Frequency Trading (HFT) Module
AuraQuant Infinity Money Synthetic Intelligence System
ADD-ONLY • NO REBUILD • ULTRA-LOW LATENCY
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque
import numpy as np

@dataclass
class HFTOrder:
    """High-frequency order with priority queue support"""
    symbol: str
    side: str  # BUY/SELL
    quantity: int
    price: float
    timestamp: float
    priority: int  # 0=highest, 99=lowest
    strategy: str
    idempotency_key: str

class HFTEngine:
    """
    Ultra-low latency trading engine
    Target: <50ms execution, 1000+ orders/minute
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.order_queue = deque(maxlen=10000)
        self.batch_size = 100
        self.max_orders_per_second = 20
        self.latency_target_ms = 50
        
        # Performance metrics
        self.metrics = {
            'total_orders': 0,
            'avg_latency_ms': 0,
            'orders_per_minute': 0,
            'successful_trades': 0,
            'rejected_orders': 0
        }
        
        # Circuit breaker for HFT
        self.circuit_breaker = {
            'enabled': True,
            'max_loss_per_minute': 1000,
            'max_orders_per_minute': 1000,
            'current_loss': 0,
            'current_orders': 0,
            'tripped': False
        }
    
    async def execute_order(self, order: HFTOrder) -> Dict[str, Any]:
        """
        Execute single order with ultra-low latency
        """
        start_time = time.perf_counter()
        
        try:
            # Check circuit breaker
            if self.circuit_breaker['tripped']:
                return {
                    'status': 'REJECTED',
                    'reason': 'Circuit breaker tripped',
                    'order_id': order.idempotency_key
                }
            
            # Validate order
            if not self._validate_order(order):
                self.metrics['rejected_orders'] += 1
                return {
                    'status': 'REJECTED',
                    'reason': 'Order validation failed',
                    'order_id': order.idempotency_key
                }
            
            # Execute trade (simulated for now)
            result = await self._send_to_broker(order)
            
            # Update metrics
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_metrics(latency_ms, result['status'])
            
            # Store in MongoDB
            if self.mongodb:
                await self._store_trade(order, result)
            
            return result
            
        except Exception as e:
            return {
                'status': 'ERROR',
                'reason': str(e),
                'order_id': order.idempotency_key
            }
    
    async def execute_batch(self, orders: List[HFTOrder]) -> List[Dict]:
        """
        Execute batch of orders with optimized throughput
        """
        results = []
        
        # Sort by priority
        sorted_orders = sorted(orders, key=lambda x: x.priority)
        
        # Execute in batches to maintain throughput
        for i in range(0, len(sorted_orders), self.batch_size):
            batch = sorted_orders[i:i + self.batch_size]
            
            # Parallel execution within batch
            tasks = [self.execute_order(order) for order in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Rate limiting
            await asyncio.sleep(0.05)  # 50ms between batches
        
        return results
    
    def _validate_order(self, order: HFTOrder) -> bool:
        """
        Ultra-fast order validation
        """
        # Check order limits
        if order.quantity <= 0 or order.quantity > 10000:
            return False
        
        # Check price bounds (prevent fat finger)
        if order.price <= 0 or order.price > 1000000:
            return False
        
        # Check circuit breaker limits
        self.circuit_breaker['current_orders'] += 1
        if self.circuit_breaker['current_orders'] > self.circuit_breaker['max_orders_per_minute']:
            self.circuit_breaker['tripped'] = True
            return False
        
        return True
    
    async def _send_to_broker(self, order: HFTOrder) -> Dict:
        """
        Send order to broker with minimal latency
        """
        # Simulated broker execution
        await asyncio.sleep(0.01)  # 10ms simulated broker latency
        
        # Simulate 95% success rate
        success = np.random.random() > 0.05
        
        if success:
            return {
                'status': 'FILLED',
                'order_id': order.idempotency_key,
                'fill_price': order.price * (1 + np.random.uniform(-0.001, 0.001)),
                'fill_quantity': order.quantity,
                'timestamp': time.time()
            }
        else:
            return {
                'status': 'REJECTED',
                'order_id': order.idempotency_key,
                'reason': 'Broker rejection',
                'timestamp': time.time()
            }
    
    async def _store_trade(self, order: HFTOrder, result: Dict):
        """
        Store trade in MongoDB for audit
        """
        trade_doc = {
            'timestamp': result['timestamp'],
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'requested_price': order.price,
            'fill_price': result.get('fill_price'),
            'status': result['status'],
            'strategy': 'HFT',
            'latency_ms': self.metrics['avg_latency_ms'],
            'idempotency_key': order.idempotency_key
        }
        
        if self.mongodb:
            await self.mongodb.trades.insert_one(trade_doc)
    
    def _update_metrics(self, latency_ms: float, status: str):
        """
        Update performance metrics
        """
        self.metrics['total_orders'] += 1
        
        # Update average latency (exponential moving average)
        alpha = 0.1
        self.metrics['avg_latency_ms'] = (
            alpha * latency_ms + 
            (1 - alpha) * self.metrics['avg_latency_ms']
        )
        
        if status == 'FILLED':
            self.metrics['successful_trades'] += 1
        elif status == 'REJECTED':
            self.metrics['rejected_orders'] += 1
        
        # Calculate orders per minute
        self.metrics['orders_per_minute'] = self.metrics['total_orders']
    
    def get_metrics(self) -> Dict:
        """
        Get current performance metrics
        """
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful_trades'] / 
                max(self.metrics['total_orders'], 1) * 100
            ),
            'latency_target_met': self.metrics['avg_latency_ms'] < self.latency_target_ms,
            'circuit_breaker_status': 'TRIPPED' if self.circuit_breaker['tripped'] else 'ACTIVE'
        }
    
    def reset_circuit_breaker(self):
        """
        Reset circuit breaker after cooldown
        """
        self.circuit_breaker['tripped'] = False
        self.circuit_breaker['current_orders'] = 0
        self.circuit_breaker['current_loss'] = 0

# HFT Strategy Implementations

class MarketMakingStrategy:
    """
    Provide liquidity by placing bid/ask orders
    """
    
    def __init__(self, engine: HFTEngine):
        self.engine = engine
        self.spread_basis_points = 10  # 0.1% spread
        
    async def generate_orders(self, symbol: str, mid_price: float) -> List[HFTOrder]:
        """
        Generate bid/ask orders around mid price
        """
        spread = mid_price * self.spread_basis_points / 10000
        
        orders = [
            HFTOrder(
                symbol=symbol,
                side='BUY',
                quantity=100,
                price=mid_price - spread/2,
                timestamp=time.time(),
                priority=1,
                strategy='market_making',
                idempotency_key=f"MM_{symbol}_{time.time()}_BID"
            ),
            HFTOrder(
                symbol=symbol,
                side='SELL',
                quantity=100,
                price=mid_price + spread/2,
                timestamp=time.time(),
                priority=1,
                strategy='market_making',
                idempotency_key=f"MM_{symbol}_{time.time()}_ASK"
            )
        ]
        
        return orders

class MomentumScalpingStrategy:
    """
    Capture micro price movements
    """
    
    def __init__(self, engine: HFTEngine):
        self.engine = engine
        self.momentum_threshold = 0.001  # 0.1% momentum
        
    async def analyze_and_trade(self, symbol: str, prices: List[float]) -> Optional[HFTOrder]:
        """
        Detect momentum and generate scalping order
        """
        if len(prices) < 10:
            return None
        
        # Calculate momentum
        momentum = (prices[-1] - prices[-10]) / prices[-10]
        
        if abs(momentum) > self.momentum_threshold:
            side = 'BUY' if momentum > 0 else 'SELL'
            
            return HFTOrder(
                symbol=symbol,
                side=side,
                quantity=50,
                price=prices[-1],
                timestamp=time.time(),
                priority=0,  # High priority
                strategy='momentum_scalping',
                idempotency_key=f"SCALP_{symbol}_{time.time()}"
            )
        
        return None

# QA/QC Test for HFT
async def qa_stress_test():
    """
    QA: Verify 1000 orders/minute with <50ms latency
    """
    engine = HFTEngine()
    
    # Generate 1000 test orders
    test_orders = []
    for i in range(1000):
        order = HFTOrder(
            symbol='TEST',
            side='BUY' if i % 2 == 0 else 'SELL',
            quantity=100,
            price=100.0 + i * 0.01,
            timestamp=time.time(),
            priority=i % 10,
            strategy='stress_test',
            idempotency_key=f"TEST_{i}_{time.time()}"
        )
        test_orders.append(order)
    
    # Execute stress test
    start = time.time()
    results = await engine.execute_batch(test_orders)
    duration = time.time() - start
    
    # Verify metrics
    metrics = engine.get_metrics()
    
    qa_results = {
        'total_orders': len(results),
        'duration_seconds': duration,
        'orders_per_minute': (len(results) / duration) * 60,
        'avg_latency_ms': metrics['avg_latency_ms'],
        'latency_target_met': metrics['avg_latency_ms'] < 50,
        'throughput_target_met': (len(results) / duration) * 60 >= 1000,
        'success_rate': metrics['success_rate']
    }
    
    return qa_results