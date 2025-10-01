"""
State Recovery System for AuraQuant Trading System
Professor/Engineer's Note: Ensures system can recover from any failure and resume learning
WITHOUT modifying existing code - Task 9/12
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import pickle
import zlib
import hashlib
import threading
import atexit

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import get_persistence_service

class StateRecoverySystem:
    """
    Comprehensive state recovery and persistence system
    Ensures AI brain can resume from exact state after any shutdown
    """
    
    def __init__(self):
        """Initialize state recovery system"""
        # MongoDB persistence
        self.persistence = get_persistence_service()
        
        # State components
        self.brain_state = {}
        self.memory_state = {}
        self.learning_state = {}
        self.trading_state = {}
        self.evolution_state = {}
        
        # State validation
        self.state_checksums = {}
        self.state_versions = {}
        self.last_valid_state = None
        
        # Recovery tracking
        self.recovery_attempts = 0
        self.recovery_history = []
        self.corrupted_states = []
        
        # Auto-save configuration
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5 minutes
        self.last_save = datetime.now()
        
        # Graceful shutdown
        self.shutdown_handlers = []
        self.emergency_save_triggered = False
        
        # State validation rules
        self.validation_rules = {
            'quantum_state': self._validate_quantum_state,
            'neural_weights': self._validate_neural_weights,
            'memory_context': self._validate_memory_context,
            'learning_progress': self._validate_learning_progress
        }
        
        # Background save thread
        self.save_thread = None
        self.running = True
        
        # Initialize MongoDB collections
        self._init_collections()
        
        # Register shutdown handlers
        self._register_shutdown_handlers()
        
        print("🔄 State Recovery System Initialized")
        self._start_auto_save()
        
    def _init_collections(self):
        """Initialize MongoDB collections for state recovery"""
        if self.persistence is None or self.persistence.db is None:
            return
            
        try:
            db = self.persistence.db
            
            # Create state collections with indexes
            db.system_states.create_index([('timestamp', -1)])
            db.system_states.create_index([('state_type', 1)])
            db.system_states.create_index([('version', -1)])
            db.system_states.create_index([('checksum', 1)])
            
            # Recovery logs
            db.recovery_logs.create_index([('timestamp', -1)])
            db.recovery_logs.create_index([('status', 1)])
            
            # State validations
            db.state_validations.create_index([('timestamp', -1)])
            db.state_validations.create_index([('is_valid', 1)])
            
            print("📊 State recovery collections initialized")
            
        except Exception as e:
            print(f"Error initializing collections: {e}")
            
    def _register_shutdown_handlers(self):
        """Register graceful shutdown handlers"""
        # Register atexit handler
        atexit.register(self.graceful_shutdown)
        
        # Register signal handlers (Windows compatible)
        try:
            import signal
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except:
            pass  # Signals might not work on Windows
            
        print("🛡️ Shutdown handlers registered")
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n⚠️ Shutdown signal received: {signum}")
        self.graceful_shutdown()
        
    def _start_auto_save(self):
        """Start automatic state saving"""
        self.save_thread = threading.Thread(
            target=self._auto_save_loop,
            daemon=True
        )
        self.save_thread.start()
        print("💾 Auto-save enabled (every 5 minutes)")
        
    def _auto_save_loop(self):
        """Background auto-save loop"""
        while self.running:
            try:
                import time
                time.sleep(30)  # Check every 30 seconds
                
                if self.auto_save_enabled:
                    if (datetime.now() - self.last_save).seconds > self.auto_save_interval:
                        self.save_complete_state()
                        
            except Exception as e:
                print(f"Error in auto-save: {e}")
                
    def emergency_save(self) -> bool:
        """
        Emergency save of system state
        Bypass all checks and save immediately
        
        Returns:
            Success status
        """
        print("🆘 EMERGENCY SAVE INITIATED")
        return self.save_complete_state('emergency')
        
    def save_complete_state(self, state_type: str = 'checkpoint') -> bool:
        """
        Save complete system state to MongoDB
        
        Args:
            state_type: Type of save (periodic, checkpoint, emergency)
            
        Returns:
            Success status
        """
        print(f"💾 Saving complete system state ({state_type})...")
        
        try:
            # Collect all states
            complete_state = self._collect_all_states()
            
            # Validate state
            if not self._validate_complete_state(complete_state):
                print("⚠️ State validation failed")
                return False
                
            # Calculate checksum
            checksum = self._calculate_checksum(complete_state)
            
            # Compress state
            compressed_state = self._compress_state(complete_state)
            
            # Create state document
            state_doc = {
                'timestamp': datetime.now(),
                'state_type': state_type,
                'version': self._get_next_version(),
                'checksum': checksum,
                'compressed_state': compressed_state,
                'state_size': len(compressed_state),
                'components': list(complete_state.keys()),
                'metadata': {
                    'recovery_attempts': self.recovery_attempts,
                    'auto_save': self.auto_save_enabled
                }
            }
            
            # Save to MongoDB
            if self.persistence is not None and self.persistence.db is not None:
                result = self.persistence.db.system_states.insert_one(state_doc)
                
                # Update last save time
                self.last_save = datetime.now()
                self.last_valid_state = result.inserted_id
                
                # Log save
                self._log_recovery_event('state_saved', {
                    'state_id': str(result.inserted_id),
                    'state_type': state_type,
                    'checksum': checksum
                })
                
                print(f"✅ State saved successfully (ID: {result.inserted_id})")
                return True
                
        except Exception as e:
            print(f"❌ Error saving state: {e}")
            self._log_recovery_event('save_failed', {'error': str(e)})
            
        return False
        
    def load_complete_state(self, save_path: str = None) -> bool:
        """
        Load complete system state from MongoDB
        Alias for load_last_state for compatibility
        
        Args:
            save_path: Optional path (not used, for compatibility)
            
        Returns:
            Success status
        """
        return self.load_last_state()
        
    def load_last_state(self) -> bool:
        """
        Load and restore the last valid system state
        
        Returns:
            Success status
        """
        print("🔄 Loading last system state...")
        self.recovery_attempts += 1
        
        try:
            if self.persistence is None or self.persistence.db is None:
                print("❌ MongoDB not available")
                return False
                
            # Find last valid state
            last_state = self.persistence.db.system_states.find_one(
                {},
                sort=[('timestamp', -1)]
            )
            
            if not last_state:
                print("⚠️ No previous state found")
                return False
                
            # Decompress state
            compressed_state = last_state['compressed_state']
            complete_state = self._decompress_state(compressed_state)
            
            # Verify checksum
            checksum = self._calculate_checksum(complete_state)
            if checksum != last_state['checksum']:
                print("❌ Checksum verification failed")
                self.corrupted_states.append(last_state['_id'])
                return False
                
            # Restore all components
            success = self._restore_all_states(complete_state)
            
            if success:
                # Log successful recovery
                self._log_recovery_event('state_restored', {
                    'state_id': str(last_state['_id']),
                    'version': last_state['version'],
                    'timestamp': last_state['timestamp'].isoformat()
                })
                
                print(f"✅ State restored from {last_state['timestamp']}")
                return True
            else:
                print("❌ Failed to restore state components")
                
        except Exception as e:
            print(f"❌ Error loading state: {e}")
            self._log_recovery_event('recovery_failed', {
                'error': str(e),
                'attempt': self.recovery_attempts
            })
            
        return False
        
    def _collect_all_states(self) -> Dict[str, Any]:
        """Collect all system states"""
        complete_state = {}
        
        # Collect quantum brain state
        quantum_state = self._collect_quantum_state()
        if quantum_state:
            complete_state['quantum_brain'] = quantum_state
            
        # Collect neural weights
        neural_weights = self._collect_neural_weights()
        if neural_weights:
            complete_state['neural_weights'] = neural_weights
            
        # Collect memory context
        memory_context = self._collect_memory_context()
        if memory_context:
            complete_state['memory_context'] = memory_context
            
        # Collect learning progress
        learning_progress = self._collect_learning_progress()
        if learning_progress:
            complete_state['learning_progress'] = learning_progress
            
        # Collect evolution state
        evolution_state = self._collect_evolution_state()
        if evolution_state:
            complete_state['evolution_state'] = evolution_state
            
        # Collect trading state
        trading_state = self._collect_trading_state()
        if trading_state:
            complete_state['trading_state'] = trading_state
            
        return complete_state
        
    def _restore_all_states(self, complete_state: Dict[str, Any]) -> bool:
        """Restore all system states"""
        success_count = 0
        total_count = len(complete_state)
        
        # Restore quantum brain
        if 'quantum_brain' in complete_state:
            if self._restore_quantum_state(complete_state['quantum_brain']):
                success_count += 1
                print("  ✓ Quantum brain restored")
                
        # Restore neural weights
        if 'neural_weights' in complete_state:
            if self._restore_neural_weights(complete_state['neural_weights']):
                success_count += 1
                print("  ✓ Neural weights restored")
                
        # Restore memory context
        if 'memory_context' in complete_state:
            if self._restore_memory_context(complete_state['memory_context']):
                success_count += 1
                print("  ✓ Memory context restored")
                
        # Restore learning progress
        if 'learning_progress' in complete_state:
            if self._restore_learning_progress(complete_state['learning_progress']):
                success_count += 1
                print("  ✓ Learning progress restored")
                
        # Restore evolution state
        if 'evolution_state' in complete_state:
            if self._restore_evolution_state(complete_state['evolution_state']):
                success_count += 1
                print("  ✓ Evolution state restored")
                
        # Restore trading state
        if 'trading_state' in complete_state:
            if self._restore_trading_state(complete_state['trading_state']):
                success_count += 1
                print("  ✓ Trading state restored")
                
        return success_count == total_count
        
    def _collect_quantum_state(self) -> Optional[Dict]:
        """Collect quantum brain state"""
        try:
            if self.persistence is not None and self.persistence.db is not None:
                # Get latest quantum state
                quantum_doc = self.persistence.db.quantum_states.find_one(
                    {},
                    sort=[('timestamp', -1)]
                )
                
                if quantum_doc:
                    return {
                        'state_vector': quantum_doc.get('state_vector'),
                        'consciousness_level': quantum_doc.get('consciousness_level'),
                        'generation': quantum_doc.get('generation'),
                        'timestamp': quantum_doc.get('timestamp')
                    }
        except Exception as e:
            print(f"Error collecting quantum state: {e}")
            
        return None
        
    def _collect_neural_weights(self) -> Optional[Dict]:
        """Collect neural network weights"""
        try:
            if self.persistence is not None and self.persistence.db is not None:
                # Get all latest neural weights
                weights = {}
                
                for model_name in ['pattern_model', 'decision_model', 'rl_model']:
                    weight_doc = self.persistence.db.neural_weights.find_one(
                        {'model_name': model_name},
                        sort=[('version', -1)]
                    )
                    
                    if weight_doc:
                        weights[model_name] = {
                            'weights': weight_doc.get('weights'),
                            'version': weight_doc.get('version'),
                            'timestamp': weight_doc.get('timestamp')
                        }
                        
                return weights if weights else None
                
        except Exception as e:
            print(f"Error collecting neural weights: {e}")
            
        return None
        
    def _collect_memory_context(self) -> Optional[Dict]:
        """Collect memory context"""
        try:
            if self.persistence is not None and self.persistence.db is not None:
                # Get recent memories
                memories = list(self.persistence.db.brain_memories.find(
                    {},
                    limit=1000
                ).sort('timestamp', -1))
                
                if memories:
                    return {
                        'short_term': memories[:100],
                        'long_term': memories[100:],
                        'count': len(memories)
                    }
                    
        except Exception as e:
            print(f"Error collecting memory context: {e}")
            
        return None
        
    def _collect_learning_progress(self) -> Optional[Dict]:
        """Collect learning progress"""
        try:
            from brain.learning_feedback import get_learning_feedback
            feedback = get_learning_feedback()
            
            if feedback:
                return feedback.get_learning_metrics()
                
        except Exception as e:
            print(f"Error collecting learning progress: {e}")
            
        return None
        
    def _collect_evolution_state(self) -> Optional[Dict]:
        """Collect evolution state"""
        try:
            from brain.evolution_monitor import get_evolution_monitor
            monitor = get_evolution_monitor()
            
            if monitor:
                return monitor.get_evolution_summary()
                
        except Exception as e:
            print(f"Error collecting evolution state: {e}")
            
        return None
        
    def _collect_trading_state(self) -> Optional[Dict]:
        """Collect trading state"""
        try:
            from brain.decision_logger import get_decision_logger
            logger = get_decision_logger()
            
            if logger:
                return logger.get_statistics()
                
        except Exception as e:
            print(f"Error collecting trading state: {e}")
            
        return None
        
    def _restore_quantum_state(self, state_data: Dict) -> bool:
        """Restore quantum brain state"""
        try:
            from brain.quantum_brain_persistence import get_quantum_wrapper
            wrapper = get_quantum_wrapper()
            
            if wrapper and wrapper.brain:
                # Restore quantum state vector
                if 'state_vector' in state_data:
                    import pickle
                    import zlib
                    quantum_state = pickle.loads(zlib.decompress(state_data['state_vector']))
                    wrapper.brain.quantum_state = quantum_state
                    
                # Restore consciousness level
                if 'consciousness_level' in state_data:
                    wrapper.brain.consciousness_level = state_data['consciousness_level']
                    
                # Restore generation
                if 'generation' in state_data:
                    wrapper.brain.evolution_generation = state_data['generation']
                    
                return True
                
        except Exception as e:
            print(f"Error restoring quantum state: {e}")
            
        return False
        
    def _restore_neural_weights(self, weights_data: Dict) -> bool:
        """Restore neural network weights"""
        try:
            from brain.quantum_brain_persistence import get_quantum_wrapper
            wrapper = get_quantum_wrapper()
            
            if wrapper and wrapper.brain:
                import pickle
                import zlib
                
                for model_name, weight_info in weights_data.items():
                    if hasattr(wrapper.brain, model_name):
                        model = getattr(wrapper.brain, model_name)
                        weights = pickle.loads(zlib.decompress(weight_info['weights']))
                        
                        # Set weights based on framework
                        if hasattr(model, 'set_weights'):
                            model.set_weights(weights)
                        elif hasattr(model, 'load_state_dict'):
                            model.load_state_dict(weights)
                            
                return True
                
        except Exception as e:
            print(f"Error restoring neural weights: {e}")
            
        return False
        
    def _restore_memory_context(self, memory_data: Dict) -> bool:
        """Restore memory context"""
        try:
            from brain.memory_manager_enhanced import get_hybrid_memory_manager
            manager = get_hybrid_memory_manager()
            
            if manager:
                # Clear current memories
                manager.short_term_memory.clear()
                manager.memory_cache.clear()
                
                # Restore memories
                for memory in memory_data.get('short_term', []):
                    manager.short_term_memory.append(memory)
                    
                return True
                
        except Exception as e:
            print(f"Error restoring memory context: {e}")
            
        return False
        
    def _restore_learning_progress(self, learning_data: Dict) -> bool:
        """Restore learning progress"""
        try:
            from brain.learning_feedback import get_learning_feedback
            feedback = get_learning_feedback()
            
            if feedback:
                # Restore learning parameters
                feedback.current_learning_rate = learning_data.get('learning_rate', 0.001)
                feedback.exploration_rate = learning_data.get('exploration_rate', 0.1)
                feedback.consciousness_baseline = learning_data.get('consciousness_level', 0.5)
                
                return True
                
        except Exception as e:
            print(f"Error restoring learning progress: {e}")
            
        return False
        
    def _restore_evolution_state(self, evolution_data: Dict) -> bool:
        """Restore evolution state"""
        try:
            from brain.evolution_monitor import get_evolution_monitor
            monitor = get_evolution_monitor()
            
            if monitor:
                # Restore generation
                monitor.current_generation = evolution_data.get('current_generation', 1)
                
                return True
                
        except Exception as e:
            print(f"Error restoring evolution state: {e}")
            
        return False
        
    def _restore_trading_state(self, trading_data: Dict) -> bool:
        """Restore trading state"""
        try:
            from brain.decision_logger import get_decision_logger
            logger = get_decision_logger()
            
            if logger:
                # Restore statistics
                for key, value in trading_data.items():
                    if key in logger.decision_stats:
                        logger.decision_stats[key] = value
                        
                return True
                
        except Exception as e:
            print(f"Error restoring trading state: {e}")
            
        return False
        
    def _validate_complete_state(self, state: Dict) -> bool:
        """Validate complete system state"""
        if not state:
            return False
            
        # Validate each component
        for component, validator in self.validation_rules.items():
            if component in state:
                if not validator(state[component]):
                    print(f"  ✗ Validation failed for {component}")
                    return False
                    
        return True
        
    def _validate_quantum_state(self, state: Any) -> bool:
        """Validate quantum state"""
        return state is not None and isinstance(state, dict)
        
    def _validate_neural_weights(self, weights: Any) -> bool:
        """Validate neural weights"""
        return weights is not None and isinstance(weights, dict)
        
    def _validate_memory_context(self, memory: Any) -> bool:
        """Validate memory context"""
        return memory is not None and isinstance(memory, dict)
        
    def _validate_learning_progress(self, progress: Any) -> bool:
        """Validate learning progress"""
        return progress is not None and isinstance(progress, dict)
        
    def _compress_state(self, state: Dict) -> bytes:
        """Compress state for storage"""
        return zlib.compress(pickle.dumps(state))
        
    def _decompress_state(self, compressed: bytes) -> Dict:
        """Decompress state from storage"""
        return pickle.loads(zlib.decompress(compressed))
        
    def _calculate_checksum(self, state: Dict) -> str:
        """Calculate state checksum"""
        state_str = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(state_str.encode()).hexdigest()
        
    def _get_next_version(self) -> int:
        """Get next state version number"""
        if self.persistence is not None and self.persistence.db is not None:
            last_state = self.persistence.db.system_states.find_one(
                {},
                sort=[('version', -1)]
            )
            
            if last_state:
                return last_state['version'] + 1
                
        return 1
        
    def _log_recovery_event(self, event_type: str, details: Dict):
        """Log recovery event"""
        if self.persistence is not None and self.persistence.db is not None:
            try:
                self.persistence.db.recovery_logs.insert_one({
                    'timestamp': datetime.now(),
                    'event_type': event_type,
                    'details': details,
                    'recovery_attempts': self.recovery_attempts
                })
            except:
                pass
                
        # Add to history
        self.recovery_history.append({
            'timestamp': datetime.now(),
            'event_type': event_type,
            'details': details
        })
        
    def graceful_shutdown(self):
        """Perform graceful shutdown with state save"""
        if self.emergency_save_triggered:
            return  # Avoid duplicate saves
            
        self.emergency_save_triggered = True
        print("\n🛑 Initiating graceful shutdown...")
        
        # Stop auto-save thread
        self.running = False
        
        # Save final state
        self.save_complete_state(state_type="shutdown")
        
        # Run custom shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                handler()
            except Exception as e:
                print(f"Error in shutdown handler: {e}")
                
        print("✅ Graceful shutdown complete")
        
    def register_shutdown_handler(self, handler):
        """Register custom shutdown handler"""
        self.shutdown_handlers.append(handler)
        
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get current recovery system status"""
        return {
            'last_save': self.last_save.isoformat() if self.last_save else None,
            'recovery_attempts': self.recovery_attempts,
            'corrupted_states': len(self.corrupted_states),
            'auto_save_enabled': self.auto_save_enabled,
            'state_versions': len(self.state_versions),
            'last_valid_state': str(self.last_valid_state) if self.last_valid_state else None
        }


# Global instance
_state_recovery = None

def get_state_recovery():
    """Get or create state recovery system"""
    global _state_recovery
    if _state_recovery is None:
        _state_recovery = StateRecoverySystem()
    return _state_recovery

# Helper functions
def save_system_state(state_type: str = "manual"):
    """Save complete system state"""
    recovery = get_state_recovery()
    return recovery.save_complete_state(state_type)

def restore_system_state():
    """Restore system from last state"""
    recovery = get_state_recovery()
    return recovery.load_last_state()

def enable_auto_save(enabled: bool = True):
    """Enable or disable auto-save"""
    recovery = get_state_recovery()
    recovery.auto_save_enabled = enabled

def get_recovery_status():
    """Get recovery system status"""
    recovery = get_state_recovery()
    return recovery.get_recovery_status()
