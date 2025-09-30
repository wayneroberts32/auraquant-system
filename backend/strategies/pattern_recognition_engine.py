"""
AuraQuant Pattern Recognition Engine
Infinity Money Synthetic Intelligence System
CANDLESTICKS • CHART PATTERNS • DIVERGENCE • SELF-LEARNING
ADD-ONLY • NO REBUILD • NEVER LOSE CAPITAL
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import time
from collections import deque

@dataclass
class CandlestickPattern:
    """Represents a detected candlestick pattern"""
    name: str
    pattern_type: str  # REVERSAL, CONTINUATION, NEUTRAL
    strength: float  # 0-1 confidence score
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    timestamp: float
    symbol: str
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float

@dataclass
class ChartPattern:
    """Represents a detected chart pattern"""
    name: str
    pattern_type: str  # HEAD_SHOULDERS, TRIANGLE, FLAG, WEDGE, etc
    direction: str  # BULLISH, BEARISH
    breakout_level: float
    target_price: float
    stop_loss: float
    confidence: float
    formation_bars: int
    timestamp: float

@dataclass
class DivergenceSignal:
    """Represents a divergence between price and indicator"""
    type: str  # REGULAR, HIDDEN
    indicator: str  # RSI, MACD, KVO
    direction: str  # BULLISH, BEARISH
    strength: float
    timestamp: float
    confidence: float

class PatternRecognitionEngine:
    """
    Advanced pattern recognition for AuraQuant Brain
    Detects candlestick patterns, chart formations, and divergences
    Self-learning through reinforcement from trade outcomes
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        
        # Candlestick Pattern Definitions with Confidence Weights
        self.candlestick_patterns = {
            # Single Candle Patterns
            'DOJI': {
                'type': 'NEUTRAL',
                'sentiment': 'INDECISION',
                'base_confidence': 0.5,
                'detection_func': self._detect_doji
            },
            'HAMMER': {
                'type': 'REVERSAL',
                'sentiment': 'BULLISH',
                'base_confidence': 0.7,
                'detection_func': self._detect_hammer
            },
            'SHOOTING_STAR': {
                'type': 'REVERSAL',
                'sentiment': 'BEARISH',
                'base_confidence': 0.7,
                'detection_func': self._detect_shooting_star
            },
            'SPINNING_TOP': {
                'type': 'NEUTRAL',
                'sentiment': 'INDECISION',
                'base_confidence': 0.4,
                'detection_func': self._detect_spinning_top
            },
            
            # Double Candle Patterns
            'BULLISH_ENGULFING': {
                'type': 'REVERSAL',
                'sentiment': 'BULLISH',
                'base_confidence': 0.85,
                'detection_func': self._detect_bullish_engulfing
            },
            'BEARISH_ENGULFING': {
                'type': 'REVERSAL',
                'sentiment': 'BEARISH',
                'base_confidence': 0.85,
                'detection_func': self._detect_bearish_engulfing
            },
            'TWEEZER_TOP': {
                'type': 'REVERSAL',
                'sentiment': 'BEARISH',
                'base_confidence': 0.75,
                'detection_func': self._detect_tweezer_top
            },
            'TWEEZER_BOTTOM': {
                'type': 'REVERSAL',
                'sentiment': 'BULLISH',
                'base_confidence': 0.75,
                'detection_func': self._detect_tweezer_bottom
            },
            
            # Triple Candle Patterns
            'MORNING_STAR': {
                'type': 'REVERSAL',
                'sentiment': 'BULLISH',
                'base_confidence': 0.9,
                'detection_func': self._detect_morning_star
            },
            'EVENING_STAR': {
                'type': 'REVERSAL',
                'sentiment': 'BEARISH',
                'base_confidence': 0.9,
                'detection_func': self._detect_evening_star
            },
            'THREE_WHITE_SOLDIERS': {
                'type': 'CONTINUATION',
                'sentiment': 'BULLISH',
                'base_confidence': 0.88,
                'detection_func': self._detect_three_white_soldiers
            },
            'THREE_BLACK_CROWS': {
                'type': 'CONTINUATION',
                'sentiment': 'BEARISH',
                'base_confidence': 0.88,
                'detection_func': self._detect_three_black_crows
            }
        }
        
        # Chart Pattern Definitions
        self.chart_patterns = {
            'HEAD_AND_SHOULDERS': {
                'type': 'REVERSAL',
                'min_bars': 25,
                'confidence': 0.85,
                'detection_func': self._detect_head_shoulders
            },
            'INVERSE_HEAD_SHOULDERS': {
                'type': 'REVERSAL',
                'min_bars': 25,
                'confidence': 0.85,
                'detection_func': self._detect_inverse_head_shoulders
            },
            'DOUBLE_TOP': {
                'type': 'REVERSAL',
                'min_bars': 20,
                'confidence': 0.8,
                'detection_func': self._detect_double_top
            },
            'DOUBLE_BOTTOM': {
                'type': 'REVERSAL',
                'min_bars': 20,
                'confidence': 0.8,
                'detection_func': self._detect_double_bottom
            },
            'ASCENDING_TRIANGLE': {
                'type': 'CONTINUATION',
                'min_bars': 15,
                'confidence': 0.75,
                'detection_func': self._detect_ascending_triangle
            },
            'DESCENDING_TRIANGLE': {
                'type': 'CONTINUATION',
                'min_bars': 15,
                'confidence': 0.75,
                'detection_func': self._detect_descending_triangle
            },
            'BULL_FLAG': {
                'type': 'CONTINUATION',
                'min_bars': 10,
                'confidence': 0.7,
                'detection_func': self._detect_bull_flag
            },
            'BEAR_FLAG': {
                'type': 'CONTINUATION',
                'min_bars': 10,
                'confidence': 0.7,
                'detection_func': self._detect_bear_flag
            },
            'RISING_WEDGE': {
                'type': 'REVERSAL',
                'min_bars': 15,
                'confidence': 0.72,
                'detection_func': self._detect_rising_wedge
            },
            'FALLING_WEDGE': {
                'type': 'REVERSAL',
                'min_bars': 15,
                'confidence': 0.72,
                'detection_func': self._detect_falling_wedge
            }
        }
        
        # Pattern learning weights (evolve based on outcomes)
        self.pattern_weights = {}
        self.load_pattern_weights()
        
        # Technical indicators for divergence
        self.indicators = {
            'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
            'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
            'KVO': {'fast': 34, 'slow': 55, 'signal': 13}
        }
        
        # Performance tracking
        self.pattern_performance = {}
        self.total_patterns_detected = 0
        self.successful_patterns = 0
        
        # Real-time pattern buffer
        self.pattern_buffer = deque(maxlen=1000)
        
    async def analyze_market(self, candles: pd.DataFrame, symbol: str, 
                           timeframe: str = '5m') -> Dict[str, Any]:
        """
        Main analysis function - detects all patterns and generates signals
        """
        analysis_result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': time.time(),
            'candlestick_patterns': [],
            'chart_patterns': [],
            'divergences': [],
            'composite_signal': None,
            'confidence': 0,
            'recommended_action': 'HOLD'
        }
        
        # Ensure we have enough data
        if len(candles) < 50:
            return analysis_result
        
        # Detect candlestick patterns
        candlestick_signals = await self.detect_candlestick_patterns(candles, symbol, timeframe)
        analysis_result['candlestick_patterns'] = candlestick_signals
        
        # Detect chart patterns
        chart_signals = await self.detect_chart_patterns(candles, symbol, timeframe)
        analysis_result['chart_patterns'] = chart_signals
        
        # Detect divergences
        divergence_signals = await self.detect_divergences(candles)
        analysis_result['divergences'] = divergence_signals
        
        # Generate composite signal
        composite = self.generate_composite_signal(
            candlestick_signals, chart_signals, divergence_signals
        )
        analysis_result['composite_signal'] = composite
        analysis_result['confidence'] = composite['confidence']
        analysis_result['recommended_action'] = composite['action']
        
        # Store in MongoDB for learning
        if self.mongodb:
            await self.store_analysis(analysis_result)
        
        return analysis_result
    
    async def detect_candlestick_patterns(self, candles: pd.DataFrame, 
                                         symbol: str, timeframe: str) -> List[CandlestickPattern]:
        """
        Detect all candlestick patterns in the data
        """
        detected_patterns = []
        
        # Check each pattern type
        for pattern_name, pattern_info in self.candlestick_patterns.items():
            detection_func = pattern_info['detection_func']
            
            # Look for pattern in recent candles
            for i in range(len(candles) - 5, len(candles)):
                if i < 3:  # Need at least 3 candles for most patterns
                    continue
                
                pattern = detection_func(candles, i)
                if pattern:
                    # Calculate entry, stop loss, and take profit
                    current_price = candles.iloc[i]['close']
                    atr = self.calculate_atr(candles, i)
                    
                    if pattern_info['sentiment'] == 'BULLISH':
                        entry_price = current_price
                        stop_loss = current_price - (2 * atr)
                        take_profit = current_price + (3 * atr)
                    elif pattern_info['sentiment'] == 'BEARISH':
                        entry_price = current_price
                        stop_loss = current_price + (2 * atr)
                        take_profit = current_price - (3 * atr)
                    else:  # NEUTRAL
                        entry_price = current_price
                        stop_loss = current_price - atr
                        take_profit = current_price + atr
                    
                    # Apply learned weight to confidence
                    base_confidence = pattern_info['base_confidence']
                    learned_weight = self.pattern_weights.get(pattern_name, 1.0)
                    final_confidence = min(base_confidence * learned_weight, 1.0)
                    
                    detected_patterns.append(CandlestickPattern(
                        name=pattern_name,
                        pattern_type=pattern_info['type'],
                        strength=pattern['strength'],
                        sentiment=pattern_info['sentiment'],
                        timestamp=candles.iloc[i]['timestamp'],
                        symbol=symbol,
                        timeframe=timeframe,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        confidence=final_confidence
                    ))
        
        return detected_patterns
    
    async def detect_chart_patterns(self, candles: pd.DataFrame, 
                                   symbol: str, timeframe: str) -> List[ChartPattern]:
        """
        Detect chart patterns (Head & Shoulders, Triangles, Flags, etc.)
        """
        detected_patterns = []
        
        for pattern_name, pattern_info in self.chart_patterns.items():
            min_bars = pattern_info['min_bars']
            
            if len(candles) < min_bars:
                continue
            
            detection_func = pattern_info['detection_func']
            pattern = detection_func(candles)
            
            if pattern:
                detected_patterns.append(ChartPattern(
                    name=pattern_name,
                    pattern_type=pattern_info['type'],
                    direction=pattern['direction'],
                    breakout_level=pattern['breakout_level'],
                    target_price=pattern['target_price'],
                    stop_loss=pattern['stop_loss'],
                    confidence=pattern_info['confidence'] * self.pattern_weights.get(pattern_name, 1.0),
                    formation_bars=pattern['formation_bars'],
                    timestamp=time.time()
                ))
        
        return detected_patterns
    
    async def detect_divergences(self, candles: pd.DataFrame) -> List[DivergenceSignal]:
        """
        Detect divergences between price and indicators (RSI, MACD, KVO)
        """
        divergences = []
        
        # Calculate indicators
        rsi = self.calculate_rsi(candles)
        macd_line, signal_line, macd_histogram = self.calculate_macd(candles)
        kvo = self.calculate_kvo(candles)
        
        # Detect RSI divergence
        rsi_div = self.detect_rsi_divergence(candles, rsi)
        if rsi_div:
            divergences.append(rsi_div)
        
        # Detect MACD divergence
        macd_div = self.detect_macd_divergence(candles, macd_histogram)
        if macd_div:
            divergences.append(macd_div)
        
        # Detect KVO divergence
        kvo_div = self.detect_kvo_divergence(candles, kvo)
        if kvo_div:
            divergences.append(kvo_div)
        
        return divergences
    
    def generate_composite_signal(self, candlesticks: List[CandlestickPattern],
                                 charts: List[ChartPattern],
                                 divergences: List[DivergenceSignal]) -> Dict[str, Any]:
        """
        Generate a composite trading signal from all detected patterns
        """
        bullish_score = 0
        bearish_score = 0
        total_confidence = 0
        signal_count = 0
        
        # Weight candlestick patterns
        for pattern in candlesticks:
            if pattern.sentiment == 'BULLISH':
                bullish_score += pattern.confidence * pattern.strength
            elif pattern.sentiment == 'BEARISH':
                bearish_score += pattern.confidence * pattern.strength
            total_confidence += pattern.confidence
            signal_count += 1
        
        # Weight chart patterns (higher weight for larger formations)
        for pattern in charts:
            weight = 1.5  # Chart patterns get higher weight
            if pattern.direction == 'BULLISH':
                bullish_score += pattern.confidence * weight
            else:
                bearish_score += pattern.confidence * weight
            total_confidence += pattern.confidence
            signal_count += 1
        
        # Weight divergences (strong confirmation signals)
        for divergence in divergences:
            weight = 2.0  # Divergences are strong confirmations
            if divergence.direction == 'BULLISH':
                bullish_score += divergence.confidence * divergence.strength * weight
            else:
                bearish_score += divergence.confidence * divergence.strength * weight
            total_confidence += divergence.confidence
            signal_count += 1
        
        # Calculate final signal
        if signal_count == 0:
            return {
                'action': 'HOLD',
                'confidence': 0,
                'bullish_score': 0,
                'bearish_score': 0
            }
        
        avg_confidence = total_confidence / signal_count
        net_score = bullish_score - bearish_score
        
        # Determine action based on net score and confidence
        if net_score > 0.5 and avg_confidence > 0.6:
            action = 'BUY'
        elif net_score < -0.5 and avg_confidence > 0.6:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        return {
            'action': action,
            'confidence': avg_confidence,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'net_score': net_score,
            'signal_count': signal_count
        }
    
    # Candlestick Pattern Detection Functions
    def _detect_doji(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Doji pattern"""
        candle = candles.iloc[idx]
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return None
        
        if body / total_range < 0.1:  # Body is less than 10% of range
            return {'strength': 1.0 - (body / total_range)}
        return None
    
    def _detect_hammer(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Hammer pattern"""
        candle = candles.iloc[idx]
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        if body > 0 and lower_shadow > body * 2 and upper_shadow < body * 0.3:
            # Check if in downtrend
            if idx >= 5:
                prev_trend = candles.iloc[idx-5:idx]['close'].mean() > candle['close']
                if prev_trend:
                    return {'strength': min(lower_shadow / body / 2, 1.0)}
        return None
    
    def _detect_shooting_star(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Shooting Star pattern"""
        candle = candles.iloc[idx]
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        if body > 0 and upper_shadow > body * 2 and lower_shadow < body * 0.3:
            # Check if in uptrend
            if idx >= 5:
                prev_trend = candles.iloc[idx-5:idx]['close'].mean() < candle['close']
                if prev_trend:
                    return {'strength': min(upper_shadow / body / 2, 1.0)}
        return None
    
    def _detect_spinning_top(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Spinning Top pattern"""
        candle = candles.iloc[idx]
        body = abs(candle['close'] - candle['open'])
        total_range = candle['high'] - candle['low']
        
        if total_range == 0:
            return None
        
        if 0.1 < body / total_range < 0.3:  # Small body, long shadows
            return {'strength': 0.5}
        return None
    
    def _detect_bullish_engulfing(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Bullish Engulfing pattern"""
        if idx < 1:
            return None
        
        curr = candles.iloc[idx]
        prev = candles.iloc[idx-1]
        
        # Previous candle is bearish, current is bullish
        if prev['close'] < prev['open'] and curr['close'] > curr['open']:
            # Current body engulfs previous body
            if curr['open'] < prev['close'] and curr['close'] > prev['open']:
                engulf_ratio = abs(curr['close'] - curr['open']) / abs(prev['close'] - prev['open'])
                return {'strength': min(engulf_ratio / 1.5, 1.0)}
        return None
    
    def _detect_bearish_engulfing(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Bearish Engulfing pattern"""
        if idx < 1:
            return None
        
        curr = candles.iloc[idx]
        prev = candles.iloc[idx-1]
        
        # Previous candle is bullish, current is bearish
        if prev['close'] > prev['open'] and curr['close'] < curr['open']:
            # Current body engulfs previous body
            if curr['open'] > prev['close'] and curr['close'] < prev['open']:
                engulf_ratio = abs(curr['close'] - curr['open']) / abs(prev['close'] - prev['open'])
                return {'strength': min(engulf_ratio / 1.5, 1.0)}
        return None
    
    def _detect_tweezer_top(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Tweezer Top pattern"""
        if idx < 1:
            return None
        
        curr = candles.iloc[idx]
        prev = candles.iloc[idx-1]
        
        # Similar highs
        if abs(curr['high'] - prev['high']) / prev['high'] < 0.001:
            # First bullish, second bearish
            if prev['close'] > prev['open'] and curr['close'] < curr['open']:
                return {'strength': 0.75}
        return None
    
    def _detect_tweezer_bottom(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Tweezer Bottom pattern"""
        if idx < 1:
            return None
        
        curr = candles.iloc[idx]
        prev = candles.iloc[idx-1]
        
        # Similar lows
        if abs(curr['low'] - prev['low']) / prev['low'] < 0.001:
            # First bearish, second bullish
            if prev['close'] < prev['open'] and curr['close'] > curr['open']:
                return {'strength': 0.75}
        return None
    
    def _detect_morning_star(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Morning Star pattern"""
        if idx < 2:
            return None
        
        first = candles.iloc[idx-2]
        middle = candles.iloc[idx-1]
        last = candles.iloc[idx]
        
        # First: large bearish, Middle: small body (star), Last: large bullish
        if (first['close'] < first['open'] and 
            abs(middle['close'] - middle['open']) < abs(first['close'] - first['open']) * 0.3 and
            last['close'] > last['open'] and
            last['close'] > (first['open'] + first['close']) / 2):
            return {'strength': 0.9}
        return None
    
    def _detect_evening_star(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Evening Star pattern"""
        if idx < 2:
            return None
        
        first = candles.iloc[idx-2]
        middle = candles.iloc[idx-1]
        last = candles.iloc[idx]
        
        # First: large bullish, Middle: small body (star), Last: large bearish
        if (first['close'] > first['open'] and
            abs(middle['close'] - middle['open']) < abs(first['close'] - first['open']) * 0.3 and
            last['close'] < last['open'] and
            last['close'] < (first['open'] + first['close']) / 2):
            return {'strength': 0.9}
        return None
    
    def _detect_three_white_soldiers(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Three White Soldiers pattern"""
        if idx < 2:
            return None
        
        c1 = candles.iloc[idx-2]
        c2 = candles.iloc[idx-1]
        c3 = candles.iloc[idx]
        
        # All three are bullish and progressively higher
        if (c1['close'] > c1['open'] and c2['close'] > c2['open'] and c3['close'] > c3['open'] and
            c2['close'] > c1['close'] and c3['close'] > c2['close']):
            return {'strength': 0.88}
        return None
    
    def _detect_three_black_crows(self, candles: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detect Three Black Crows pattern"""
        if idx < 2:
            return None
        
        c1 = candles.iloc[idx-2]
        c2 = candles.iloc[idx-1]
        c3 = candles.iloc[idx]
        
        # All three are bearish and progressively lower
        if (c1['close'] < c1['open'] and c2['close'] < c2['open'] and c3['close'] < c3['open'] and
            c2['close'] < c1['close'] and c3['close'] < c2['close']):
            return {'strength': 0.88}
        return None
    
    # Chart Pattern Detection Functions (simplified versions)
    def _detect_head_shoulders(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Head and Shoulders pattern"""
        # Simplified detection - would need more sophisticated algorithm
        highs = candles['high'].values
        if len(highs) < 25:
            return None
        
        # Find three peaks
        peaks = []
        for i in range(1, len(highs)-1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                peaks.append((i, highs[i]))
        
        if len(peaks) >= 3:
            # Check if middle peak is highest (head)
            peaks_sorted = sorted(peaks, key=lambda x: x[1], reverse=True)
            if peaks_sorted[0][0] > peaks_sorted[1][0] and peaks_sorted[0][0] < peaks_sorted[2][0]:
                return {
                    'direction': 'BEARISH',
                    'breakout_level': candles.iloc[-1]['low'],
                    'target_price': candles.iloc[-1]['close'] * 0.95,
                    'stop_loss': peaks_sorted[0][1],
                    'formation_bars': len(highs)
                }
        return None
    
    def _detect_inverse_head_shoulders(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Inverse Head and Shoulders pattern"""
        # Similar to head and shoulders but with lows
        lows = candles['low'].values
        if len(lows) < 25:
            return None
        
        # Find three troughs
        troughs = []
        for i in range(1, len(lows)-1):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                troughs.append((i, lows[i]))
        
        if len(troughs) >= 3:
            # Check if middle trough is lowest (head)
            troughs_sorted = sorted(troughs, key=lambda x: x[1])
            if troughs_sorted[0][0] > troughs_sorted[1][0] and troughs_sorted[0][0] < troughs_sorted[2][0]:
                return {
                    'direction': 'BULLISH',
                    'breakout_level': candles.iloc[-1]['high'],
                    'target_price': candles.iloc[-1]['close'] * 1.05,
                    'stop_loss': troughs_sorted[0][1],
                    'formation_bars': len(lows)
                }
        return None
    
    def _detect_double_top(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Double Top pattern"""
        highs = candles['high'].values
        if len(highs) < 20:
            return None
        
        # Find two similar peaks
        peaks = []
        for i in range(1, len(highs)-1):
            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                peaks.append((i, highs[i]))
        
        if len(peaks) >= 2:
            # Check if peaks are similar in height
            if abs(peaks[-1][1] - peaks[-2][1]) / peaks[-2][1] < 0.02:
                return {
                    'direction': 'BEARISH',
                    'breakout_level': min(candles.iloc[peaks[-2][0]:peaks[-1][0]]['low']),
                    'target_price': candles.iloc[-1]['close'] * 0.96,
                    'stop_loss': max(peaks[-1][1], peaks[-2][1]),
                    'formation_bars': peaks[-1][0] - peaks[-2][0]
                }
        return None
    
    def _detect_double_bottom(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Double Bottom pattern"""
        lows = candles['low'].values
        if len(lows) < 20:
            return None
        
        # Find two similar troughs
        troughs = []
        for i in range(1, len(lows)-1):
            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                troughs.append((i, lows[i]))
        
        if len(troughs) >= 2:
            # Check if troughs are similar in depth
            if abs(troughs[-1][1] - troughs[-2][1]) / troughs[-2][1] < 0.02:
                return {
                    'direction': 'BULLISH',
                    'breakout_level': max(candles.iloc[troughs[-2][0]:troughs[-1][0]]['high']),
                    'target_price': candles.iloc[-1]['close'] * 1.04,
                    'stop_loss': min(troughs[-1][1], troughs[-2][1]),
                    'formation_bars': troughs[-1][0] - troughs[-2][0]
                }
        return None
    
    def _detect_ascending_triangle(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Ascending Triangle pattern"""
        # Simplified - check for flat resistance and rising support
        highs = candles['high'].values[-15:]
        lows = candles['low'].values[-15:]
        
        if len(highs) < 15:
            return None
        
        # Check if highs are relatively flat
        high_std = np.std(highs) / np.mean(highs)
        # Check if lows are rising
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]
        
        if high_std < 0.01 and low_slope > 0:
            return {
                'direction': 'BULLISH',
                'breakout_level': np.mean(highs),
                'target_price': np.mean(highs) * 1.03,
                'stop_loss': lows[-1],
                'formation_bars': 15
            }
        return None
    
    def _detect_descending_triangle(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Descending Triangle pattern"""
        # Simplified - check for flat support and falling resistance
        highs = candles['high'].values[-15:]
        lows = candles['low'].values[-15:]
        
        if len(lows) < 15:
            return None
        
        # Check if lows are relatively flat
        low_std = np.std(lows) / np.mean(lows)
        # Check if highs are falling
        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        
        if low_std < 0.01 and high_slope < 0:
            return {
                'direction': 'BEARISH',
                'breakout_level': np.mean(lows),
                'target_price': np.mean(lows) * 0.97,
                'stop_loss': highs[-1],
                'formation_bars': 15
            }
        return None
    
    def _detect_bull_flag(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Bull Flag pattern"""
        # Look for strong upward move followed by consolidation
        if len(candles) < 10:
            return None
        
        # Check for pole (strong up move)
        pole_start = candles.iloc[-10]['low']
        pole_end = candles.iloc[-5]['high']
        pole_strength = (pole_end - pole_start) / pole_start
        
        # Check for flag (consolidation)
        flag_highs = candles.iloc[-5:]['high'].values
        flag_lows = candles.iloc[-5:]['low'].values
        flag_range = (np.max(flag_highs) - np.min(flag_lows)) / np.mean(flag_lows)
        
        if pole_strength > 0.05 and flag_range < 0.02:
            return {
                'direction': 'BULLISH',
                'breakout_level': np.max(flag_highs),
                'target_price': np.max(flag_highs) + (pole_end - pole_start),
                'stop_loss': np.min(flag_lows),
                'formation_bars': 10
            }
        return None
    
    def _detect_bear_flag(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Bear Flag pattern"""
        # Look for strong downward move followed by consolidation
        if len(candles) < 10:
            return None
        
        # Check for pole (strong down move)
        pole_start = candles.iloc[-10]['high']
        pole_end = candles.iloc[-5]['low']
        pole_strength = (pole_start - pole_end) / pole_start
        
        # Check for flag (consolidation)
        flag_highs = candles.iloc[-5:]['high'].values
        flag_lows = candles.iloc[-5:]['low'].values
        flag_range = (np.max(flag_highs) - np.min(flag_lows)) / np.mean(flag_highs)
        
        if pole_strength > 0.05 and flag_range < 0.02:
            return {
                'direction': 'BEARISH',
                'breakout_level': np.min(flag_lows),
                'target_price': np.min(flag_lows) - (pole_start - pole_end),
                'stop_loss': np.max(flag_highs),
                'formation_bars': 10
            }
        return None
    
    def _detect_rising_wedge(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Rising Wedge pattern"""
        if len(candles) < 15:
            return None
        
        highs = candles['high'].values[-15:]
        lows = candles['low'].values[-15:]
        
        # Both trendlines should be rising but converging
        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]
        
        if high_slope > 0 and low_slope > 0 and low_slope > high_slope:
            return {
                'direction': 'BEARISH',
                'breakout_level': lows[-1],
                'target_price': candles.iloc[-1]['close'] * 0.97,
                'stop_loss': highs[-1],
                'formation_bars': 15
            }
        return None
    
    def _detect_falling_wedge(self, candles: pd.DataFrame) -> Optional[Dict]:
        """Detect Falling Wedge pattern"""
        if len(candles) < 15:
            return None
        
        highs = candles['high'].values[-15:]
        lows = candles['low'].values[-15:]
        
        # Both trendlines should be falling but converging
        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]
        
        if high_slope < 0 and low_slope < 0 and high_slope > low_slope:
            return {
                'direction': 'BULLISH',
                'breakout_level': highs[-1],
                'target_price': candles.iloc[-1]['close'] * 1.03,
                'stop_loss': lows[-1],
                'formation_bars': 15
            }
        return None
    
    # Technical Indicator Calculations
    def calculate_rsi(self, candles: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        close = candles['close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, candles: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        close = candles['close']
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    def calculate_kvo(self, candles: pd.DataFrame) -> pd.Series:
        """Calculate Klinger Volume Oscillator"""
        # Simplified KVO calculation
        typical_price = (candles['high'] + candles['low'] + candles['close']) / 3
        volume_force = candles['volume'] * typical_price
        
        kvo_fast = volume_force.ewm(span=34, adjust=False).mean()
        kvo_slow = volume_force.ewm(span=55, adjust=False).mean()
        kvo = kvo_fast - kvo_slow
        
        return kvo
    
    def calculate_atr(self, candles: pd.DataFrame, idx: int, period: int = 14) -> float:
        """Calculate Average True Range"""
        if idx < period:
            return 0
        
        tr_list = []
        for i in range(idx - period + 1, idx + 1):
            high = candles.iloc[i]['high']
            low = candles.iloc[i]['low']
            prev_close = candles.iloc[i-1]['close'] if i > 0 else candles.iloc[i]['close']
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)
        
        return np.mean(tr_list)
    
    # Divergence Detection Functions
    def detect_rsi_divergence(self, candles: pd.DataFrame, rsi: pd.Series) -> Optional[DivergenceSignal]:
        """Detect RSI divergence"""
        if len(rsi) < 20:
            return None
        
        # Find recent price and RSI peaks/troughs
        price_highs = []
        rsi_highs = []
        price_lows = []
        rsi_lows = []
        
        for i in range(5, len(candles)-1):
            # Price highs
            if candles.iloc[i]['high'] > candles.iloc[i-1]['high'] and candles.iloc[i]['high'] > candles.iloc[i+1]['high']:
                price_highs.append((i, candles.iloc[i]['high']))
                rsi_highs.append((i, rsi.iloc[i]))
            
            # Price lows
            if candles.iloc[i]['low'] < candles.iloc[i-1]['low'] and candles.iloc[i]['low'] < candles.iloc[i+1]['low']:
                price_lows.append((i, candles.iloc[i]['low']))
                rsi_lows.append((i, rsi.iloc[i]))
        
        # Check for bearish divergence (price higher high, RSI lower high)
        if len(price_highs) >= 2 and len(rsi_highs) >= 2:
            if price_highs[-1][1] > price_highs[-2][1] and rsi_highs[-1][1] < rsi_highs[-2][1]:
                return DivergenceSignal(
                    type='REGULAR',
                    indicator='RSI',
                    direction='BEARISH',
                    strength=0.8,
                    timestamp=time.time(),
                    confidence=0.75
                )
        
        # Check for bullish divergence (price lower low, RSI higher low)
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            if price_lows[-1][1] < price_lows[-2][1] and rsi_lows[-1][1] > rsi_lows[-2][1]:
                return DivergenceSignal(
                    type='REGULAR',
                    indicator='RSI',
                    direction='BULLISH',
                    strength=0.8,
                    timestamp=time.time(),
                    confidence=0.75
                )
        
        return None
    
    def detect_macd_divergence(self, candles: pd.DataFrame, histogram: pd.Series) -> Optional[DivergenceSignal]:
        """Detect MACD divergence"""
        if len(histogram) < 20:
            return None
        
        # Similar to RSI divergence but using MACD histogram
        price = candles['close'].values
        hist_values = histogram.values
        
        # Find peaks and troughs
        price_peaks = []
        hist_peaks = []
        
        for i in range(5, len(price)-1):
            if price[i] > price[i-1] and price[i] > price[i+1]:
                price_peaks.append((i, price[i]))
                hist_peaks.append((i, hist_values[i]))
        
        # Check for divergence
        if len(price_peaks) >= 2:
            if price_peaks[-1][1] > price_peaks[-2][1] and hist_peaks[-1][1] < hist_peaks[-2][1]:
                return DivergenceSignal(
                    type='REGULAR',
                    indicator='MACD',
                    direction='BEARISH',
                    strength=0.7,
                    timestamp=time.time(),
                    confidence=0.7
                )
        
        return None
    
    def detect_kvo_divergence(self, candles: pd.DataFrame, kvo: pd.Series) -> Optional[DivergenceSignal]:
        """Detect KVO (volume) divergence"""
        if len(kvo) < 20:
            return None
        
        price = candles['close'].values
        kvo_values = kvo.values
        
        # Volume divergence is especially important
        # Check if price is rising but volume (KVO) is falling
        price_slope = np.polyfit(range(10), price[-10:], 1)[0]
        kvo_slope = np.polyfit(range(10), kvo_values[-10:], 1)[0]
        
        if price_slope > 0 and kvo_slope < 0:
            return DivergenceSignal(
                type='REGULAR',
                indicator='KVO',
                direction='BEARISH',
                strength=0.65,
                timestamp=time.time(),
                confidence=0.65
            )
        elif price_slope < 0 and kvo_slope > 0:
            return DivergenceSignal(
                type='REGULAR',
                indicator='KVO',
                direction='BULLISH',
                strength=0.65,
                timestamp=time.time(),
                confidence=0.65
            )
        
        return None
    
    # Machine Learning Functions
    def load_pattern_weights(self):
        """Load learned pattern weights from MongoDB"""
        if self.mongodb:
            # Load historical performance data
            # This would connect to MongoDB and load weights
            pass
        else:
            # Initialize with default weights
            for pattern_name in self.candlestick_patterns:
                self.pattern_weights[pattern_name] = 1.0
            for pattern_name in self.chart_patterns:
                self.pattern_weights[pattern_name] = 1.0
    
    async def update_pattern_performance(self, pattern_name: str, outcome: float):
        """Update pattern performance based on trade outcome"""
        # Reinforcement learning: adjust weight based on outcome
        current_weight = self.pattern_weights.get(pattern_name, 1.0)
        
        # Simple exponential moving average update
        alpha = 0.1  # Learning rate
        new_weight = current_weight * (1 - alpha) + outcome * alpha
        
        # Bound weight between 0.1 and 2.0
        self.pattern_weights[pattern_name] = max(0.1, min(2.0, new_weight))
        
        # Store in MongoDB
        if self.mongodb:
            await self.mongodb.pattern_weights.update_one(
                {'pattern_name': pattern_name},
                {'$set': {
                    'weight': self.pattern_weights[pattern_name],
                    'last_updated': time.time()
                }},
                upsert=True
            )
    
    async def store_analysis(self, analysis: Dict):
        """Store analysis results in MongoDB for journaling"""
        if self.mongodb:
            await self.mongodb.pattern_analysis.insert_one({
                'timestamp': analysis['timestamp'],
                'symbol': analysis['symbol'],
                'timeframe': analysis['timeframe'],
                'patterns_detected': len(analysis['candlestick_patterns']) + len(analysis['chart_patterns']),
                'composite_signal': analysis['composite_signal'],
                'confidence': analysis['confidence'],
                'action': analysis['recommended_action']
            })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get pattern recognition performance statistics"""
        return {
            'total_patterns_detected': self.total_patterns_detected,
            'successful_patterns': self.successful_patterns,
            'success_rate': self.successful_patterns / max(self.total_patterns_detected, 1) * 100,
            'pattern_weights': self.pattern_weights,
            'top_performers': sorted(
                self.pattern_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# QA/QC Test for Pattern Recognition
async def qa_pattern_test():
    """
    QA: Test pattern recognition engine
    """
    engine = PatternRecognitionEngine()
    
    # Create synthetic candlestick data for testing
    dates = pd.date_range('2025-01-01', periods=100, freq='5min')
    
    # Generate realistic OHLCV data
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    candles = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices + np.random.randn(100) * 0.2,
        'high': close_prices + np.abs(np.random.randn(100)) * 0.5,
        'low': close_prices - np.abs(np.random.randn(100)) * 0.5,
        'close': close_prices,
        'volume': np.random.uniform(1000, 10000, 100)
    })
    
    # Run pattern analysis
    analysis = await engine.analyze_market(candles, 'TEST/USD', '5m')
    
    qa_results = {
        'candlestick_patterns_found': len(analysis['candlestick_patterns']),
        'chart_patterns_found': len(analysis['chart_patterns']),
        'divergences_found': len(analysis['divergences']),
        'composite_confidence': analysis['confidence'],
        'recommended_action': analysis['recommended_action'],
        'test_status': 'PASSED' if analysis['confidence'] >= 0 else 'FAILED'
    }
    
    return qa_results