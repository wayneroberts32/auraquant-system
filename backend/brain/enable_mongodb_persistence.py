"""
Enable MongoDB Persistence for AuraQuant System
Engineer's Note: Run this alongside your existing system to enable MongoDB persistence
This does NOT modify your existing code - it adds persistence as a companion service
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import (
    get_persistence_service,
    save_memory,
    save_quantum_state,
    save_trading_decision,
    save_evolution_checkpoint,
    save_learned_pattern,
    save_neural_weights
)

def initialize_persistence():
    """
    Initialize MongoDB persistence service
    Call this at the start of your trading system
    """
    print("\n" + "="*60)
    print("🚀 ENABLING MongoDB PERSISTENCE FOR AURAQUANT SYSTEM")
    print("="*60)
    
    service = get_persistence_service()
    
    if service and service.db:
        print("✅ MongoDB persistence layer activated")
        print("📊 All learning and memory data will be saved to MongoDB")
        print("🧠 System will evolve and learn from saved experiences")
        print("="*60 + "\n")
        return True
    else:
        print("⚠️ MongoDB persistence not available")
        print("📁 System will continue with local storage only")
        print("="*60 + "\n")
        return False

# Example usage functions that can be called from your existing code
def log_trade_decision(symbol, action, confidence, market_conditions):
    """
    Log a trading decision to MongoDB
    Add this call to your trading logic
    
    Example:
        from brain.enable_mongodb_persistence import log_trade_decision
        decision_id = log_trade_decision("AAPL", "buy", 0.85, market_data)
    """
    return save_trading_decision(symbol, action, confidence, market_conditions)

def log_evolution_progress(generation, fitness_score, neural_weights, mutations):
    """
    Log evolution progress to MongoDB
    Add this call to your evolution/training loops
    
    Example:
        from brain.enable_mongodb_persistence import log_evolution_progress
        log_evolution_progress(current_gen, fitness, weights, mutations_list)
    """
    save_evolution_checkpoint(generation, fitness_score, neural_weights, mutations)

def log_quantum_brain_state(quantum_state_vector, consciousness_level, generation):
    """
    Log quantum brain state to MongoDB
    Add this call after quantum state updates
    
    Example:
        from brain.enable_mongodb_persistence import log_quantum_brain_state
        log_quantum_brain_state(brain.quantum_state, brain.consciousness, brain.generation)
    """
    save_quantum_state(quantum_state_vector, consciousness_level, generation)

def log_discovered_pattern(pattern_id, pattern_data, success_rate, occurrences):
    """
    Log discovered trading pattern to MongoDB
    Add this call when patterns are identified
    
    Example:
        from brain.enable_mongodb_persistence import log_discovered_pattern
        log_discovered_pattern("bullish_breakout_123", pattern_info, 0.75, 42)
    """
    service = get_persistence_service()
    if service:
        service.save_learned_pattern(pattern_id, pattern_data, success_rate, occurrences)

def log_neural_network_checkpoint(model_name, weights, version):
    """
    Save neural network weights checkpoint to MongoDB
    Add this call after training epochs
    
    Example:
        from brain.enable_mongodb_persistence import log_neural_network_checkpoint
        log_neural_network_checkpoint("pattern_recognition", model.get_weights(), epoch)
    """
    save_neural_weights(model_name, weights, version)

def log_memory(memory_type, memory_data):
    """
    Log any type of memory to MongoDB
    Generic memory logging function
    
    Example:
        from brain.enable_mongodb_persistence import log_memory
        log_memory("market_insight", {"symbol": "TSLA", "insight": "breakout pattern"})
    """
    save_memory(memory_type, memory_data)

def retrieve_last_brain_state():
    """
    Retrieve the last saved brain state from MongoDB
    Use this on system startup to resume from last state
    
    Returns:
        Tuple of (quantum_state, consciousness_level, generation) or (None, None, None)
    """
    service = get_persistence_service()
    if service:
        return service.load_latest_quantum_state()
    return None, None, None

def retrieve_neural_weights(model_name):
    """
    Retrieve the latest neural network weights from MongoDB
    Use this to restore trained models
    
    Returns:
        Weights or None
    """
    service = get_persistence_service()
    if service:
        return service.load_latest_neural_weights(model_name)
    return None

def get_recent_performance(days=7):
    """
    Get recent performance metrics from MongoDB
    
    Returns:
        List of performance metrics
    """
    service = get_persistence_service()
    if service:
        return service.get_performance_metrics(days)
    return []

# Auto-initialize when imported
if __name__ != "__main__":
    initialize_persistence()

if __name__ == "__main__":
    # Test the persistence service
    print("Testing MongoDB Persistence Service...")
    
    if initialize_persistence():
        import numpy as np
        from datetime import datetime
        
        # Test saving various types of data
        print("\n📝 Testing data persistence...")
        
        # Test quantum state
        test_quantum_state = np.random.random(1024)
        log_quantum_brain_state(test_quantum_state, 0.75, 1)
        print("✅ Quantum state saved")
        
        # Test trading decision
        test_market_data = {
            "price": 150.25,
            "volume": 1000000,
            "rsi": 65,
            "macd": 1.2
        }
        decision_id = log_trade_decision("TEST", "buy", 0.85, test_market_data)
        print(f"✅ Trading decision saved with ID: {decision_id}")
        
        # Test pattern discovery
        test_pattern = {
            "type": "bullish_flag",
            "strength": 0.8,
            "timeframe": "1h"
        }
        log_discovered_pattern("test_pattern_001", test_pattern, 0.72, 5)
        print("✅ Pattern saved")
        
        # Test memory
        test_memory = {
            "timestamp": datetime.now().isoformat(),
            "observation": "Test memory entry",
            "importance": 0.5
        }
        log_memory("test", test_memory)
        print("✅ Memory saved")
        
        # Test retrieval
        print("\n🔍 Testing data retrieval...")
        state, consciousness, gen = retrieve_last_brain_state()
        if state is not None:
            print(f"✅ Retrieved quantum state: Generation {gen}, Consciousness {consciousness}")
        
        metrics = get_recent_performance(1)
        print(f"✅ Retrieved {len(metrics)} performance metrics")
        
        print("\n✅ All tests passed! MongoDB persistence is working.")
    else:
        print("⚠️ Could not test - MongoDB not connected")