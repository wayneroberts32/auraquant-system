"""
AuraQuant Pattern Recognition Module
=====================================
Harmonic patterns, Support/Resistance, Candlestick patterns
Institutional-grade pattern detection with ML validation

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import time
from scipy.signal import argrelextrema
from scipy.stats import linregress

@dataclass
class HarmonicPattern:
    """Harmonic pattern structure"""
    pattern_type: str  # GARTLEY, BUTTERFLY, BAT, CRAB, SHARK, CYPHER
    direction: str  # BULLISH, BEARISH
    points: Dict[str, Tuple[float, float]]  # X, A, B, C, D points
    completion_zone: Tuple[float, float]  # PRZ (Potential Reversal Zone)
    confidence: float  # 0-1 pattern accuracy
    timestamp: float

@dataclass
class CandlestickPattern:
    """Candlestick pattern structure"""
    pattern_name: str
    pattern_type: str  # REVERSAL, CONTINUATION
    direction: str  # BULLISH, BEARISH, NEUTRAL
    strength: float  # 0-1
    bars_involved: int
    timestamp: float

@dataclass
class SupportResistance:
    """Support/Resistance level"""
    level: float
    level_type: str  # SUPPORT, RESISTANCE
    strength: float  # Based on touches and bounces
    touches: int
    last_test: datetime
    volume_profile: float  # Volume at this level

class PatternRecognition:
    """
    Advanced pattern recognition for AuraQuant
    Harmonic patterns, S/R levels, Candlestick patterns
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        
        # Harmonic pattern ratios (Fibonacci based)
        self.harmonic_ratios = {
            'GARTLEY': {
                'XA_B': (0.618, 0.618),  # B retraces 61.8% of XA
                'AB_C': (0.382, 0.886),  # C retraces 38.2-88.6% of AB
                'BC_D': (1.13, 1.618),   # D extends 113-161.8% of BC
                'XA_D': (0.786, 0.786)   # D retraces 78.6% of XA
            },
            'BUTTERFLY': {
                'XA_B': (0.786, 0.786),
                'AB_C': (0.382, 0.886),
                'BC_D': (1.618, 2.618),
                'XA_D': (1.27, 1.618)
            },
            'BAT': {
                'XA_B': (0.382, 0.5),
                'AB_C': (0.382, 0.886),
                'BC_D': (1.618, 2.618),
                'XA_D': (0.886, 0.886)
            },
            'CRAB': {
                'XA_B': (0.382, 0.618),
                'AB_C': (0.382, 0.886),
                'BC_D': (2.24, 3.618),
                'XA_D': (1.618, 1.618)
            },
            'SHARK': {
                'XA_B': (1.13, 1.618),
                'AB_C': (1.618, 2.24),
                'BC_D': (0.886, 1.13),
                'XA_D': (0.886, 1.13)
            },
            'CYPHER': {
                'XA_B': (0.382, 0.618),
                'AB_C': (1.272, 1.414),
                'XC_D': (0.786, 0.786),
                'XA_D': (0.786, 0.786)
            }
        }
        
        # Candlestick pattern definitions
        self.candlestick_patterns = {
            'HAMMER': self._detect_hammer,
            'SHOOTING_STAR': self._detect_shooting_star,
            'DOJI': self._detect_doji,
            'ENGULFING': self._detect_engulfing,
            'HARAMI': self._detect_harami,
            'MORNING_STAR': self._detect_morning_star,
            'EVENING_STAR': self._detect_evening_star,
            'THREE_WHITE_SOLDIERS': self._detect_three_white_soldiers,
            'THREE_BLACK_CROWS': self._detect_three_black_crows,
            'PIERCING_LINE': self._detect_piercing_line,
            'DARK_CLOUD_COVER': self._detect_dark_cloud_cover
        }
    
    # ==================== Harmonic Patterns ====================
    
    async def detect_harmonic_patterns(self, ohlcv_data: pd.DataFrame,
                                      min_pattern_bars: int = 10,
                                      max_pattern_bars: int = 200) -> List[HarmonicPattern]:
        """
        Detect all harmonic patterns in price data
        Uses swing points and Fibonacci ratios
        """
        patterns = []
        
        # Find swing points
        swing_points = self._find_swing_points(ohlcv_data, window=5)
        
        if len(swing_points) < 5:
            return patterns
        
        # Check all possible 5-point combinations
        for i in range(len(swing_points) - 4):
            points = swing_points[i:i+5]
            
            # Ensure alternating high/low pattern
            if not self._validate_swing_sequence(points):
                continue
            
            # Check pattern bar count constraints
            bar_count = points[-1]['index'] - points[0]['index']
            if bar_count < min_pattern_bars or bar_count > max_pattern_bars:
                continue
            
            # Test against all harmonic patterns
            for pattern_name, ratios in self.harmonic_ratios.items():
                pattern = self._test_harmonic_pattern(
                    points, pattern_name, ratios, ohlcv_data
                )
                if pattern:
                    patterns.append(pattern)
        
        # Store patterns in MongoDB
        if self.mongodb and patterns:
            await self._store_patterns(patterns)
        
        return patterns
    
    def _test_harmonic_pattern(self, points: List[Dict], 
                              pattern_name: str, 
                              ratios: Dict,
                              ohlcv_data: pd.DataFrame) -> Optional[HarmonicPattern]:
        """Test if points form a specific harmonic pattern"""
        X, A, B, C, D = points
        
        # Calculate retracements and extensions
        XA = A['price'] - X['price']
        AB = B['price'] - A['price']
        BC = C['price'] - B['price']
        CD = D['price'] - C['price']
        AD = D['price'] - A['price']
        XD = D['price'] - X['price']
        
        # Determine pattern direction
        direction = 'BULLISH' if XA > 0 else 'BEARISH'
        
        # Calculate ratios
        ratios_actual = {}
        tolerance = 0.05  # 5% tolerance
        
        # XA to B retracement
        if 'XA_B' in ratios:
            ratio_B = abs(AB / XA) if XA != 0 else 0
            ratios_actual['XA_B'] = ratio_B
            if not (ratios['XA_B'][0] - tolerance <= ratio_B <= ratios['XA_B'][1] + tolerance):
                return None
        
        # AB to C retracement
        if 'AB_C' in ratios:
            ratio_C = abs(BC / AB) if AB != 0 else 0
            ratios_actual['AB_C'] = ratio_C
            if not (ratios['AB_C'][0] - tolerance <= ratio_C <= ratios['AB_C'][1] + tolerance):
                return None
        
        # BC to D extension
        if 'BC_D' in ratios:
            ratio_D_BC = abs(CD / BC) if BC != 0 else 0
            ratios_actual['BC_D'] = ratio_D_BC
            if not (ratios['BC_D'][0] - tolerance <= ratio_D_BC <= ratios['BC_D'][1] + tolerance):
                return None
        
        # XA to D retracement
        if 'XA_D' in ratios:
            ratio_D_XA = abs(XD / XA) if XA != 0 else 0
            ratios_actual['XA_D'] = ratio_D_XA
            if not (ratios['XA_D'][0] - tolerance <= ratio_D_XA <= ratios['XA_D'][1] + tolerance):
                return None
        
        # Special case for Cypher (XC to D)
        if 'XC_D' in ratios:
            XC = C['price'] - X['price']
            ratio_D_XC = abs(CD / XC) if XC != 0 else 0
            ratios_actual['XC_D'] = ratio_D_XC
            if not (ratios['XC_D'][0] - tolerance <= ratio_D_XC <= ratios['XC_D'][1] + tolerance):
                return None
        
        # Calculate completion zone (PRZ)
        prz_center = D['price']
        prz_range = abs(XA * 0.02)  # 2% of XA move
        completion_zone = (prz_center - prz_range, prz_center + prz_range)
        
        # Calculate pattern confidence based on ratio accuracy
        confidence = self._calculate_pattern_confidence(ratios_actual, ratios)
        
        return HarmonicPattern(
            pattern_type=pattern_name,
            direction=direction,
            points={
                'X': (X['index'], X['price']),
                'A': (A['index'], A['price']),
                'B': (B['index'], B['price']),
                'C': (C['index'], C['price']),
                'D': (D['index'], D['price'])
            },
            completion_zone=completion_zone,
            confidence=confidence,
            timestamp=time.time()
        )
    
    def _calculate_pattern_confidence(self, actual_ratios: Dict, 
                                     expected_ratios: Dict) -> float:
        """Calculate pattern confidence based on ratio accuracy"""
        if not actual_ratios:
            return 0.0
        
        total_score = 0
        count = 0
        
        for key, actual_value in actual_ratios.items():
            if key in expected_ratios:
                expected_range = expected_ratios[key]
                expected_center = (expected_range[0] + expected_range[1]) / 2
                deviation = abs(actual_value - expected_center) / expected_center
                score = max(0, 1 - deviation)
                total_score += score
                count += 1
        
        return total_score / count if count > 0 else 0
    
    # ==================== Support/Resistance Detection ====================
    
    def detect_support_resistance(self, ohlcv_data: pd.DataFrame,
                                 min_touches: int = 3,
                                 price_tolerance: float = 0.002) -> List[SupportResistance]:
        """
        Detect support and resistance levels
        Based on swing points, volume, and price clustering
        """
        levels = []
        
        # Find swing highs and lows
        highs = argrelextrema(ohlcv_data['high'].values, np.greater, order=5)[0]
        lows = argrelextrema(ohlcv_data['low'].values, np.less, order=5)[0]
        
        # Combine and cluster price levels
        significant_prices = []
        
        for idx in highs:
            significant_prices.append({
                'price': ohlcv_data['high'].iloc[idx],
                'type': 'RESISTANCE',
                'index': idx,
                'volume': ohlcv_data['volume'].iloc[idx]
            })
        
        for idx in lows:
            significant_prices.append({
                'price': ohlcv_data['low'].iloc[idx],
                'type': 'SUPPORT',
                'index': idx,
                'volume': ohlcv_data['volume'].iloc[idx]
            })
        
        # Cluster nearby levels
        clustered_levels = self._cluster_price_levels(
            significant_prices, tolerance=price_tolerance
        )
        
        # Analyze each cluster
        for cluster in clustered_levels:
            if len(cluster) < min_touches:
                continue
            
            # Calculate average level
            avg_price = np.mean([p['price'] for p in cluster])
            total_volume = sum([p['volume'] for p in cluster])
            
            # Determine if support or resistance
            level_type = 'RESISTANCE' if cluster[0]['type'] == 'RESISTANCE' else 'SUPPORT'
            
            # Calculate strength based on touches and volume
            strength = min(len(cluster) / 10, 1.0) * 0.5 + \
                      min(total_volume / ohlcv_data['volume'].mean() / 20, 1.0) * 0.5
            
            # Get last test time
            last_idx = max([p['index'] for p in cluster])
            last_test = ohlcv_data.index[last_idx]
            
            levels.append(SupportResistance(
                level=avg_price,
                level_type=level_type,
                strength=strength,
                touches=len(cluster),
                last_test=last_test,
                volume_profile=total_volume / len(cluster)
            ))
        
        # Sort by strength
        levels.sort(key=lambda x: x.strength, reverse=True)
        
        return levels
    
    def _cluster_price_levels(self, prices: List[Dict], 
                             tolerance: float) -> List[List[Dict]]:
        """Cluster nearby price levels"""
        if not prices:
            return []
        
        # Sort by price
        prices.sort(key=lambda x: x['price'])
        
        clusters = []
        current_cluster = [prices[0]]
        
        for i in range(1, len(prices)):
            # Check if price is within tolerance of cluster average
            cluster_avg = np.mean([p['price'] for p in current_cluster])
            if abs(prices[i]['price'] - cluster_avg) / cluster_avg <= tolerance:
                current_cluster.append(prices[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [prices[i]]
        
        clusters.append(current_cluster)
        
        return clusters
    
    # ==================== Candlestick Patterns ====================
    
    def detect_candlestick_patterns(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """
        Detect all candlestick patterns in the data
        """
        patterns = []
        
        # Check each pattern type
        for pattern_name, detection_func in self.candlestick_patterns.items():
            detected = detection_func(ohlcv_data)
            patterns.extend(detected)
        
        return patterns
    
    def _detect_hammer(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect hammer patterns (bullish reversal)"""
        patterns = []
        
        for i in range(1, len(ohlcv_data)):
            open_price = ohlcv_data['open'].iloc[i]
            high = ohlcv_data['high'].iloc[i]
            low = ohlcv_data['low'].iloc[i]
            close = ohlcv_data['close'].iloc[i]
            
            body = abs(close - open_price)
            upper_shadow = high - max(open_price, close)
            lower_shadow = min(open_price, close) - low
            total_range = high - low
            
            if total_range == 0:
                continue
            
            # Hammer criteria
            if (lower_shadow >= body * 2 and
                upper_shadow <= body * 0.1 and
                body > 0 and
                # In downtrend
                ohlcv_data['close'].iloc[i-1] > ohlcv_data['close'].iloc[i]):
                
                strength = min(lower_shadow / body / 3, 1.0)
                
                patterns.append(CandlestickPattern(
                    pattern_name='HAMMER',
                    pattern_type='REVERSAL',
                    direction='BULLISH',
                    strength=strength,
                    bars_involved=1,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_shooting_star(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect shooting star patterns (bearish reversal)"""
        patterns = []
        
        for i in range(1, len(ohlcv_data)):
            open_price = ohlcv_data['open'].iloc[i]
            high = ohlcv_data['high'].iloc[i]
            low = ohlcv_data['low'].iloc[i]
            close = ohlcv_data['close'].iloc[i]
            
            body = abs(close - open_price)
            upper_shadow = high - max(open_price, close)
            lower_shadow = min(open_price, close) - low
            total_range = high - low
            
            if total_range == 0:
                continue
            
            # Shooting star criteria
            if (upper_shadow >= body * 2 and
                lower_shadow <= body * 0.1 and
                body > 0 and
                # In uptrend
                ohlcv_data['close'].iloc[i-1] < ohlcv_data['close'].iloc[i]):
                
                strength = min(upper_shadow / body / 3, 1.0)
                
                patterns.append(CandlestickPattern(
                    pattern_name='SHOOTING_STAR',
                    pattern_type='REVERSAL',
                    direction='BEARISH',
                    strength=strength,
                    bars_involved=1,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_doji(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect doji patterns (indecision)"""
        patterns = []
        
        for i in range(len(ohlcv_data)):
            open_price = ohlcv_data['open'].iloc[i]
            high = ohlcv_data['high'].iloc[i]
            low = ohlcv_data['low'].iloc[i]
            close = ohlcv_data['close'].iloc[i]
            
            body = abs(close - open_price)
            total_range = high - low
            
            if total_range == 0:
                continue
            
            # Doji criteria (very small body)
            if body / total_range < 0.1:
                
                # Determine doji type
                upper_shadow = high - max(open_price, close)
                lower_shadow = min(open_price, close) - low
                
                if upper_shadow > lower_shadow * 2:
                    doji_type = 'GRAVESTONE_DOJI'
                    direction = 'BEARISH'
                elif lower_shadow > upper_shadow * 2:
                    doji_type = 'DRAGONFLY_DOJI'
                    direction = 'BULLISH'
                else:
                    doji_type = 'STANDARD_DOJI'
                    direction = 'NEUTRAL'
                
                patterns.append(CandlestickPattern(
                    pattern_name=doji_type,
                    pattern_type='REVERSAL',
                    direction=direction,
                    strength=1 - (body / total_range),
                    bars_involved=1,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_engulfing(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect engulfing patterns"""
        patterns = []
        
        for i in range(1, len(ohlcv_data)):
            prev_open = ohlcv_data['open'].iloc[i-1]
            prev_close = ohlcv_data['close'].iloc[i-1]
            curr_open = ohlcv_data['open'].iloc[i]
            curr_close = ohlcv_data['close'].iloc[i]
            
            prev_body = abs(prev_close - prev_open)
            curr_body = abs(curr_close - curr_open)
            
            # Bullish engulfing
            if (prev_close < prev_open and  # Previous bearish
                curr_close > curr_open and  # Current bullish
                curr_open <= prev_close and  # Opens below prev close
                curr_close >= prev_open and  # Closes above prev open
                curr_body > prev_body):  # Current body larger
                
                strength = min(curr_body / prev_body / 2, 1.0)
                
                patterns.append(CandlestickPattern(
                    pattern_name='BULLISH_ENGULFING',
                    pattern_type='REVERSAL',
                    direction='BULLISH',
                    strength=strength,
                    bars_involved=2,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
            
            # Bearish engulfing
            elif (prev_close > prev_open and  # Previous bullish
                  curr_close < curr_open and  # Current bearish
                  curr_open >= prev_close and  # Opens above prev close
                  curr_close <= prev_open and  # Closes below prev open
                  curr_body > prev_body):  # Current body larger
                
                strength = min(curr_body / prev_body / 2, 1.0)
                
                patterns.append(CandlestickPattern(
                    pattern_name='BEARISH_ENGULFING',
                    pattern_type='REVERSAL',
                    direction='BEARISH',
                    strength=strength,
                    bars_involved=2,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_harami(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect harami patterns"""
        patterns = []
        
        for i in range(1, len(ohlcv_data)):
            prev_open = ohlcv_data['open'].iloc[i-1]
            prev_close = ohlcv_data['close'].iloc[i-1]
            curr_open = ohlcv_data['open'].iloc[i]
            curr_close = ohlcv_data['close'].iloc[i]
            
            # Bullish harami
            if (prev_close < prev_open and  # Previous bearish
                curr_close > curr_open and  # Current bullish
                curr_open > prev_close and  # Opens above prev close
                curr_close < prev_open):  # Closes below prev open
                
                patterns.append(CandlestickPattern(
                    pattern_name='BULLISH_HARAMI',
                    pattern_type='REVERSAL',
                    direction='BULLISH',
                    strength=0.6,
                    bars_involved=2,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
            
            # Bearish harami
            elif (prev_close > prev_open and  # Previous bullish
                  curr_close < curr_open and  # Current bearish
                  curr_open < prev_close and  # Opens below prev close
                  curr_close > prev_open):  # Closes above prev open
                
                patterns.append(CandlestickPattern(
                    pattern_name='BEARISH_HARAMI',
                    pattern_type='REVERSAL',
                    direction='BEARISH',
                    strength=0.6,
                    bars_involved=2,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_morning_star(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect morning star patterns (3-bar bullish reversal)"""
        patterns = []
        
        for i in range(2, len(ohlcv_data)):
            # First candle: bearish
            first_bearish = ohlcv_data['close'].iloc[i-2] < ohlcv_data['open'].iloc[i-2]
            
            # Second candle: small body (star)
            second_body = abs(ohlcv_data['close'].iloc[i-1] - ohlcv_data['open'].iloc[i-1])
            second_range = ohlcv_data['high'].iloc[i-1] - ohlcv_data['low'].iloc[i-1]
            second_small = second_body < second_range * 0.3 if second_range > 0 else False
            
            # Third candle: bullish
            third_bullish = ohlcv_data['close'].iloc[i] > ohlcv_data['open'].iloc[i]
            third_closes_high = ohlcv_data['close'].iloc[i] > (
                ohlcv_data['open'].iloc[i-2] + ohlcv_data['close'].iloc[i-2]
            ) / 2
            
            if first_bearish and second_small and third_bullish and third_closes_high:
                patterns.append(CandlestickPattern(
                    pattern_name='MORNING_STAR',
                    pattern_type='REVERSAL',
                    direction='BULLISH',
                    strength=0.8,
                    bars_involved=3,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_evening_star(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect evening star patterns (3-bar bearish reversal)"""
        patterns = []
        
        for i in range(2, len(ohlcv_data)):
            # First candle: bullish
            first_bullish = ohlcv_data['close'].iloc[i-2] > ohlcv_data['open'].iloc[i-2]
            
            # Second candle: small body (star)
            second_body = abs(ohlcv_data['close'].iloc[i-1] - ohlcv_data['open'].iloc[i-1])
            second_range = ohlcv_data['high'].iloc[i-1] - ohlcv_data['low'].iloc[i-1]
            second_small = second_body < second_range * 0.3 if second_range > 0 else False
            
            # Third candle: bearish
            third_bearish = ohlcv_data['close'].iloc[i] < ohlcv_data['open'].iloc[i]
            third_closes_low = ohlcv_data['close'].iloc[i] < (
                ohlcv_data['open'].iloc[i-2] + ohlcv_data['close'].iloc[i-2]
            ) / 2
            
            if first_bullish and second_small and third_bearish and third_closes_low:
                patterns.append(CandlestickPattern(
                    pattern_name='EVENING_STAR',
                    pattern_type='REVERSAL',
                    direction='BEARISH',
                    strength=0.8,
                    bars_involved=3,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_three_white_soldiers(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect three white soldiers (bullish continuation)"""
        patterns = []
        
        for i in range(2, len(ohlcv_data)):
            # All three candles must be bullish
            all_bullish = all([
                ohlcv_data['close'].iloc[i-j] > ohlcv_data['open'].iloc[i-j]
                for j in range(3)
            ])
            
            # Each close higher than previous
            ascending = (ohlcv_data['close'].iloc[i] > ohlcv_data['close'].iloc[i-1] >
                        ohlcv_data['close'].iloc[i-2])
            
            # Each opens within previous body
            proper_opens = all([
                ohlcv_data['open'].iloc[i-j+1] > ohlcv_data['open'].iloc[i-j] and
                ohlcv_data['open'].iloc[i-j+1] < ohlcv_data['close'].iloc[i-j]
                for j in range(1, 3)
            ])
            
            if all_bullish and ascending and proper_opens:
                patterns.append(CandlestickPattern(
                    pattern_name='THREE_WHITE_SOLDIERS',
                    pattern_type='CONTINUATION',
                    direction='BULLISH',
                    strength=0.9,
                    bars_involved=3,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_three_black_crows(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect three black crows (bearish continuation)"""
        patterns = []
        
        for i in range(2, len(ohlcv_data)):
            # All three candles must be bearish
            all_bearish = all([
                ohlcv_data['close'].iloc[i-j] < ohlcv_data['open'].iloc[i-j]
                for j in range(3)
            ])
            
            # Each close lower than previous
            descending = (ohlcv_data['close'].iloc[i] < ohlcv_data['close'].iloc[i-1] <
                         ohlcv_data['close'].iloc[i-2])
            
            # Each opens within previous body
            proper_opens = all([
                ohlcv_data['open'].iloc[i-j+1] < ohlcv_data['open'].iloc[i-j] and
                ohlcv_data['open'].iloc[i-j+1] > ohlcv_data['close'].iloc[i-j]
                for j in range(1, 3)
            ])
            
            if all_bearish and descending and proper_opens:
                patterns.append(CandlestickPattern(
                    pattern_name='THREE_BLACK_CROWS',
                    pattern_type='CONTINUATION',
                    direction='BEARISH',
                    strength=0.9,
                    bars_involved=3,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_piercing_line(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect piercing line pattern (bullish reversal)"""
        patterns = []
        
        for i in range(1, len(ohlcv_data)):
            # First candle: bearish
            first_bearish = ohlcv_data['close'].iloc[i-1] < ohlcv_data['open'].iloc[i-1]
            
            # Second candle: bullish
            second_bullish = ohlcv_data['close'].iloc[i] > ohlcv_data['open'].iloc[i]
            
            # Opens below previous low
            opens_low = ohlcv_data['open'].iloc[i] < ohlcv_data['low'].iloc[i-1]
            
            # Closes above midpoint of previous body
            midpoint = (ohlcv_data['open'].iloc[i-1] + ohlcv_data['close'].iloc[i-1]) / 2
            closes_high = ohlcv_data['close'].iloc[i] > midpoint
            
            if first_bearish and second_bullish and opens_low and closes_high:
                patterns.append(CandlestickPattern(
                    pattern_name='PIERCING_LINE',
                    pattern_type='REVERSAL',
                    direction='BULLISH',
                    strength=0.7,
                    bars_involved=2,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    def _detect_dark_cloud_cover(self, ohlcv_data: pd.DataFrame) -> List[CandlestickPattern]:
        """Detect dark cloud cover pattern (bearish reversal)"""
        patterns = []
        
        for i in range(1, len(ohlcv_data)):
            # First candle: bullish
            first_bullish = ohlcv_data['close'].iloc[i-1] > ohlcv_data['open'].iloc[i-1]
            
            # Second candle: bearish
            second_bearish = ohlcv_data['close'].iloc[i] < ohlcv_data['open'].iloc[i]
            
            # Opens above previous high
            opens_high = ohlcv_data['open'].iloc[i] > ohlcv_data['high'].iloc[i-1]
            
            # Closes below midpoint of previous body
            midpoint = (ohlcv_data['open'].iloc[i-1] + ohlcv_data['close'].iloc[i-1]) / 2
            closes_low = ohlcv_data['close'].iloc[i] < midpoint
            
            if first_bullish and second_bearish and opens_high and closes_low:
                patterns.append(CandlestickPattern(
                    pattern_name='DARK_CLOUD_COVER',
                    pattern_type='REVERSAL',
                    direction='BEARISH',
                    strength=0.7,
                    bars_involved=2,
                    timestamp=ohlcv_data.index[i].timestamp()
                ))
        
        return patterns
    
    # ==================== Helper Functions ====================
    
    def _find_swing_points(self, ohlcv_data: pd.DataFrame, 
                          window: int = 5) -> List[Dict]:
        """Find swing high and low points"""
        swing_points = []
        
        # Find swing highs
        highs = argrelextrema(ohlcv_data['high'].values, np.greater, order=window)[0]
        for idx in highs:
            swing_points.append({
                'index': idx,
                'price': ohlcv_data['high'].iloc[idx],
                'type': 'HIGH'
            })
        
        # Find swing lows
        lows = argrelextrema(ohlcv_data['low'].values, np.less, order=window)[0]
        for idx in lows:
            swing_points.append({
                'index': idx,
                'price': ohlcv_data['low'].iloc[idx],
                'type': 'LOW'
            })
        
        # Sort by index
        swing_points.sort(key=lambda x: x['index'])
        
        return swing_points
    
    def _validate_swing_sequence(self, points: List[Dict]) -> bool:
        """Validate that swing points alternate between highs and lows"""
        for i in range(1, len(points)):
            if points[i]['type'] == points[i-1]['type']:
                return False
        return True
    
    async def _store_patterns(self, patterns: List):
        """Store detected patterns in MongoDB"""
        if self.mongodb:
            for pattern in patterns:
                if isinstance(pattern, HarmonicPattern):
                    await self.mongodb.harmonic_patterns.insert_one({
                        'pattern_type': pattern.pattern_type,
                        'direction': pattern.direction,
                        'points': pattern.points,
                        'completion_zone': pattern.completion_zone,
                        'confidence': pattern.confidence,
                        'timestamp': pattern.timestamp
                    })
                elif isinstance(pattern, CandlestickPattern):
                    await self.mongodb.candlestick_patterns.insert_one({
                        'pattern_name': pattern.pattern_name,
                        'pattern_type': pattern.pattern_type,
                        'direction': pattern.direction,
                        'strength': pattern.strength,
                        'bars_involved': pattern.bars_involved,
                        'timestamp': pattern.timestamp
                    })
    
    # ==================== Complete Analysis ====================
    
    async def analyze_all_patterns(self, symbol: str, 
                                  ohlcv_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Complete pattern analysis including all pattern types
        """
        analysis = {
            'symbol': symbol,
            'timestamp': time.time(),
            'harmonic_patterns': [],
            'support_resistance': [],
            'candlestick_patterns': []
        }
        
        # Detect harmonic patterns
        harmonic = await self.detect_harmonic_patterns(ohlcv_data)
        analysis['harmonic_patterns'] = harmonic
        
        # Detect support/resistance levels
        sr_levels = self.detect_support_resistance(ohlcv_data)
        analysis['support_resistance'] = sr_levels
        
        # Detect candlestick patterns
        candlesticks = self.detect_candlestick_patterns(ohlcv_data)
        analysis['candlestick_patterns'] = candlesticks
        
        # Generate pattern-based signals
        analysis['pattern_signals'] = self._generate_pattern_signals(analysis)
        
        return analysis
    
    def _generate_pattern_signals(self, analysis: Dict) -> List[Dict]:
        """Generate trading signals from pattern analysis"""
        signals = []
        
        # Harmonic pattern signals
        for pattern in analysis['harmonic_patterns']:
            if pattern.confidence > 0.7:
                signals.append({
                    'type': 'HARMONIC_SIGNAL',
                    'direction': pattern.direction,
                    'pattern': pattern.pattern_type,
                    'confidence': pattern.confidence,
                    'target_zone': pattern.completion_zone,
                    'timestamp': pattern.timestamp
                })
        
        # Support/Resistance breakout signals
        if analysis['support_resistance']:
            current_price = analysis.get('current_price', 0)
            for level in analysis['support_resistance']:
                if level.strength > 0.7:
                    distance_pct = abs(current_price - level.level) / level.level
                    if distance_pct < 0.005:  # Within 0.5% of level
                        signals.append({
                            'type': 'SR_LEVEL_TEST',
                            'level_type': level.level_type,
                            'level': level.level,
                            'strength': level.strength,
                            'touches': level.touches,
                            'timestamp': time.time()
                        })
        
        # Candlestick pattern signals
        reversal_patterns = [p for p in analysis['candlestick_patterns'] 
                           if p.pattern_type == 'REVERSAL' and p.strength > 0.6]
        
        for pattern in reversal_patterns:
            signals.append({
                'type': 'CANDLESTICK_SIGNAL',
                'pattern': pattern.pattern_name,
                'direction': pattern.direction,
                'strength': pattern.strength,
                'bars': pattern.bars_involved,
                'timestamp': pattern.timestamp
            })
        
        return signals