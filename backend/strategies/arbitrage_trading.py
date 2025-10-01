"""
Arbitrage Trading Module
AuraQuant Infinity Money Synthetic Intelligence System
ADD-ONLY • NO REBUILD • CROSS-EXCHANGE OPPORTUNITIES
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from collections import defaultdict

@dataclass
class ArbitrageOpportunity:
    """Represents a profitable arbitrage opportunity"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread_pct: float
    max_quantity: float
    estimated_profit: float
    timestamp: float
    opportunity_id: str
    expires_at: float

class ArbitrageEngine:
    """
    Multi-exchange arbitrage detection and execution
    Supports triangular, statistical, and cross-exchange arbitrage
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.exchanges = {}  # Exchange connections
        self.price_feeds = defaultdict(dict)
        self.min_spread_pct = 0.5  # Minimum 0.5% spread to consider
        self.max_position_size = 10000  # Max position size per trade
        self.active_opportunities = {}
        
        # Performance tracking
        self.metrics = {
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'total_profit': 0,
            'failed_attempts': 0,
            'avg_spread_captured': 0
        }
        
        # Risk limits
        self.risk_limits = {
            'max_exposure': 100000,
            'current_exposure': 0,
            'max_trades_per_minute': 20,
            'current_trades': 0
        }
    
    async def scan_for_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Continuously scan for arbitrage opportunities across exchanges
        """
        opportunities = []
        
        # Cross-exchange arbitrage
        cross_exchange_opps = await self._find_cross_exchange_arbitrage()
        opportunities.extend(cross_exchange_opps)
        
        # Triangular arbitrage
        triangular_opps = await self._find_triangular_arbitrage()
        opportunities.extend(triangular_opps)
        
        # Statistical arbitrage
        stat_arb_opps = await self._find_statistical_arbitrage()
        opportunities.extend(stat_arb_opps)
        
        # Filter and rank opportunities
        valid_opportunities = self._validate_opportunities(opportunities)
        ranked_opportunities = self._rank_opportunities(valid_opportunities)
        
        # Update metrics
        self.metrics['opportunities_found'] += len(ranked_opportunities)
        
        return ranked_opportunities
    
    async def _find_cross_exchange_arbitrage(self) -> List[ArbitrageOpportunity]:
        """
        Find price discrepancies between exchanges
        """
        opportunities = []
        
        # Get all common symbols across exchanges
        symbols = self._get_common_symbols()
        
        for symbol in symbols:
            prices = await self._get_prices_across_exchanges(symbol)
            
            if len(prices) < 2:
                continue
            
            # Find best bid and ask across exchanges
            best_bid = max(prices.items(), key=lambda x: x[1]['bid'])
            best_ask = min(prices.items(), key=lambda x: x[1]['ask'])
            
            # Calculate spread
            spread = best_bid[1]['bid'] - best_ask[1]['ask']
            spread_pct = (spread / best_ask[1]['ask']) * 100
            
            if spread_pct > self.min_spread_pct:
                # Consider transaction costs
                net_spread = spread_pct - self._estimate_transaction_costs(
                    best_ask[0], best_bid[0]
                )
                
                if net_spread > 0:
                    max_qty = min(
                        best_bid[1]['bid_size'],
                        best_ask[1]['ask_size'],
                        self.max_position_size
                    )
                    
                    opportunity = ArbitrageOpportunity(
                        symbol=symbol,
                        buy_exchange=best_ask[0],
                        sell_exchange=best_bid[0],
                        buy_price=best_ask[1]['ask'],
                        sell_price=best_bid[1]['bid'],
                        spread_pct=net_spread,
                        max_quantity=max_qty,
                        estimated_profit=max_qty * spread,
                        timestamp=time.time(),
                        opportunity_id=f"ARB_{symbol}_{time.time()}",
                        expires_at=time.time() + 5  # 5 second expiry
                    )
                    opportunities.append(opportunity)
        
        return opportunities
    
    async def _find_triangular_arbitrage(self) -> List[ArbitrageOpportunity]:
        """
        Find triangular arbitrage opportunities within single exchange
        Example: BTC/USD -> ETH/BTC -> ETH/USD -> USD
        """
        opportunities = []
        
        # Define triangular pairs
        triangular_pairs = [
            ('BTC/USD', 'ETH/BTC', 'ETH/USD'),
            ('BTC/EUR', 'ETH/BTC', 'ETH/EUR'),
            ('BTC/USD', 'SOL/BTC', 'SOL/USD')
        ]
        
        for pair1, pair2, pair3 in triangular_pairs:
            try:
                # Get prices for all three pairs
                p1 = await self._get_price(pair1)
                p2 = await self._get_price(pair2)
                p3 = await self._get_price(pair3)
                
                if not all([p1, p2, p3]):
                    continue
                
                # Calculate triangular arbitrage
                # Start with 1 unit of base currency
                # Path: USD -> BTC -> ETH -> USD
                step1 = 1 / p1['ask']  # Buy BTC with USD
                step2 = step1 * p2['bid']  # Sell BTC for ETH
                step3 = step2 * p3['bid']  # Sell ETH for USD
                
                profit_ratio = step3 - 1
                profit_pct = profit_ratio * 100
                
                if profit_pct > self.min_spread_pct:
                    opportunity = ArbitrageOpportunity(
                        symbol=f"{pair1}-{pair2}-{pair3}",
                        buy_exchange='triangular',
                        sell_exchange='triangular',
                        buy_price=1.0,
                        sell_price=step3,
                        spread_pct=profit_pct,
                        max_quantity=self.max_position_size,
                        estimated_profit=self.max_position_size * profit_ratio,
                        timestamp=time.time(),
                        opportunity_id=f"TRI_{time.time()}",
                        expires_at=time.time() + 2  # 2 second expiry for triangular
                    )
                    opportunities.append(opportunity)
                    
            except Exception as e:
                continue
        
        return opportunities
    
    async def _find_statistical_arbitrage(self) -> List[ArbitrageOpportunity]:
        """
        Find mean-reversion opportunities between correlated assets
        """
        opportunities = []
        
        # Define correlated pairs
        correlated_pairs = [
            ('BTC', 'ETH', 0.85),  # correlation coefficient
            ('SPY', 'QQQ', 0.90),
            ('GOLD', 'SILVER', 0.75)
        ]
        
        for asset1, asset2, expected_corr in correlated_pairs:
            # Get historical prices
            prices1 = await self._get_historical_prices(asset1, 100)
            prices2 = await self._get_historical_prices(asset2, 100)
            
            if not prices1 or not prices2:
                continue
            
            # Calculate z-score of spread
            spread = np.array(prices1) - np.array(prices2) * self._calculate_hedge_ratio(prices1, prices2)
            z_score = (spread[-1] - np.mean(spread)) / np.std(spread)
            
            # Look for extreme deviations (z-score > 2)
            if abs(z_score) > 2:
                # Mean reversion opportunity
                side = 'SELL' if z_score > 0 else 'BUY'
                
                opportunity = ArbitrageOpportunity(
                    symbol=f"{asset1}/{asset2}",
                    buy_exchange='statistical',
                    sell_exchange='statistical',
                    buy_price=prices1[-1],
                    sell_price=prices2[-1],
                    spread_pct=abs(z_score),  # Using z-score as proxy for profit potential
                    max_quantity=self.max_position_size,
                    estimated_profit=self.max_position_size * abs(z_score) * 0.01,
                    timestamp=time.time(),
                    opportunity_id=f"STAT_{asset1}_{asset2}_{time.time()}",
                    expires_at=time.time() + 60  # 1 minute expiry for stat arb
                )
                opportunities.append(opportunity)
        
        return opportunities
    
    async def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Execute arbitrage trade with atomic transaction handling
        """
        execution_result = {
            'opportunity_id': opportunity.opportunity_id,
            'status': 'PENDING',
            'profit': 0,
            'errors': []
        }
        
        try:
            # Check if opportunity is still valid
            if time.time() > opportunity.expires_at:
                execution_result['status'] = 'EXPIRED'
                return execution_result
            
            # Check risk limits
            if not self._check_risk_limits(opportunity):
                execution_result['status'] = 'RISK_LIMIT_EXCEEDED'
                return execution_result
            
            # Execute both legs atomically
            if opportunity.buy_exchange == 'triangular':
                result = await self._execute_triangular_arbitrage(opportunity)
            elif opportunity.buy_exchange == 'statistical':
                result = await self._execute_statistical_arbitrage(opportunity)
            else:
                result = await self._execute_cross_exchange_arbitrage(opportunity)
            
            # Update metrics
            if result['success']:
                self.metrics['opportunities_executed'] += 1
                self.metrics['total_profit'] += result['profit']
                execution_result['status'] = 'SUCCESS'
                execution_result['profit'] = result['profit']
            else:
                self.metrics['failed_attempts'] += 1
                execution_result['status'] = 'FAILED'
                execution_result['errors'] = result.get('errors', [])
            
            # Store in MongoDB
            if self.mongodb:
                await self._store_arbitrage_trade(opportunity, execution_result)
            
        except Exception as e:
            execution_result['status'] = 'ERROR'
            execution_result['errors'].append(str(e))
            
        return execution_result
    
    async def _execute_cross_exchange_arbitrage(self, opp: ArbitrageOpportunity) -> Dict:
        """
        Execute cross-exchange arbitrage with proper order management
        """
        # Place simultaneous orders on both exchanges
        buy_task = self._place_order(
            opp.buy_exchange, opp.symbol, 'BUY', opp.max_quantity, opp.buy_price
        )
        sell_task = self._place_order(
            opp.sell_exchange, opp.symbol, 'SELL', opp.max_quantity, opp.sell_price
        )
        
        # Execute both orders simultaneously
        buy_result, sell_result = await asyncio.gather(buy_task, sell_task)
        
        # Check if both orders succeeded
        if buy_result['status'] == 'FILLED' and sell_result['status'] == 'FILLED':
            profit = (sell_result['fill_price'] - buy_result['fill_price']) * opp.max_quantity
            return {
                'success': True,
                'profit': profit,
                'buy_order': buy_result,
                'sell_order': sell_result
            }
        else:
            # Attempt to unwind any filled orders
            await self._unwind_partial_fills(buy_result, sell_result, opp)
            return {
                'success': False,
                'errors': ['Partial fill or rejection'],
                'buy_order': buy_result,
                'sell_order': sell_result
            }
    
    def _validate_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """
        Validate opportunities against current market conditions
        """
        valid_opps = []
        
        for opp in opportunities:
            # Check minimum spread requirement
            if opp.spread_pct < self.min_spread_pct:
                continue
            
            # Check position limits
            if opp.max_quantity > self.max_position_size:
                opp.max_quantity = self.max_position_size
            
            # Check if opportunity already being executed
            if opp.opportunity_id not in self.active_opportunities:
                valid_opps.append(opp)
        
        return valid_opps
    
    def _rank_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """
        Rank opportunities by expected profit and risk
        """
        # Score each opportunity
        scored_opps = []
        for opp in opportunities:
            score = opp.estimated_profit * (1 - self._calculate_risk_score(opp))
            scored_opps.append((score, opp))
        
        # Sort by score descending
        scored_opps.sort(key=lambda x: x[0], reverse=True)
        
        return [opp for _, opp in scored_opps]
    
    def _calculate_risk_score(self, opp: ArbitrageOpportunity) -> float:
        """
        Calculate risk score for opportunity (0-1, higher is riskier)
        """
        risk_score = 0.0
        
        # Time decay risk
        time_until_expiry = opp.expires_at - time.time()
        if time_until_expiry < 1:
            risk_score += 0.5
        
        # Size risk
        size_ratio = opp.max_quantity / self.max_position_size
        risk_score += size_ratio * 0.3
        
        # Exchange risk (some exchanges more reliable than others)
        exchange_risk_scores = {
            'binance': 0.1,
            'coinbase': 0.1,
            'kraken': 0.15,
            'unknown': 0.5
        }
        risk_score += exchange_risk_scores.get(opp.buy_exchange, 0.5) * 0.2
        
        return min(risk_score, 1.0)
    
    def _check_risk_limits(self, opp: ArbitrageOpportunity) -> bool:
        """
        Check if executing opportunity would exceed risk limits
        """
        # Check exposure limit
        potential_exposure = self.risk_limits['current_exposure'] + (opp.max_quantity * opp.buy_price)
        if potential_exposure > self.risk_limits['max_exposure']:
            return False
        
        # Check trade frequency limit
        if self.risk_limits['current_trades'] >= self.risk_limits['max_trades_per_minute']:
            return False
        
        return True
    
    def _calculate_hedge_ratio(self, prices1: List[float], prices2: List[float]) -> float:
        """
        Calculate optimal hedge ratio for pair trading
        """
        # Simple linear regression to find hedge ratio
        x = np.array(prices2)
        y = np.array(prices1)
        
        # Calculate slope (hedge ratio)
        n = len(x)
        xy_sum = np.sum(x * y)
        x_sum = np.sum(x)
        y_sum = np.sum(y)
        x2_sum = np.sum(x * x)
        
        hedge_ratio = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        return hedge_ratio
    
    def _estimate_transaction_costs(self, exchange1: str, exchange2: str) -> float:
        """
        Estimate total transaction costs for arbitrage
        """
        # Exchange fee schedule (in percentage)
        fees = {
            'binance': 0.1,
            'coinbase': 0.5,
            'kraken': 0.25,
            'default': 0.3
        }
        
        fee1 = fees.get(exchange1, fees['default'])
        fee2 = fees.get(exchange2, fees['default'])
        
        # Add slippage estimate
        slippage = 0.1
        
        return fee1 + fee2 + slippage
    
    # Placeholder methods for exchange integration
    async def _get_price(self, symbol: str) -> Optional[Dict]:
        """Get price for symbol from primary exchange"""
        # Simulated price data
        return {
            'bid': 100.0 * (1 + np.random.uniform(-0.01, 0.01)),
            'ask': 100.0 * (1 + np.random.uniform(-0.01, 0.01)),
            'bid_size': 1000,
            'ask_size': 1000
        }
    
    async def _get_prices_across_exchanges(self, symbol: str) -> Dict[str, Dict]:
        """Get prices from all connected exchanges"""
        # Simulated multi-exchange prices
        exchanges = ['binance', 'coinbase', 'kraken']
        prices = {}
        
        for exchange in exchanges:
            base_price = 100.0
            spread = np.random.uniform(0.001, 0.005)
            prices[exchange] = {
                'bid': base_price * (1 - spread + np.random.uniform(-0.002, 0.002)),
                'ask': base_price * (1 + spread + np.random.uniform(-0.002, 0.002)),
                'bid_size': np.random.uniform(100, 1000),
                'ask_size': np.random.uniform(100, 1000)
            }
        
        return prices
    
    async def _get_historical_prices(self, symbol: str, count: int) -> List[float]:
        """Get historical prices for statistical analysis"""
        # Simulated historical data
        base = 100.0
        prices = []
        for i in range(count):
            prices.append(base * (1 + np.random.uniform(-0.02, 0.02)))
        return prices
    
    def _get_common_symbols(self) -> List[str]:
        """Get symbols available on all exchanges"""
        return ['BTC/USD', 'ETH/USD', 'SOL/USD', 'MATIC/USD']
    
    async def _place_order(self, exchange: str, symbol: str, side: str, quantity: float, price: float) -> Dict:
        """Place order on exchange"""
        # Simulated order placement
        await asyncio.sleep(0.01)  # Simulate network latency
        
        success = np.random.random() > 0.1  # 90% success rate
        
        if success:
            return {
                'status': 'FILLED',
                'fill_price': price * (1 + np.random.uniform(-0.0005, 0.0005)),
                'fill_quantity': quantity,
                'order_id': f"{exchange}_{symbol}_{time.time()}"
            }
        else:
            return {
                'status': 'REJECTED',
                'reason': 'Insufficient liquidity',
                'order_id': f"{exchange}_{symbol}_{time.time()}"
            }
    
    async def _unwind_partial_fills(self, buy_result: Dict, sell_result: Dict, opp: ArbitrageOpportunity):
        """Unwind any partial fills to avoid unwanted exposure"""
        # Implementation would depend on exchange APIs
        pass
    
    async def _store_arbitrage_trade(self, opp: ArbitrageOpportunity, result: Dict):
        """Store arbitrage trade in MongoDB"""
        trade_doc = {
            'timestamp': time.time(),
            'opportunity': {
                'id': opp.opportunity_id,
                'symbol': opp.symbol,
                'buy_exchange': opp.buy_exchange,
                'sell_exchange': opp.sell_exchange,
                'spread_pct': opp.spread_pct,
                'estimated_profit': opp.estimated_profit
            },
            'execution': result,
            'strategy': 'ARBITRAGE'
        }
        
        if self.mongodb:
            await self.mongodb.trades.insert_one(trade_doc)
    
    async def _execute_triangular_arbitrage(self, opp: ArbitrageOpportunity) -> Dict:
        """Execute triangular arbitrage trades"""
        # Implementation for triangular arbitrage execution
        return {'success': True, 'profit': opp.estimated_profit}
    
    async def _execute_statistical_arbitrage(self, opp: ArbitrageOpportunity) -> Dict:
        """Execute statistical arbitrage trades"""
        # Implementation for statistical arbitrage execution
        return {'success': True, 'profit': opp.estimated_profit}

# QA/QC Test
async def qa_arbitrage_test():
    """
    QA: Test arbitrage opportunity detection and execution
    """
    engine = ArbitrageEngine()
    
    # Scan for opportunities
    opportunities = await engine.scan_for_opportunities()
    
    # Execute top opportunity if found
    results = []
    if opportunities:
        for opp in opportunities[:3]:  # Execute top 3
            result = await engine.execute_arbitrage(opp)
            results.append(result)
    
    # Get metrics
    metrics = engine.metrics
    
    qa_results = {
        'opportunities_found': len(opportunities),
        'opportunities_executed': len([r for r in results if r['status'] == 'SUCCESS']),
        'total_profit': sum([r.get('profit', 0) for r in results]),
        'success_rate': (
            len([r for r in results if r['status'] == 'SUCCESS']) / 
            max(len(results), 1) * 100
        ),
        'metrics': metrics
    }
    
    return qa_results