"""
MongoDB Persistence Service for AuraQuant Trading System
Engineer's Note: This module ADDS MongoDB persistence to the existing system
WITHOUT modifying any existing code. It works as a companion service.
"""

import os
import sys
import json
import pickle
import zlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import hashlib
from dotenv import load_dotenv

# Add parent directory to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import config
except ImportError:
    config = None

# Try to import numpy, but make it optional
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("⚠️ NumPy not available - some features will be limited")

# MongoDB imports
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import motor.motor_asyncio

# Load environment
load_dotenv()

class MongoDBPersistence:
    """
    MongoDB persistence layer that runs alongside the existing system
    Captures and saves all learning data without modifying existing code
    """
    
    def __init__(self):
        """Initialize MongoDB persistence service"""
        # Get MongoDB URI from config or environment
        if config:
            self.mongodb_uri = config.MONGODB_URI
        else:
            self.mongodb_uri = os.getenv("MONGO_URI", os.getenv("MONGODB_URI"))
        
        # Initialize connections
        self.sync_client = None
        self.async_client = None
        self.db = None
        self.async_db = None
        
        # Memory buffers for batch operations
        self.memory_buffer = []
        self.buffer_size = 100
        self.last_flush = datetime.now()
        self.flush_interval = timedelta(seconds=30)
        
        # Initialize MongoDB connection
        self._connect_mongodb()
        
        # Start background tasks
        self.running = True
        
    def _connect_mongodb(self):
        """Establish MongoDB connection"""
        try:
            # Synchronous client
            self.sync_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            self.sync_client.admin.command('ping')
            
            # Asynchronous client
            self.async_client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_uri)
            
            # Database references
            self.db = self.sync_client['auraquant']
            self.async_db = self.async_client['auraquant']
            
            # Create collections if they don't exist
            self._setup_collections()
            
            print("✅ MongoDB Persistence Service Connected")
            
        except Exception as e:
            print(f"⚠️ MongoDB connection failed, running without persistence: {e}")
            
    def _setup_collections(self):
        """Setup MongoDB collections with indexes"""
        if self.db is None:
            return
            
        # Define collections and their indexes
        collections_config = {
            'brain_memories': [
                ('timestamp', DESCENDING),
                ('memory_type', ASCENDING),
                ('pattern_hash', ASCENDING)
            ],
            'evolution_states': [
                ('generation', DESCENDING),
                ('fitness_score', DESCENDING),
                ('timestamp', DESCENDING)
            ],
            'quantum_states': [
                ('timestamp', DESCENDING),
                ('consciousness_level', DESCENDING)
            ],
            'trading_decisions': [
                ('timestamp', DESCENDING),
                ('symbol', ASCENDING),
                ('confidence', DESCENDING),
                ('outcome', DESCENDING)
            ],
            'learned_patterns': [
                ('pattern_id', ASCENDING),
                ('success_rate', DESCENDING),
                ('last_seen', DESCENDING)
            ],
            'neural_weights': [
                ('model_name', ASCENDING),
                ('version', DESCENDING),
                ('timestamp', DESCENDING)
            ],
            'performance_metrics': [
                ('metric_type', ASCENDING),
                ('timestamp', DESCENDING)
            ]
        }
        
        # Create collections and indexes
        for collection_name, indexes in collections_config.items():
            collection = self.db[collection_name]
            for index in indexes:
                try:
                    if isinstance(index, tuple):
                        collection.create_index([(index[0], index[1])])
                    else:
                        collection.create_index(index)
                except Exception as e:
                    pass  # Index might already exist
                    
        print(f"📊 MongoDB collections configured: {list(collections_config.keys())}")
        
    async def save_memory_async(self, memory_type: str, data: Dict[str, Any]):
        """
        Asynchronously save memory to MongoDB
        
        Args:
            memory_type: Type of memory (trade, pattern, evolution, etc.)
            data: Memory data to save
        """
        if self.async_db is None:
            return
            
        try:
            document = {
                'timestamp': datetime.now(),
                'memory_type': memory_type,
                'data': data,
                'pattern_hash': self._generate_hash(data)
            }
            
            await self.async_db.brain_memories.insert_one(document)
            
        except Exception as e:
            print(f"Error saving memory: {e}")
            
    def save_quantum_state(self, quantum_state, consciousness_level: float, 
                          generation: int):
        """
        Save quantum brain state to MongoDB
        
        Args:
            quantum_state: Numpy array representing quantum state
            consciousness_level: Current consciousness level
            generation: Evolution generation number
        """
        if self.db is None:
            return
            
        try:
            # Compress quantum state for efficient storage
            compressed_state = zlib.compress(pickle.dumps(quantum_state))
            
            document = {
                'timestamp': datetime.now(),
                'generation': generation,
                'consciousness_level': consciousness_level,
                'state_vector': compressed_state,
                'state_size': len(quantum_state),
                'state_hash': hashlib.md5(quantum_state.tobytes()).hexdigest()
            }
            
            self.db.quantum_states.insert_one(document)
            
        except Exception as e:
            print(f"Error saving quantum state: {e}")
            
    def save_evolution_checkpoint(self, generation: int, fitness_score: float, 
                                 neural_weights: Dict, mutations: List[str]):
        """
        Save evolution checkpoint to MongoDB
        
        Args:
            generation: Evolution generation number
            fitness_score: Current fitness score
            neural_weights: Dictionary of neural network weights
            mutations: List of mutations applied
        """
        if self.db is None:
            return
            
        try:
            # Compress neural weights
            compressed_weights = zlib.compress(pickle.dumps(neural_weights))
            
            document = {
                'timestamp': datetime.now(),
                'generation': generation,
                'fitness_score': fitness_score,
                'neural_weights': compressed_weights,
                'mutations': mutations,
                'weights_hash': self._generate_hash(neural_weights)
            }
            
            self.db.evolution_states.insert_one(document)
            print(f"💾 Evolution checkpoint saved: Gen {generation}, Fitness {fitness_score:.4f}")
            
        except Exception as e:
            print(f"Error saving evolution checkpoint: {e}")
            
    def save_trading_decision(self, symbol: str, action: str, confidence: float, 
                            market_data: Dict, neural_activations: Dict = None):
        """
        Save trading decision to MongoDB
        
        Args:
            symbol: Trading symbol
            action: Trading action (buy/sell/hold)
            confidence: Decision confidence score
            market_data: Market conditions at decision time
            neural_activations: Neural network activation patterns
        """
        if self.db is None:
            return
            
        try:
            document = {
                'timestamp': datetime.now(),
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'market_data': market_data,
                'neural_activations': neural_activations,
                'outcome': None  # To be updated with actual outcome
            }
            
            result = self.db.trading_decisions.insert_one(document)
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"Error saving trading decision: {e}")
            return None
            
    def update_decision_outcome(self, decision_id: str, outcome: float, actual_price: float):
        """
        Update trading decision with actual outcome
        
        Args:
            decision_id: MongoDB ObjectId of the decision
            outcome: Profit/loss outcome
            actual_price: Actual execution price
        """
        if self.db is None:
            return
            
        try:
            from bson.objectid import ObjectId
            
            self.db.trading_decisions.update_one(
                {'_id': ObjectId(decision_id)},
                {
                    '$set': {
                        'outcome': outcome,
                        'actual_price': actual_price,
                        'outcome_timestamp': datetime.now()
                    }
                }
            )
            
        except Exception as e:
            print(f"Error updating decision outcome: {e}")
            
    def save_learned_pattern(self, pattern_id: str, pattern_data: Dict, 
                           success_rate: float, occurrences: int):
        """
        Save or update learned pattern in MongoDB
        
        Args:
            pattern_id: Unique pattern identifier
            pattern_data: Pattern characteristics
            success_rate: Pattern success rate
            occurrences: Number of times pattern observed
        """
        if self.db is None:
            return
            
        try:
            document = {
                'pattern_id': pattern_id,
                'pattern_data': pattern_data,
                'success_rate': success_rate,
                'occurrences': occurrences,
                'last_seen': datetime.now(),
                'first_seen': datetime.now()
            }
            
            # Upsert pattern (update if exists, insert if new)
            self.db.learned_patterns.update_one(
                {'pattern_id': pattern_id},
                {
                    '$set': {
                        'pattern_data': pattern_data,
                        'success_rate': success_rate,
                        'last_seen': datetime.now()
                    },
                    '$inc': {'occurrences': 1},
                    '$setOnInsert': {'first_seen': datetime.now()}
                },
                upsert=True
            )
            
        except Exception as e:
            print(f"Error saving learned pattern: {e}")
            
    def save_neural_weights(self, model_name: str, weights: Any, version: int):
        """
        Save neural network weights to MongoDB
        
        Args:
            model_name: Name of the neural network model
            weights: Model weights (numpy arrays or tensors)
            version: Model version number
        """
        if self.db is None:
            return
            
        try:
            # Compress weights for storage
            compressed_weights = zlib.compress(pickle.dumps(weights))
            
            document = {
                'timestamp': datetime.now(),
                'model_name': model_name,
                'version': version,
                'weights': compressed_weights,
                'weights_size': len(compressed_weights),
                'weights_hash': self._generate_hash(weights)
            }
            
            self.db.neural_weights.insert_one(document)
            print(f"🧠 Neural weights saved: {model_name} v{version}")
            
        except Exception as e:
            print(f"Error saving neural weights: {e}")
            
    def load_latest_quantum_state(self, generation: int = None):
        """
        Load the latest quantum state from MongoDB
        
        Args:
            generation: Optional specific generation to load
            
        Returns:
            Tuple of (quantum_state, consciousness_level, generation)
        """
        if self.db is None:
            return None, None, None
            
        try:
            query = {'generation': generation} if generation else {}
            
            document = self.db.quantum_states.find_one(
                query,
                sort=[('timestamp', DESCENDING)]
            )
            
            if document:
                quantum_state = pickle.loads(zlib.decompress(document['state_vector']))
                return (
                    quantum_state,
                    document['consciousness_level'],
                    document['generation']
                )
                
        except Exception as e:
            print(f"Error loading quantum state: {e}")
            
        return None, None, None
        
    def load_latest_neural_weights(self, model_name: str):
        """
        Load the latest neural network weights from MongoDB
        
        Args:
            model_name: Name of the model
            
        Returns:
            Loaded weights or None
        """
        if self.db is None:
            return None
            
        try:
            document = self.db.neural_weights.find_one(
                {'model_name': model_name},
                sort=[('version', DESCENDING)]
            )
            
            if document:
                weights = pickle.loads(zlib.decompress(document['weights']))
                print(f"✅ Loaded weights: {model_name} v{document['version']}")
                return weights
                
        except Exception as e:
            print(f"Error loading neural weights: {e}")
            
        return None
        
    def get_performance_metrics(self, days: int = 7):
        """
        Get performance metrics from MongoDB
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of performance metrics
        """
        if self.db is None:
            return []
            
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            metrics = list(self.db.trading_decisions.aggregate([
                {'$match': {'timestamp': {'$gte': cutoff_date}}},
                {'$group': {
                    '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$timestamp'}},
                    'total_decisions': {'$sum': 1},
                    'avg_confidence': {'$avg': '$confidence'},
                    'successful': {
                        '$sum': {'$cond': [{'$gt': ['$outcome', 0]}, 1, 0]}
                    }
                }},
                {'$sort': {'_id': 1}}
            ]))
            
            return metrics
            
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return []
            
    def _generate_hash(self, data: Any) -> str:
        """Generate hash for data"""
        try:
            if isinstance(data, dict):
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            return hashlib.md5(data_str.encode()).hexdigest()
        except:
            return hashlib.md5(str(data).encode()).hexdigest()
            
    async def flush_memory_buffer(self):
        """Flush memory buffer to MongoDB"""
        if self.async_db is None or not self.memory_buffer:
            return
            
        try:
            await self.async_db.brain_memories.insert_many(self.memory_buffer)
            buffer_size = len(self.memory_buffer)
            self.memory_buffer.clear()
            self.last_flush = datetime.now()
            print(f"💾 Flushed {buffer_size} memories to MongoDB")
            
        except Exception as e:
            print(f"Error flushing memory buffer: {e}")
            
    async def background_sync(self):
        """Background task for periodic synchronization"""
        while self.running:
            try:
                # Check if flush is needed
                if (datetime.now() - self.last_flush) > self.flush_interval:
                    await self.flush_memory_buffer()
                    
                # Sleep for a short interval
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Background sync error: {e}")
                await asyncio.sleep(10)
                
    def check_connection(self) -> bool:
        """Check if MongoDB is connected"""
        try:
            if self.sync_client is not None:
                self.sync_client.admin.command('ping')
                return True
        except:
            pass
        return False
        
    def close(self):
        """Close MongoDB connections"""
        self.running = False
        if self.sync_client:
            self.sync_client.close()
        print("MongoDB Persistence Service closed")

# Global instance
_persistence_service = None

def get_persistence_service():
    """Get or create persistence service instance"""
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = MongoDBPersistence()
    return _persistence_service

# Helper functions for easy integration
def save_memory(memory_type: str, data: Dict):
    """Save memory to MongoDB"""
    service = get_persistence_service()
    if service and service.db:
        asyncio.create_task(service.save_memory_async(memory_type, data))

def save_quantum_state(quantum_state, consciousness: float, generation: int):
    """Save quantum state to MongoDB"""
    service = get_persistence_service()
    if service:
        service.save_quantum_state(quantum_state, consciousness, generation)

def save_trading_decision(symbol: str, action: str, confidence: float, market_data: Dict):
    """Save trading decision to MongoDB"""
    service = get_persistence_service()
    if service:
        return service.save_trading_decision(symbol, action, confidence, market_data)

def save_evolution_checkpoint(generation: int, fitness: float, weights: Dict, mutations: List):
    """Save evolution checkpoint to MongoDB"""
    service = get_persistence_service()
    if service:
        service.save_evolution_checkpoint(generation, fitness, weights, mutations)