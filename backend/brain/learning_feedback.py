"""
Learning Feedback Loop for AuraQuant Trading System
Professor/Engineer's Note: This implements reinforcement learning and self-improvement
WITHOUT modifying existing code - Task 6/12
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
import statistics
import math

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import get_persistence_service
from brain.evolution_monitor import get_evolution_monitor

class LearningFeedback:
    """
    Implements reinforcement learning feedback loop
    Analyzes performance and adjusts system parameters
    """
    
    def __init__(self):
        """Initialize learning feedback system"""
        # MongoDB persistence
        self.persistence = get_persistence_service()
        self.evolution_monitor = get_evolution_monitor()
        
        # Learning parameters
        self.base_learning_rate = 0.001
        self.current_learning_rate = self.base_learning_rate
        self.exploration_rate = 0.1
        self.discount_factor = 0.95
        
        # Performance tracking
        self.performance_window = deque(maxlen=100)
        self.reward_history = deque(maxlen=1000)
        self.q_table = {}  # State-action value table
        
        # Pattern analysis
        self.success_patterns = {}
        self.failure_patterns = {}
        
        # Consciousness adjustment
        self.consciousness_baseline = 0.5
        self.consciousness_adjustment_rate = 0.01
        
        # Self-evaluation settings
        self.evaluation_interval = 3600  # Hourly evaluation
        self.last_evaluation = datetime.now()
        
        # Strategy evolution
        self.strategy_weights = {
            'momentum': 0.25,
            'mean_reversion': 0.25,
            'breakout': 0.25,
            'volume_analysis': 0.25
        }
        
        # Background thread
        self.feedback_thread = None
        self.running = True
        
        print("🔄 Learning Feedback Loop Initialized")
        self._start_feedback_loop()
        
    def _start_feedback_loop(self):
        """Start background feedback processing"""
        self.feedback_thread = threading.Thread(
            target=self._feedback_loop,
            daemon=True
        )
        self.feedback_thread.start()
        print("📊 Feedback loop started")
        
    def _feedback_loop(self):
        """Main feedback processing loop"""
        while self.running:
            try:
                # Check if evaluation is needed
                if (datetime.now() - self.last_evaluation).seconds > self.evaluation_interval:
                    self.perform_self_evaluation()
                    self.last_evaluation = datetime.now()
                    
                # Process recent performance
                self._analyze_recent_performance()
                
                # Update learning parameters
                self._adjust_learning_parameters()
                
                # Evolve strategies
                self._evolve_strategies()
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in feedback loop: {e}")
                time.sleep(120)
                
    def analyze_trade_outcome(self, decision_id: str, outcome: float, 
                            market_conditions: Dict[str, Any]):
        """
        Analyze trade outcome and update learning
        
        Args:
            decision_id: Trading decision ID
            outcome: Trade outcome (profit/loss)
            market_conditions: Market state during trade
        """
        # Calculate reward
        reward = self._calculate_reward(outcome)
        self.reward_history.append(reward)
        
        # Update Q-table
        state = self._encode_state(market_conditions)
        action = market_conditions.get('action', 'hold')
        self._update_q_value(state, action, reward)
        
        # Analyze pattern success/failure
        if outcome > 0:
            self._record_success_pattern(market_conditions)
        else:
            self._record_failure_pattern(market_conditions)
            
        # Store feedback in MongoDB
        if self.persistence and self.persistence.db:
            try:
                feedback_doc = {
                    'timestamp': datetime.now(),
                    'decision_id': decision_id,
                    'outcome': outcome,
                    'reward': reward,
                    'state': state,
                    'action': action,
                    'learning_rate': self.current_learning_rate
                }
                self.persistence.db.learning_feedback.insert_one(feedback_doc)
            except Exception as e:
                print(f"Error saving feedback: {e}")
                
    def _calculate_reward(self, outcome: float) -> float:
        """
        Calculate reinforcement learning reward
        
        Args:
            outcome: Trade outcome
            
        Returns:
            Calculated reward
        """
        # Basic reward is the outcome
        reward = outcome
        
        # Add risk-adjusted component
        if len(self.reward_history) > 10:
            recent_volatility = statistics.stdev(list(self.reward_history)[-10:])
            if recent_volatility > 0:
                sharpe_component = outcome / recent_volatility
                reward += sharpe_component * 0.1
                
        # Penalize large losses more
        if outcome < -0.02:  # More than 2% loss
            reward *= 1.5  # Increase negative reward
            
        return reward
        
    def _encode_state(self, market_conditions: Dict) -> str:
        """
        Encode market conditions into state representation
        
        Args:
            market_conditions: Market data
            
        Returns:
            Encoded state string
        """
        # Extract key features
        features = {
            'rsi': self._discretize(market_conditions.get('rsi', 50), [30, 50, 70]),
            'volume': self._discretize(market_conditions.get('volume', 1000000), 
                                      [500000, 1000000, 2000000]),
            'price_trend': market_conditions.get('trend', 'neutral'),
            'volatility': self._discretize(market_conditions.get('volatility', 0.02),
                                         [0.01, 0.02, 0.05])
        }
        
        # Create state string
        state = json.dumps(features, sort_keys=True)
        return state
        
    def _discretize(self, value: float, bins: List[float]) -> str:
        """Discretize continuous value into categories"""
        for i, threshold in enumerate(bins):
            if value < threshold:
                return f"bin_{i}"
        return f"bin_{len(bins)}"
        
    def _update_q_value(self, state: str, action: str, reward: float):
        """
        Update Q-value using Q-learning algorithm
        
        Args:
            state: Current state
            action: Action taken
            reward: Received reward
        """
        # Initialize Q-value if not exists
        if state not in self.q_table:
            self.q_table[state] = {}
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0.0
            
        # Q-learning update
        old_q = self.q_table[state][action]
        
        # Find max Q-value for next state (simplified - using average)
        max_next_q = 0
        if len(self.q_table) > 0:
            all_q_values = []
            for s in self.q_table.values():
                all_q_values.extend(s.values())
            if all_q_values:
                max_next_q = max(all_q_values)
                
        # Update Q-value
        new_q = old_q + self.current_learning_rate * (
            reward + self.discount_factor * max_next_q - old_q
        )
        self.q_table[state][action] = new_q
        
    def get_best_action(self, market_conditions: Dict) -> Tuple[str, float]:
        """
        Get best action based on Q-learning
        
        Args:
            market_conditions: Current market state
            
        Returns:
            Tuple of (action, confidence)
        """
        state = self._encode_state(market_conditions)
        
        # Exploration vs exploitation
        import random
        if random.random() < self.exploration_rate:
            # Explore: random action
            actions = ['buy', 'sell', 'hold']
            return random.choice(actions), self.exploration_rate
            
        # Exploit: best known action
        if state in self.q_table:
            action_values = self.q_table[state]
            if action_values:
                best_action = max(action_values, key=action_values.get)
                confidence = self._sigmoid(action_values[best_action])
                return best_action, confidence
                
        # Default action
        return 'hold', 0.5
        
    def _sigmoid(self, x: float) -> float:
        """Sigmoid function for confidence mapping"""
        return 1 / (1 + math.exp(-x))
        
    def perform_self_evaluation(self):
        """Perform comprehensive self-evaluation"""
        print("🔍 Performing self-evaluation...")
        
        evaluation_results = {
            'timestamp': datetime.now(),
            'performance_score': 0,
            'learning_progress': 0,
            'adaptation_needed': False,
            'recommendations': []
        }
        
        # Analyze historical performance
        if self.persistence and self.persistence.db:
            try:
                # Get recent trades
                recent_trades = list(self.persistence.db.trading_decisions.find(
                    {'timestamp': {'$gte': datetime.now() - timedelta(days=7)}},
                    limit=100
                ).sort('timestamp', -1))
                
                if recent_trades:
                    # Calculate performance metrics
                    wins = sum(1 for t in recent_trades if t.get('outcome', 0) > 0)
                    total = len(recent_trades)
                    win_rate = wins / total if total > 0 else 0
                    
                    evaluation_results['performance_score'] = win_rate
                    
                    # Check if adaptation needed
                    if win_rate < 0.45:
                        evaluation_results['adaptation_needed'] = True
                        evaluation_results['recommendations'].append('Increase exploration rate')
                    elif win_rate > 0.65:
                        evaluation_results['recommendations'].append('Decrease exploration rate')
                        
                    # Calculate learning progress
                    if len(self.reward_history) > 50:
                        early_rewards = list(self.reward_history)[:25]
                        recent_rewards = list(self.reward_history)[-25:]
                        
                        early_avg = statistics.mean(early_rewards)
                        recent_avg = statistics.mean(recent_rewards)
                        
                        learning_progress = (recent_avg - early_avg) / abs(early_avg) if early_avg != 0 else 0
                        evaluation_results['learning_progress'] = learning_progress
                        
                    # Adjust consciousness based on performance
                    self._adjust_consciousness(win_rate)
                    
            except Exception as e:
                print(f"Error in self-evaluation: {e}")
                
        # Save evaluation results
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.self_evaluations.insert_one(evaluation_results)
            except:
                pass
                
        print(f"✅ Evaluation complete: Performance {evaluation_results['performance_score']:.2%}")
        
    def _adjust_consciousness(self, performance_score: float):
        """
        Adjust consciousness level based on performance
        
        Args:
            performance_score: Current performance (0-1)
        """
        # Calculate adjustment
        target_consciousness = 0.3 + (performance_score * 0.7)  # Range 0.3-1.0
        adjustment = (target_consciousness - self.consciousness_baseline) * self.consciousness_adjustment_rate
        
        # Apply adjustment
        self.consciousness_baseline += adjustment
        self.consciousness_baseline = max(0.3, min(1.0, self.consciousness_baseline))
        
        # Update in evolution monitor
        if self.evolution_monitor:
            metrics = {
                'consciousness_level': self.consciousness_baseline,
                'adjustment_reason': 'performance_based'
            }
            self.evolution_monitor.track_evolution_progress(metrics)
            
    def _record_success_pattern(self, market_conditions: Dict):
        """Record successful trading pattern"""
        pattern_key = self._extract_pattern_key(market_conditions)
        
        if pattern_key not in self.success_patterns:
            self.success_patterns[pattern_key] = {
                'count': 0,
                'total_profit': 0,
                'conditions': market_conditions
            }
            
        self.success_patterns[pattern_key]['count'] += 1
        self.success_patterns[pattern_key]['total_profit'] += market_conditions.get('outcome', 0)
        
    def _record_failure_pattern(self, market_conditions: Dict):
        """Record failed trading pattern"""
        pattern_key = self._extract_pattern_key(market_conditions)
        
        if pattern_key not in self.failure_patterns:
            self.failure_patterns[pattern_key] = {
                'count': 0,
                'total_loss': 0,
                'conditions': market_conditions
            }
            
        self.failure_patterns[pattern_key]['count'] += 1
        self.failure_patterns[pattern_key]['total_loss'] += abs(market_conditions.get('outcome', 0))
        
    def _extract_pattern_key(self, conditions: Dict) -> str:
        """Extract pattern key from market conditions"""
        key_features = {
            'rsi_range': self._discretize(conditions.get('rsi', 50), [30, 50, 70]),
            'volume_level': self._discretize(conditions.get('volume', 1000000), 
                                           [500000, 1000000, 2000000]),
            'trend': conditions.get('trend', 'neutral')
        }
        return json.dumps(key_features, sort_keys=True)
        
    def _analyze_recent_performance(self):
        """Analyze recent trading performance"""
        if len(self.reward_history) < 10:
            return
            
        recent_rewards = list(self.reward_history)[-10:]
        
        # Check for consistent losses
        if sum(recent_rewards) < -0.05:  # Cumulative loss > 5%
            print("⚠️ Consistent losses detected - increasing exploration")
            self.exploration_rate = min(0.3, self.exploration_rate * 1.2)
            
        # Check for consistent wins
        elif sum(recent_rewards) > 0.1:  # Cumulative gain > 10%
            print("✅ Good performance - decreasing exploration")
            self.exploration_rate = max(0.05, self.exploration_rate * 0.9)
            
    def _adjust_learning_parameters(self):
        """Dynamically adjust learning parameters"""
        if len(self.reward_history) < 50:
            return
            
        # Calculate reward volatility
        recent_rewards = list(self.reward_history)[-50:]
        volatility = statistics.stdev(recent_rewards) if len(recent_rewards) > 1 else 0
        
        # Adjust learning rate based on volatility
        if volatility > 0.05:  # High volatility
            self.current_learning_rate = max(0.0001, self.current_learning_rate * 0.95)
        elif volatility < 0.01:  # Low volatility
            self.current_learning_rate = min(0.01, self.current_learning_rate * 1.05)
            
    def _evolve_strategies(self):
        """Evolve strategy weights based on performance"""
        if not self.evolution_monitor:
            return
            
        # Get strategy performance from evolution monitor
        summary = self.evolution_monitor.get_evolution_summary()
        strategy_rankings = summary.get('strategy_rankings', [])
        
        if not strategy_rankings:
            return
            
        # Update weights based on effectiveness
        total_effectiveness = sum(s['effectiveness'] for s in strategy_rankings)
        
        if total_effectiveness > 0:
            for strategy in strategy_rankings:
                name = strategy['name']
                if name in self.strategy_weights:
                    # New weight proportional to effectiveness
                    new_weight = strategy['effectiveness'] / total_effectiveness
                    
                    # Smooth update
                    alpha = 0.1
                    self.strategy_weights[name] = (
                        alpha * new_weight + (1 - alpha) * self.strategy_weights[name]
                    )
                    
            # Normalize weights
            total_weight = sum(self.strategy_weights.values())
            if total_weight > 0:
                for name in self.strategy_weights:
                    self.strategy_weights[name] /= total_weight
                    
    def get_strategy_weights(self) -> Dict[str, float]:
        """Get current strategy weights"""
        return self.strategy_weights.copy()
        
    def get_learning_metrics(self) -> Dict[str, Any]:
        """Get current learning metrics"""
        metrics = {
            'learning_rate': self.current_learning_rate,
            'exploration_rate': self.exploration_rate,
            'consciousness_level': self.consciousness_baseline,
            'q_table_size': len(self.q_table),
            'reward_history_size': len(self.reward_history),
            'success_patterns': len(self.success_patterns),
            'failure_patterns': len(self.failure_patterns),
            'strategy_weights': self.strategy_weights.copy()
        }
        
        if self.reward_history:
            metrics['recent_avg_reward'] = statistics.mean(list(self.reward_history)[-10:])
            
        return metrics
        
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down Learning Feedback...")
        self.running = False
        if self.feedback_thread:
            self.feedback_thread.join(timeout=5)
        print("✅ Learning Feedback shutdown complete")

# Global instance
_learning_feedback = None

def get_learning_feedback():
    """Get or create learning feedback instance"""
    global _learning_feedback
    if _learning_feedback is None:
        _learning_feedback = LearningFeedback()
    return _learning_feedback

# Helper functions
def process_trade_outcome(decision_id: str, outcome: float, market_conditions: Dict):
    """Process trade outcome for learning"""
    feedback = get_learning_feedback()
    feedback.analyze_trade_outcome(decision_id, outcome, market_conditions)

def get_ai_recommendation(market_conditions: Dict) -> Tuple[str, float]:
    """Get AI recommendation based on learning"""
    feedback = get_learning_feedback()
    return feedback.get_best_action(market_conditions)

def trigger_self_evaluation():
    """Manually trigger self-evaluation"""
    feedback = get_learning_feedback()
    feedback.perform_self_evaluation()

def get_current_learning_metrics():
    """Get current learning metrics"""
    feedback = get_learning_feedback()
    return feedback.get_learning_metrics()