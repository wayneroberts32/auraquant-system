"""
Autonomous Trading Executor for AuraQuant Trading System
Professor/Engineer's Note: Fully autonomous execution with safety checks
WITHOUT modifying existing code - Task 11/12
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import asyncio
import threading
from enum import Enum
import hashlib
from collections import deque
# import numpy as np  # Optional - use random instead

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import get_persistence_service
from brain.evolution_monitor import get_evolution_monitor
from brain.learning_feedback import get_learning_feedback
from brain.decision_logger import get_decision_logger
from brain.performance_dashboard import get_performance_dashboard
from brain.state_recovery import get_state_recovery

class ExecutionMode(Enum):
    """Trading execution modes"""
    SIMULATION = "simulation"
    PAPER = "paper"
    LIVE = "live"
    HYBRID = "hybrid"  # Live with simulation fallback

class RiskLevel(Enum):
    """Risk assessment levels"""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5

class SafetyStatus(Enum):
    """System safety status"""
    GREEN = "green"    # All systems normal
    YELLOW = "yellow"  # Caution advised
    RED = "red"        # Stop trading
    EMERGENCY = "emergency"  # Emergency shutdown

class AutonomousTradingExecutor:
    """
    Fully autonomous trading with comprehensive safety mechanisms
    Executes trades based on AI decisions with risk management
    """
    
    def __init__(self, mode: ExecutionMode = ExecutionMode.SIMULATION):
        """
        Initialize autonomous trading executor
        
        Args:
            mode: Execution mode (simulation, paper, live, hybrid)
        """
        # Execution mode
        self.mode = mode
        self.previous_mode = None
        
        # MongoDB persistence
        self.persistence = get_persistence_service()
        
        # Component references
        self.evolution_monitor = get_evolution_monitor()
        self.learning_feedback = get_learning_feedback()
        self.decision_logger = get_decision_logger()
        self.dashboard = get_performance_dashboard()
        self.state_recovery = get_state_recovery()
        
        # Safety mechanisms
        self.safety_status = SafetyStatus.GREEN
        self.emergency_stop = False
        self.safety_checks = {
            'position_limits': True,
            'risk_limits': True,
            'drawdown_protection': True,
            'circuit_breaker': True,
            'anomaly_detection': True,
            'connectivity_check': True
        }
        
        # Risk management
        self.risk_parameters = {
            'max_position_size': 10000,  # Maximum per position
            'max_total_exposure': 50000,  # Maximum total exposure
            'max_daily_loss': 5000,       # Daily loss limit
            'max_drawdown': 0.20,         # 20% maximum drawdown
            'position_limit': 10,         # Max concurrent positions
            'risk_per_trade': 0.02,       # 2% risk per trade
            'leverage_limit': 2.0,        # Maximum leverage
            'correlation_limit': 0.7      # Max correlation between positions
        }
        
        # Execution state
        self.active_positions = {}
        self.pending_orders = {}
        self.execution_history = deque(maxlen=1000)
        self.daily_pnl = 0
        self.total_exposure = 0
        self.peak_balance = 100000  # Starting balance
        self.current_balance = 100000
        
        # Performance tracking
        self.execution_metrics = {
            'total_executed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'rejected_trades': 0,
            'slippage_total': 0,
            'execution_time_avg': 0,
            'win_rate': 0,
            'profit_factor': 0
        }
        
        # Autonomous control
        self.autonomous_enabled = False
        self.confidence_threshold = 0.7  # Minimum confidence for execution
        self.learning_enabled = True
        
        # Execution queue
        self.execution_queue = asyncio.Queue() if asyncio.get_event_loop().is_running() else None
        
        # Background threads
        self.executor_thread = None
        self.monitor_thread = None
        self.running = True
        
        print(f"🤖 Autonomous Trading Executor Initialized in {mode.value} mode")
        self._start_autonomous_system()
        
    def _start_autonomous_system(self):
        """Start autonomous trading system"""
        # Start execution thread
        self.executor_thread = threading.Thread(
            target=self._execution_loop,
            daemon=True
        )
        self.executor_thread.start()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitor_thread.start()
        
        print("✅ Autonomous system started")
        
    def _execution_loop(self):
        """Main execution loop for autonomous trading"""
        while self.running:
            try:
                if self.autonomous_enabled and not self.emergency_stop:
                    # Get AI decision
                    decision = self._get_next_decision()
                    
                    if decision:
                        # Validate and execute
                        self._process_decision(decision)
                        
                import time
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error in execution loop: {e}")
                self._handle_execution_error(e)
                import time
                time.sleep(5)
                
    def _monitoring_loop(self):
        """Monitor system health and safety"""
        while self.running:
            try:
                # Perform safety checks
                self._perform_safety_checks()
                
                # Check for anomalies
                self._detect_anomalies()
                
                # Auto-adjust parameters
                if self.learning_enabled:
                    self._adaptive_adjustment()
                    
                import time
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                import time
                time.sleep(30)
                
    def execute_trade(self, trade_signal: Dict) -> Dict[str, Any]:
        """
        Execute a trade with full safety checks
        
        Args:
            trade_signal: Trading signal from AI
            
        Returns:
            Execution result
        """
        # Generate execution ID
        exec_id = self._generate_execution_id(trade_signal)
        
        # Pre-execution validation
        validation = self._validate_trade(trade_signal)
        if not validation['valid']:
            return {
                'success': False,
                'execution_id': exec_id,
                'reason': validation['reason'],
                'timestamp': datetime.now().isoformat()
            }
            
        # Risk assessment
        risk = self._assess_risk(trade_signal)
        if risk['level'] == RiskLevel.EXTREME:
            return {
                'success': False,
                'execution_id': exec_id,
                'reason': 'Risk level too high',
                'risk_assessment': risk,
                'timestamp': datetime.now().isoformat()
            }
            
        # Execute based on mode
        result = self._execute_by_mode(trade_signal, exec_id)
        
        # Post-execution processing
        self._post_execution_processing(result, trade_signal)
        
        # Learn from execution
        if self.learning_enabled:
            self._learn_from_execution(result)
            
        return result
        
    def _validate_trade(self, signal: Dict) -> Dict[str, Any]:
        """
        Validate trade signal before execution
        
        Args:
            signal: Trade signal to validate
            
        Returns:
            Validation result
        """
        # Check safety status
        if self.safety_status in [SafetyStatus.RED, SafetyStatus.EMERGENCY]:
            return {
                'valid': False,
                'reason': f'Safety status: {self.safety_status.value}'
            }
            
        # Check emergency stop
        if self.emergency_stop:
            return {
                'valid': False,
                'reason': 'Emergency stop active'
            }
            
        # Check position limits
        if len(self.active_positions) >= self.risk_parameters['position_limit']:
            return {
                'valid': False,
                'reason': 'Position limit reached'
            }
            
        # Check exposure limits
        position_size = signal.get('size', 0)
        if self.total_exposure + position_size > self.risk_parameters['max_total_exposure']:
            return {
                'valid': False,
                'reason': 'Exposure limit exceeded'
            }
            
        # Check daily loss limit
        if self.daily_pnl <= -self.risk_parameters['max_daily_loss']:
            return {
                'valid': False,
                'reason': 'Daily loss limit reached'
            }
            
        # Check confidence threshold
        confidence = signal.get('confidence', 0)
        if confidence < self.confidence_threshold:
            return {
                'valid': False,
                'reason': f'Confidence {confidence:.2%} below threshold'
            }
            
        # Check correlation with existing positions
        correlation = self._check_correlation(signal)
        if correlation > self.risk_parameters['correlation_limit']:
            return {
                'valid': False,
                'reason': f'High correlation {correlation:.2f} with existing positions'
            }
            
        return {'valid': True, 'reason': 'All checks passed'}
        
    def _assess_risk(self, signal: Dict) -> Dict[str, Any]:
        """
        Assess risk level of trade
        
        Args:
            signal: Trade signal
            
        Returns:
            Risk assessment
        """
        risk_score = 0
        risk_factors = []
        
        # Position size risk
        size = signal.get('size', 0)
        size_ratio = size / self.risk_parameters['max_position_size']
        if size_ratio > 0.8:
            risk_score += 2
            risk_factors.append('Large position size')
        elif size_ratio > 0.5:
            risk_score += 1
            risk_factors.append('Moderate position size')
            
        # Market volatility
        volatility = signal.get('market_volatility', 0)
        if volatility > 0.3:
            risk_score += 2
            risk_factors.append('High volatility')
        elif volatility > 0.15:
            risk_score += 1
            risk_factors.append('Moderate volatility')
            
        # Drawdown proximity
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if current_drawdown > self.risk_parameters['max_drawdown'] * 0.8:
            risk_score += 3
            risk_factors.append('Near max drawdown')
        elif current_drawdown > self.risk_parameters['max_drawdown'] * 0.5:
            risk_score += 1
            risk_factors.append('Significant drawdown')
            
        # Time of day risk
        hour = datetime.now().hour
        if hour < 9 or hour > 16:  # Outside regular hours
            risk_score += 1
            risk_factors.append('Outside regular hours')
            
        # Determine risk level
        if risk_score >= 5:
            level = RiskLevel.EXTREME
        elif risk_score >= 4:
            level = RiskLevel.HIGH
        elif risk_score >= 3:
            level = RiskLevel.MODERATE
        elif risk_score >= 1:
            level = RiskLevel.LOW
        else:
            level = RiskLevel.MINIMAL
            
        return {
            'level': level,
            'score': risk_score,
            'factors': risk_factors,
            'timestamp': datetime.now().isoformat()
        }
        
    def _execute_by_mode(self, signal: Dict, exec_id: str) -> Dict[str, Any]:
        """
        Execute trade based on current mode
        
        Args:
            signal: Trade signal
            exec_id: Execution ID
            
        Returns:
            Execution result
        """
        start_time = datetime.now()
        
        if self.mode == ExecutionMode.SIMULATION:
            result = self._execute_simulation(signal, exec_id)
            
        elif self.mode == ExecutionMode.PAPER:
            result = self._execute_paper_trade(signal, exec_id)
            
        elif self.mode == ExecutionMode.LIVE:
            result = self._execute_live_trade(signal, exec_id)
            
        elif self.mode == ExecutionMode.HYBRID:
            # Try live, fallback to simulation
            try:
                result = self._execute_live_trade(signal, exec_id)
            except Exception as e:
                print(f"Live execution failed, falling back to simulation: {e}")
                result = self._execute_simulation(signal, exec_id)
                result['fallback'] = True
                
        else:
            result = {
                'success': False,
                'reason': f'Unknown mode: {self.mode}'
            }
            
        # Add execution metadata
        execution_time = (datetime.now() - start_time).total_seconds()
        result['execution_time'] = execution_time
        result['execution_id'] = exec_id
        result['mode'] = self.mode.value
        result['timestamp'] = datetime.now().isoformat()
        
        # Update metrics
        self.execution_metrics['total_executed'] += 1
        self.execution_metrics['execution_time_avg'] = (
            (self.execution_metrics['execution_time_avg'] * 
             (self.execution_metrics['total_executed'] - 1) + 
             execution_time) / self.execution_metrics['total_executed']
        )
        
        return result
        
    def _execute_simulation(self, signal: Dict, exec_id: str) -> Dict[str, Any]:
        """Execute simulated trade"""
        # Simulate market conditions
        import random
        slippage = random.gauss(0, 0.001)  # 0.1% slippage
        execution_price = signal.get('price', 100) * (1 + slippage)
        
        # Create position
        position = {
            'id': exec_id,
            'symbol': signal.get('symbol', 'UNKNOWN'),
            'side': signal.get('side', 'BUY'),
            'size': signal.get('size', 0),
            'entry_price': execution_price,
            'current_price': execution_price,
            'pnl': 0,
            'status': 'OPEN',
            'opened_at': datetime.now().isoformat()
        }
        
        # Store position
        self.active_positions[exec_id] = position
        self.total_exposure += position['size'] * position['entry_price']
        
        return {
            'success': True,
            'position': position,
            'slippage': slippage,
            'execution_price': execution_price
        }
        
    def _execute_paper_trade(self, signal: Dict, exec_id: str) -> Dict[str, Any]:
        """Execute paper trade with realistic conditions"""
        # Similar to simulation but with more realistic constraints
        # Check market hours, liquidity, etc.
        market_open = self._check_market_hours(signal.get('symbol', ''))
        
        if not market_open:
            return {
                'success': False,
                'reason': 'Market closed'
            }
            
        # Simulate order book and liquidity
        import random
        liquidity_factor = random.uniform(0.8, 1.0)
        available_size = signal.get('size', 0) * liquidity_factor
        
        if available_size < signal.get('size', 0) * 0.5:
            return {
                'success': False,
                'reason': 'Insufficient liquidity'
            }
            
        # Execute with realistic slippage
        slippage = random.gauss(0.001, 0.002)  # Higher slippage
        execution_price = signal.get('price', 100) * (1 + slippage)
        
        # Create position
        position = {
            'id': exec_id,
            'symbol': signal.get('symbol', 'UNKNOWN'),
            'side': signal.get('side', 'BUY'),
            'size': available_size,
            'entry_price': execution_price,
            'current_price': execution_price,
            'pnl': 0,
            'status': 'OPEN',
            'opened_at': datetime.now().isoformat()
        }
        
        # Store position
        self.active_positions[exec_id] = position
        self.total_exposure += position['size'] * position['entry_price']
        
        return {
            'success': True,
            'position': position,
            'slippage': slippage,
            'execution_price': execution_price,
            'liquidity_factor': liquidity_factor
        }
        
    def _execute_live_trade(self, signal: Dict, exec_id: str) -> Dict[str, Any]:
        """
        Execute live trade (placeholder for broker integration)
        
        THIS IS A PLACEHOLDER - Actual implementation would connect to broker API
        """
        # SAFETY: This is a placeholder
        # Real implementation would:
        # 1. Connect to broker API
        # 2. Place actual orders
        # 3. Handle confirmations
        # 4. Manage positions
        
        print(f"⚠️ LIVE TRADE PLACEHOLDER - Would execute: {signal}")
        
        # For now, return simulated result
        return self._execute_simulation(signal, exec_id)
        
    def _post_execution_processing(self, result: Dict, signal: Dict):
        """Post-execution processing and bookkeeping"""
        if result.get('success'):
            # Log successful execution
            self.execution_metrics['successful_trades'] += 1
            
            # Store in history
            self.execution_history.append({
                'result': result,
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            })
            
            # Persist to MongoDB
            if self.persistence and self.persistence.db:
                try:
                    self.persistence.db.trade_executions.insert_one({
                        'execution_id': result.get('execution_id'),
                        'signal': signal,
                        'result': result,
                        'mode': self.mode.value,
                        'timestamp': datetime.now()
                    })
                except Exception as e:
                    print(f"Error persisting execution: {e}")
                    
        else:
            # Log failed execution
            if 'Risk level' in result.get('reason', ''):
                self.execution_metrics['rejected_trades'] += 1
            else:
                self.execution_metrics['failed_trades'] += 1
                
        # Update win rate
        total = (self.execution_metrics['successful_trades'] + 
                self.execution_metrics['failed_trades'])
        if total > 0:
            self.execution_metrics['win_rate'] = (
                self.execution_metrics['successful_trades'] / total
            )
            
    def _perform_safety_checks(self):
        """Perform comprehensive safety checks"""
        all_safe = True
        safety_issues = []
        
        # Check drawdown
        current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        if current_drawdown > self.risk_parameters['max_drawdown']:
            all_safe = False
            safety_issues.append('Maximum drawdown exceeded')
            self.safety_checks['drawdown_protection'] = False
            
        # Check daily loss
        if self.daily_pnl <= -self.risk_parameters['max_daily_loss']:
            all_safe = False
            safety_issues.append('Daily loss limit reached')
            self.safety_checks['risk_limits'] = False
            
        # Check position concentration
        if len(self.active_positions) > 0:
            largest_position = max(
                self.active_positions.values(),
                key=lambda x: x['size'] * x['current_price']
            )
            concentration = (largest_position['size'] * 
                           largest_position['current_price'] / 
                           self.current_balance)
            if concentration > 0.3:  # 30% in single position
                all_safe = False
                safety_issues.append('Position concentration too high')
                self.safety_checks['position_limits'] = False
                
        # Update safety status
        if not all_safe:
            if len(safety_issues) >= 3:
                self.safety_status = SafetyStatus.RED
            else:
                self.safety_status = SafetyStatus.YELLOW
        else:
            self.safety_status = SafetyStatus.GREEN
            
        # Log safety status
        if safety_issues:
            print(f"⚠️ Safety Issues: {', '.join(safety_issues)}")
            
    def _detect_anomalies(self):
        """Detect trading anomalies"""
        anomalies = []
        
        # Check for rapid losses
        if len(self.execution_history) >= 5:
            recent_trades = list(self.execution_history)[-5:]
            recent_losses = sum(
                1 for trade in recent_trades
                if trade['result'].get('pnl', 0) < 0
            )
            if recent_losses >= 4:
                anomalies.append('Consecutive losses detected')
                
        # Check for unusual volume
        if self.execution_metrics['total_executed'] > 0:
            avg_size = sum(
                pos['size'] for pos in self.active_positions.values()
            ) / max(len(self.active_positions), 1)
            
            for position in self.active_positions.values():
                if position['size'] > avg_size * 3:
                    anomalies.append(f"Unusual position size: {position['id']}")
                    
        # Check execution time anomalies
        if self.execution_metrics['execution_time_avg'] > 0:
            if self.execution_metrics['execution_time_avg'] > 5:  # 5 seconds
                anomalies.append('Slow execution detected')
                
        # Take action on anomalies
        if anomalies:
            print(f"🔍 Anomalies detected: {anomalies}")
            self.safety_checks['anomaly_detection'] = False
            
            # Reduce risk on multiple anomalies
            if len(anomalies) >= 2:
                self._reduce_risk_exposure()
                
    def _adaptive_adjustment(self):
        """Adaptively adjust trading parameters based on performance"""
        if self.execution_metrics['total_executed'] < 10:
            return  # Not enough data
            
        # Adjust confidence threshold based on win rate
        if self.execution_metrics['win_rate'] < 0.4:
            # Increase confidence requirement
            self.confidence_threshold = min(0.9, self.confidence_threshold + 0.05)
            print(f"📈 Increasing confidence threshold to {self.confidence_threshold:.2%}")
            
        elif self.execution_metrics['win_rate'] > 0.6:
            # Can be less conservative
            self.confidence_threshold = max(0.6, self.confidence_threshold - 0.05)
            print(f"📉 Decreasing confidence threshold to {self.confidence_threshold:.2%}")
            
        # Adjust position sizing based on performance
        if self.daily_pnl < 0:
            # Reduce position sizes
            self.risk_parameters['max_position_size'] *= 0.9
            print(f"📊 Reducing max position size to {self.risk_parameters['max_position_size']}")
            
        # Save adjustments to MongoDB
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.adaptive_parameters.insert_one({
                    'confidence_threshold': self.confidence_threshold,
                    'risk_parameters': self.risk_parameters,
                    'win_rate': self.execution_metrics['win_rate'],
                    'timestamp': datetime.now()
                })
            except Exception as e:
                print(f"Error saving adaptive parameters: {e}")
                
    def _reduce_risk_exposure(self):
        """Reduce risk exposure in response to issues"""
        print("⚠️ Reducing risk exposure")
        
        # Reduce position limits
        self.risk_parameters['position_limit'] = max(
            1, 
            self.risk_parameters['position_limit'] - 2
        )
        
        # Reduce max exposure
        self.risk_parameters['max_total_exposure'] *= 0.7
        
        # Increase confidence requirement
        self.confidence_threshold = min(0.95, self.confidence_threshold + 0.1)
        
    def _check_correlation(self, signal: Dict) -> float:
        """
        Check correlation with existing positions
        
        Args:
            signal: New trade signal
            
        Returns:
            Maximum correlation coefficient
        """
        if not self.active_positions:
            return 0
            
        # Simplified correlation check
        # Real implementation would use price history
        symbol = signal.get('symbol', '')
        max_correlation = 0
        
        for position in self.active_positions.values():
            if position['symbol'] == symbol:
                max_correlation = 1.0  # Same symbol
            elif position['symbol'][:3] == symbol[:3]:  # Same base currency
                max_correlation = max(max_correlation, 0.7)
                
        return max_correlation
        
    def _check_market_hours(self, symbol: str) -> bool:
        """
        Check if market is open for trading
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if market is open
        """
        # Simplified check - real implementation would check actual market hours
        hour = datetime.now().hour
        weekday = datetime.now().weekday()
        
        # Forex/Crypto - 24/7
        if 'BTC' in symbol or 'ETH' in symbol or 'USD' in symbol:
            return True
            
        # Stock market hours (simplified)
        if weekday >= 5:  # Weekend
            return False
            
        if 9 <= hour <= 16:  # Market hours
            return True
            
        return False
        
    def _generate_execution_id(self, signal: Dict) -> str:
        """Generate unique execution ID"""
        data = f"{signal}{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]
        
    def _get_next_decision(self) -> Optional[Dict]:
        """Get next trading decision from AI"""
        # This would integrate with your AI decision maker
        # For now, return None
        return None
        
    def _learn_from_execution(self, result: Dict):
        """Learn from execution results"""
        if self.learning_feedback:
            # Send execution result to learning system
            self.learning_feedback.process_feedback({
                'type': 'execution',
                'result': result,
                'metrics': self.execution_metrics.copy(),
                'timestamp': datetime.now().isoformat()
            })
            
    def _handle_execution_error(self, error: Exception):
        """Handle execution errors"""
        print(f"❌ Execution error: {error}")
        
        # Log error
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.execution_errors.insert_one({
                    'error': str(error),
                    'type': type(error).__name__,
                    'mode': self.mode.value,
                    'safety_status': self.safety_status.value,
                    'timestamp': datetime.now()
                })
            except:
                pass
                
    def enable_autonomous_trading(self):
        """Enable autonomous trading"""
        if self.safety_status == SafetyStatus.GREEN:
            self.autonomous_enabled = True
            print("✅ Autonomous trading ENABLED")
        else:
            print(f"❌ Cannot enable autonomous trading - Safety status: {self.safety_status.value}")
            
    def disable_autonomous_trading(self):
        """Disable autonomous trading"""
        self.autonomous_enabled = False
        print("⏸️ Autonomous trading DISABLED")
        
    def emergency_shutdown(self):
        """Emergency shutdown of all trading"""
        print("🚨 EMERGENCY SHUTDOWN INITIATED")
        
        self.emergency_stop = True
        self.autonomous_enabled = False
        self.safety_status = SafetyStatus.EMERGENCY
        
        # Close all positions (in simulation)
        for position_id in list(self.active_positions.keys()):
            self._close_position(position_id, emergency=True)
            
        # Save state
        if self.state_recovery:
            self.state_recovery.emergency_save()
            
        print("🛑 Emergency shutdown complete")
        
    def _close_position(self, position_id: str, emergency: bool = False):
        """Close a position"""
        if position_id not in self.active_positions:
            return
            
        position = self.active_positions[position_id]
        position['status'] = 'CLOSED'
        position['closed_at'] = datetime.now().isoformat()
        
        if emergency:
            position['close_reason'] = 'EMERGENCY'
            
        # Update exposure
        self.total_exposure -= position['size'] * position['entry_price']
        
        # Move to history
        del self.active_positions[position_id]
        
        print(f"📊 Position {position_id} closed")
        
    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            'mode': self.mode.value,
            'autonomous_enabled': self.autonomous_enabled,
            'safety_status': self.safety_status.value,
            'emergency_stop': self.emergency_stop,
            'active_positions': len(self.active_positions),
            'total_exposure': self.total_exposure,
            'daily_pnl': self.daily_pnl,
            'current_balance': self.current_balance,
            'execution_metrics': self.execution_metrics.copy(),
            'risk_parameters': self.risk_parameters.copy(),
            'confidence_threshold': self.confidence_threshold,
            'safety_checks': self.safety_checks.copy(),
            'timestamp': datetime.now().isoformat()
        }
        
    def switch_mode(self, new_mode: ExecutionMode):
        """
        Switch execution mode
        
        Args:
            new_mode: New execution mode
        """
        self.previous_mode = self.mode
        self.mode = new_mode
        print(f"🔄 Switched from {self.previous_mode.value} to {new_mode.value} mode")
        
        # Log mode switch
        if self.persistence and self.persistence.db:
            try:
                self.persistence.db.mode_switches.insert_one({
                    'from_mode': self.previous_mode.value,
                    'to_mode': new_mode.value,
                    'reason': 'Manual switch',
                    'timestamp': datetime.now()
                })
            except:
                pass
                
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down Autonomous Executor...")
        
        # Disable trading
        self.autonomous_enabled = False
        self.running = False
        
        # Wait for threads
        if self.executor_thread:
            self.executor_thread.join(timeout=5)
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        # Close all positions
        for position_id in list(self.active_positions.keys()):
            self._close_position(position_id)
            
        print("✅ Autonomous Executor shutdown complete")


# Global instance
_executor = None

def get_autonomous_executor(mode: ExecutionMode = ExecutionMode.SIMULATION):
    """Get or create autonomous executor"""
    global _executor
    if _executor is None:
        _executor = AutonomousTradingExecutor(mode)
    return _executor

# Helper functions
def execute_autonomous_trade(signal: Dict) -> Dict:
    """Execute autonomous trade"""
    executor = get_autonomous_executor()
    return executor.execute_trade(signal)

def get_execution_status() -> Dict:
    """Get execution status"""
    executor = get_autonomous_executor()
    return executor.get_execution_status()

def enable_autonomous_mode():
    """Enable autonomous trading"""
    executor = get_autonomous_executor()
    executor.enable_autonomous_trading()

def disable_autonomous_mode():
    """Disable autonomous trading"""
    executor = get_autonomous_executor()
    executor.disable_autonomous_trading()

def emergency_stop():
    """Emergency stop all trading"""
    executor = get_autonomous_executor()
    executor.emergency_shutdown()