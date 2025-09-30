"""
Evolution Monitoring System for AuraQuant
Professor/Engineer's Note: This monitors and tracks the learning evolution of your trading AI
WITHOUT modifying existing code - Task 5/12
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import threading
import time
from collections import deque
from dataclasses import dataclass, asdict
import statistics

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import get_persistence_service

@dataclass
class EvolutionMetric:
    """Evolution metric data structure"""
    timestamp: datetime
    generation: int
    fitness_score: float
    win_rate: float
    avg_confidence: float
    consciousness_level: float
    learning_rate: float
    total_trades: int
    successful_trades: int
    failed_trades: int
    patterns_discovered: int
    strategy_effectiveness: Dict[str, float]

@dataclass
class DiscoveredPattern:
    """Discovered trading pattern"""
    pattern_id: str
    discovered_at: datetime
    pattern_type: str
    confidence: float
    occurrences: int
    success_rate: float
    last_seen: datetime
    market_conditions: Dict[str, Any]

class EvolutionMonitor:
    """
    Monitors and tracks the evolution of the trading AI system
    Provides real-time insights into learning progress
    """
    
    def __init__(self):
        """Initialize evolution monitoring system"""
        # MongoDB persistence
        self.persistence = get_persistence_service()
        
        # Evolution tracking
        self.current_generation = 1
        self.evolution_history = deque(maxlen=1000)
        self.discovered_patterns = {}
        self.strategy_performance = {}
        self.adaptation_history = []
        
        # Performance metrics
        self.metrics_buffer = deque(maxlen=100)
        self.real_time_metrics = {}
        
        # Monitoring settings
        self.monitoring_interval = 60  # Check every minute
        self.analysis_window = 100  # Last 100 trades for analysis
        
        # Background monitoring
        self.monitoring_thread = None
        self.running = True
        
        # Initialize collections
        self._init_mongodb_collections()
        
        print("🔬 Evolution Monitoring System Initialized")
        self._start_monitoring()
        
    def _init_mongodb_collections(self):
        """Initialize MongoDB collections for evolution tracking"""
        if self.persistence is None or self.persistence.db is None:
            return
            
        db = self.persistence.db
        
        # Create collections with indexes
        collections = {
            'evolution_metrics': [
                ('generation', -1),
                ('timestamp', -1),
                ('fitness_score', -1)
            ],
            'discovered_patterns': [
                ('pattern_id', 1),
                ('success_rate', -1),
                ('discovered_at', -1)
            ],
            'strategy_performance': [
                ('strategy_name', 1),
                ('timestamp', -1),
                ('effectiveness', -1)
            ],
            'adaptation_history': [
                ('timestamp', -1),
                ('trigger', 1),
                ('adaptation_type', 1)
            ]
        }
        
        for collection_name, indexes in collections.items():
            try:
                collection = db[collection_name]
                for index in indexes:
                    collection.create_index([index])
            except Exception as e:
                print(f"Error creating collection {collection_name}: {e}")
                
        print("📊 Evolution tracking collections initialized")
        
    def _start_monitoring(self):
        """Start background monitoring thread"""
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            daemon=True
        )
        self.monitoring_thread.start()
        print("📡 Evolution monitoring started")
        
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.running:
            try:
                # Collect metrics
                metrics = self._collect_current_metrics()
                if metrics:
                    self.track_evolution_progress(metrics)
                    
                # Analyze patterns
                self._analyze_pattern_discovery()
                
                # Check strategy performance
                self._evaluate_strategies()
                
                # Check for adaptations needed
                self._check_adaptation_triggers()
                
                # Sleep
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval * 2)
                
    def track_evolution_progress(self, metrics: Dict[str, Any]) -> str:
        """
        Track evolution progress metrics
        
        Args:
            metrics: Current metrics dictionary
            
        Returns:
            Metric ID
        """
        # Create evolution metric
        evolution_metric = EvolutionMetric(
            timestamp=datetime.now(),
            generation=self.current_generation,
            fitness_score=metrics.get('fitness_score', 0.5),
            win_rate=metrics.get('win_rate', 0.0),
            avg_confidence=metrics.get('avg_confidence', 0.5),
            consciousness_level=metrics.get('consciousness_level', 0.5),
            learning_rate=metrics.get('learning_rate', 0.001),
            total_trades=metrics.get('total_trades', 0),
            successful_trades=metrics.get('successful_trades', 0),
            failed_trades=metrics.get('failed_trades', 0),
            patterns_discovered=len(self.discovered_patterns),
            strategy_effectiveness=self.strategy_performance.copy()
        )
        
        # Add to history
        self.evolution_history.append(evolution_metric)
        self.metrics_buffer.append(metrics)
        
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            try:
                doc = asdict(evolution_metric)
                doc['_id'] = f"em_{self.current_generation}_{datetime.now().timestamp()}"
                self.persistence.db.evolution_metrics.insert_one(doc)
                return doc['_id']
            except Exception as e:
                print(f"Error saving evolution metric: {e}")
                
        return ""
        
    def discover_pattern(self, pattern_type: str, pattern_data: Dict[str, Any], 
                        confidence: float = 0.5) -> str:
        """
        Record a newly discovered trading pattern
        
        Args:
            pattern_type: Type of pattern
            pattern_data: Pattern characteristics
            confidence: Discovery confidence
            
        Returns:
            Pattern ID
        """
        import hashlib
        
        # Generate pattern ID
        pattern_str = f"{pattern_type}:{json.dumps(pattern_data, sort_keys=True)}"
        pattern_id = hashlib.md5(pattern_str.encode()).hexdigest()
        
        # Check if pattern exists
        if pattern_id in self.discovered_patterns:
            # Update existing pattern
            pattern = self.discovered_patterns[pattern_id]
            pattern.occurrences += 1
            pattern.last_seen = datetime.now()
            pattern.confidence = (pattern.confidence + confidence) / 2
        else:
            # Create new pattern
            pattern = DiscoveredPattern(
                pattern_id=pattern_id,
                discovered_at=datetime.now(),
                pattern_type=pattern_type,
                confidence=confidence,
                occurrences=1,
                success_rate=0.0,
                last_seen=datetime.now(),
                market_conditions=pattern_data
            )
            self.discovered_patterns[pattern_id] = pattern
            
            print(f"🔍 New pattern discovered: {pattern_type} (confidence: {confidence:.2%})")
            
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            try:
                doc = asdict(pattern)
                self.persistence.db.discovered_patterns.update_one(
                    {'_id': pattern_id},
                    {'$set': doc},
                    upsert=True
                )
            except Exception as e:
                print(f"Error saving pattern: {e}")
                
        return pattern_id
        
    def update_pattern_performance(self, pattern_id: str, success: bool):
        """
        Update pattern performance metrics
        
        Args:
            pattern_id: Pattern identifier
            success: Whether the pattern led to successful trade
        """
        if pattern_id not in self.discovered_patterns:
            return
            
        pattern = self.discovered_patterns[pattern_id]
        
        # Update success rate (exponential moving average)
        alpha = 0.1  # Smoothing factor
        current_success = 1.0 if success else 0.0
        pattern.success_rate = alpha * current_success + (1 - alpha) * pattern.success_rate
        
        # Update in MongoDB
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.discovered_patterns.update_one(
                    {'_id': pattern_id},
                    {'$set': {'success_rate': pattern.success_rate}}
                )
            except Exception as e:
                print(f"Error updating pattern performance: {e}")
                
    def track_strategy_performance(self, strategy_name: str, 
                                 effectiveness: float, trades: int):
        """
        Track strategy performance over time
        
        Args:
            strategy_name: Name of the strategy
            effectiveness: Current effectiveness score (0-1)
            trades: Number of trades executed
        """
        # Update strategy performance
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = {
                'effectiveness': effectiveness,
                'trades': trades,
                'first_seen': datetime.now(),
                'last_updated': datetime.now()
            }
        else:
            # Update with exponential moving average
            alpha = 0.2
            old_effectiveness = self.strategy_performance[strategy_name]['effectiveness']
            self.strategy_performance[strategy_name]['effectiveness'] = \
                alpha * effectiveness + (1 - alpha) * old_effectiveness
            self.strategy_performance[strategy_name]['trades'] += trades
            self.strategy_performance[strategy_name]['last_updated'] = datetime.now()
            
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            try:
                doc = {
                    'strategy_name': strategy_name,
                    'timestamp': datetime.now(),
                    'effectiveness': self.strategy_performance[strategy_name]['effectiveness'],
                    'total_trades': self.strategy_performance[strategy_name]['trades']
                }
                self.persistence.db.strategy_performance.insert_one(doc)
            except Exception as e:
                print(f"Error saving strategy performance: {e}")
                
    def record_adaptation(self, trigger: str, adaptation_type: str, 
                         details: Dict[str, Any]):
        """
        Record system adaptation event
        
        Args:
            trigger: What triggered the adaptation
            adaptation_type: Type of adaptation
            details: Adaptation details
        """
        adaptation = {
            'timestamp': datetime.now(),
            'trigger': trigger,
            'adaptation_type': adaptation_type,
            'details': details,
            'generation': self.current_generation
        }
        
        self.adaptation_history.append(adaptation)
        
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.adaptation_history.insert_one(adaptation)
                print(f"🔄 Adaptation recorded: {adaptation_type} triggered by {trigger}")
            except Exception as e:
                print(f"Error saving adaptation: {e}")
                
    def _collect_current_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        metrics = {
            'timestamp': datetime.now(),
            'generation': self.current_generation
        }
        
        # Get trading performance from MongoDB
        if self.persistence and self.persistence.db:
            try:
                # Get recent trading decisions
                recent_trades = list(self.persistence.db.trading_decisions.find(
                    {},
                    limit=self.analysis_window
                ).sort('timestamp', -1))
                
                if recent_trades:
                    # Calculate metrics
                    successful = sum(1 for t in recent_trades if t.get('outcome', 0) > 0)
                    total = len(recent_trades)
                    
                    metrics['win_rate'] = successful / total if total > 0 else 0
                    metrics['total_trades'] = total
                    metrics['successful_trades'] = successful
                    metrics['failed_trades'] = total - successful
                    
                    # Average confidence
                    confidences = [t.get('confidence', 0.5) for t in recent_trades]
                    metrics['avg_confidence'] = statistics.mean(confidences) if confidences else 0.5
                    
                # Get quantum brain state
                quantum_state = self.persistence.db.quantum_states.find_one(
                    {},
                    sort=[('timestamp', -1)]
                )
                if quantum_state:
                    metrics['consciousness_level'] = quantum_state.get('consciousness_level', 0.5)
                    metrics['fitness_score'] = quantum_state.get('fitness_score', 0.5)
                    
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                
        return metrics
        
    def _analyze_pattern_discovery(self):
        """Analyze and validate discovered patterns"""
        # Remove old patterns with low success rate
        patterns_to_remove = []
        for pattern_id, pattern in self.discovered_patterns.items():
            # Remove if not seen in 7 days and low success rate
            days_since = (datetime.now() - pattern.last_seen).days
            if days_since > 7 and pattern.success_rate < 0.3:
                patterns_to_remove.append(pattern_id)
                
        for pattern_id in patterns_to_remove:
            del self.discovered_patterns[pattern_id]
            print(f"🗑️ Removed ineffective pattern: {pattern_id[:8]}...")
            
    def _evaluate_strategies(self):
        """Evaluate strategy effectiveness"""
        # Calculate relative performance
        if not self.strategy_performance:
            return
            
        total_effectiveness = sum(
            s['effectiveness'] for s in self.strategy_performance.values()
        )
        
        if total_effectiveness > 0:
            for strategy_name in self.strategy_performance:
                relative_effectiveness = \
                    self.strategy_performance[strategy_name]['effectiveness'] / total_effectiveness
                    
                # Alert if strategy is underperforming
                if relative_effectiveness < 0.1:  # Less than 10% relative effectiveness
                    print(f"⚠️ Strategy '{strategy_name}' underperforming: {relative_effectiveness:.1%}")
                    
    def _check_adaptation_triggers(self):
        """Check if system needs to adapt"""
        if len(self.metrics_buffer) < 10:
            return
            
        recent_metrics = list(self.metrics_buffer)[-10:]
        
        # Check for declining performance
        win_rates = [m.get('win_rate', 0.5) for m in recent_metrics]
        if win_rates:
            trend = win_rates[-1] - win_rates[0]
            if trend < -0.1:  # 10% decline
                self.record_adaptation(
                    'performance_decline',
                    'learning_rate_adjustment',
                    {'old_win_rate': win_rates[0], 'new_win_rate': win_rates[-1]}
                )
                
        # Check for stagnant learning
        confidences = [m.get('avg_confidence', 0.5) for m in recent_metrics]
        if confidences:
            variance = statistics.variance(confidences) if len(confidences) > 1 else 0
            if variance < 0.001:  # Very low variance
                self.record_adaptation(
                    'learning_stagnation',
                    'exploration_increase',
                    {'confidence_variance': variance}
                )
                
    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get comprehensive evolution summary"""
        summary = {
            'current_generation': self.current_generation,
            'total_patterns_discovered': len(self.discovered_patterns),
            'active_strategies': len(self.strategy_performance),
            'total_adaptations': len(self.adaptation_history),
            'evolution_metrics': []
        }
        
        # Add recent evolution metrics
        for metric in list(self.evolution_history)[-10:]:
            summary['evolution_metrics'].append({
                'generation': metric.generation,
                'fitness': metric.fitness_score,
                'win_rate': metric.win_rate,
                'timestamp': metric.timestamp.isoformat()
            })
            
        # Add top patterns
        top_patterns = sorted(
            self.discovered_patterns.values(),
            key=lambda p: p.success_rate,
            reverse=True
        )[:5]
        
        summary['top_patterns'] = [
            {
                'type': p.pattern_type,
                'success_rate': p.success_rate,
                'occurrences': p.occurrences
            }
            for p in top_patterns
        ]
        
        # Add strategy rankings
        summary['strategy_rankings'] = sorted(
            [
                {
                    'name': name,
                    'effectiveness': data['effectiveness'],
                    'trades': data['trades']
                }
                for name, data in self.strategy_performance.items()
            ],
            key=lambda s: s['effectiveness'],
            reverse=True
        )
        
        return summary
        
    def advance_generation(self):
        """Advance to next evolution generation"""
        self.current_generation += 1
        print(f"📈 Advanced to Generation {self.current_generation}")
        
        # Record generation advancement
        self.record_adaptation(
            'generation_advance',
            'evolution_progress',
            {'new_generation': self.current_generation}
        )
        
    def trigger_evolution_cycle(self):
        """
        Manually trigger an evolution cycle
        """
        print(f"🧬 Manual evolution cycle triggered (Generation {self.current_generation})")
        
        # Simple evolution simulation
        self.current_generation += 1
        
        # Update metrics
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.evolution_metrics.insert_one({
                    'generation': self.current_generation,
                    'triggered_manually': True,
                    'timestamp': datetime.now()
                })
            except:
                pass
                
        return self.current_generation
        
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down Evolution Monitor...")
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        print("✅ Evolution Monitor shutdown complete")

# Global instance
_evolution_monitor = None

def get_evolution_monitor():
    """Get or create evolution monitor"""
    global _evolution_monitor
    if _evolution_monitor is None:
        _evolution_monitor = EvolutionMonitor()
    return _evolution_monitor

# Helper functions
def track_evolution(metrics: Dict[str, Any]):
    """Track evolution progress"""
    monitor = get_evolution_monitor()
    return monitor.track_evolution_progress(metrics)

def discover_pattern(pattern_type: str, pattern_data: Dict, confidence: float = 0.5):
    """Record discovered pattern"""
    monitor = get_evolution_monitor()
    return monitor.discover_pattern(pattern_type, pattern_data, confidence)

def track_strategy(strategy_name: str, effectiveness: float, trades: int = 1):
    """Track strategy performance"""
    monitor = get_evolution_monitor()
    monitor.track_strategy_performance(strategy_name, effectiveness, trades)

def get_evolution_status():
    """Get current evolution status"""
    monitor = get_evolution_monitor()
    return monitor.get_evolution_summary()