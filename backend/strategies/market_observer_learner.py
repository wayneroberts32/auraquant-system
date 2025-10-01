"""
AuraQuant Market Observer & Learning Module
Infinity Money Synthetic Intelligence System
ALWAYS WATCHING • ALWAYS LEARNING • ALWAYS EVOLVING
Even When Not Trading - Building Intelligence 24/7
"""

import asyncio
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
import hashlib

@dataclass
class MarketObservation:
    """Single market observation snapshot"""
    timestamp: float
    symbol: str
    timeframe: str
    price: float
    volume: float
    volatility: float
    trend: str  # BULLISH, BEARISH, NEUTRAL
    strength: float
    patterns_detected: List[str]
    market_regime: str  # TRENDING, RANGING, VOLATILE
    sentiment: float  # -1 to 1
    metadata: Dict = field(default_factory=dict)

@dataclass
class LearningInsight:
    """Insight learned from observations"""
    insight_type: str  # PATTERN, CORRELATION, ANOMALY, REGIME_CHANGE
    symbol: str
    confidence: float
    description: str
    action_recommendation: str
    supporting_data: Dict
    timestamp: float
    expiry: float  # When this insight becomes stale

@dataclass
class MarketMemory:
    """Long-term market memory"""
    pattern_success_rates: Dict[str, float]
    regime_transitions: List[Dict]
    correlation_matrix: pd.DataFrame
    volatility_clusters: List[Dict]
    anomaly_catalog: List[Dict]
    learned_strategies: Dict[str, Dict]

class MarketObserverLearner:
    """
    Continuous market observation and learning system
    Watches markets 24/7, learns patterns, builds intelligence
    Even when not trading, the system is getting smarter
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        
        # Observation settings
        self.observation_config = {
            'symbols': ['BTC/USD', 'ETH/USD', 'SOL/USD', 'SPY', 'GLD', 'EUR/USD'],
            'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
            'observation_interval': 10,  # seconds
            'learning_interval': 60,  # seconds
            'memory_consolidation_interval': 3600  # 1 hour
        }
        
        # Real-time observation buffers
        self.observation_buffer = defaultdict(lambda: deque(maxlen=10000))
        self.pattern_observations = defaultdict(list)
        self.regime_observations = defaultdict(list)
        
        # Learning state
        self.learning_state = {
            'total_observations': 0,
            'patterns_learned': 0,
            'insights_generated': 0,
            'accuracy_improvements': 0,
            'last_learning_cycle': time.time()
        }
        
        # Market memory (long-term storage)
        self.market_memory = MarketMemory(
            pattern_success_rates={},
            regime_transitions=[],
            correlation_matrix=pd.DataFrame(),
            volatility_clusters=[],
            anomaly_catalog=[],
            learned_strategies={}
        )
        
        # Pattern evolution tracking
        self.pattern_evolution = defaultdict(lambda: {
            'occurrences': 0,
            'success_count': 0,
            'failure_count': 0,
            'avg_profit': 0,
            'avg_duration': 0,
            'confidence_score': 0.5,
            'last_seen': None,
            'evolution_stage': 'DISCOVERING'  # DISCOVERING -> TESTING -> VALIDATING -> PROVEN
        })
        
        # Market regime detection
        self.market_regimes = {
            'BULL_TREND': {'indicators': [], 'confidence': 0},
            'BEAR_TREND': {'indicators': [], 'confidence': 0},
            'RANGING': {'indicators': [], 'confidence': 0},
            'HIGH_VOLATILITY': {'indicators': [], 'confidence': 0},
            'LOW_VOLATILITY': {'indicators': [], 'confidence': 0},
            'ACCUMULATION': {'indicators': [], 'confidence': 0},
            'DISTRIBUTION': {'indicators': [], 'confidence': 0}
        }
        
        # Correlation tracking
        self.correlation_tracker = defaultdict(lambda: deque(maxlen=1000))
        
        # Anomaly detection
        self.anomaly_detector = {
            'baseline_stats': {},
            'anomaly_threshold': 3.0,  # Standard deviations
            'recent_anomalies': deque(maxlen=100)
        }
        
        # Strategy learning
        self.strategy_learner = {
            'discovered_strategies': [],
            'strategy_performance': {},
            'optimal_conditions': {},
            'strategy_combinations': []
        }
        
        # Real-time insights
        self.current_insights = deque(maxlen=100)
        
        # Performance metrics
        self.observer_metrics = {
            'observations_per_second': 0,
            'patterns_per_hour': 0,
            'insights_per_day': 0,
            'learning_rate': 0,
            'prediction_accuracy': 0
        }
    
    async def start_continuous_observation(self):
        """
        Main observation loop - runs 24/7
        This is the 'always on' brain of AuraQuant
        """
        print("🧠 AuraQuant Market Observer Started - Learning Mode Active")
        
        # Start parallel observation tasks
        tasks = [
            asyncio.create_task(self._observation_loop()),
            asyncio.create_task(self._learning_loop()),
            asyncio.create_task(self._memory_consolidation_loop()),
            asyncio.create_task(self._insight_generation_loop()),
            asyncio.create_task(self._evolution_loop())
        ]
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    
    async def _observation_loop(self):
        """
        Continuous market observation - the 'eyes' of the system
        """
        while True:
            try:
                for symbol in self.observation_config['symbols']:
                    # Observe market for each symbol
                    observation = await self._observe_market(symbol)
                    
                    # Store observation
                    self.observation_buffer[symbol].append(observation)
                    self.learning_state['total_observations'] += 1
                    
                    # Detect patterns in real-time
                    patterns = await self._detect_patterns_realtime(symbol, observation)
                    if patterns:
                        self.pattern_observations[symbol].extend(patterns)
                    
                    # Update market regime
                    await self._update_market_regime(symbol, observation)
                    
                    # Check for anomalies
                    anomaly = await self._detect_anomaly(symbol, observation)
                    if anomaly:
                        await self._handle_anomaly(anomaly)
                
                # Update metrics
                self.observer_metrics['observations_per_second'] = (
                    self.learning_state['total_observations'] / 
                    max(time.time() - self.learning_state['last_learning_cycle'], 1)
                )
                
                await asyncio.sleep(self.observation_config['observation_interval'])
                
            except Exception as e:
                print(f"Observation error: {e}")
                await asyncio.sleep(5)
    
    async def _learning_loop(self):
        """
        Continuous learning from observations - the 'brain evolution'
        """
        while True:
            try:
                await asyncio.sleep(self.observation_config['learning_interval'])
                
                # Learn from recent observations
                for symbol in self.observation_config['symbols']:
                    if symbol in self.observation_buffer:
                        observations = list(self.observation_buffer[symbol])
                        
                        if len(observations) > 10:
                            # Learn patterns
                            learned_patterns = await self._learn_patterns(symbol, observations)
                            
                            # Update pattern evolution
                            for pattern in learned_patterns:
                                await self._evolve_pattern_knowledge(pattern)
                            
                            # Learn correlations
                            await self._learn_correlations(symbol, observations)
                            
                            # Learn optimal strategies
                            await self._learn_strategies(symbol, observations)
                
                # Generate learning report
                await self._generate_learning_report()
                
                self.learning_state['last_learning_cycle'] = time.time()
                
            except Exception as e:
                print(f"Learning error: {e}")
                await asyncio.sleep(30)
    
    async def _memory_consolidation_loop(self):
        """
        Consolidate short-term observations into long-term memory
        """
        while True:
            try:
                await asyncio.sleep(self.observation_config['memory_consolidation_interval'])
                
                # Consolidate pattern knowledge
                await self._consolidate_pattern_memory()
                
                # Update correlation matrix
                await self._update_correlation_matrix()
                
                # Consolidate regime transitions
                await self._consolidate_regime_memory()
                
                # Prune old observations
                await self._prune_old_observations()
                
                # Save to MongoDB
                if self.mongodb:
                    await self._persist_memory_to_database()
                
                print(f"📊 Memory Consolidated - Patterns: {len(self.market_memory.pattern_success_rates)}, "
                      f"Insights: {self.learning_state['insights_generated']}")
                
            except Exception as e:
                print(f"Memory consolidation error: {e}")
                await asyncio.sleep(300)
    
    async def _insight_generation_loop(self):
        """
        Generate actionable insights from learning
        """
        while True:
            try:
                await asyncio.sleep(30)  # Generate insights every 30 seconds
                
                # Analyze all observations
                insights = []
                
                # Pattern-based insights
                pattern_insights = await self._generate_pattern_insights()
                insights.extend(pattern_insights)
                
                # Correlation-based insights
                correlation_insights = await self._generate_correlation_insights()
                insights.extend(correlation_insights)
                
                # Regime-based insights
                regime_insights = await self._generate_regime_insights()
                insights.extend(regime_insights)
                
                # Anomaly-based insights
                anomaly_insights = await self._generate_anomaly_insights()
                insights.extend(anomaly_insights)
                
                # Add insights to queue
                for insight in insights:
                    self.current_insights.append(insight)
                    self.learning_state['insights_generated'] += 1
                
                # Broadcast insights if significant
                significant_insights = [i for i in insights if i.confidence > 0.8]
                if significant_insights:
                    await self._broadcast_insights(significant_insights)
                
            except Exception as e:
                print(f"Insight generation error: {e}")
                await asyncio.sleep(30)
    
    async def _evolution_loop(self):
        """
        Evolve trading strategies based on learned patterns
        """
        while True:
            try:
                await asyncio.sleep(300)  # Evolve every 5 minutes
                
                # Evolve pattern recognition
                evolved_patterns = await self._evolve_patterns()
                
                # Evolve trading strategies
                evolved_strategies = await self._evolve_strategies()
                
                # Test evolved strategies on paper
                test_results = await self._test_evolved_strategies(evolved_strategies)
                
                # Promote successful evolutions
                for strategy in test_results:
                    if strategy['success_rate'] > 0.7:
                        await self._promote_strategy(strategy)
                
                self.learning_state['accuracy_improvements'] += len(evolved_patterns)
                
            except Exception as e:
                print(f"Evolution error: {e}")
                await asyncio.sleep(300)
    
    async def _observe_market(self, symbol: str) -> MarketObservation:
        """
        Observe current market state for a symbol
        """
        # In production, this would fetch real market data
        # For now, simulate observation
        
        current_price = 100 + np.random.randn() * 2
        volume = np.random.uniform(1000, 10000)
        volatility = np.abs(np.random.randn() * 0.02)
        
        # Determine trend
        if len(self.observation_buffer[symbol]) > 20:
            recent_prices = [obs.price for obs in list(self.observation_buffer[symbol])[-20:]]
            trend_slope = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
            
            if trend_slope > 0.01:
                trend = 'BULLISH'
            elif trend_slope < -0.01:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
            
            strength = min(abs(trend_slope) * 100, 1.0)
        else:
            trend = 'NEUTRAL'
            strength = 0.5
        
        # Determine market regime
        if volatility > 0.03:
            regime = 'VOLATILE'
        elif abs(strength) < 0.3:
            regime = 'RANGING'
        else:
            regime = 'TRENDING'
        
        return MarketObservation(
            timestamp=time.time(),
            symbol=symbol,
            timeframe='5m',
            price=current_price,
            volume=volume,
            volatility=volatility,
            trend=trend,
            strength=strength,
            patterns_detected=[],
            market_regime=regime,
            sentiment=np.random.uniform(-1, 1),
            metadata={'source': 'observation_loop'}
        )
    
    async def _detect_patterns_realtime(self, symbol: str, observation: MarketObservation) -> List[str]:
        """
        Detect patterns in real-time from observations
        """
        patterns = []
        
        if len(self.observation_buffer[symbol]) < 20:
            return patterns
        
        recent_obs = list(self.observation_buffer[symbol])[-20:]
        prices = [obs.price for obs in recent_obs]
        
        # Simple pattern detection
        # Higher high, higher low (uptrend)
        if len(prices) > 4:
            if prices[-1] > prices[-3] and prices[-2] > prices[-4]:
                patterns.append('UPTREND_CONTINUATION')
        
        # Lower high, lower low (downtrend)
        if len(prices) > 4:
            if prices[-1] < prices[-3] and prices[-2] < prices[-4]:
                patterns.append('DOWNTREND_CONTINUATION')
        
        # Volatility breakout
        recent_volatility = np.std(prices[-10:]) if len(prices) > 10 else 0
        if observation.volatility > recent_volatility * 2:
            patterns.append('VOLATILITY_BREAKOUT')
        
        # Volume spike
        recent_volumes = [obs.volume for obs in recent_obs]
        avg_volume = np.mean(recent_volumes)
        if observation.volume > avg_volume * 1.5:
            patterns.append('VOLUME_SPIKE')
        
        return patterns
    
    async def _update_market_regime(self, symbol: str, observation: MarketObservation):
        """
        Update market regime detection
        """
        regime = observation.market_regime
        
        # Update regime confidence
        if regime in self.market_regimes:
            # Increase confidence if regime persists
            self.market_regimes[regime]['confidence'] = min(
                self.market_regimes[regime]['confidence'] + 0.1, 1.0
            )
            self.market_regimes[regime]['indicators'].append(observation.timestamp)
        
        # Decay other regime confidences
        for other_regime in self.market_regimes:
            if other_regime != regime:
                self.market_regimes[other_regime]['confidence'] *= 0.95
    
    async def _detect_anomaly(self, symbol: str, observation: MarketObservation) -> Optional[Dict]:
        """
        Detect market anomalies
        """
        if symbol not in self.anomaly_detector['baseline_stats']:
            # Initialize baseline
            if len(self.observation_buffer[symbol]) > 100:
                recent = list(self.observation_buffer[symbol])[-100:]
                prices = [obs.price for obs in recent]
                self.anomaly_detector['baseline_stats'][symbol] = {
                    'mean': np.mean(prices),
                    'std': np.std(prices)
                }
            return None
        
        baseline = self.anomaly_detector['baseline_stats'][symbol]
        z_score = abs((observation.price - baseline['mean']) / baseline['std'])
        
        if z_score > self.anomaly_detector['anomaly_threshold']:
            return {
                'symbol': symbol,
                'type': 'PRICE_ANOMALY',
                'z_score': z_score,
                'observation': observation,
                'timestamp': time.time()
            }
        
        return None
    
    async def _handle_anomaly(self, anomaly: Dict):
        """
        Handle detected anomaly
        """
        self.anomaly_detector['recent_anomalies'].append(anomaly)
        
        # Add to anomaly catalog for learning
        self.market_memory.anomaly_catalog.append({
            'timestamp': anomaly['timestamp'],
            'symbol': anomaly['symbol'],
            'type': anomaly['type'],
            'magnitude': anomaly['z_score']
        })
        
        # Generate insight from anomaly
        insight = LearningInsight(
            insight_type='ANOMALY',
            symbol=anomaly['symbol'],
            confidence=min(anomaly['z_score'] / 5, 1.0),
            description=f"Price anomaly detected: {anomaly['z_score']:.2f} standard deviations",
            action_recommendation='MONITOR_CLOSELY',
            supporting_data=anomaly,
            timestamp=time.time(),
            expiry=time.time() + 3600  # 1 hour expiry
        )
        
        self.current_insights.append(insight)
    
    async def _learn_patterns(self, symbol: str, observations: List[MarketObservation]) -> List[Dict]:
        """
        Learn patterns from observations
        """
        learned = []
        
        # Extract features
        prices = [obs.price for obs in observations]
        volumes = [obs.volume for obs in observations]
        trends = [obs.trend for obs in observations]
        
        # Pattern: Trend persistence
        if len(set(trends[-5:])) == 1 and trends[-1] != 'NEUTRAL':
            pattern = {
                'name': f'{trends[-1]}_PERSISTENCE',
                'symbol': symbol,
                'confidence': 0.8,
                'observations': 5
            }
            learned.append(pattern)
        
        # Pattern: Volume-price correlation
        if len(prices) > 10:
            price_change = (prices[-1] - prices[-10]) / prices[-10]
            volume_change = (volumes[-1] - np.mean(volumes[-10:])) / np.mean(volumes[-10:])
            
            if abs(price_change) > 0.02 and volume_change > 0.5:
                pattern = {
                    'name': 'VOLUME_CONFIRMED_MOVE',
                    'symbol': symbol,
                    'confidence': 0.75,
                    'price_change': price_change,
                    'volume_change': volume_change
                }
                learned.append(pattern)
        
        # Pattern: Volatility clustering
        if len(observations) > 20:
            recent_vol = [obs.volatility for obs in observations[-10:]]
            older_vol = [obs.volatility for obs in observations[-20:-10]]
            
            if np.mean(recent_vol) > np.mean(older_vol) * 1.5:
                pattern = {
                    'name': 'VOLATILITY_EXPANSION',
                    'symbol': symbol,
                    'confidence': 0.7,
                    'expansion_ratio': np.mean(recent_vol) / np.mean(older_vol)
                }
                learned.append(pattern)
        
        self.learning_state['patterns_learned'] += len(learned)
        return learned
    
    async def _evolve_pattern_knowledge(self, pattern: Dict):
        """
        Evolve understanding of a pattern over time
        """
        pattern_name = pattern['name']
        
        # Update pattern evolution tracking
        evolution = self.pattern_evolution[pattern_name]
        evolution['occurrences'] += 1
        evolution['last_seen'] = time.time()
        
        # Update confidence based on frequency
        if evolution['occurrences'] > 10:
            evolution['confidence_score'] = min(evolution['confidence_score'] + 0.05, 0.95)
        
        # Progress evolution stage
        if evolution['occurrences'] > 100 and evolution['confidence_score'] > 0.8:
            evolution['evolution_stage'] = 'PROVEN'
        elif evolution['occurrences'] > 50 and evolution['confidence_score'] > 0.6:
            evolution['evolution_stage'] = 'VALIDATING'
        elif evolution['occurrences'] > 20:
            evolution['evolution_stage'] = 'TESTING'
    
    async def _learn_correlations(self, symbol: str, observations: List[MarketObservation]):
        """
        Learn correlations between different market aspects
        """
        if len(observations) < 20:
            return
        
        # Build correlation data
        prices = [obs.price for obs in observations]
        volumes = [obs.volume for obs in observations]
        volatilities = [obs.volatility for obs in observations]
        
        # Calculate correlations
        price_volume_corr = np.corrcoef(prices, volumes)[0, 1]
        price_volatility_corr = np.corrcoef(prices, volatilities)[0, 1]
        volume_volatility_corr = np.corrcoef(volumes, volatilities)[0, 1]
        
        # Store correlations
        self.correlation_tracker[symbol].append({
            'timestamp': time.time(),
            'price_volume': price_volume_corr,
            'price_volatility': price_volatility_corr,
            'volume_volatility': volume_volatility_corr
        })
    
    async def _learn_strategies(self, symbol: str, observations: List[MarketObservation]):
        """
        Learn and discover new trading strategies
        """
        if len(observations) < 50:
            return
        
        # Analyze successful patterns
        successful_patterns = []
        for i in range(20, len(observations) - 10):
            # Look for price increases after specific patterns
            price_before = observations[i].price
            price_after = observations[i + 10].price
            profit = (price_after - price_before) / price_before
            
            if profit > 0.02:  # 2% profit
                # Analyze what patterns preceded this
                patterns_before = []
                for j in range(max(0, i-5), i):
                    patterns_before.extend(observations[j].patterns_detected)
                
                if patterns_before:
                    successful_patterns.append({
                        'patterns': patterns_before,
                        'profit': profit,
                        'symbol': symbol,
                        'timestamp': observations[i].timestamp
                    })
        
        # Learn from successful patterns
        if successful_patterns:
            # Group by pattern combination
            pattern_combos = defaultdict(list)
            for sp in successful_patterns:
                combo_key = ','.join(sorted(sp['patterns']))
                pattern_combos[combo_key].append(sp['profit'])
            
            # Find best performing combinations
            for combo, profits in pattern_combos.items():
                avg_profit = np.mean(profits)
                if avg_profit > 0.015 and len(profits) > 3:
                    # Discovered a potentially profitable strategy
                    strategy = {
                        'name': f'PATTERN_COMBO_{hashlib.md5(combo.encode()).hexdigest()[:8]}',
                        'patterns': combo.split(','),
                        'avg_profit': avg_profit,
                        'occurrences': len(profits),
                        'symbol': symbol,
                        'discovered_at': time.time()
                    }
                    
                    self.strategy_learner['discovered_strategies'].append(strategy)
                    self.market_memory.learned_strategies[strategy['name']] = strategy
    
    async def _consolidate_pattern_memory(self):
        """
        Consolidate pattern knowledge into long-term memory
        """
        for pattern_name, evolution in self.pattern_evolution.items():
            if evolution['occurrences'] > 0:
                success_rate = evolution['success_count'] / max(evolution['occurrences'], 1)
                self.market_memory.pattern_success_rates[pattern_name] = success_rate
    
    async def _update_correlation_matrix(self):
        """
        Update the correlation matrix between symbols
        """
        symbols = list(self.observation_buffer.keys())
        if len(symbols) < 2:
            return
        
        # Build price matrix
        price_data = {}
        for symbol in symbols:
            if len(self.observation_buffer[symbol]) > 100:
                prices = [obs.price for obs in list(self.observation_buffer[symbol])[-100:]]
                price_data[symbol] = prices
        
        if len(price_data) > 1:
            df = pd.DataFrame(price_data)
            self.market_memory.correlation_matrix = df.corr()
    
    async def _consolidate_regime_memory(self):
        """
        Consolidate market regime transitions
        """
        # Find regime with highest confidence
        dominant_regime = max(self.market_regimes.items(), 
                             key=lambda x: x[1]['confidence'])
        
        if dominant_regime[1]['confidence'] > 0.7:
            self.market_memory.regime_transitions.append({
                'regime': dominant_regime[0],
                'confidence': dominant_regime[1]['confidence'],
                'timestamp': time.time()
            })
    
    async def _prune_old_observations(self):
        """
        Remove old observations to manage memory
        """
        cutoff_time = time.time() - 86400  # 24 hours
        
        for symbol in list(self.pattern_observations.keys()):
            self.pattern_observations[symbol] = [
                p for p in self.pattern_observations[symbol]
                if p.get('timestamp', 0) > cutoff_time
            ]
    
    async def _persist_memory_to_database(self):
        """
        Save market memory to MongoDB
        """
        if not self.mongodb:
            return
        
        memory_doc = {
            'timestamp': time.time(),
            'pattern_success_rates': self.market_memory.pattern_success_rates,
            'regime_transitions': self.market_memory.regime_transitions[-100:],  # Last 100
            'correlation_matrix': self.market_memory.correlation_matrix.to_dict() if not self.market_memory.correlation_matrix.empty else {},
            'volatility_clusters': self.market_memory.volatility_clusters[-50:],  # Last 50
            'anomaly_catalog': self.market_memory.anomaly_catalog[-100:],  # Last 100
            'learned_strategies': self.market_memory.learned_strategies,
            'learning_state': self.learning_state,
            'observer_metrics': self.observer_metrics
        }
        
        await self.mongodb.market_memory.replace_one(
            {'type': 'market_memory'},
            memory_doc,
            upsert=True
        )
    
    async def _generate_pattern_insights(self) -> List[LearningInsight]:
        """
        Generate insights from pattern observations
        """
        insights = []
        
        for pattern_name, evolution in self.pattern_evolution.items():
            if evolution['evolution_stage'] == 'PROVEN' and evolution['confidence_score'] > 0.8:
                insight = LearningInsight(
                    insight_type='PATTERN',
                    symbol='MULTIPLE',
                    confidence=evolution['confidence_score'],
                    description=f"Pattern {pattern_name} proven reliable with {evolution['occurrences']} observations",
                    action_recommendation='CONSIDER_FOR_TRADING',
                    supporting_data={'pattern': pattern_name, 'evolution': dict(evolution)},
                    timestamp=time.time(),
                    expiry=time.time() + 7200  # 2 hour expiry
                )
                insights.append(insight)
        
        return insights
    
    async def _generate_correlation_insights(self) -> List[LearningInsight]:
        """
        Generate insights from correlations
        """
        insights = []
        
        if not self.market_memory.correlation_matrix.empty:
            # Find strong correlations
            for symbol1 in self.market_memory.correlation_matrix.index:
                for symbol2 in self.market_memory.correlation_matrix.columns:
                    if symbol1 != symbol2:
                        corr = self.market_memory.correlation_matrix.loc[symbol1, symbol2]
                        
                        if abs(corr) > 0.8:
                            insight = LearningInsight(
                                insight_type='CORRELATION',
                                symbol=f"{symbol1}/{symbol2}",
                                confidence=abs(corr),
                                description=f"Strong correlation detected: {corr:.3f}",
                                action_recommendation='USE_FOR_PAIR_TRADING' if corr > 0 else 'USE_FOR_HEDGING',
                                supporting_data={'correlation': corr, 'pair': [symbol1, symbol2]},
                                timestamp=time.time(),
                                expiry=time.time() + 3600
                            )
                            insights.append(insight)
        
        return insights
    
    async def _generate_regime_insights(self) -> List[LearningInsight]:
        """
        Generate insights from market regime
        """
        insights = []
        
        # Find dominant regime
        dominant = max(self.market_regimes.items(), key=lambda x: x[1]['confidence'])
        
        if dominant[1]['confidence'] > 0.75:
            insight = LearningInsight(
                insight_type='REGIME_CHANGE',
                symbol='MARKET',
                confidence=dominant[1]['confidence'],
                description=f"Market regime: {dominant[0]}",
                action_recommendation=self._get_regime_recommendation(dominant[0]),
                supporting_data={'regime': dominant[0], 'indicators': dominant[1]['indicators'][-10:]},
                timestamp=time.time(),
                expiry=time.time() + 1800
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_anomaly_insights(self) -> List[LearningInsight]:
        """
        Generate insights from anomalies
        """
        insights = []
        
        recent_anomalies = list(self.anomaly_detector['recent_anomalies'])
        if len(recent_anomalies) > 5:
            # Multiple anomalies indicate something significant
            insight = LearningInsight(
                insight_type='ANOMALY',
                symbol='MULTIPLE',
                confidence=0.9,
                description=f"Multiple anomalies detected ({len(recent_anomalies)} in recent period)",
                action_recommendation='REDUCE_RISK',
                supporting_data={'anomaly_count': len(recent_anomalies)},
                timestamp=time.time(),
                expiry=time.time() + 900
            )
            insights.append(insight)
        
        return insights
    
    def _get_regime_recommendation(self, regime: str) -> str:
        """
        Get trading recommendation based on regime
        """
        recommendations = {
            'BULL_TREND': 'INCREASE_LONG_EXPOSURE',
            'BEAR_TREND': 'INCREASE_SHORT_EXPOSURE',
            'RANGING': 'USE_MEAN_REVERSION',
            'HIGH_VOLATILITY': 'REDUCE_POSITION_SIZES',
            'LOW_VOLATILITY': 'INCREASE_POSITION_SIZES',
            'ACCUMULATION': 'PREPARE_FOR_BREAKOUT',
            'DISTRIBUTION': 'PREPARE_FOR_BREAKDOWN'
        }
        return recommendations.get(regime, 'MONITOR')
    
    async def _broadcast_insights(self, insights: List[LearningInsight]):
        """
        Broadcast significant insights
        """
        for insight in insights:
            print(f"🎯 INSIGHT: {insight.description} (Confidence: {insight.confidence:.2f})")
            print(f"   Action: {insight.action_recommendation}")
    
    async def _evolve_patterns(self) -> List[Dict]:
        """
        Evolve pattern recognition based on observations
        """
        evolved = []
        
        for pattern_name, evolution in self.pattern_evolution.items():
            if evolution['evolution_stage'] == 'TESTING':
                # Test if pattern should be promoted
                if evolution['confidence_score'] > 0.7:
                    evolution['evolution_stage'] = 'VALIDATING'
                    evolved.append({
                        'pattern': pattern_name,
                        'new_stage': 'VALIDATING',
                        'confidence': evolution['confidence_score']
                    })
        
        return evolved
    
    async def _evolve_strategies(self) -> List[Dict]:
        """
        Evolve trading strategies
        """
        evolved = []
        
        for strategy in self.strategy_learner['discovered_strategies'][-10:]:  # Recent 10
            # Test strategy variations
            variations = await self._generate_strategy_variations(strategy)
            
            for variation in variations:
                evolved.append(variation)
        
        return evolved
    
    async def _generate_strategy_variations(self, strategy: Dict) -> List[Dict]:
        """
        Generate variations of a successful strategy
        """
        variations = []
        
        # Variation 1: Tighter conditions
        tight_strategy = strategy.copy()
        tight_strategy['name'] = f"{strategy['name']}_TIGHT"
        tight_strategy['confidence_threshold'] = 0.8
        variations.append(tight_strategy)
        
        # Variation 2: Different timeframe
        tf_strategy = strategy.copy()
        tf_strategy['name'] = f"{strategy['name']}_15M"
        tf_strategy['timeframe'] = '15m'
        variations.append(tf_strategy)
        
        return variations
    
    async def _test_evolved_strategies(self, strategies: List[Dict]) -> List[Dict]:
        """
        Paper test evolved strategies
        """
        results = []
        
        for strategy in strategies:
            # Simulate testing
            success_rate = np.random.uniform(0.4, 0.9)  # In production, actual backtesting
            
            results.append({
                'strategy': strategy,
                'success_rate': success_rate,
                'tests_run': 100,
                'avg_profit': success_rate * 0.02
            })
        
        return results
    
    async def _promote_strategy(self, strategy: Dict):
        """
        Promote successful strategy to production
        """
        print(f"🚀 Strategy Promoted: {strategy['strategy']['name']} "
              f"(Success Rate: {strategy['success_rate']:.2%})")
        
        # Add to proven strategies
        self.market_memory.learned_strategies[strategy['strategy']['name']] = {
            **strategy['strategy'],
            'promoted_at': time.time(),
            'success_rate': strategy['success_rate']
        }
    
    async def _generate_learning_report(self):
        """
        Generate periodic learning report
        """
        if self.learning_state['total_observations'] % 1000 == 0:
            print(f"\n📈 LEARNING REPORT")
            print(f"   Total Observations: {self.learning_state['total_observations']:,}")
            print(f"   Patterns Learned: {self.learning_state['patterns_learned']}")
            print(f"   Insights Generated: {self.learning_state['insights_generated']}")
            print(f"   Proven Patterns: {len([p for p, e in self.pattern_evolution.items() if e['evolution_stage'] == 'PROVEN'])}")
            print(f"   Discovered Strategies: {len(self.strategy_learner['discovered_strategies'])}")
            print(f"   Observation Rate: {self.observer_metrics['observations_per_second']:.2f}/sec")
            print()
    
    def get_learning_status(self) -> Dict[str, Any]:
        """
        Get current learning status
        """
        return {
            'learning_state': self.learning_state,
            'proven_patterns': len([p for p, e in self.pattern_evolution.items() 
                                   if e['evolution_stage'] == 'PROVEN']),
            'total_patterns': len(self.pattern_evolution),
            'discovered_strategies': len(self.strategy_learner['discovered_strategies']),
            'current_insights': len(self.current_insights),
            'dominant_regime': max(self.market_regimes.items(), 
                                  key=lambda x: x[1]['confidence'])[0],
            'observer_metrics': self.observer_metrics
        }
    
    async def get_trading_recommendations(self) -> List[Dict]:
        """
        Get current trading recommendations based on learning
        """
        recommendations = []
        
        # Get recent high-confidence insights
        for insight in self.current_insights:
            if insight.confidence > 0.75 and insight.expiry > time.time():
                recommendations.append({
                    'type': insight.insight_type,
                    'action': insight.action_recommendation,
                    'confidence': insight.confidence,
                    'description': insight.description,
                    'data': insight.supporting_data
                })
        
        # Add proven strategies
        for strategy_name, strategy in self.market_memory.learned_strategies.items():
            if strategy.get('success_rate', 0) > 0.7:
                recommendations.append({
                    'type': 'STRATEGY',
                    'action': 'EXECUTE_STRATEGY',
                    'confidence': strategy.get('success_rate', 0.7),
                    'description': f"Execute strategy: {strategy_name}",
                    'data': strategy
                })
        
        return recommendations


# QA/QC Test for Market Observer
async def qa_observer_test():
    """
    QA: Test market observer and learning capabilities
    """
    observer = MarketObserverLearner()
    
    # Run observation for a short period
    test_duration = 5  # seconds
    
    # Start observation tasks
    observation_task = asyncio.create_task(observer._observation_loop())
    learning_task = asyncio.create_task(observer._learning_loop())
    
    # Let it run for test duration
    await asyncio.sleep(test_duration)
    
    # Cancel tasks
    observation_task.cancel()
    learning_task.cancel()
    
    # Get status
    status = observer.get_learning_status()
    
    qa_results = {
        'observations_collected': status['learning_state']['total_observations'],
        'patterns_learned': status['learning_state']['patterns_learned'],
        'insights_generated': status['learning_state']['insights_generated'],
        'test_passed': status['learning_state']['total_observations'] > 0
    }
    
    return qa_results