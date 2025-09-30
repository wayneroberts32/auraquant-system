"""
AuraQuant Quantum Brain - Self-Learning Trading Intelligence
Professor's Note: This implements neural plasticity with quantum-inspired learning algorithms
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
import asyncio
from dataclasses import dataclass, asdict
import pickle
import zlib

# MongoDB integration
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
import motor.motor_asyncio

# Machine Learning components
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
import torch
import torch.nn as nn
import torch.optim as optim

# Technical Analysis
import talib
import yfinance as yf

@dataclass
class NeuralMemory:
    """Represents a single memory unit in the quantum brain"""
    timestamp: datetime
    pattern_hash: str
    market_state: Dict[str, float]
    action_taken: str
    outcome: float
    confidence: float
    learning_rate: float
    evolution_generation: int
    neural_weights: bytes  # Compressed neural network weights
    
class QuantumBrain:
    """
    Self-evolving AI brain with quantum-inspired learning capabilities
    Implements neuroplasticity and continuous learning
    """
    
    def __init__(self, mongodb_uri: str = "mongodb://localhost:27017/"):
        """
        Initialize the Quantum Brain with MongoDB connection
        
        Args:
            mongodb_uri: MongoDB connection string
        """
        self.mongodb_uri = mongodb_uri
        self.evolution_generation = 1
        self.learning_rate = 0.001
        self.quantum_state = np.random.random(1024)  # Quantum state vector
        self.consciousness_level = 0.5  # Self-awareness metric
        
        # Initialize MongoDB connections
        self._init_mongodb()
        
        # Initialize neural networks
        self._init_neural_networks()
        
        # Initialize memory banks
        self.short_term_memory = []
        self.long_term_memory = []
        self.episodic_memory = {}
        
        # Performance tracking
        self.performance_history = []
        self.adaptation_threshold = 0.7
        
        # Quantum entanglement simulation for pattern recognition
        self.entangled_patterns = {}
        
        print(f"🧠 Quantum Brain initialized - Generation {self.evolution_generation}")
        
    def _init_mongodb(self):
        """Initialize MongoDB connections for memory persistence"""
        try:
            # Synchronous client for initial setup
            self.mongo_client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ping')
            
            # Async client for runtime operations
            self.async_mongo_client = motor.motor_asyncio.AsyncIOMotorClient(self.mongodb_uri)
            
            # Database and collections
            self.db = self.mongo_client['auraquant_brain']
            self.async_db = self.async_mongo_client['auraquant_brain']
            
            # Collections
            self.memories_collection = self.db['memories']
            self.patterns_collection = self.db['patterns']
            self.evolution_collection = self.db['evolution']
            self.performance_collection = self.db['performance']
            
            # Async collections
            self.async_memories = self.async_db['memories']
            self.async_patterns = self.async_db['patterns']
            
            # Create indexes for optimal performance
            self._create_indexes()
            
            print("✅ MongoDB connection established")
            
        except ConnectionFailure as e:
            print(f"⚠️ MongoDB connection failed. Running in local mode: {e}")
            self.mongo_client = None
            self.async_mongo_client = None
            
    def _create_indexes(self):
        """Create MongoDB indexes for optimal query performance"""
        if self.mongo_client:
            # Memory indexes
            self.memories_collection.create_index([("timestamp", DESCENDING)])
            self.memories_collection.create_index([("pattern_hash", ASCENDING)])
            self.memories_collection.create_index([("outcome", DESCENDING)])
            
            # Pattern indexes
            self.patterns_collection.create_index([("frequency", DESCENDING)])
            self.patterns_collection.create_index([("success_rate", DESCENDING)])
            
            # Evolution indexes
            self.evolution_collection.create_index([("generation", DESCENDING)])
            self.evolution_collection.create_index([("fitness_score", DESCENDING)])
            
    def _init_neural_networks(self):
        """Initialize the multi-layer neural network architecture"""
        
        # TensorFlow/Keras model for pattern recognition
        self.pattern_model = self._build_pattern_recognition_model()
        
        # PyTorch model for decision making
        self.decision_model = self._build_decision_model()
        
        # Reinforcement learning model
        self.rl_model = self._build_rl_model()
        
        # Compile models
        self.pattern_model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae', 'accuracy']
        )
        
    def _build_pattern_recognition_model(self) -> Model:
        """Build deep neural network for pattern recognition"""
        inputs = keras.Input(shape=(100, 15))  # 100 time steps, 15 features
        
        # LSTM layers for temporal patterns
        x = layers.LSTM(128, return_sequences=True)(inputs)
        x = layers.Dropout(0.2)(x)
        x = layers.LSTM(64, return_sequences=True)(x)
        x = layers.Dropout(0.2)(x)
        x = layers.LSTM(32)(x)
        
        # Dense layers for decision
        x = layers.Dense(64, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dense(32, activation='relu')(x)
        
        # Output layers
        pattern_output = layers.Dense(10, activation='softmax', name='pattern')(x)
        confidence_output = layers.Dense(1, activation='sigmoid', name='confidence')(x)
        
        model = Model(inputs=inputs, outputs=[pattern_output, confidence_output])
        return model
        
    def _build_decision_model(self) -> nn.Module:
        """Build PyTorch model for trading decisions"""
        class DecisionNetwork(nn.Module):
            def __init__(self):
                super(DecisionNetwork, self).__init__()
                self.fc1 = nn.Linear(50, 256)
                self.fc2 = nn.Linear(256, 128)
                self.fc3 = nn.Linear(128, 64)
                self.fc4 = nn.Linear(64, 32)
                self.output = nn.Linear(32, 3)  # Buy, Sell, Hold
                self.dropout = nn.Dropout(0.2)
                self.relu = nn.ReLU()
                self.softmax = nn.Softmax(dim=1)
                
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.relu(self.fc2(x))
                x = self.dropout(x)
                x = self.relu(self.fc3(x))
                x = self.relu(self.fc4(x))
                x = self.softmax(self.output(x))
                return x
                
        return DecisionNetwork()
        
    def _build_rl_model(self) -> Model:
        """Build reinforcement learning model for strategy optimization"""
        state_input = keras.Input(shape=(30,))
        
        # Actor network
        actor = layers.Dense(128, activation='relu')(state_input)
        actor = layers.Dense(64, activation='relu')(actor)
        actor_output = layers.Dense(3, activation='softmax')(actor)
        
        # Critic network
        critic = layers.Dense(128, activation='relu')(state_input)
        critic = layers.Dense(64, activation='relu')(critic)
        critic_output = layers.Dense(1)(critic)
        
        model = Model(inputs=state_input, outputs=[actor_output, critic_output])
        return model
        
    async def learn_from_market(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Learn from market data and evolve understanding
        
        Args:
            market_data: DataFrame with OHLCV data
            
        Returns:
            Learning insights and predictions
        """
        # Extract features
        features = self._extract_features(market_data)
        
        # Detect patterns
        patterns = await self._detect_patterns(features)
        
        # Update quantum state
        self._update_quantum_state(patterns)
        
        # Make prediction
        prediction = self._make_prediction(features)
        
        # Store in memory
        memory = NeuralMemory(
            timestamp=datetime.now(),
            pattern_hash=self._hash_pattern(patterns),
            market_state=features[-1].to_dict() if len(features) > 0 else {},
            action_taken=prediction['action'],
            outcome=0.0,  # Will be updated later
            confidence=prediction['confidence'],
            learning_rate=self.learning_rate,
            evolution_generation=self.evolution_generation,
            neural_weights=self._compress_weights()
        )
        
        # Store in MongoDB
        await self._store_memory(memory)
        
        # Evolve if necessary
        if self.consciousness_level > self.adaptation_threshold:
            await self._evolve()
            
        return {
            'prediction': prediction,
            'patterns': patterns,
            'consciousness_level': self.consciousness_level,
            'generation': self.evolution_generation
        }
        
    def _extract_features(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Extract technical indicators and features from market data"""
        features = pd.DataFrame()
        
        # Price features
        features['returns'] = market_data['Close'].pct_change()
        features['log_returns'] = np.log(market_data['Close'] / market_data['Close'].shift(1))
        features['volume_ratio'] = market_data['Volume'] / market_data['Volume'].rolling(20).mean()
        
        # Technical indicators
        features['rsi'] = talib.RSI(market_data['Close'])
        features['macd'], features['macd_signal'], _ = talib.MACD(market_data['Close'])
        features['bb_upper'], features['bb_middle'], features['bb_lower'] = talib.BBANDS(market_data['Close'])
        features['atr'] = talib.ATR(market_data['High'], market_data['Low'], market_data['Close'])
        features['adx'] = talib.ADX(market_data['High'], market_data['Low'], market_data['Close'])
        
        # Candlestick patterns
        features['doji'] = talib.CDLDOJI(market_data['Open'], market_data['High'], 
                                         market_data['Low'], market_data['Close'])
        features['hammer'] = talib.CDLHAMMER(market_data['Open'], market_data['High'],
                                             market_data['Low'], market_data['Close'])
        features['engulfing'] = talib.CDLENGULFING(market_data['Open'], market_data['High'],
                                                   market_data['Low'], market_data['Close'])
        
        # Market microstructure
        features['spread'] = market_data['High'] - market_data['Low']
        features['volatility'] = features['returns'].rolling(20).std()
        features['skew'] = features['returns'].rolling(20).skew()
        features['kurtosis'] = features['returns'].rolling(20).kurt()
        
        return features.dropna()
        
    async def _detect_patterns(self, features: pd.DataFrame) -> List[Dict]:
        """Detect trading patterns using neural networks"""
        if len(features) < 100:
            return []
            
        # Prepare input
        X = features.tail(100).values.reshape(1, 100, -1)
        
        # Get predictions from pattern model
        patterns, confidence = self.pattern_model.predict(X, verbose=0)
        
        # Decode patterns
        detected_patterns = []
        pattern_types = ['Breakout', 'Reversal', 'Continuation', 'Consolidation', 
                        'Triangle', 'Channel', 'Head&Shoulders', 'DoubleTop',
                        'DoubleBottom', 'Flag']
                        
        for i, prob in enumerate(patterns[0]):
            if prob > 0.3:  # Confidence threshold
                pattern = {
                    'type': pattern_types[i],
                    'probability': float(prob),
                    'confidence': float(confidence[0][0]),
                    'timestamp': datetime.now().isoformat()
                }
                detected_patterns.append(pattern)
                
                # Store pattern in MongoDB
                if self.async_mongo_client:
                    await self.async_patterns.insert_one(pattern)
                    
        return detected_patterns
        
    def _update_quantum_state(self, patterns: List[Dict]):
        """Update quantum state based on detected patterns"""
        if patterns:
            # Quantum superposition of pattern states
            pattern_vector = np.zeros(1024)
            for pattern in patterns:
                # Hash pattern to quantum position
                hash_val = int(hashlib.md5(pattern['type'].encode()).hexdigest()[:8], 16)
                position = hash_val % 1024
                pattern_vector[position] = pattern['probability']
                
            # Quantum interference
            self.quantum_state = 0.9 * self.quantum_state + 0.1 * pattern_vector
            
            # Normalize (quantum state normalization)
            norm = np.linalg.norm(self.quantum_state)
            if norm > 0:
                self.quantum_state /= norm
                
            # Update consciousness level
            self.consciousness_level = min(1.0, self.consciousness_level + 0.01)
            
    def _make_prediction(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Make trading prediction using ensemble of models"""
        if len(features) < 50:
            return {'action': 'HOLD', 'confidence': 0.0, 'reasoning': 'Insufficient data'}
            
        # Prepare input
        X = torch.FloatTensor(features.tail(50).values.flatten().reshape(1, -1))
        
        # Get decision from PyTorch model
        with torch.no_grad():
            decision_probs = self.decision_model(X).numpy()[0]
            
        actions = ['BUY', 'SELL', 'HOLD']
        action_idx = np.argmax(decision_probs)
        
        # Get reinforcement learning suggestion
        rl_input = features.tail(30).values.flatten().reshape(1, -1)
        rl_action, rl_value = self.rl_model.predict(rl_input, verbose=0)
        
        # Ensemble decision
        final_confidence = (decision_probs[action_idx] + rl_action[0][action_idx]) / 2
        
        # Quantum adjustment
        quantum_factor = np.mean(self.quantum_state[:10])
        final_confidence *= (1 + quantum_factor * 0.1)
        
        return {
            'action': actions[action_idx],
            'confidence': float(min(1.0, final_confidence)),
            'reasoning': self._generate_reasoning(features, patterns=None),
            'quantum_influence': float(quantum_factor),
            'consciousness_level': float(self.consciousness_level)
        }
        
    def _generate_reasoning(self, features: pd.DataFrame, patterns: Optional[List] = None) -> str:
        """Generate human-readable reasoning for decisions"""
        reasoning_parts = []
        
        # Technical analysis reasoning
        last_row = features.iloc[-1]
        
        if 'rsi' in last_row:
            rsi_val = last_row['rsi']
            if rsi_val > 70:
                reasoning_parts.append(f"RSI overbought at {rsi_val:.2f}")
            elif rsi_val < 30:
                reasoning_parts.append(f"RSI oversold at {rsi_val:.2f}")
                
        if 'macd' in last_row and 'macd_signal' in last_row:
            if last_row['macd'] > last_row['macd_signal']:
                reasoning_parts.append("MACD bullish crossover")
            else:
                reasoning_parts.append("MACD bearish signal")
                
        # Pattern reasoning
        if patterns:
            pattern_names = [p['type'] for p in patterns[:3]]
            reasoning_parts.append(f"Patterns detected: {', '.join(pattern_names)}")
            
        # Quantum state reasoning
        if self.consciousness_level > 0.8:
            reasoning_parts.append(f"High confidence from quantum analysis")
            
        return " | ".join(reasoning_parts) if reasoning_parts else "Standard market conditions"
        
    def _hash_pattern(self, patterns: List[Dict]) -> str:
        """Generate unique hash for pattern combination"""
        pattern_str = json.dumps(sorted([p['type'] for p in patterns]))
        return hashlib.sha256(pattern_str.encode()).hexdigest()
        
    def _compress_weights(self) -> bytes:
        """Compress neural network weights for storage"""
        weights = {}
        
        # TensorFlow weights
        weights['pattern_model'] = [w.tolist() for w in self.pattern_model.get_weights()]
        
        # PyTorch weights
        weights['decision_model'] = {
            name: param.detach().numpy().tolist() 
            for name, param in self.decision_model.named_parameters()
        }
        
        # Compress
        weights_json = json.dumps(weights)
        compressed = zlib.compress(weights_json.encode())
        
        return compressed
        
    async def _store_memory(self, memory: NeuralMemory):
        """Store memory in MongoDB"""
        if self.async_mongo_client:
            memory_dict = asdict(memory)
            memory_dict['timestamp'] = memory.timestamp
            memory_dict['neural_weights'] = memory.neural_weights
            
            await self.async_memories.insert_one(memory_dict)
            
        # Also store in local memory
        self.short_term_memory.append(memory)
        
        # Move old memories to long term
        if len(self.short_term_memory) > 100:
            self.long_term_memory.extend(self.short_term_memory[:50])
            self.short_term_memory = self.short_term_memory[50:]
            
    async def _evolve(self):
        """Evolve the brain to next generation"""
        print(f"🧬 Evolving to Generation {self.evolution_generation + 1}")
        
        # Calculate fitness score
        fitness = self._calculate_fitness()
        
        # Store evolution record
        if self.mongo_client:
            evolution_record = {
                'generation': self.evolution_generation,
                'timestamp': datetime.now(),
                'fitness_score': fitness,
                'consciousness_level': self.consciousness_level,
                'quantum_state_hash': hashlib.sha256(self.quantum_state.tobytes()).hexdigest(),
                'neural_weights': self._compress_weights()
            }
            self.evolution_collection.insert_one(evolution_record)
            
        # Mutate neural networks
        self._mutate_networks()
        
        # Update generation
        self.evolution_generation += 1
        
        # Adjust learning rate
        self.learning_rate *= 0.99  # Decay learning rate
        
        print(f"✅ Evolution complete. Fitness: {fitness:.4f}")
        
    def _calculate_fitness(self) -> float:
        """Calculate fitness score based on recent performance"""
        if not self.short_term_memory:
            return 0.5
            
        # Calculate average outcome
        outcomes = [m.outcome for m in self.short_term_memory if m.outcome != 0]
        if not outcomes:
            return 0.5
            
        avg_outcome = np.mean(outcomes)
        avg_confidence = np.mean([m.confidence for m in self.short_term_memory])
        
        # Fitness combines performance and confidence
        fitness = (avg_outcome + 1) / 2 * 0.7 + avg_confidence * 0.3
        
        return float(np.clip(fitness, 0, 1))
        
    def _mutate_networks(self):
        """Apply genetic mutations to neural networks"""
        # Mutate TensorFlow model
        weights = self.pattern_model.get_weights()
        for i in range(len(weights)):
            if np.random.random() < 0.1:  # 10% mutation rate
                mutation = np.random.normal(0, 0.01, weights[i].shape)
                weights[i] += mutation
        self.pattern_model.set_weights(weights)
        
        # Mutate PyTorch model
        with torch.no_grad():
            for param in self.decision_model.parameters():
                if np.random.random() < 0.1:
                    mutation = torch.randn_like(param) * 0.01
                    param.add_(mutation)
                    
    async def recall_memory(self, pattern_hash: str) -> Optional[NeuralMemory]:
        """Recall specific memory from MongoDB"""
        if self.async_mongo_client:
            memory_doc = await self.async_memories.find_one({'pattern_hash': pattern_hash})
            if memory_doc:
                return NeuralMemory(**memory_doc)
        return None
        
    async def get_trading_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive trading recommendation for a symbol"""
        # Fetch market data
        ticker = yf.Ticker(symbol)
        market_data = ticker.history(period="3mo")
        
        if market_data.empty:
            return {
                'symbol': symbol,
                'recommendation': 'NO_DATA',
                'confidence': 0.0,
                'error': 'Unable to fetch market data'
            }
            
        # Learn and predict
        insights = await self.learn_from_market(market_data)
        
        # Fetch similar historical patterns
        similar_patterns = []
        if self.async_mongo_client and insights['patterns']:
            pattern_hash = self._hash_pattern(insights['patterns'])
            cursor = self.async_memories.find({'pattern_hash': pattern_hash}).limit(5)
            async for doc in cursor:
                similar_patterns.append({
                    'timestamp': doc['timestamp'],
                    'outcome': doc['outcome'],
                    'confidence': doc['confidence']
                })
                
        return {
            'symbol': symbol,
            'recommendation': insights['prediction']['action'],
            'confidence': insights['prediction']['confidence'],
            'reasoning': insights['prediction']['reasoning'],
            'patterns': insights['patterns'],
            'consciousness_level': insights['consciousness_level'],
            'generation': insights['generation'],
            'similar_historical_patterns': similar_patterns,
            'quantum_influence': insights['prediction'].get('quantum_influence', 0)
        }
        
    def save_brain_state(self, filepath: str):
        """Save complete brain state to disk"""
        brain_state = {
            'generation': self.evolution_generation,
            'learning_rate': self.learning_rate,
            'consciousness_level': self.consciousness_level,
            'quantum_state': self.quantum_state.tolist(),
            'pattern_model_weights': [w.tolist() for w in self.pattern_model.get_weights()],
            'decision_model_state': self.decision_model.state_dict(),
            'short_term_memory': [asdict(m) for m in self.short_term_memory[-50:]],
            'timestamp': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(brain_state, f)
            
        print(f"💾 Brain state saved to {filepath}")
        
    def load_brain_state(self, filepath: str):
        """Load brain state from disk"""
        with open(filepath, 'rb') as f:
            brain_state = pickle.load(f)
            
        self.evolution_generation = brain_state['generation']
        self.learning_rate = brain_state['learning_rate']
        self.consciousness_level = brain_state['consciousness_level']
        self.quantum_state = np.array(brain_state['quantum_state'])
        
        # Restore neural network weights
        self.pattern_model.set_weights([np.array(w) for w in brain_state['pattern_model_weights']])
        self.decision_model.load_state_dict(brain_state['decision_model_state'])
        
        print(f"🧠 Brain state loaded from {filepath}")
        
    async def sync_to_mongodb(self):
        """Sync all local memories to MongoDB"""
        if not self.async_mongo_client:
            print("⚠️ MongoDB not connected")
            return
            
        # Sync short term memories
        for memory in self.short_term_memory:
            memory_dict = asdict(memory)
            await self.async_memories.update_one(
                {'pattern_hash': memory.pattern_hash, 'timestamp': memory.timestamp},
                {'$set': memory_dict},
                upsert=True
            )
            
        # Sync long term memories
        for memory in self.long_term_memory:
            memory_dict = asdict(memory)
            await self.async_memories.update_one(
                {'pattern_hash': memory.pattern_hash, 'timestamp': memory.timestamp},
                {'$set': memory_dict},
                upsert=True
            )
            
        print(f"✅ Synced {len(self.short_term_memory) + len(self.long_term_memory)} memories to MongoDB")

# Example usage
async def main():
    """Example usage of the Quantum Brain"""
    
    # Initialize brain
    brain = QuantumBrain(mongodb_uri="mongodb://localhost:27017/")
    
    # Get trading recommendation
    recommendation = await brain.get_trading_recommendation("AAPL")
    
    print("\n📊 Trading Recommendation:")
    print(f"Symbol: {recommendation['symbol']}")
    print(f"Action: {recommendation['recommendation']}")
    print(f"Confidence: {recommendation['confidence']:.2%}")
    print(f"Reasoning: {recommendation['reasoning']}")
    print(f"Consciousness Level: {recommendation['consciousness_level']:.2%}")
    print(f"Brain Generation: {recommendation['generation']}")
    
    # Save brain state
    brain.save_brain_state("brain_backup.pkl")
    
    # Sync to MongoDB
    await brain.sync_to_mongodb()

if __name__ == "__main__":
    asyncio.run(main())