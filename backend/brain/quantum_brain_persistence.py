"""
Quantum Brain Persistence Wrapper for AuraQuant
Engineer's Note: This WRAPS your existing quantum_brain.py to add MongoDB persistence
WITHOUT modifying the original code - Task 3/12
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio
import threading
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import (
    save_quantum_state,
    save_evolution_checkpoint,
    save_trading_decision,
    save_neural_weights,
    get_persistence_service
)

class QuantumBrainPersistenceWrapper:
    """
    Wraps the existing QuantumBrain to add MongoDB persistence
    This runs alongside your existing quantum_brain.py without modifying it
    """
    
    def __init__(self, quantum_brain_instance=None):
        """
        Initialize persistence wrapper
        
        Args:
            quantum_brain_instance: Your existing QuantumBrain instance
        """
        self.brain = quantum_brain_instance
        self.persistence_enabled = True
        self.save_interval = 30  # Save every 30 seconds
        self.last_save = datetime.now()
        
        # Background thread for periodic saving
        self.running = True
        self.save_thread = None
        
        # Evolution tracking
        self.generation_checkpoints = {}
        self.performance_history = []
        
        print("🧠 Quantum Brain Persistence Wrapper Initialized")
        
    def wrap_brain(self, brain_instance):
        """
        Wrap an existing QuantumBrain instance
        
        Args:
            brain_instance: Your existing QuantumBrain instance
        """
        self.brain = brain_instance
        
        # Start background persistence
        self.start_persistence_loop()
        
        print("✅ Quantum Brain wrapped with MongoDB persistence")
        
    def persist_quantum_state(self):
        """Save current quantum state to MongoDB"""
        if not self.brain or not self.persistence_enabled:
            return
            
        try:
            # Get quantum state from brain
            quantum_state = getattr(self.brain, 'quantum_state', None)
            consciousness = getattr(self.brain, 'consciousness_level', 0.5)
            generation = getattr(self.brain, 'evolution_generation', 1)
            
            if quantum_state is not None:
                save_quantum_state(quantum_state, consciousness, generation)
                print(f"💾 Quantum state saved: Gen {generation}, Consciousness {consciousness:.3f}")
                
        except Exception as e:
            print(f"Error persisting quantum state: {e}")
            
    def persist_neural_weights(self, model_name: str = "pattern_model"):
        """Save neural network weights to MongoDB"""
        if not self.brain or not self.persistence_enabled:
            return
            
        try:
            # Try to get different model types
            models = {
                'pattern_model': getattr(self.brain, 'pattern_model', None),
                'decision_model': getattr(self.brain, 'decision_model', None),
                'rl_model': getattr(self.brain, 'rl_model', None)
            }
            
            for name, model in models.items():
                if model is not None:
                    # Get weights based on framework
                    weights = None
                    version = getattr(self.brain, 'evolution_generation', 1)
                    
                    # TensorFlow/Keras model
                    if hasattr(model, 'get_weights'):
                        weights = model.get_weights()
                    # PyTorch model
                    elif hasattr(model, 'state_dict'):
                        weights = model.state_dict()
                        
                    if weights is not None:
                        save_neural_weights(name, weights, version)
                        print(f"🧠 Neural weights saved: {name} v{version}")
                        
        except Exception as e:
            print(f"Error persisting neural weights: {e}")
            
    def persist_evolution_checkpoint(self):
        """Save evolution checkpoint to MongoDB"""
        if not self.brain or not self.persistence_enabled:
            return
            
        try:
            generation = getattr(self.brain, 'evolution_generation', 1)
            
            # Calculate fitness score
            fitness = self._calculate_fitness_score()
            
            # Collect all neural weights
            weights = {}
            models = ['pattern_model', 'decision_model', 'rl_model']
            for model_name in models:
                model = getattr(self.brain, model_name, None)
                if model:
                    if hasattr(model, 'get_weights'):
                        weights[model_name] = model.get_weights()
                    elif hasattr(model, 'state_dict'):
                        weights[model_name] = model.state_dict()
                        
            # Get mutations if tracked
            mutations = getattr(self.brain, 'applied_mutations', [])
            
            save_evolution_checkpoint(generation, fitness, weights, mutations)
            
            # Track checkpoint
            self.generation_checkpoints[generation] = {
                'fitness': fitness,
                'timestamp': datetime.now(),
                'consciousness': getattr(self.brain, 'consciousness_level', 0.5)
            }
            
            print(f"📊 Evolution checkpoint saved: Gen {generation}, Fitness {fitness:.4f}")
            
        except Exception as e:
            print(f"Error persisting evolution checkpoint: {e}")
            
    def log_trading_decision(self, symbol: str, action: str, confidence: float, 
                           market_data: Dict[str, Any]):
        """
        Log trading decision to MongoDB
        
        Args:
            symbol: Trading symbol
            action: Trading action (buy/sell/hold)
            confidence: Confidence score
            market_data: Current market conditions
        """
        try:
            # Add neural network state
            neural_state = {}
            if self.brain:
                neural_state = {
                    'consciousness': getattr(self.brain, 'consciousness_level', 0.5),
                    'generation': getattr(self.brain, 'evolution_generation', 1),
                    'learning_rate': getattr(self.brain, 'learning_rate', 0.001)
                }
                
            decision_id = save_trading_decision(
                symbol, action, confidence, 
                {**market_data, 'neural_state': neural_state}
            )
            
            # Track for performance evaluation
            self.performance_history.append({
                'decision_id': decision_id,
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': action,
                'confidence': confidence
            })
            
            return decision_id
            
        except Exception as e:
            print(f"Error logging trading decision: {e}")
            return None
            
    def _calculate_fitness_score(self) -> float:
        """Calculate fitness score based on recent performance"""
        if not self.performance_history:
            return 0.5
            
        # Simple fitness calculation based on recent decisions
        recent = self.performance_history[-100:]  # Last 100 decisions
        
        if not recent:
            return 0.5
            
        # Average confidence as a proxy for fitness
        avg_confidence = sum(d['confidence'] for d in recent) / len(recent)
        
        # Adjust based on brain's consciousness level
        if self.brain:
            consciousness = getattr(self.brain, 'consciousness_level', 0.5)
            fitness = (avg_confidence * 0.7) + (consciousness * 0.3)
        else:
            fitness = avg_confidence
            
        return min(max(fitness, 0.0), 1.0)
        
    def start_persistence_loop(self):
        """Start background thread for periodic persistence"""
        if self.save_thread is None or not self.save_thread.is_alive():
            self.running = True
            self.save_thread = threading.Thread(target=self._persistence_loop, daemon=True)
            self.save_thread.start()
            print("🔄 Background persistence loop started")
            
    def _persistence_loop(self):
        """Background loop for periodic saving"""
        while self.running:
            try:
                time.sleep(self.save_interval)
                
                if self.brain and self.persistence_enabled:
                    # Save quantum state
                    self.persist_quantum_state()
                    
                    # Save neural weights periodically
                    if (datetime.now() - self.last_save).seconds > 300:  # Every 5 minutes
                        self.persist_neural_weights()
                        self.persist_evolution_checkpoint()
                        self.last_save = datetime.now()
                        
            except Exception as e:
                print(f"Error in persistence loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
                
    def stop_persistence_loop(self):
        """Stop background persistence"""
        self.running = False
        if self.save_thread:
            self.save_thread.join(timeout=5)
            
        # Final save
        self.persist_quantum_state()
        self.persist_neural_weights()
        self.persist_evolution_checkpoint()
        
        print("🛑 Persistence loop stopped")
        
    def load_last_state(self):
        """Load the last saved state from MongoDB"""
        service = get_persistence_service()
        if not service:
            return False
            
        try:
            # Load quantum state
            quantum_state, consciousness, generation = service.load_latest_quantum_state()
            
            if quantum_state is not None and self.brain:
                # Restore state to brain
                if hasattr(self.brain, 'quantum_state'):
                    self.brain.quantum_state = quantum_state
                if hasattr(self.brain, 'consciousness_level'):
                    self.brain.consciousness_level = consciousness
                if hasattr(self.brain, 'evolution_generation'):
                    self.brain.evolution_generation = generation
                    
                print(f"✅ Restored state: Gen {generation}, Consciousness {consciousness:.3f}")
                
                # Load neural weights
                models = ['pattern_model', 'decision_model', 'rl_model']
                for model_name in models:
                    weights = service.load_latest_neural_weights(model_name)
                    if weights and hasattr(self.brain, model_name):
                        model = getattr(self.brain, model_name)
                        if model:
                            if hasattr(model, 'set_weights'):
                                model.set_weights(weights)
                            elif hasattr(model, 'load_state_dict'):
                                model.load_state_dict(weights)
                                
                return True
                
        except Exception as e:
            print(f"Error loading last state: {e}")
            
        return False
        
    def get_evolution_history(self) -> Dict[int, Dict]:
        """Get evolution history from saved checkpoints"""
        return self.generation_checkpoints
        
    def enable_persistence(self):
        """Enable MongoDB persistence"""
        self.persistence_enabled = True
        print("✅ Persistence enabled")
        
    def disable_persistence(self):
        """Disable MongoDB persistence (for testing)"""
        self.persistence_enabled = False
        print("⏸️ Persistence disabled")

# Global wrapper instance
_quantum_wrapper = None

def get_quantum_wrapper():
    """Get or create quantum brain wrapper"""
    global _quantum_wrapper
    if _quantum_wrapper is None:
        _quantum_wrapper = QuantumBrainPersistenceWrapper()
    return _quantum_wrapper

# Helper functions for easy integration
def wrap_quantum_brain(brain_instance):
    """
    Wrap existing QuantumBrain with persistence
    
    Usage:
        from brain.quantum_brain import QuantumBrain
        from brain.quantum_brain_persistence import wrap_quantum_brain
        
        brain = QuantumBrain()
        wrap_quantum_brain(brain)  # Now it auto-saves to MongoDB
    """
    wrapper = get_quantum_wrapper()
    wrapper.wrap_brain(brain_instance)
    return wrapper

def log_brain_decision(symbol: str, action: str, confidence: float, market_data: Dict):
    """Log trading decision from quantum brain"""
    wrapper = get_quantum_wrapper()
    return wrapper.log_trading_decision(symbol, action, confidence, market_data)

def save_brain_checkpoint():
    """Manually trigger brain checkpoint save"""
    wrapper = get_quantum_wrapper()
    wrapper.persist_evolution_checkpoint()

def restore_brain_state():
    """Restore brain state from MongoDB"""
    wrapper = get_quantum_wrapper()
    return wrapper.load_last_state()

if __name__ == "__main__":
    print("Testing Quantum Brain Persistence Wrapper...")
    
    # Test without actual brain (simulation)
    wrapper = QuantumBrainPersistenceWrapper()
    
    # Simulate a trading decision
    decision_id = wrapper.log_trading_decision(
        "AAPL", "buy", 0.85,
        {"price": 150.00, "volume": 1000000, "rsi": 65}
    )
    
    print(f"✅ Test decision logged: {decision_id}")
    print("Quantum Brain Persistence Wrapper ready for integration!")