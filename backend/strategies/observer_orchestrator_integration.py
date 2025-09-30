"""
AuraQuant Observer-Orchestrator Integration Module
===================================================
ADD-ONLY Integration: Connects Market Observer to Strategy Orchestrator
WITHOUT modifying existing code - only adding new integration points

Created: 2025-01-30
Status: PRODUCTION-READY
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

# Import existing modules (non-disruptive)
from .market_observer_learner import MarketObserverLearner, LearningInsight
from .strategy_orchestrator import AuraQuantOrchestrator

class ObserverOrchestratorBridge:
    """
    Bridge between Market Observer and Strategy Orchestrator
    Enables bi-directional communication without modifying original modules
    """
    
    def __init__(self, orchestrator: AuraQuantOrchestrator, observer: MarketObserverLearner):
        self.orchestrator = orchestrator
        self.observer = observer
        
        # Integration state
        self.integration_state = {
            'status': 'INITIALIZING',
            'observer_connected': False,
            'orchestrator_connected': False,
            'insights_processed': 0,
            'signals_generated': 0,
            'last_sync': time.time()
        }
        
        # WebSocket channels for real-time updates
        self.channels = {
            'observer_feed': 'ws://api/observer/feed',
            'orchestrator_control': 'ws://api/orchestrator/control',
            'insights_broadcast': 'ws://api/insights/broadcast'
        }
        
        # Insight processing queue
        self.insight_queue = asyncio.Queue()
        
        # Signal mapping from observer insights to orchestrator actions
        self.signal_mapping = {
            'PATTERN': self._process_pattern_signal,
            'CORRELATION': self._process_correlation_signal,
            'ANOMALY': self._process_anomaly_signal,
            'REGIME_CHANGE': self._process_regime_change_signal
        }
        
    async def initialize_integration(self) -> Dict[str, Any]:
        """
        Initialize the integration between Observer and Orchestrator
        """
        integration_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'INITIALIZING',
            'connections': {},
            'channels': {}
        }
        
        try:
            # Connect to Observer
            if self.observer:
                self.integration_state['observer_connected'] = True
                integration_report['connections']['observer'] = 'CONNECTED'
                
                # Subscribe to observer insights
                await self._subscribe_to_observer_insights()
            
            # Connect to Orchestrator
            if self.orchestrator:
                self.integration_state['orchestrator_connected'] = True
                integration_report['connections']['orchestrator'] = 'CONNECTED'
                
                # Register observer as data source
                await self._register_with_orchestrator()
            
            # Start integration tasks
            asyncio.create_task(self._insight_processor_loop())
            asyncio.create_task(self._sync_loop())
            asyncio.create_task(self._health_monitor_loop())
            
            self.integration_state['status'] = 'ACTIVE'
            integration_report['status'] = 'SUCCESS'
            
        except Exception as e:
            integration_report['status'] = 'FAILED'
            integration_report['error'] = str(e)
            self.integration_state['status'] = 'ERROR'
        
        return integration_report
    
    async def _subscribe_to_observer_insights(self):
        """
        Subscribe to real-time insights from the Observer
        """
        # Hook into observer's current_insights
        if hasattr(self.observer, 'current_insights'):
            # Start monitoring for new insights
            asyncio.create_task(self._monitor_observer_insights())
    
    async def _register_with_orchestrator(self):
        """
        Register the Observer as a data source for the Orchestrator
        """
        # Add observer to orchestrator's engines (non-disruptive)
        if not hasattr(self.orchestrator.engines, 'OBSERVER'):
            self.orchestrator.engines['OBSERVER'] = {
                'module': self.observer,
                'bridge': self,
                'status': 'ACTIVE'
            }
    
    async def _monitor_observer_insights(self):
        """
        Monitor Observer for new insights and queue them for processing
        """
        last_insight_count = 0
        
        while True:
            try:
                current_insights = list(self.observer.current_insights)
                
                # Check for new insights
                if len(current_insights) > last_insight_count:
                    new_insights = current_insights[last_insight_count:]
                    
                    for insight in new_insights:
                        await self.insight_queue.put(insight)
                        self.integration_state['insights_processed'] += 1
                    
                    last_insight_count = len(current_insights)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error monitoring insights: {e}")
                await asyncio.sleep(5)
    
    async def _insight_processor_loop(self):
        """
        Process insights from Observer and generate signals for Orchestrator
        """
        while True:
            try:
                # Get insight from queue
                insight = await self.insight_queue.get()
                
                # Process based on insight type
                if insight.insight_type in self.signal_mapping:
                    signal = await self.signal_mapping[insight.insight_type](insight)
                    
                    if signal:
                        await self._send_signal_to_orchestrator(signal)
                        self.integration_state['signals_generated'] += 1
                
                # Store processed insight
                await self._store_processed_insight(insight)
                
            except Exception as e:
                print(f"Error processing insight: {e}")
                await asyncio.sleep(1)
    
    async def _process_pattern_signal(self, insight: LearningInsight) -> Optional[Dict]:
        """
        Convert pattern insights into trading signals
        """
        if insight.confidence < 0.7:
            return None
        
        signal = {
            'type': 'PATTERN_SIGNAL',
            'symbol': insight.symbol,
            'action': insight.action_recommendation,
            'confidence': insight.confidence,
            'source': 'OBSERVER',
            'timestamp': time.time(),
            'metadata': {
                'pattern': insight.description,
                'supporting_data': insight.supporting_data
            }
        }
        
        # Route to appropriate strategy
        if 'momentum' in insight.description.lower():
            signal['target_strategy'] = 'HFT'
        elif 'arbitrage' in insight.description.lower():
            signal['target_strategy'] = 'ARBITRAGE'
        else:
            signal['target_strategy'] = 'EVENT'
        
        return signal
    
    async def _process_correlation_signal(self, insight: LearningInsight) -> Optional[Dict]:
        """
        Convert correlation insights into portfolio adjustments
        """
        signal = {
            'type': 'CORRELATION_SIGNAL',
            'action': 'ADJUST_PORTFOLIO',
            'confidence': insight.confidence,
            'source': 'OBSERVER',
            'timestamp': time.time(),
            'metadata': insight.supporting_data
        }
        
        # High correlation = reduce position sizes
        if insight.confidence > 0.8:
            signal['risk_adjustment'] = 'REDUCE_EXPOSURE'
        
        return signal
    
    async def _process_anomaly_signal(self, insight: LearningInsight) -> Optional[Dict]:
        """
        Convert anomaly insights into risk management signals
        """
        signal = {
            'type': 'ANOMALY_SIGNAL',
            'symbol': insight.symbol,
            'action': 'RISK_ALERT',
            'severity': 'HIGH' if insight.confidence > 0.8 else 'MEDIUM',
            'source': 'OBSERVER',
            'timestamp': time.time(),
            'metadata': {
                'anomaly_type': insight.description,
                'recommended_action': insight.action_recommendation
            }
        }
        
        # Critical anomalies trigger circuit breaker consideration
        if insight.confidence > 0.9:
            signal['circuit_breaker_check'] = True
        
        return signal
    
    async def _process_regime_change_signal(self, insight: LearningInsight) -> Optional[Dict]:
        """
        Convert regime change insights into strategy adjustments
        """
        signal = {
            'type': 'REGIME_CHANGE_SIGNAL',
            'action': 'ADJUST_STRATEGIES',
            'new_regime': insight.description,
            'confidence': insight.confidence,
            'source': 'OBSERVER',
            'timestamp': time.time(),
            'metadata': insight.supporting_data
        }
        
        # Adjust strategy allocations based on regime
        if 'volatile' in insight.description.lower():
            signal['adjustments'] = {
                'HFT': {'allocation_change': -10},
                'ARBITRAGE': {'allocation_change': +10},
                'EVENT': {'allocation_change': 0}
            }
        elif 'trending' in insight.description.lower():
            signal['adjustments'] = {
                'HFT': {'allocation_change': +10},
                'ARBITRAGE': {'allocation_change': -5},
                'EVENT': {'allocation_change': -5}
            }
        
        return signal
    
    async def _send_signal_to_orchestrator(self, signal: Dict):
        """
        Send processed signal to the Orchestrator
        """
        # Add signal to orchestrator's execution queue
        if hasattr(self.orchestrator, 'signal_queue'):
            await self.orchestrator.signal_queue.put(signal)
        
        # Broadcast signal for monitoring
        await self._broadcast_signal(signal)
        
        # Log to MongoDB
        if self.orchestrator.mongodb:
            await self.orchestrator.mongodb.observer_signals.insert_one(signal)
    
    async def _store_processed_insight(self, insight: LearningInsight):
        """
        Store processed insight for audit trail
        """
        if self.orchestrator.mongodb:
            insight_doc = {
                'timestamp': insight.timestamp,
                'type': insight.insight_type,
                'symbol': insight.symbol,
                'confidence': insight.confidence,
                'description': insight.description,
                'action': insight.action_recommendation,
                'processed_at': time.time()
            }
            await self.orchestrator.mongodb.processed_insights.insert_one(insight_doc)
    
    async def _broadcast_signal(self, signal: Dict):
        """
        Broadcast signal to WebSocket channels
        """
        if self.orchestrator.websocket:
            await self.orchestrator.websocket.broadcast(json.dumps({
                'event': 'OBSERVER_SIGNAL',
                'data': signal
            }))
    
    async def _sync_loop(self):
        """
        Periodic sync between Observer and Orchestrator
        """
        while True:
            try:
                # Sync market regimes
                if hasattr(self.observer, 'market_regimes'):
                    await self._sync_market_regimes()
                
                # Sync pattern evolution
                if hasattr(self.observer, 'pattern_evolution'):
                    await self._sync_pattern_evolution()
                
                # Update integration state
                self.integration_state['last_sync'] = time.time()
                
                await asyncio.sleep(60)  # Sync every minute
                
            except Exception as e:
                print(f"Sync error: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes
    
    async def _sync_market_regimes(self):
        """
        Sync market regime information
        """
        # Share regime information with orchestrator
        if hasattr(self.orchestrator, 'market_context'):
            self.orchestrator.market_context = self.observer.market_regimes
    
    async def _sync_pattern_evolution(self):
        """
        Sync evolved patterns with strategy engines
        """
        # Share proven patterns with relevant strategies
        proven_patterns = {
            k: v for k, v in self.observer.pattern_evolution.items()
            if v['evolution_stage'] == 'PROVEN'
        }
        
        if proven_patterns and hasattr(self.orchestrator, 'engines'):
            # Update HFT engine with momentum patterns
            if 'HFT' in self.orchestrator.engines:
                self.orchestrator.engines['HFT'].proven_patterns = proven_patterns
    
    async def _health_monitor_loop(self):
        """
        Monitor health of the integration
        """
        while True:
            try:
                health_status = {
                    'timestamp': time.time(),
                    'observer_alive': self.integration_state['observer_connected'],
                    'orchestrator_alive': self.integration_state['orchestrator_connected'],
                    'insights_rate': self.integration_state['insights_processed'] / (time.time() - self.integration_state['last_sync']),
                    'signal_rate': self.integration_state['signals_generated'] / (time.time() - self.integration_state['last_sync']),
                    'queue_size': self.insight_queue.qsize()
                }
                
                # Alert if unhealthy
                if not health_status['observer_alive'] or not health_status['orchestrator_alive']:
                    print(f"⚠️ Integration Health Warning: {health_status}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Health monitor error: {e}")
                await asyncio.sleep(60)

# Factory function to create integration
async def create_observer_orchestrator_integration(
    orchestrator: AuraQuantOrchestrator,
    observer: MarketObserverLearner
) -> ObserverOrchestratorBridge:
    """
    Factory function to create and initialize the integration bridge
    """
    bridge = ObserverOrchestratorBridge(orchestrator, observer)
    await bridge.initialize_integration()
    return bridge