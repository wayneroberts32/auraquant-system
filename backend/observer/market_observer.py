"""
AuraQuant Market Observer Module
The Infinity Money Synthetic Intelligence System
Real-time market monitoring, pattern detection, and opportunity identification
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_db_config
from trading_lib.indicators import *
from trading_lib.strategies import StrategyRegistry

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """Market regime classification"""
    BULL = "bull"
    BEAR = "bear"
    RANGING = "ranging"
    VOLATILE = "volatile"
    CALM = "calm"

class SignalStrength(Enum):
    """Trading signal strength levels"""
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1
    NEUTRAL = 0

@dataclass
class MarketSignal:
    """Market signal data structure"""
    timestamp: datetime
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    strength: SignalStrength
    confidence: float  # 0-100%
    source: str  # Which indicator/strategy generated this
    metadata: Dict[str, Any]
    
    def to_dict(self):
        """Convert to dictionary for MongoDB storage"""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'source': self.source,
            'metadata': self.metadata
        }

@dataclass
class MarketOpportunity:
    """Detected market opportunity"""
    timestamp: datetime
    symbol: str
    opportunity_type: str  # 'breakout', 'reversal', 'trend', 'arbitrage'
    expected_return: float
    risk_level: float  # 1-10
    time_horizon: str  # 'scalp', 'day', 'swing', 'position'
    entry_price: float
    target_price: float
    stop_loss: float
    confidence: float
    signals: List[MarketSignal]
    
    def to_dict(self):
        """Convert to dictionary for MongoDB storage"""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'opportunity_type': self.opportunity_type,
            'expected_return': self.expected_return,
            'risk_level': self.risk_level,
            'time_horizon': self.time_horizon,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss': self.stop_loss,
            'confidence': self.confidence,
            'signals': [s.to_dict() for s in self.signals]
        }

class MarketObserver:
    """
    AuraQuant Market Observer - The All-Seeing Eye
    Continuously monitors global markets for opportunities
    """
    
    def __init__(self):
        """Initialize the Market Observer"""
        self.db_config = get_db_config()
        self.db = None
        self.monitoring = False
        self.market_data = {}
        self.current_regime = {}
        self.active_signals = {}
        self.opportunities = []
        
        # Configuration
        self.scan_interval = 60  # seconds
        self.lookback_period = 100  # bars for analysis
        self.min_confidence = 60  # minimum confidence for signals
        
        # Markets to observe
        self.watchlist = {
            'crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'SOL-USD'],
            'stocks': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'],
            'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X'],
            'commodities': ['GC=F', 'CL=F', 'SI=F'],  # Gold, Oil, Silver
            'indices': ['^GSPC', '^DJI', '^IXIC']
        }
        
        # Pattern detection patterns
        self.patterns = {
            'double_top': self._detect_double_top,
            'double_bottom': self._detect_double_bottom,
            'head_shoulders': self._detect_head_shoulders,
            'triangle': self._detect_triangle,
            'flag': self._detect_flag,
            'wedge': self._detect_wedge
        }
        
        logger.info("🔭 Market Observer initialized")
    
    async def connect(self):
        """Connect to MongoDB"""
        if self.db_config.async_client:
            self.db = self.db_config.async_db
            logger.info("✅ Market Observer connected to MongoDB")
        else:
            logger.warning("⚠️ MongoDB not available, running in memory-only mode")
    
    async def start_monitoring(self):
        """Start continuous market monitoring"""
        self.monitoring = True
        logger.info("👁️ Market Observer started monitoring")
        
        while self.monitoring:
            try:
                # Scan all markets
                await self._scan_markets()
                
                # Detect patterns
                await self._detect_patterns()
                
                # Generate signals
                await self._generate_signals()
                
                # Identify opportunities
                await self._identify_opportunities()
                
                # Store insights
                await self._store_insights()
                
                # Wait for next scan
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def stop_monitoring(self):
        """Stop market monitoring"""
        self.monitoring = False
        logger.info("🛑 Market Observer stopped monitoring")
    
    async def _scan_markets(self):
        """Scan all markets for current data"""
        for market_type, symbols in self.watchlist.items():
            for symbol in symbols:
                try:
                    # Fetch market data (implement with real data source)
                    data = await self._fetch_market_data(symbol)
                    if data is not None:
                        self.market_data[symbol] = data
                        
                        # Detect market regime
                        regime = self._detect_market_regime(data)
                        self.current_regime[symbol] = regime
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol}: {e}")
    
    async def _fetch_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch market data for a symbol"""
        # This should be implemented with real market data source
        # For now, return None (implement with yfinance, Alpha Vantage, etc.)
        return None
    
    def _detect_market_regime(self, df: pd.DataFrame) -> MarketRegime:
        """Detect current market regime"""
        if df is None or len(df) < 50:
            return MarketRegime.CALM
        
        # Calculate indicators
        sma_20 = df['close'].rolling(20).mean().iloc[-1]
        sma_50 = df['close'].rolling(50).mean().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Calculate volatility
        returns = df['close'].pct_change()
        volatility = returns.std() * np.sqrt(252)
        
        # Determine regime
        if volatility > 0.4:
            return MarketRegime.VOLATILE
        elif current_price > sma_20 > sma_50:
            return MarketRegime.BULL
        elif current_price < sma_20 < sma_50:
            return MarketRegime.BEAR
        elif abs(current_price - sma_20) / sma_20 < 0.02:
            return MarketRegime.RANGING
        else:
            return MarketRegime.CALM
    
    async def _detect_patterns(self):
        """Detect chart patterns in all monitored markets"""
        for symbol, data in self.market_data.items():
            if data is None or len(data) < self.lookback_period:
                continue
            
            for pattern_name, detector in self.patterns.items():
                pattern_found = detector(data)
                if pattern_found:
                    await self._record_pattern(symbol, pattern_name, pattern_found)
    
    def _detect_double_top(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect double top pattern"""
        if len(df) < 50:
            return None
        
        highs = df['high'].rolling(5).max()
        peaks = highs[highs == highs.rolling(20, center=True).max()]
        
        if len(peaks) >= 2:
            last_two_peaks = peaks.iloc[-2:]
            if abs(last_two_peaks.iloc[0] - last_two_peaks.iloc[1]) / last_two_peaks.iloc[0] < 0.02:
                return {
                    'pattern': 'double_top',
                    'confidence': 75,
                    'peak_price': float(last_two_peaks.mean()),
                    'signal': 'SELL'
                }
        return None
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect double bottom pattern"""
        if len(df) < 50:
            return None
        
        lows = df['low'].rolling(5).min()
        troughs = lows[lows == lows.rolling(20, center=True).min()]
        
        if len(troughs) >= 2:
            last_two_troughs = troughs.iloc[-2:]
            if abs(last_two_troughs.iloc[0] - last_two_troughs.iloc[1]) / last_two_troughs.iloc[0] < 0.02:
                return {
                    'pattern': 'double_bottom',
                    'confidence': 75,
                    'trough_price': float(last_two_troughs.mean()),
                    'signal': 'BUY'
                }
        return None
    
    def _detect_head_shoulders(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect head and shoulders pattern"""
        # Simplified detection - implement full logic
        return None
    
    def _detect_triangle(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect triangle pattern"""
        # Simplified detection - implement full logic
        return None
    
    def _detect_flag(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect flag pattern"""
        # Simplified detection - implement full logic
        return None
    
    def _detect_wedge(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect wedge pattern"""
        # Simplified detection - implement full logic
        return None
    
    async def _generate_signals(self):
        """Generate trading signals from multiple indicators"""
        for symbol, data in self.market_data.items():
            if data is None or len(data) < self.lookback_period:
                continue
            
            signals = []
            
            # Technical indicator signals
            signals.extend(await self._get_technical_signals(symbol, data))
            
            # Pattern-based signals
            signals.extend(await self._get_pattern_signals(symbol))
            
            # Momentum signals
            signals.extend(await self._get_momentum_signals(symbol, data))
            
            # Volume signals
            if 'volume' in data.columns:
                signals.extend(await self._get_volume_signals(symbol, data))
            
            # Combine and score signals
            combined_signal = self._combine_signals(signals)
            if combined_signal:
                self.active_signals[symbol] = combined_signal
    
    async def _get_technical_signals(self, symbol: str, df: pd.DataFrame) -> List[MarketSignal]:
        """Generate signals from technical indicators"""
        signals = []
        timestamp = datetime.now()
        
        # RSI Signal
        rsi_value = rsi(df['close'], 14).iloc[-1]
        if rsi_value < 30:
            signals.append(MarketSignal(
                timestamp=timestamp,
                symbol=symbol,
                signal_type='BUY',
                strength=SignalStrength.STRONG,
                confidence=80,
                source='RSI_Oversold',
                metadata={'rsi': float(rsi_value)}
            ))
        elif rsi_value > 70:
            signals.append(MarketSignal(
                timestamp=timestamp,
                symbol=symbol,
                signal_type='SELL',
                strength=SignalStrength.STRONG,
                confidence=80,
                source='RSI_Overbought',
                metadata={'rsi': float(rsi_value)}
            ))
        
        # MACD Signal
        macd_result = macd(df['close'])
        if macd_result['macd'].iloc[-1] > macd_result['signal'].iloc[-1]:
            if macd_result['macd'].iloc[-2] <= macd_result['signal'].iloc[-2]:
                signals.append(MarketSignal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type='BUY',
                    strength=SignalStrength.MODERATE,
                    confidence=70,
                    source='MACD_Crossover',
                    metadata={'macd': float(macd_result['macd'].iloc[-1])}
                ))
        
        # Moving Average Signal
        sma_fast = sma(df['close'], 10).iloc[-1]
        sma_slow = sma(df['close'], 30).iloc[-1]
        if df['close'].iloc[-1] > sma_fast > sma_slow:
            signals.append(MarketSignal(
                timestamp=timestamp,
                symbol=symbol,
                signal_type='BUY',
                strength=SignalStrength.MODERATE,
                confidence=65,
                source='MA_Trend',
                metadata={'sma_fast': float(sma_fast), 'sma_slow': float(sma_slow)}
            ))
        
        return signals
    
    async def _get_pattern_signals(self, symbol: str) -> List[MarketSignal]:
        """Generate signals from detected patterns"""
        # Implement pattern-based signal generation
        return []
    
    async def _get_momentum_signals(self, symbol: str, df: pd.DataFrame) -> List[MarketSignal]:
        """Generate momentum-based signals"""
        signals = []
        timestamp = datetime.now()
        
        # Rate of change
        roc = ((df['close'].iloc[-1] / df['close'].iloc[-10]) - 1) * 100
        if roc > 5:
            signals.append(MarketSignal(
                timestamp=timestamp,
                symbol=symbol,
                signal_type='BUY',
                strength=SignalStrength.MODERATE,
                confidence=60,
                source='Momentum_ROC',
                metadata={'roc': float(roc)}
            ))
        elif roc < -5:
            signals.append(MarketSignal(
                timestamp=timestamp,
                symbol=symbol,
                signal_type='SELL',
                strength=SignalStrength.MODERATE,
                confidence=60,
                source='Momentum_ROC',
                metadata={'roc': float(roc)}
            ))
        
        return signals
    
    async def _get_volume_signals(self, symbol: str, df: pd.DataFrame) -> List[MarketSignal]:
        """Generate volume-based signals"""
        signals = []
        timestamp = datetime.now()
        
        # Volume spike detection
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        
        if current_volume > avg_volume * 2:
            # High volume with price increase
            if df['close'].iloc[-1] > df['close'].iloc[-2]:
                signals.append(MarketSignal(
                    timestamp=timestamp,
                    symbol=symbol,
                    signal_type='BUY',
                    strength=SignalStrength.STRONG,
                    confidence=75,
                    source='Volume_Spike_Bullish',
                    metadata={'volume_ratio': float(current_volume / avg_volume)}
                ))
        
        return signals
    
    def _combine_signals(self, signals: List[MarketSignal]) -> Optional[MarketSignal]:
        """Combine multiple signals into a consensus signal"""
        if not signals:
            return None
        
        # Count signal types
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        sell_signals = [s for s in signals if s.signal_type == 'SELL']
        
        # Calculate weighted confidence
        if buy_signals:
            buy_confidence = np.mean([s.confidence * s.strength.value for s in buy_signals])
        else:
            buy_confidence = 0
        
        if sell_signals:
            sell_confidence = np.mean([s.confidence * s.strength.value for s in sell_signals])
        else:
            sell_confidence = 0
        
        # Determine consensus
        if buy_confidence > sell_confidence and buy_confidence > self.min_confidence:
            return MarketSignal(
                timestamp=datetime.now(),
                symbol=signals[0].symbol,
                signal_type='BUY',
                strength=SignalStrength(min(5, int(buy_confidence / 20))),
                confidence=float(buy_confidence),
                source='Consensus',
                metadata={'signal_count': len(buy_signals)}
            )
        elif sell_confidence > buy_confidence and sell_confidence > self.min_confidence:
            return MarketSignal(
                timestamp=datetime.now(),
                symbol=signals[0].symbol,
                signal_type='SELL',
                strength=SignalStrength(min(5, int(sell_confidence / 20))),
                confidence=float(sell_confidence),
                source='Consensus',
                metadata={'signal_count': len(sell_signals)}
            )
        
        return None
    
    async def _identify_opportunities(self):
        """Identify high-probability trading opportunities"""
        self.opportunities.clear()
        
        for symbol, signal in self.active_signals.items():
            if signal.confidence < self.min_confidence:
                continue
            
            data = self.market_data.get(symbol)
            if data is None or len(data) < 20:
                continue
            
            # Calculate opportunity parameters
            current_price = float(data['close'].iloc[-1])
            atr_value = float(atr(data['high'], data['low'], data['close'], 14).iloc[-1])
            
            if signal.signal_type == 'BUY':
                target_price = current_price + (atr_value * 2)
                stop_loss = current_price - atr_value
                expected_return = ((target_price - current_price) / current_price) * 100
            else:
                target_price = current_price - (atr_value * 2)
                stop_loss = current_price + atr_value
                expected_return = ((current_price - target_price) / current_price) * 100
            
            # Determine time horizon based on volatility
            volatility = data['close'].pct_change().std() * np.sqrt(252)
            if volatility > 0.5:
                time_horizon = 'scalp'
            elif volatility > 0.3:
                time_horizon = 'day'
            elif volatility > 0.15:
                time_horizon = 'swing'
            else:
                time_horizon = 'position'
            
            # Calculate risk level
            risk_level = min(10, max(1, int(volatility * 20)))
            
            opportunity = MarketOpportunity(
                timestamp=datetime.now(),
                symbol=symbol,
                opportunity_type=self._classify_opportunity(signal, self.current_regime.get(symbol)),
                expected_return=expected_return,
                risk_level=risk_level,
                time_horizon=time_horizon,
                entry_price=current_price,
                target_price=target_price,
                stop_loss=stop_loss,
                confidence=signal.confidence,
                signals=[signal]
            )
            
            self.opportunities.append(opportunity)
    
    def _classify_opportunity(self, signal: MarketSignal, regime: Optional[MarketRegime]) -> str:
        """Classify the type of opportunity"""
        if 'breakout' in signal.source.lower():
            return 'breakout'
        elif 'reversal' in signal.source.lower() or 'oversold' in signal.source.lower():
            return 'reversal'
        elif regime in [MarketRegime.BULL, MarketRegime.BEAR]:
            return 'trend'
        else:
            return 'tactical'
    
    async def _store_insights(self):
        """Store market insights to MongoDB"""
        if not self.db:
            return
        
        try:
            # Store active signals
            if self.active_signals:
                await self.db.market_signals.insert_many([
                    signal.to_dict() for signal in self.active_signals.values()
                ])
            
            # Store opportunities
            if self.opportunities:
                await self.db.market_opportunities.insert_many([
                    opp.to_dict() for opp in self.opportunities
                ])
            
            # Store market regimes
            if self.current_regime:
                await self.db.market_regimes.insert_one({
                    'timestamp': datetime.now(),
                    'regimes': {k: v.value for k, v in self.current_regime.items()}
                })
            
            logger.info(f"📊 Stored {len(self.active_signals)} signals and {len(self.opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Failed to store insights: {e}")
    
    async def _record_pattern(self, symbol: str, pattern_name: str, pattern_data: Dict):
        """Record detected pattern"""
        if self.db:
            try:
                await self.db.detected_patterns.insert_one({
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'pattern': pattern_name,
                    'data': pattern_data
                })
            except Exception as e:
                logger.error(f"Failed to record pattern: {e}")
    
    async def get_current_opportunities(self) -> List[MarketOpportunity]:
        """Get current market opportunities"""
        return self.opportunities
    
    async def get_market_regime(self, symbol: str) -> Optional[MarketRegime]:
        """Get current market regime for a symbol"""
        return self.current_regime.get(symbol)
    
    async def get_active_signals(self) -> Dict[str, MarketSignal]:
        """Get all active signals"""
        return self.active_signals

# Export observer instance
observer = MarketObserver()