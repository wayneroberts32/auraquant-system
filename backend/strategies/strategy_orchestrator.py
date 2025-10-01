"""
AuraQuant Strategy Orchestrator
Infinity Money Synthetic Intelligence System
ADD-ONLY • CLOUD-READY • SELF-EVOLVING
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime, timedelta

# Import all strategy modules
from .hft_trading import HFTEngine, MarketMakingStrategy, MomentumScalpingStrategy
from .arbitrage_trading import ArbitrageEngine
from .event_news_trading import EventDrivenEngine

@dataclass
class StrategyStatus:
    """Real-time status of each strategy"""
    name: str
    enabled: bool
    health: str  # HEALTHY, WARNING, CRITICAL
    metrics: Dict
    last_update: float
    active_positions: int
    daily_pnl: float

class AuraQuantOrchestrator:
    """
    Master orchestrator for all AuraQuant trading strategies
    Coordinates, monitors, and optimizes all trading activities
    """
    
    def __init__(self, mongodb_client=None, websocket_server=None):
        self.mongodb = mongodb_client
        self.websocket = websocket_server
        
        # Initialize all trading engines
        self.engines = {
            'HFT': HFTEngine(mongodb_client),
            'ARBITRAGE': ArbitrageEngine(mongodb_client),
            'EVENT': EventDrivenEngine(mongodb_client)
        }
        
        # Initialize strategy helpers
        self.market_maker = MarketMakingStrategy(self.engines['HFT'])
        self.momentum_scalper = MomentumScalpingStrategy(self.engines['HFT'])
        
        # Strategy configuration
        self.strategy_config = {
            'HFT': {
                'enabled': True,
                'allocation_pct': 30,
                'max_risk': 5000,
                'strategies': ['market_making', 'momentum_scalping']
            },
            'ARBITRAGE': {
                'enabled': True,
                'allocation_pct': 40,
                'max_risk': 10000,
                'strategies': ['cross_exchange', 'triangular', 'statistical']
            },
            'EVENT': {
                'enabled': True,
                'allocation_pct': 30,
                'max_risk': 5000,
                'strategies': ['news', 'earnings', 'economic']
            }
        }
        
        # Global risk management
        self.global_risk = {
            'max_daily_loss': 50000,
            'max_position_value': 100000,
            'max_correlation': 0.7,
            'current_daily_pnl': 0,
            'circuit_breaker_triggered': False
        }
        
        # Performance tracking
        self.performance = {
            'start_time': time.time(),
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'strategies_health': {}
        }
        
        # Real-time monitoring
        self.monitoring = {
            'heartbeat_interval': 5,  # seconds
            'last_heartbeat': time.time(),
            'alerts': [],
            'system_status': 'INITIALIZING'
        }
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize all systems and perform startup checks
        """
        initialization_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'INITIALIZING',
            'engines': {},
            'health_checks': {}
        }
        
        try:
            # Health check for each engine
            for name, engine in self.engines.items():
                health = await self._check_engine_health(engine)
                initialization_report['engines'][name] = health
                
                if not health['healthy']:
                    self.strategy_config[name]['enabled'] = False
                    await self._send_alert(f"Engine {name} failed health check", 'CRITICAL')
            
            # Initialize MongoDB collections
            if self.mongodb:
                await self._initialize_database()
                initialization_report['database'] = 'CONNECTED'
            else:
                initialization_report['database'] = 'SIMULATED'
            
            # Start monitoring tasks
            asyncio.create_task(self._heartbeat_loop())
            asyncio.create_task(self._risk_monitor_loop())
            asyncio.create_task(self._performance_tracker_loop())
            
            self.monitoring['system_status'] = 'RUNNING'
            initialization_report['status'] = 'SUCCESS'
            
            # Broadcast initialization complete
            await self._broadcast_status({
                'event': 'SYSTEM_INITIALIZED',
                'data': initialization_report
            })
            
        except Exception as e:
            initialization_report['status'] = 'FAILED'
            initialization_report['error'] = str(e)
            self.monitoring['system_status'] = 'ERROR'
        
        return initialization_report
    
    async def execute_orchestrated_strategy(self) -> Dict[str, Any]:
        """
        Main execution loop coordinating all strategies
        """
        execution_results = {
            'cycle_time': time.time(),
            'strategies_executed': [],
            'total_orders': 0,
            'errors': []
        }
        
        try:
            # Check global circuit breaker
            if self.global_risk['circuit_breaker_triggered']:
                return {
                    'status': 'HALTED',
                    'reason': 'Circuit breaker triggered',
                    'resume_time': time.time() + 300  # 5 minute cooldown
                }
            
            # Execute HFT strategies
            if self.strategy_config['HFT']['enabled']:
                hft_result = await self._execute_hft_strategies()
                execution_results['strategies_executed'].append(hft_result)
                execution_results['total_orders'] += hft_result.get('orders_placed', 0)
            
            # Execute Arbitrage strategies
            if self.strategy_config['ARBITRAGE']['enabled']:
                arb_result = await self._execute_arbitrage_strategies()
                execution_results['strategies_executed'].append(arb_result)
                execution_results['total_orders'] += arb_result.get('opportunities_executed', 0)
            
            # Execute Event-driven strategies
            if self.strategy_config['EVENT']['enabled']:
                event_result = await self._execute_event_strategies()
                execution_results['strategies_executed'].append(event_result)
                execution_results['total_orders'] += event_result.get('trades_executed', 0)
            
            # Update performance metrics
            await self._update_performance_metrics(execution_results)
            
            # Broadcast execution summary
            await self._broadcast_execution_summary(execution_results)
            
        except Exception as e:
            execution_results['errors'].append(str(e))
            await self._send_alert(f"Orchestrator error: {e}", 'HIGH')
        
        return execution_results
    
    async def _execute_hft_strategies(self) -> Dict[str, Any]:
        """
        Execute HFT trading strategies
        """
        hft_results = {
            'strategy': 'HFT',
            'timestamp': time.time(),
            'orders_placed': 0,
            'latency_ms': 0,
            'pnl': 0
        }
        
        try:
            # Market making
            if 'market_making' in self.strategy_config['HFT']['strategies']:
                # Get current market prices (simulated)
                symbols = ['BTC/USD', 'ETH/USD', 'SOL/USD']
                
                for symbol in symbols:
                    mid_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 100
                    orders = await self.market_maker.generate_orders(symbol, mid_price)
                    
                    for order in orders:
                        result = await self.engines['HFT'].execute_order(order)
                        if result['status'] in ['FILLED', 'ACTIVE']:
                            hft_results['orders_placed'] += 1
            
            # Get metrics
            metrics = self.engines['HFT'].get_metrics()
            hft_results['latency_ms'] = metrics['avg_latency_ms']
            hft_results['success_rate'] = metrics.get('success_rate', 0)
            
        except Exception as e:
            hft_results['error'] = str(e)
        
        return hft_results
    
    async def _execute_arbitrage_strategies(self) -> Dict[str, Any]:
        """
        Execute arbitrage trading strategies
        """
        arb_results = {
            'strategy': 'ARBITRAGE',
            'timestamp': time.time(),
            'opportunities_found': 0,
            'opportunities_executed': 0,
            'estimated_profit': 0
        }
        
        try:
            # Scan for opportunities
            opportunities = await self.engines['ARBITRAGE'].scan_for_opportunities()
            arb_results['opportunities_found'] = len(opportunities)
            
            # Execute top opportunities within risk limits
            executed_value = 0
            max_value = self.strategy_config['ARBITRAGE']['max_risk']
            
            for opp in opportunities[:5]:  # Limit to top 5
                if executed_value + (opp.max_quantity * opp.buy_price) > max_value:
                    break
                
                result = await self.engines['ARBITRAGE'].execute_arbitrage(opp)
                
                if result['status'] == 'SUCCESS':
                    arb_results['opportunities_executed'] += 1
                    arb_results['estimated_profit'] += result.get('profit', 0)
                    executed_value += opp.max_quantity * opp.buy_price
        
        except Exception as e:
            arb_results['error'] = str(e)
        
        return arb_results
    
    async def _execute_event_strategies(self) -> Dict[str, Any]:
        """
        Execute event-driven trading strategies
        """
        event_results = {
            'strategy': 'EVENT',
            'timestamp': time.time(),
            'events_processed': 0,
            'trades_executed': 0,
            'avg_confidence': 0
        }
        
        try:
            # Process any pending news in queue
            while not self.engines['EVENT'].news_queue.empty():
                event = await self.engines['EVENT'].news_queue.get()
                
                # Generate trade signals
                trades = await self.engines['EVENT'].generate_trade_signals(event)
                
                for trade in trades:
                    # Check confidence threshold
                    if trade.confidence > 0.7:
                        result = await self.engines['EVENT'].execute_event_trade(trade)
                        
                        if result['status'] in ['ACTIVE', 'FILLED']:
                            event_results['trades_executed'] += 1
                            event_results['avg_confidence'] += trade.confidence
                
                event_results['events_processed'] += 1
            
            # Calculate average confidence
            if event_results['trades_executed'] > 0:
                event_results['avg_confidence'] /= event_results['trades_executed']
        
        except Exception as e:
            event_results['error'] = str(e)
        
        return event_results
    
    async def _check_engine_health(self, engine: Any) -> Dict[str, Any]:
        """
        Perform health check on trading engine
        """
        health_status = {
            'healthy': True,
            'latency': 0,
            'metrics': {},
            'warnings': []
        }
        
        try:
            # Test latency
            start = time.perf_counter()
            
            # Get engine metrics
            if hasattr(engine, 'get_metrics'):
                health_status['metrics'] = engine.get_metrics()
            elif hasattr(engine, 'metrics'):
                health_status['metrics'] = engine.metrics
            
            health_status['latency'] = (time.perf_counter() - start) * 1000
            
            # Check latency threshold
            if health_status['latency'] > 100:
                health_status['warnings'].append('High latency detected')
            
            # Check specific engine health
            if hasattr(engine, 'circuit_breaker'):
                if engine.circuit_breaker.get('tripped', False):
                    health_status['warnings'].append('Circuit breaker tripped')
                    health_status['healthy'] = False
        
        except Exception as e:
            health_status['healthy'] = False
            health_status['error'] = str(e)
        
        return health_status
    
    async def _heartbeat_loop(self):
        """
        Send regular heartbeat signals
        """
        while self.monitoring['system_status'] == 'RUNNING':
            self.monitoring['last_heartbeat'] = time.time()
            
            # Collect system status
            status = await self.get_system_status()
            
            # Broadcast heartbeat
            await self._broadcast_status({
                'event': 'HEARTBEAT',
                'timestamp': time.time(),
                'data': status
            })
            
            await asyncio.sleep(self.monitoring['heartbeat_interval'])
    
    async def _risk_monitor_loop(self):
        """
        Continuous risk monitoring
        """
        while self.monitoring['system_status'] == 'RUNNING':
            try:
                # Calculate current exposure
                total_exposure = 0
                
                # Check each engine's exposure
                for name, engine in self.engines.items():
                    if hasattr(engine, 'risk_limits'):
                        exposure = engine.risk_limits.get('current_exposure', 0)
                        total_exposure += exposure
                
                # Check against limits
                if total_exposure > self.global_risk['max_position_value']:
                    self.global_risk['circuit_breaker_triggered'] = True
                    await self._send_alert(
                        f"Max exposure exceeded: ${total_exposure:,.2f}",
                        'CRITICAL'
                    )
                
                # Check daily loss
                if self.global_risk['current_daily_pnl'] < -self.global_risk['max_daily_loss']:
                    self.global_risk['circuit_breaker_triggered'] = True
                    await self._send_alert(
                        f"Max daily loss exceeded: ${self.global_risk['current_daily_pnl']:,.2f}",
                        'CRITICAL'
                    )
                
            except Exception as e:
                await self._send_alert(f"Risk monitor error: {e}", 'HIGH')
            
            await asyncio.sleep(1)  # Check every second
    
    async def _performance_tracker_loop(self):
        """
        Track and update performance metrics
        """
        while self.monitoring['system_status'] == 'RUNNING':
            try:
                # Aggregate metrics from all engines
                total_trades = 0
                total_pnl = 0
                winning_trades = 0
                
                for name, engine in self.engines.items():
                    if hasattr(engine, 'metrics'):
                        metrics = engine.metrics
                        total_trades += metrics.get('total_orders', 0) + metrics.get('trades_executed', 0)
                        total_pnl += metrics.get('total_profit', 0) + metrics.get('total_pnl', 0)
                        winning_trades += metrics.get('successful_trades', 0) + metrics.get('winning_trades', 0)
                
                # Update global performance
                self.performance['total_trades'] = total_trades
                self.performance['winning_trades'] = winning_trades
                self.performance['total_pnl'] = total_pnl
                
                if total_trades > 0:
                    self.performance['win_rate'] = (winning_trades / total_trades) * 100
                
                # Update daily PnL
                self.global_risk['current_daily_pnl'] = total_pnl
                
                # Store in MongoDB
                if self.mongodb:
                    await self._store_performance_snapshot()
                
            except Exception as e:
                print(f"Performance tracker error: {e}")
            
            await asyncio.sleep(10)  # Update every 10 seconds
    
    async def _initialize_database(self):
        """
        Initialize MongoDB collections and indexes
        """
        if not self.mongodb:
            return
        
        # Create collections
        collections = [
            'trades',
            'events', 
            'opportunities',
            'performance',
            'alerts',
            'system_status'
        ]
        
        for collection_name in collections:
            # Ensure collection exists
            if collection_name not in await self.mongodb.list_collection_names():
                await self.mongodb.create_collection(collection_name)
        
        # Create indexes
        await self.mongodb.trades.create_index([('timestamp', -1), ('strategy', 1)])
        await self.mongodb.events.create_index([('timestamp', -1), ('impact', 1)])
        await self.mongodb.opportunities.create_index([('timestamp', -1), ('spread_pct', -1)])
        await self.mongodb.performance.create_index([('timestamp', -1)])
        await self.mongodb.alerts.create_index([('timestamp', -1), ('severity', 1)])
    
    async def _update_performance_metrics(self, execution_results: Dict):
        """
        Update performance metrics after execution
        """
        self.performance['last_update'] = time.time()
        
        # Calculate additional metrics
        if self.performance['total_trades'] > 0:
            # Simple Sharpe ratio calculation (would need proper implementation)
            returns_mean = self.performance['total_pnl'] / self.performance['total_trades']
            self.performance['avg_trade_pnl'] = returns_mean
    
    async def _broadcast_status(self, status: Dict):
        """
        Broadcast status update via WebSocket
        """
        if self.websocket:
            await self.websocket.broadcast(json.dumps(status))
    
    async def _broadcast_execution_summary(self, summary: Dict):
        """
        Broadcast execution summary
        """
        broadcast_data = {
            'event': 'EXECUTION_SUMMARY',
            'timestamp': time.time(),
            'data': summary
        }
        await self._broadcast_status(broadcast_data)
    
    async def _send_alert(self, message: str, severity: str):
        """
        Send alert and store in database
        """
        alert = {
            'timestamp': time.time(),
            'message': message,
            'severity': severity,  # LOW, MEDIUM, HIGH, CRITICAL
            'acknowledged': False
        }
        
        self.monitoring['alerts'].append(alert)
        
        # Store in MongoDB
        if self.mongodb:
            await self.mongodb.alerts.insert_one(alert)
        
        # Broadcast alert
        await self._broadcast_status({
            'event': 'ALERT',
            'data': alert
        })
    
    async def _store_performance_snapshot(self):
        """
        Store performance snapshot in MongoDB
        """
        snapshot = {
            'timestamp': time.time(),
            'performance': self.performance.copy(),
            'global_risk': self.global_risk.copy(),
            'strategy_config': self.strategy_config.copy(),
            'system_status': self.monitoring['system_status']
        }
        
        await self.mongodb.performance.insert_one(snapshot)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        """
        status = {
            'timestamp': time.time(),
            'uptime': time.time() - self.performance['start_time'],
            'system_status': self.monitoring['system_status'],
            'strategies': {},
            'performance': self.performance.copy(),
            'risk': self.global_risk.copy(),
            'alerts_count': len(self.monitoring['alerts'])
        }
        
        # Get status for each strategy
        for name, engine in self.engines.items():
            health = await self._check_engine_health(engine)
            
            status['strategies'][name] = StrategyStatus(
                name=name,
                enabled=self.strategy_config[name]['enabled'],
                health='HEALTHY' if health['healthy'] else 'CRITICAL',
                metrics=health['metrics'],
                last_update=time.time(),
                active_positions=0,  # Would need proper implementation
                daily_pnl=health['metrics'].get('total_pnl', 0)
            ).__dict__
        
        return status
    
    async def shutdown(self):
        """
        Graceful shutdown of all systems
        """
        self.monitoring['system_status'] = 'SHUTTING_DOWN'
        
        # Close all positions
        for name, engine in self.engines.items():
            if hasattr(engine, 'shutdown'):
                await engine.shutdown()
        
        # Final performance snapshot
        if self.mongodb:
            await self._store_performance_snapshot()
        
        # Send shutdown notification
        await self._broadcast_status({
            'event': 'SYSTEM_SHUTDOWN',
            'timestamp': time.time(),
            'final_performance': self.performance
        })
        
        self.monitoring['system_status'] = 'STOPPED'

# QA/QC Test for Orchestrator
async def qa_orchestrator_test():
    """
    QA: Test the complete orchestrator system
    """
    orchestrator = AuraQuantOrchestrator()
    
    # Initialize system
    init_result = await orchestrator.initialize()
    
    # Run execution cycles
    test_results = {
        'initialization': init_result,
        'execution_cycles': [],
        'system_status': None,
        'performance': None
    }
    
    # Execute 5 test cycles
    for i in range(5):
        cycle_result = await orchestrator.execute_orchestrated_strategy()
        test_results['execution_cycles'].append(cycle_result)
        await asyncio.sleep(0.1)  # Small delay between cycles
    
    # Get final status
    test_results['system_status'] = await orchestrator.get_system_status()
    test_results['performance'] = orchestrator.performance
    
    # Shutdown
    await orchestrator.shutdown()
    
    return test_results