"""
Trading Decision Logger with Complete Market Analysis
Professor/Engineer's Note: Records EVERY trading decision with full context
WITHOUT modifying existing code - Task 8/12
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
import hashlib
import uuid

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import get_persistence_service
from brain.learning_feedback import get_learning_feedback
from brain.evolution_monitor import get_evolution_monitor

class TradingDecisionLogger:
    """
    Comprehensive trading decision logging system
    Records every signal, execution, and outcome with full context
    """
    
    def __init__(self):
        """Initialize trading decision logger"""
        # MongoDB persistence
        self.persistence = get_persistence_service()
        self.learning_feedback = get_learning_feedback()
        self.evolution_monitor = get_evolution_monitor()
        
        # Decision tracking
        self.active_decisions = {}  # Decisions awaiting outcomes
        self.decision_history = deque(maxlen=10000)
        self.decision_correlations = {}
        
        # Neural network tracking
        self.neural_activations = {}
        self.activation_patterns = deque(maxlen=1000)
        
        # Performance tracking
        self.decision_stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'pending': 0,
            'avg_confidence': 0,
            'total_pnl': 0
        }
        
        # Risk tracking
        self.risk_assessments = {}
        self.risk_violations = []
        
        # Market condition snapshots
        self.market_snapshots = {}
        
        # Correlation with memory states
        self.memory_correlations = {}
        
        # Background processing
        self.processing_thread = None
        self.running = True
        
        # Initialize MongoDB collections
        self._init_collections()
        
        print("📝 Trading Decision Logger Initialized")
        self._start_processing()
        
    def _init_collections(self):
        """Initialize MongoDB collections for decision logging"""
        if self.persistence is None or self.persistence.db is None:
            return
            
        db = self.persistence.db
        
        # Create indexes for efficient queries
        try:
            # Trading decisions collection
            db.trading_decisions.create_index([('timestamp', -1)])
            db.trading_decisions.create_index([('symbol', 1)])
            db.trading_decisions.create_index([('confidence', -1)])
            db.trading_decisions.create_index([('outcome', -1)])
            db.trading_decisions.create_index([('decision_id', 1)])
            
            # Neural activations collection
            db.neural_activations.create_index([('decision_id', 1)])
            db.neural_activations.create_index([('timestamp', -1)])
            
            # Risk assessments collection
            db.risk_assessments.create_index([('decision_id', 1)])
            db.risk_assessments.create_index([('risk_score', -1)])
            
            # Market snapshots collection
            db.market_snapshots.create_index([('decision_id', 1)])
            db.market_snapshots.create_index([('timestamp', -1)])
            
            print("📊 Decision logging collections initialized")
            
        except Exception as e:
            print(f"Error initializing collections: {e}")
            
    def _start_processing(self):
        """Start background processing thread"""
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()
        print("🔄 Decision processing started")
        
    def _processing_loop(self):
        """Background processing loop"""
        while self.running:
            try:
                # Process pending decisions
                self._process_pending_decisions()
                
                # Analyze patterns
                self._analyze_activation_patterns()
                
                # Update correlations
                self._update_correlations()
                
                # Calculate statistics
                self._update_statistics()
                
                time.sleep(30)  # Process every 30 seconds
                
            except Exception as e:
                print(f"Error in processing loop: {e}")
                time.sleep(60)
                
    def log_trading_signal(self, symbol: str, signal_type: str, 
                          signal_strength: float, 
                          source: str = "unknown") -> str:
        """
        Log initial trading signal
        
        Args:
            symbol: Trading symbol
            signal_type: Type of signal (buy/sell/hold)
            signal_strength: Signal strength (0-1)
            source: Signal source (strategy name, etc.)
            
        Returns:
            Signal ID
        """
        signal_id = str(uuid.uuid4())
        
        signal_data = {
            'signal_id': signal_id,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'signal_type': signal_type,
            'signal_strength': signal_strength,
            'source': source,
            'status': 'received'
        }
        
        # Store in MongoDB
        if self.persistence is not None and self.persistence.db is not None:
            try:
                self.persistence.db.trading_signals.insert_one(signal_data)
            except Exception as e:
                print(f"Error logging signal: {e}")
                
        return signal_id
        
    def log_trading_decision(self, symbol: str, action: str, 
                           quantity: float, price: float,
                           confidence: float, 
                           market_conditions: Dict[str, Any],
                           neural_state: Optional[Dict] = None,
                           signal_id: Optional[str] = None) -> str:
        """
        Log complete trading decision with all context
        
        Args:
            symbol: Trading symbol
            action: Trading action (buy/sell/hold)
            quantity: Trade quantity
            price: Trade price
            confidence: Decision confidence (0-1)
            market_conditions: Current market conditions
            neural_state: Optional neural network state
            signal_id: Optional originating signal ID
            
        Returns:
            Decision ID
        """
        decision_id = str(uuid.uuid4())
        
        # Capture market snapshot
        market_snapshot = self._capture_market_snapshot(symbol, market_conditions)
        
        # Capture neural activations if available
        neural_activations = self._capture_neural_activations(neural_state)
        
        # Perform risk assessment
        risk_assessment = self._assess_risk(symbol, action, quantity, price, market_conditions)
        
        # Create decision record
        decision = {
            'decision_id': decision_id,
            'signal_id': signal_id,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'confidence': confidence,
            'market_conditions': market_conditions,
            'market_snapshot_id': market_snapshot['snapshot_id'],
            'neural_activation_id': neural_activations.get('activation_id'),
            'risk_assessment_id': risk_assessment['assessment_id'],
            'risk_score': risk_assessment['risk_score'],
            'status': 'pending',
            'outcome': None,
            'actual_price': None,
            'pnl': None
        }
        
        # Track active decision
        self.active_decisions[decision_id] = decision
        self.decision_history.append(decision_id)
        
        # Store in MongoDB
        if self.persistence is not None and self.persistence.db is not None:
            try:
                # Store decision
                self.persistence.db.trading_decisions.insert_one(decision)
                
                # Store related data
                self.persistence.db.market_snapshots.insert_one(market_snapshot)
                
                if neural_activations:
                    self.persistence.db.neural_activations.insert_one(neural_activations)
                    
                self.persistence.db.risk_assessments.insert_one(risk_assessment)
                
                print(f"📝 Decision logged: {symbol} {action} (confidence: {confidence:.2%})")
                
            except Exception as e:
                print(f"Error logging decision: {e}")
                
        # Update stats
        self.decision_stats['total'] += 1
        self.decision_stats['pending'] += 1
        
        # Notify learning system
        if self.learning_feedback:
            self.learning_feedback.analyze_trade_outcome(
                decision_id, 0, market_conditions  # Initial with no outcome yet
            )
            
        return decision_id
        
    def log_execution(self, decision_id: str, execution_price: float,
                     execution_time: datetime, slippage: float = 0):
        """
        Log trade execution details
        
        Args:
            decision_id: Decision ID
            execution_price: Actual execution price
            execution_time: Execution timestamp
            slippage: Price slippage
        """
        if decision_id not in self.active_decisions:
            print(f"Warning: Unknown decision ID: {decision_id}")
            return
            
        # Update decision
        self.active_decisions[decision_id]['actual_price'] = execution_price
        self.active_decisions[decision_id]['execution_time'] = execution_time
        self.active_decisions[decision_id]['slippage'] = slippage
        self.active_decisions[decision_id]['status'] = 'executed'
        
        # Update in MongoDB
        if self.persistence is not None and self.persistence.db is not None:
            try:
                self.persistence.db.trading_decisions.update_one(
                    {'decision_id': decision_id},
                    {'$set': {
                        'actual_price': execution_price,
                        'execution_time': execution_time,
                        'slippage': slippage,
                        'status': 'executed'
                    }}
                )
            except Exception as e:
                print(f"Error updating execution: {e}")
                
    def log_outcome(self, decision_id: str, outcome: float, 
                   exit_price: float, exit_time: datetime):
        """
        Log trade outcome
        
        Args:
            decision_id: Decision ID
            outcome: Trade outcome (profit/loss)
            exit_price: Exit price
            exit_time: Exit timestamp
        """
        if decision_id not in self.active_decisions:
            print(f"Warning: Unknown decision ID: {decision_id}")
            return
            
        decision = self.active_decisions[decision_id]
        
        # Calculate P&L
        if decision['action'] == 'buy':
            pnl = (exit_price - decision['actual_price']) * decision['quantity']
        else:  # sell
            pnl = (decision['actual_price'] - exit_price) * decision['quantity']
            
        # Update decision
        decision['outcome'] = outcome
        decision['exit_price'] = exit_price
        decision['exit_time'] = exit_time
        decision['pnl'] = pnl
        decision['status'] = 'completed'
        
        # Update stats
        self.decision_stats['pending'] -= 1
        if pnl > 0:
            self.decision_stats['successful'] += 1
        else:
            self.decision_stats['failed'] += 1
        self.decision_stats['total_pnl'] += pnl
        
        # Update in MongoDB
        if self.persistence is not None and self.persistence.db is not None:
            try:
                self.persistence.db.trading_decisions.update_one(
                    {'decision_id': decision_id},
                    {'$set': {
                        'outcome': outcome,
                        'exit_price': exit_price,
                        'exit_time': exit_time,
                        'pnl': pnl,
                        'status': 'completed'
                    }}
                )
            except Exception as e:
                print(f"Error updating outcome: {e}")
                
        # Notify learning system
        if self.learning_feedback:
            market_conditions = decision.get('market_conditions', {})
            market_conditions['outcome'] = outcome
            self.learning_feedback.analyze_trade_outcome(
                decision_id, outcome, market_conditions
            )
            
        # Update evolution monitor
        if self.evolution_monitor:
            if pnl > 0:
                self.evolution_monitor.update_pattern_performance(
                    decision.get('signal_id', ''), True
                )
                
        # Remove from active decisions
        del self.active_decisions[decision_id]
        
        print(f"💰 Outcome logged: {decision['symbol']} P&L: ${pnl:.2f}")
        
    def _capture_market_snapshot(self, symbol: str, 
                                conditions: Dict) -> Dict[str, Any]:
        """Capture complete market snapshot"""
        snapshot_id = str(uuid.uuid4())
        
        snapshot = {
            'snapshot_id': snapshot_id,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'price': conditions.get('price'),
            'volume': conditions.get('volume'),
            'bid': conditions.get('bid'),
            'ask': conditions.get('ask'),
            'spread': conditions.get('spread'),
            'rsi': conditions.get('rsi'),
            'macd': conditions.get('macd'),
            'bollinger': conditions.get('bollinger'),
            'vwap': conditions.get('vwap'),
            'market_cap': conditions.get('market_cap'),
            'pe_ratio': conditions.get('pe_ratio'),
            'volatility': conditions.get('volatility'),
            'trend': conditions.get('trend'),
            'sentiment': conditions.get('sentiment'),
            'news_count': conditions.get('news_count', 0),
            'social_mentions': conditions.get('social_mentions', 0)
        }
        
        self.market_snapshots[snapshot_id] = snapshot
        return snapshot
        
    def _capture_neural_activations(self, neural_state: Optional[Dict]) -> Dict:
        """Capture neural network activation patterns"""
        if not neural_state:
            return {}
            
        activation_id = str(uuid.uuid4())
        
        activations = {
            'activation_id': activation_id,
            'timestamp': datetime.now(),
            'layers': neural_state.get('layers', {}),
            'weights': neural_state.get('weights', {}),
            'attention_scores': neural_state.get('attention', {}),
            'confidence_distribution': neural_state.get('confidence_dist', {}),
            'feature_importance': neural_state.get('feature_importance', {}),
            'pattern_matches': neural_state.get('patterns', []),
            'consciousness_level': neural_state.get('consciousness', 0.5),
            'learning_rate': neural_state.get('learning_rate', 0.001)
        }
        
        self.neural_activations[activation_id] = activations
        self.activation_patterns.append(activation_id)
        
        return activations
        
    def _assess_risk(self, symbol: str, action: str, 
                    quantity: float, price: float,
                    market_conditions: Dict) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        assessment_id = str(uuid.uuid4())
        
        # Calculate various risk metrics
        position_value = quantity * price
        volatility = market_conditions.get('volatility', 0.02)
        
        # Value at Risk (VaR)
        var_95 = position_value * volatility * 1.65  # 95% confidence
        
        # Maximum probable loss
        max_loss = position_value * 0.1  # 10% stop loss assumption
        
        # Liquidity risk
        volume = market_conditions.get('volume', 1000000)
        liquidity_risk = min(1.0, quantity / (volume * 0.01))  # 1% of volume
        
        # Overall risk score (0-1)
        risk_score = (
            (var_95 / position_value) * 0.3 +
            liquidity_risk * 0.3 +
            volatility * 0.4
        )
        
        assessment = {
            'assessment_id': assessment_id,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'action': action,
            'position_value': position_value,
            'risk_score': min(1.0, risk_score),
            'var_95': var_95,
            'max_loss': max_loss,
            'volatility': volatility,
            'liquidity_risk': liquidity_risk,
            'market_phase': market_conditions.get('market_phase', 'normal'),
            'risk_factors': self._identify_risk_factors(market_conditions)
        }
        
        self.risk_assessments[assessment_id] = assessment
        
        # Check for risk violations
        if risk_score > 0.7:
            self.risk_violations.append({
                'timestamp': datetime.now(),
                'assessment_id': assessment_id,
                'risk_score': risk_score,
                'reason': 'High risk score'
            })
            print(f"⚠️ High risk detected: {risk_score:.2%}")
            
        return assessment
        
    def _identify_risk_factors(self, market_conditions: Dict) -> List[str]:
        """Identify active risk factors"""
        risk_factors = []
        
        # Check various risk conditions
        if market_conditions.get('volatility', 0) > 0.05:
            risk_factors.append('high_volatility')
            
        if market_conditions.get('volume', 0) < 100000:
            risk_factors.append('low_liquidity')
            
        if market_conditions.get('trend') == 'strong_down':
            risk_factors.append('downtrend')
            
        if market_conditions.get('news_count', 0) > 10:
            risk_factors.append('high_news_activity')
            
        if market_conditions.get('sentiment', 0) < -0.5:
            risk_factors.append('negative_sentiment')
            
        return risk_factors
        
    def _process_pending_decisions(self):
        """Process pending decisions"""
        # Check for stale decisions
        current_time = datetime.now()
        
        for decision_id, decision in list(self.active_decisions.items()):
            if decision['status'] == 'pending':
                # Check if decision is too old (>1 hour)
                if (current_time - decision['timestamp']).seconds > 3600:
                    decision['status'] = 'expired'
                    self.decision_stats['pending'] -= 1
                    
                    # Update in MongoDB
                    if self.persistence is not None and self.persistence.db is not None:
                        try:
                            self.persistence.db.trading_decisions.update_one(
                                {'decision_id': decision_id},
                                {'$set': {'status': 'expired'}}
                            )
                        except:
                            pass
                            
    def _analyze_activation_patterns(self):
        """Analyze neural activation patterns"""
        if len(self.activation_patterns) < 10:
            return
            
        # Analyze recent patterns for anomalies or trends
        recent_patterns = list(self.activation_patterns)[-10:]
        
        # This would contain sophisticated pattern analysis
        # For now, basic tracking
        pattern_summary = {
            'timestamp': datetime.now(),
            'pattern_count': len(recent_patterns),
            'unique_patterns': len(set(recent_patterns))
        }
        
        # Store analysis
        if self.persistence is not None and self.persistence.db is not None:
            try:
                self.persistence.db.activation_analysis.insert_one(pattern_summary)
            except:
                pass
                
    def _update_correlations(self):
        """Update decision correlations with memory states"""
        # Correlate decisions with memory states
        for decision_id in list(self.decision_history)[-10:]:
            if decision_id in self.active_decisions:
                decision = self.active_decisions[decision_id]
                
                # Get memory state at decision time
                # This would query memory manager for state
                memory_state = {
                    'timestamp': decision['timestamp'],
                    'memory_hash': hashlib.md5(
                        json.dumps(decision, sort_keys=True, default=str).encode()
                    ).hexdigest()
                }
                
                self.memory_correlations[decision_id] = memory_state
                
    def _update_statistics(self):
        """Update decision statistics"""
        if self.decision_stats['total'] > 0:
            # Calculate average confidence
            total_confidence = sum(
                d.get('confidence', 0) 
                for d in self.active_decisions.values()
            )
            active_count = len(self.active_decisions)
            
            if active_count > 0:
                self.decision_stats['avg_confidence'] = total_confidence / active_count
                
            # Calculate success rate
            completed = self.decision_stats['successful'] + self.decision_stats['failed']
            if completed > 0:
                success_rate = self.decision_stats['successful'] / completed
                
                # Store metrics
                if self.persistence is not None and self.persistence.db is not None:
                    try:
                        metrics = {
                            'timestamp': datetime.now(),
                            'total_decisions': self.decision_stats['total'],
                            'success_rate': success_rate,
                            'avg_confidence': self.decision_stats['avg_confidence'],
                            'total_pnl': self.decision_stats['total_pnl'],
                            'pending': self.decision_stats['pending']
                        }
                        self.persistence.db.decision_metrics.insert_one(metrics)
                    except:
                        pass
                        
    def get_decision_history(self, symbol: Optional[str] = None,
                            days: int = 7) -> List[Dict]:
        """
        Get decision history
        
        Args:
            symbol: Optional symbol filter
            days: Number of days to look back
            
        Returns:
            List of decisions
        """
        if self.persistence is None or self.persistence.db is None:
            return []
            
        try:
            query = {'timestamp': {'$gte': datetime.now() - timedelta(days=days)}}
            if symbol:
                query['symbol'] = symbol
                
            decisions = list(self.persistence.db.trading_decisions.find(
                query
            ).sort('timestamp', -1))
            
            return decisions
            
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get current decision statistics"""
        stats = self.decision_stats.copy()
        
        # Add risk statistics
        stats['risk_violations'] = len(self.risk_violations)
        
        # Add recent performance
        recent_decisions = self.get_decision_history(days=1)
        if recent_decisions:
            recent_wins = sum(1 for d in recent_decisions if d.get('pnl', 0) > 0)
            stats['today_success_rate'] = recent_wins / len(recent_decisions)
            
        return stats
        
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down Decision Logger...")
        self.running = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
            
        # Final statistics
        print(f"📊 Final Stats: {self.decision_stats['total']} decisions logged")
        print("✅ Decision Logger shutdown complete")


# Global instance
_decision_logger = None

def get_decision_logger():
    """Get or create decision logger"""
    global _decision_logger
    if _decision_logger is None:
        _decision_logger = TradingDecisionLogger()
    return _decision_logger

# Helper functions for easy integration
def log_signal(symbol: str, signal_type: str, strength: float, source: str = "unknown"):
    """Log trading signal"""
    logger = get_decision_logger()
    return logger.log_trading_signal(symbol, signal_type, strength, source)

def log_decision(symbol: str, action: str, quantity: float, price: float,
                confidence: float, market_conditions: Dict, **kwargs):
    """Log trading decision"""
    logger = get_decision_logger()
    return logger.log_trading_decision(
        symbol, action, quantity, price, confidence, market_conditions, **kwargs
    )

def log_execution(decision_id: str, execution_price: float):
    """Log trade execution"""
    logger = get_decision_logger()
    logger.log_execution(decision_id, execution_price, datetime.now())

def log_outcome(decision_id: str, outcome: float, exit_price: float):
    """Log trade outcome"""
    logger = get_decision_logger()
    logger.log_outcome(decision_id, outcome, exit_price, datetime.now())

def get_decision_stats():
    """Get decision statistics"""
    logger = get_decision_logger()
    return logger.get_statistics()
