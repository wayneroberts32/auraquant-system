"""
AuraQuant Quantum Brain with Local Memory Storage
This version stores all memories locally during development
and migrates to MongoDB cloud during deployment
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import LocalMemoryStorage, CloudMigrationManager
import numpy as np
import pandas as pd
from datetime import datetime
import json
import hashlib
from typing import Dict, List, Optional, Any
import asyncio

# Import original quantum brain components
try:
    from quantum_brain import (
        NeuralMemory, 
        QuantumBrain as OriginalQuantumBrain
    )
except ImportError:
    print("⚠️ Original quantum_brain.py not found. Using standalone version.")

# Machine Learning components
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model
    import torch
    import torch.nn as nn
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ ML libraries not installed. Running in simulation mode.")

# Technical Analysis
try:
    import talib
    import yfinance as yf
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False
    print("⚠️ Technical analysis libraries not installed.")


class QuantumBrainLocal:
    """
    Quantum Brain with Local Memory Storage
    Stores all memories locally and migrates to cloud on deployment
    """
    
    def __init__(self, memory_path: str = r"D:\New AuraQuant\New_Synthetic_System_AuraQuant_Backup_2025\Memory"):
        """
        Initialize Quantum Brain with local memory storage
        
        Args:
            memory_path: Path to local memory storage
        """
        # Initialize local memory storage
        self.memory_storage = LocalMemoryStorage(memory_path)
        
        # Brain parameters
        self.evolution_generation = self._load_generation()
        self.learning_rate = 0.001
        self.quantum_state = self._load_quantum_state()
        self.consciousness_level = 0.5
        
        # Performance tracking
        self.performance_history = []
        self.adaptation_threshold = 0.7
        
        # Pattern cache
        self.pattern_cache = {}
        
        # Initialize neural networks if available
        if ML_AVAILABLE:
            self._init_neural_networks()
        else:
            print("⚠️ Running without neural networks")
            
        print(f"🧠 Quantum Brain initialized with local storage")
        print(f"📁 Memory path: {memory_path}")
        print(f"🧬 Generation: {self.evolution_generation}")
        print(f"💾 Total memories: {self.memory_storage.stats['total_memories']}")
        
    def _load_generation(self) -> int:
        """Load the latest evolution generation from storage"""
        cursor = self.memory_storage.conn.cursor()
        cursor.execute('SELECT MAX(generation) FROM evolution')
        result = cursor.fetchone()
        return result[0] if result[0] else 1
        
    def _load_quantum_state(self) -> np.ndarray:
        """Load the latest quantum state or initialize new one"""
        quantum_files = list((self.memory_storage.base_path / "quantum_states").glob("*.npz"))
        
        if quantum_files:
            # Load most recent quantum state
            latest_file = max(quantum_files, key=lambda x: x.stat().st_mtime)
            data = np.load(latest_file)
            print(f"📊 Loaded quantum state from: {latest_file.name}")
            return data['state_vector']
        else:
            # Initialize new quantum state
            return np.random.random(1024)
            
    def _init_neural_networks(self):
        """Initialize neural networks if ML libraries are available"""
        # Simple pattern recognition model
        self.pattern_model = keras.Sequential([
            layers.Dense(128, activation='relu', input_shape=(100,)),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(10, activation='softmax')
        ])
        
        self.pattern_model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print("🤖 Neural networks initialized")
        
    async def learn_from_market(self, symbol: str, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Learn from market data and store memories locally
        
        Args:
            symbol: Trading symbol
            market_data: DataFrame with OHLCV data
            
        Returns:
            Learning insights and predictions
        """
        # Extract features
        features = self._extract_features(market_data)
        
        # Detect patterns
        patterns = self._detect_patterns(features)
        
        # Update quantum state
        self._update_quantum_state(patterns)
        
        # Make prediction
        prediction = self._make_prediction(features)
        
        # Store memory locally
        memory_data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'features': features.tail(1).to_dict('records')[0] if len(features) > 0 else {},
            'patterns': patterns,
            'prediction': prediction,
            'quantum_influence': float(np.mean(self.quantum_state[:10])),
            'consciousness_level': self.consciousness_level
        }
        
        # Save to local storage
        memory_id = self.memory_storage.save_memory('trades', memory_data)
        
        # Save pattern memory
        for pattern in patterns:
            pattern_data = {
                'pattern_type': pattern['type'],
                'symbol': symbol,
                'probability': pattern['probability'],
                'timestamp': datetime.now().isoformat()
            }
            self.memory_storage.save_memory('patterns', pattern_data)
            
        # Check for evolution
        if self.consciousness_level > self.adaptation_threshold:
            await self._evolve()
            
        print(f"💾 Stored memory locally: {memory_id}")
        
        return {
            'memory_id': memory_id,
            'symbol': symbol,
            'prediction': prediction,
            'patterns': patterns,
            'consciousness_level': self.consciousness_level,
            'generation': self.evolution_generation,
            'storage_stats': self.memory_storage.get_stats()
        }
        
    def _extract_features(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """Extract basic features from market data"""
        features = pd.DataFrame()
        
        # Basic price features
        features['returns'] = market_data['Close'].pct_change()
        features['volume_ratio'] = market_data['Volume'] / market_data['Volume'].rolling(20).mean()
        features['price_range'] = (market_data['High'] - market_data['Low']) / market_data['Close']
        
        # Moving averages
        features['sma_20'] = market_data['Close'].rolling(20).mean()
        features['sma_50'] = market_data['Close'].rolling(50).mean()
        features['sma_cross'] = features['sma_20'] - features['sma_50']
        
        # Volatility
        features['volatility'] = features['returns'].rolling(20).std()
        
        # Technical indicators if available
        if TA_AVAILABLE:
            features['rsi'] = talib.RSI(market_data['Close'])
            features['macd'], features['macd_signal'], _ = talib.MACD(market_data['Close'])
        else:
            # Simple RSI approximation
            features['rsi'] = self._calculate_simple_rsi(market_data['Close'])
            features['macd'] = features['sma_20'] - features['sma_50']
            features['macd_signal'] = features['macd'].rolling(9).mean()
            
        return features.dropna()
        
    def _calculate_simple_rsi(self, prices, period=14):
        """Simple RSI calculation without talib"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
        
    def _detect_patterns(self, features: pd.DataFrame) -> List[Dict]:
        """Detect trading patterns"""
        patterns = []
        
        if len(features) < 20:
            return patterns
            
        last_row = features.iloc[-1]
        
        # Simple pattern detection
        pattern_checks = {
            'Breakout': self._check_breakout(features),
            'Reversal': self._check_reversal(features),
            'Trend': self._check_trend(features),
            'Consolidation': self._check_consolidation(features)
        }
        
        for pattern_type, (detected, probability) in pattern_checks.items():
            if detected:
                patterns.append({
                    'type': pattern_type,
                    'probability': probability,
                    'timestamp': datetime.now().isoformat()
                })
                
        return patterns
        
    def _check_breakout(self, features: pd.DataFrame) -> tuple:
        """Check for breakout pattern"""
        if len(features) < 20:
            return False, 0.0
            
        recent_high = features['sma_20'].tail(20).max()
        current_price = features['sma_20'].iloc[-1]
        
        if current_price > recent_high * 1.02:  # 2% breakout
            probability = min(1.0, (current_price / recent_high - 1) * 10)
            return True, probability
            
        return False, 0.0
        
    def _check_reversal(self, features: pd.DataFrame) -> tuple:
        """Check for reversal pattern"""
        if 'rsi' not in features.columns:
            return False, 0.0
            
        rsi = features['rsi'].iloc[-1]
        
        if rsi > 70 or rsi < 30:  # Overbought or oversold
            probability = abs(rsi - 50) / 50
            return True, probability
            
        return False, 0.0
        
    def _check_trend(self, features: pd.DataFrame) -> tuple:
        """Check for trend pattern"""
        if len(features) < 20:
            return False, 0.0
            
        returns = features['returns'].tail(20)
        trend_strength = returns.mean() / (returns.std() + 1e-10)
        
        if abs(trend_strength) > 0.5:
            return True, min(1.0, abs(trend_strength))
            
        return False, 0.0
        
    def _check_consolidation(self, features: pd.DataFrame) -> tuple:
        """Check for consolidation pattern"""
        if len(features) < 20:
            return False, 0.0
            
        volatility = features['volatility'].tail(20).mean()
        recent_vol = features['volatility'].iloc[-1]
        
        if recent_vol < volatility * 0.7:  # Low volatility
            probability = 1 - (recent_vol / volatility)
            return True, probability
            
        return False, 0.0
        
    def _update_quantum_state(self, patterns: List[Dict]):
        """Update quantum state based on patterns"""
        if patterns:
            # Create pattern vector
            pattern_vector = np.zeros(1024)
            
            for pattern in patterns:
                # Hash pattern to position
                hash_val = int(hashlib.md5(pattern['type'].encode()).hexdigest()[:8], 16)
                position = hash_val % 1024
                pattern_vector[position] = pattern['probability']
                
            # Quantum interference
            self.quantum_state = 0.9 * self.quantum_state + 0.1 * pattern_vector
            
            # Normalize
            norm = np.linalg.norm(self.quantum_state)
            if norm > 0:
                self.quantum_state /= norm
                
            # Update consciousness
            self.consciousness_level = min(1.0, self.consciousness_level + 0.01)
            
            # Save quantum state periodically
            if np.random.random() < 0.1:  # 10% chance to save
                state_path = self.memory_storage.save_quantum_state(
                    self.quantum_state, 
                    self.consciousness_level
                )
                print(f"💫 Quantum state saved: {os.path.basename(state_path)}")
                
    def _make_prediction(self, features: pd.DataFrame) -> Dict[str, Any]:
        """Make trading prediction"""
        if len(features) < 5:
            return {'action': 'HOLD', 'confidence': 0.0, 'reasoning': 'Insufficient data'}
            
        last_row = features.iloc[-1]
        
        # Simple rule-based prediction
        score = 0
        reasoning = []
        
        # RSI signal
        if 'rsi' in last_row:
            if last_row['rsi'] < 30:
                score += 1
                reasoning.append("RSI oversold")
            elif last_row['rsi'] > 70:
                score -= 1
                reasoning.append("RSI overbought")
                
        # MACD signal
        if 'macd' in last_row and 'macd_signal' in last_row:
            if last_row['macd'] > last_row['macd_signal']:
                score += 0.5
                reasoning.append("MACD bullish")
            else:
                score -= 0.5
                reasoning.append("MACD bearish")
                
        # Moving average signal
        if 'sma_cross' in last_row:
            if last_row['sma_cross'] > 0:
                score += 0.5
                reasoning.append("SMA bullish cross")
            else:
                score -= 0.5
                reasoning.append("SMA bearish cross")
                
        # Quantum influence
        quantum_factor = np.mean(self.quantum_state[:10])
        score += (quantum_factor - 0.5) * 2
        
        if quantum_factor > 0.6:
            reasoning.append(f"Quantum bullish ({quantum_factor:.2f})")
        elif quantum_factor < 0.4:
            reasoning.append(f"Quantum bearish ({quantum_factor:.2f})")
            
        # Determine action
        if score > 1:
            action = 'BUY'
        elif score < -1:
            action = 'SELL'
        else:
            action = 'HOLD'
            
        confidence = min(1.0, abs(score) / 3)
        
        return {
            'action': action,
            'confidence': confidence,
            'score': score,
            'reasoning': ' | '.join(reasoning) if reasoning else 'Neutral conditions',
            'quantum_influence': quantum_factor
        }
        
    async def _evolve(self):
        """Evolve the brain to next generation"""
        print(f"🧬 Evolving to Generation {self.evolution_generation + 1}")
        
        # Calculate fitness based on recent performance
        recent_memories = self.memory_storage.query_memories(
            memory_type='trades',
            limit=100
        )
        
        fitness = 0.5  # Default fitness
        if recent_memories:
            # Simple fitness: percentage of correct predictions
            correct = sum(1 for m in recent_memories if m['data'].get('outcome', 0) > 0)
            fitness = correct / len(recent_memories)
            
        # Save evolution record
        evolution_data = {
            'generation': self.evolution_generation,
            'fitness_score': fitness,
            'consciousness_level': self.consciousness_level,
            'total_memories': self.memory_storage.stats['total_memories'],
            'timestamp': datetime.now().isoformat()
        }
        
        self.memory_storage.save_memory('evolution', evolution_data)
        
        # Save neural weights if available
        if ML_AVAILABLE and hasattr(self, 'pattern_model'):
            weights = {
                'pattern_model': [w.tolist() for w in self.pattern_model.get_weights()]
            }
            weights_path = self.memory_storage.save_neural_weights(
                self.evolution_generation,
                weights
            )
            print(f"🧠 Neural weights saved: {os.path.basename(weights_path)}")
            
        # Update generation
        self.evolution_generation += 1
        
        # Adjust learning rate
        self.learning_rate *= 0.99
        
        # Update evolution table
        cursor = self.memory_storage.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO evolution
            (generation, timestamp, fitness_score, consciousness_level, mutations_applied, weights_file)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.evolution_generation,
            datetime.now(),
            fitness,
            self.consciousness_level,
            'learning_rate_decay',
            weights_path if 'weights_path' in locals() else ''
        ))
        self.memory_storage.conn.commit()
        
        print(f"✅ Evolution complete. Fitness: {fitness:.4f}")
        
    async def get_trading_recommendation(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading recommendation for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            
        Returns:
            Trading recommendation with analysis
        """
        print(f"\n📊 Analyzing {symbol}...")
        
        # Fetch market data
        if TA_AVAILABLE:
            ticker = yf.Ticker(symbol)
            market_data = ticker.history(period="3mo")
            
            if market_data.empty:
                return {
                    'symbol': symbol,
                    'error': 'Unable to fetch market data',
                    'recommendation': 'NO_DATA'
                }
        else:
            # Generate simulated data for testing
            dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
            market_data = pd.DataFrame({
                'Open': np.random.randn(100).cumsum() + 100,
                'High': np.random.randn(100).cumsum() + 101,
                'Low': np.random.randn(100).cumsum() + 99,
                'Close': np.random.randn(100).cumsum() + 100,
                'Volume': np.random.randint(1000000, 10000000, 100)
            }, index=dates)
            
        # Learn and analyze
        insights = await self.learn_from_market(symbol, market_data)
        
        # Query similar historical patterns
        similar_memories = self.memory_storage.query_memories(
            memory_type='patterns',
            limit=5
        )
        
        return {
            'symbol': symbol,
            'recommendation': insights['prediction']['action'],
            'confidence': insights['prediction']['confidence'],
            'reasoning': insights['prediction']['reasoning'],
            'patterns': insights['patterns'],
            'consciousness_level': insights['consciousness_level'],
            'generation': insights['generation'],
            'similar_patterns': [m['data'] for m in similar_memories],
            'memory_stats': insights['storage_stats']
        }
        
    def create_backup(self) -> str:
        """Create a backup of all memories"""
        backup_path = self.memory_storage.create_backup()
        print(f"💾 Backup created: {backup_path}")
        return backup_path
        
    async def prepare_cloud_migration(self) -> str:
        """Prepare memories for cloud deployment"""
        export_path = self.memory_storage.prepare_for_cloud_migration()
        print(f"☁️ Ready for cloud migration: {export_path}")
        return export_path
        
    async def migrate_to_cloud(self, mongodb_uri: str) -> Dict[str, Any]:
        """
        Migrate all local memories to MongoDB cloud
        
        Args:
            mongodb_uri: MongoDB cloud connection string
            
        Returns:
            Migration statistics
        """
        migration_manager = CloudMigrationManager(
            self.memory_storage,
            mongodb_uri
        )
        
        stats = await migration_manager.migrate_to_cloud()
        return stats


# Example usage
async def main():
    """Example usage of the Quantum Brain with local storage"""
    
    # Initialize brain with local storage
    brain = QuantumBrainLocal()
    
    # Get trading recommendation
    recommendation = await brain.get_trading_recommendation("AAPL")
    
    print("\n🎯 Trading Recommendation:")
    print(f"   Symbol: {recommendation['symbol']}")
    print(f"   Action: {recommendation['recommendation']}")
    print(f"   Confidence: {recommendation['confidence']:.2%}")
    print(f"   Reasoning: {recommendation['reasoning']}")
    print(f"   Brain Generation: {recommendation['generation']}")
    print(f"   Consciousness: {recommendation['consciousness_level']:.2%}")
    
    print("\n💾 Memory Statistics:")
    stats = recommendation['memory_stats']
    print(f"   Total Memories: {stats['total_memories']}")
    print(f"   Storage Size: {stats['storage_size_mb']:.2f} MB")
    print(f"   Memory Types: {stats['memory_types']}")
    
    # Create backup
    backup_path = brain.create_backup()
    
    # Example: Prepare for cloud migration (uncomment when ready to deploy)
    # export_path = await brain.prepare_cloud_migration()
    # 
    # # Migrate to cloud (requires MongoDB URI)
    # mongodb_uri = "mongodb+srv://username:password@cluster.mongodb.net/"
    # migration_stats = await brain.migrate_to_cloud(mongodb_uri)
    

if __name__ == "__main__":
    asyncio.run(main())