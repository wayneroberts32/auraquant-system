"""
AuraQuant Technical Indicators Module
======================================
MACD, RSI, KVO, VWAP, and Divergence Detection
Non-repainting, institutional-grade indicators

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import time

@dataclass
class DivergenceSignal:
    """Divergence signal detection"""
    symbol: str
    indicator: str  # RSI, MACD, KVO
    divergence_type: str  # REGULAR_BULLISH, REGULAR_BEARISH, HIDDEN_BULLISH, HIDDEN_BEARISH
    strength: float  # 0-1 confidence
    price_points: List[float]
    indicator_points: List[float]
    timestamp: float

class TechnicalIndicators:
    """
    Comprehensive technical indicators for AuraQuant
    All indicators are non-repainting and bar-close confirmed
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.bar_close_only = True  # Prevent repainting
        self.divergence_lookback = 20
        self.signal_history = {}
        
    # ==================== MACD ====================
    
    def calculate_macd(self, prices: pd.Series, 
                       fast_period: int = 12, 
                       slow_period: int = 26, 
                       signal_period: int = 9) -> Dict[str, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)
        Non-repainting implementation
        """
        if len(prices) < slow_period:
            return {'macd': pd.Series(), 'signal': pd.Series(), 'histogram': pd.Series()}
        
        # Calculate EMAs
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # MACD histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram,
            'bullish_cross': (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1)),
            'bearish_cross': (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
        }
    
    # ==================== RSI ====================
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index)
        Non-repainting Wilder's smoothing method
        """
        if len(prices) < period + 1:
            return pd.Series()
        
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Wilder's smoothing (exponential moving average)
        avg_gains = gains.ewm(com=period-1, adjust=False).mean()
        avg_losses = losses.ewm(com=period-1, adjust=False).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        # Add overbought/oversold signals
        rsi_signals = pd.DataFrame({
            'rsi': rsi,
            'overbought': rsi > 70,
            'oversold': rsi < 30,
            'extreme_overbought': rsi > 80,
            'extreme_oversold': rsi < 20
        })
        
        return rsi_signals
    
    # ==================== Klinger Volume Oscillator ====================
    
    def calculate_kvo(self, high: pd.Series, low: pd.Series, 
                     close: pd.Series, volume: pd.Series,
                     fast_period: int = 34, slow_period: int = 55,
                     signal_period: int = 13) -> Dict[str, pd.Series]:
        """
        Calculate Klinger Volume Oscillator (KVO)
        Volume-based trend confirmation indicator
        """
        if len(close) < slow_period:
            return {'kvo': pd.Series(), 'signal': pd.Series()}
        
        # Calculate Trend
        hlc = (high + low + close) / 3
        dm = high - low
        
        # Trend direction
        trend = pd.Series(0, index=close.index)
        trend[hlc > hlc.shift(1)] = 1
        trend[hlc <= hlc.shift(1)] = -1
        
        # Volume Force
        cm = dm
        for i in range(1, len(cm)):
            if trend.iloc[i] == trend.iloc[i-1]:
                cm.iloc[i] = cm.iloc[i-1] + dm.iloc[i]
            else:
                cm.iloc[i] = dm.iloc[i-1] + dm.iloc[i]
        
        # Volume Force calculation
        vf = volume * (2 * ((dm/cm) - 1)) * trend * 100
        
        # KVO calculation
        kvo = vf.ewm(span=fast_period, adjust=False).mean() - \
              vf.ewm(span=slow_period, adjust=False).mean()
        
        # Signal line
        signal = kvo.ewm(span=signal_period, adjust=False).mean()
        
        return {
            'kvo': kvo,
            'signal': signal,
            'bullish': kvo > signal,
            'bearish': kvo < signal,
            'volume_confirmation': (kvo > 0) & (volume > volume.rolling(20).mean())
        }
    
    # ==================== VWAP ====================
    
    def calculate_vwap(self, high: pd.Series, low: pd.Series, 
                      close: pd.Series, volume: pd.Series,
                      anchor_time: Optional[datetime] = None) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP)
        Can be standard (daily) or anchored to specific time
        """
        typical_price = (high + low + close) / 3
        
        if anchor_time:
            # Anchored VWAP from specific time
            mask = close.index >= anchor_time
            cumulative_tpv = (typical_price * volume)[mask].cumsum()
            cumulative_volume = volume[mask].cumsum()
        else:
            # Standard daily VWAP (reset each day)
            dates = pd.to_datetime(close.index).date
            cumulative_tpv = typical_price * volume
            cumulative_volume = volume.copy()
            
            for date in pd.unique(dates):
                mask = dates == date
                cumulative_tpv[mask] = (typical_price * volume)[mask].cumsum()
                cumulative_volume[mask] = volume[mask].cumsum()
        
        vwap = cumulative_tpv / cumulative_volume
        
        # Add VWAP bands (standard deviation based)
        squared_diff = ((typical_price - vwap) ** 2) * volume
        variance = squared_diff.cumsum() / cumulative_volume
        std_dev = np.sqrt(variance)
        
        return pd.DataFrame({
            'vwap': vwap,
            'upper_band_1': vwap + std_dev,
            'upper_band_2': vwap + (2 * std_dev),
            'lower_band_1': vwap - std_dev,
            'lower_band_2': vwap - (2 * std_dev),
            'above_vwap': close > vwap,
            'below_vwap': close < vwap
        })
    
    # ==================== Divergence Detection ====================
    
    def detect_divergence(self, prices: pd.Series, 
                         indicator: pd.Series,
                         indicator_name: str) -> List[DivergenceSignal]:
        """
        Detect regular and hidden divergences between price and indicator
        Critical for reversal and continuation signals
        """
        if len(prices) < self.divergence_lookback:
            return []
        
        divergences = []
        
        # Find price peaks and troughs
        price_highs = self._find_peaks(prices, window=5)
        price_lows = self._find_troughs(prices, window=5)
        
        # Find indicator peaks and troughs
        indicator_highs = self._find_peaks(indicator, window=5)
        indicator_lows = self._find_troughs(indicator, window=5)
        
        # Regular Bullish Divergence (price makes lower low, indicator makes higher low)
        if len(price_lows) >= 2 and len(indicator_lows) >= 2:
            if (price_lows[-1]['value'] < price_lows[-2]['value'] and
                indicator_lows[-1]['value'] > indicator_lows[-2]['value']):
                
                divergences.append(DivergenceSignal(
                    symbol='',
                    indicator=indicator_name,
                    divergence_type='REGULAR_BULLISH',
                    strength=self._calculate_divergence_strength(
                        price_lows[-2:], indicator_lows[-2:]
                    ),
                    price_points=[price_lows[-2]['value'], price_lows[-1]['value']],
                    indicator_points=[indicator_lows[-2]['value'], indicator_lows[-1]['value']],
                    timestamp=time.time()
                ))
        
        # Regular Bearish Divergence (price makes higher high, indicator makes lower high)
        if len(price_highs) >= 2 and len(indicator_highs) >= 2:
            if (price_highs[-1]['value'] > price_highs[-2]['value'] and
                indicator_highs[-1]['value'] < indicator_highs[-2]['value']):
                
                divergences.append(DivergenceSignal(
                    symbol='',
                    indicator=indicator_name,
                    divergence_type='REGULAR_BEARISH',
                    strength=self._calculate_divergence_strength(
                        price_highs[-2:], indicator_highs[-2:]
                    ),
                    price_points=[price_highs[-2]['value'], price_highs[-1]['value']],
                    indicator_points=[indicator_highs[-2]['value'], indicator_highs[-1]['value']],
                    timestamp=time.time()
                ))
        
        # Hidden Bullish Divergence (price makes higher low, indicator makes lower low)
        if len(price_lows) >= 2 and len(indicator_lows) >= 2:
            if (price_lows[-1]['value'] > price_lows[-2]['value'] and
                indicator_lows[-1]['value'] < indicator_lows[-2]['value']):
                
                divergences.append(DivergenceSignal(
                    symbol='',
                    indicator=indicator_name,
                    divergence_type='HIDDEN_BULLISH',
                    strength=self._calculate_divergence_strength(
                        price_lows[-2:], indicator_lows[-2:]
                    ),
                    price_points=[price_lows[-2]['value'], price_lows[-1]['value']],
                    indicator_points=[indicator_lows[-2]['value'], indicator_lows[-1]['value']],
                    timestamp=time.time()
                ))
        
        # Hidden Bearish Divergence (price makes lower high, indicator makes higher high)
        if len(price_highs) >= 2 and len(indicator_highs) >= 2:
            if (price_highs[-1]['value'] < price_highs[-2]['value'] and
                indicator_highs[-1]['value'] > indicator_highs[-2]['value']):
                
                divergences.append(DivergenceSignal(
                    symbol='',
                    indicator=indicator_name,
                    divergence_type='HIDDEN_BEARISH',
                    strength=self._calculate_divergence_strength(
                        price_highs[-2:], indicator_highs[-2:]
                    ),
                    price_points=[price_highs[-2]['value'], price_highs[-1]['value']],
                    indicator_points=[indicator_highs[-2]['value'], indicator_highs[-1]['value']],
                    timestamp=time.time()
                ))
        
        return divergences
    
    def _find_peaks(self, series: pd.Series, window: int = 5) -> List[Dict]:
        """Find local maxima in series"""
        peaks = []
        for i in range(window, len(series) - window):
            if series.iloc[i] == series.iloc[i-window:i+window+1].max():
                peaks.append({'index': i, 'value': series.iloc[i]})
        return peaks
    
    def _find_troughs(self, series: pd.Series, window: int = 5) -> List[Dict]:
        """Find local minima in series"""
        troughs = []
        for i in range(window, len(series) - window):
            if series.iloc[i] == series.iloc[i-window:i+window+1].min():
                troughs.append({'index': i, 'value': series.iloc[i]})
        return troughs
    
    def _calculate_divergence_strength(self, price_points: List, 
                                      indicator_points: List) -> float:
        """Calculate divergence strength (0-1)"""
        if len(price_points) < 2 or len(indicator_points) < 2:
            return 0.0
        
        # Calculate slopes
        price_slope = (price_points[-1]['value'] - price_points[-2]['value']) / \
                     (price_points[-1]['index'] - price_points[-2]['index'])
        
        indicator_slope = (indicator_points[-1]['value'] - indicator_points[-2]['value']) / \
                          (indicator_points[-1]['index'] - indicator_points[-2]['index'])
        
        # Divergence strength based on slope difference
        divergence_angle = abs(np.arctan(price_slope) - np.arctan(indicator_slope))
        strength = min(divergence_angle / (np.pi/2), 1.0)  # Normalize to 0-1
        
        return strength
    
    # ==================== Combined Analysis ====================
    
    async def analyze_complete(self, symbol: str, 
                              ohlcv_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Complete technical analysis with all indicators and divergences
        """
        analysis = {
            'symbol': symbol,
            'timestamp': time.time(),
            'indicators': {},
            'divergences': [],
            'signals': []
        }
        
        # Calculate all indicators
        close = ohlcv_data['close']
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        volume = ohlcv_data['volume']
        
        # MACD
        macd_data = self.calculate_macd(close)
        analysis['indicators']['macd'] = macd_data
        
        # RSI
        rsi_data = self.calculate_rsi(close)
        analysis['indicators']['rsi'] = rsi_data
        
        # KVO
        kvo_data = self.calculate_kvo(high, low, close, volume)
        analysis['indicators']['kvo'] = kvo_data
        
        # VWAP
        vwap_data = self.calculate_vwap(high, low, close, volume)
        analysis['indicators']['vwap'] = vwap_data
        
        # Detect divergences
        if not macd_data['macd'].empty:
            macd_divergences = self.detect_divergence(close, macd_data['macd'], 'MACD')
            analysis['divergences'].extend(macd_divergences)
        
        if not rsi_data['rsi'].empty:
            rsi_divergences = self.detect_divergence(close, rsi_data['rsi'], 'RSI')
            analysis['divergences'].extend(rsi_divergences)
        
        if not kvo_data['kvo'].empty:
            kvo_divergences = self.detect_divergence(close, kvo_data['kvo'], 'KVO')
            analysis['divergences'].extend(kvo_divergences)
        
        # Generate combined signals
        analysis['signals'] = self._generate_combined_signals(analysis)
        
        # Store in MongoDB
        if self.mongodb and self.bar_close_only:
            await self._store_analysis(analysis)
        
        return analysis
    
    def _generate_combined_signals(self, analysis: Dict) -> List[Dict]:
        """Generate trading signals from combined indicator analysis"""
        signals = []
        
        # Check for confluences
        bullish_conditions = 0
        bearish_conditions = 0
        
        # MACD conditions
        if 'macd' in analysis['indicators']:
            macd = analysis['indicators']['macd']
            if not macd['bullish_cross'].empty and macd['bullish_cross'].iloc[-1]:
                bullish_conditions += 1
            if not macd['bearish_cross'].empty and macd['bearish_cross'].iloc[-1]:
                bearish_conditions += 1
        
        # RSI conditions
        if 'rsi' in analysis['indicators']:
            rsi = analysis['indicators']['rsi']
            if not rsi['oversold'].empty and rsi['oversold'].iloc[-1]:
                bullish_conditions += 1
            if not rsi['overbought'].empty and rsi['overbought'].iloc[-1]:
                bearish_conditions += 1
        
        # KVO conditions
        if 'kvo' in analysis['indicators']:
            kvo = analysis['indicators']['kvo']
            if not kvo['bullish'].empty and kvo['bullish'].iloc[-1]:
                bullish_conditions += 1
            if not kvo['bearish'].empty and kvo['bearish'].iloc[-1]:
                bearish_conditions += 1
        
        # VWAP conditions
        if 'vwap' in analysis['indicators']:
            vwap = analysis['indicators']['vwap']
            if not vwap['above_vwap'].empty and vwap['above_vwap'].iloc[-1]:
                bullish_conditions += 0.5  # Half weight for VWAP
            if not vwap['below_vwap'].empty and vwap['below_vwap'].iloc[-1]:
                bearish_conditions += 0.5
        
        # Divergence conditions
        for div in analysis['divergences']:
            if 'BULLISH' in div.divergence_type:
                bullish_conditions += div.strength * 2  # Double weight for divergences
            if 'BEARISH' in div.divergence_type:
                bearish_conditions += div.strength * 2
        
        # Generate signals based on confluence
        if bullish_conditions >= 3:
            signals.append({
                'type': 'BUY',
                'strength': min(bullish_conditions / 5, 1.0),
                'confidence': 'HIGH' if bullish_conditions >= 4 else 'MEDIUM',
                'indicators_aligned': bullish_conditions,
                'timestamp': time.time()
            })
        
        if bearish_conditions >= 3:
            signals.append({
                'type': 'SELL',
                'strength': min(bearish_conditions / 5, 1.0),
                'confidence': 'HIGH' if bearish_conditions >= 4 else 'MEDIUM',
                'indicators_aligned': bearish_conditions,
                'timestamp': time.time()
            })
        
        return signals
    
    async def _store_analysis(self, analysis: Dict):
        """Store analysis in MongoDB for backtesting and learning"""
        if self.mongodb:
            # Store complete analysis
            await self.mongodb.technical_analysis.insert_one({
                'timestamp': analysis['timestamp'],
                'symbol': analysis['symbol'],
                'signals': analysis['signals'],
                'divergences': [
                    {
                        'type': d.divergence_type,
                        'indicator': d.indicator,
                        'strength': d.strength
                    } for d in analysis['divergences']
                ],
                'indicator_values': {
                    'macd': analysis['indicators'].get('macd', {}).get('macd', pd.Series()).iloc[-1] if 'macd' in analysis['indicators'] else None,
                    'rsi': analysis['indicators'].get('rsi', {}).get('rsi', pd.Series()).iloc[-1] if 'rsi' in analysis['indicators'] else None,
                    'kvo': analysis['indicators'].get('kvo', {}).get('kvo', pd.Series()).iloc[-1] if 'kvo' in analysis['indicators'] else None,
                    'vwap': analysis['indicators'].get('vwap', {}).get('vwap', pd.Series()).iloc[-1] if 'vwap' in analysis['indicators'] else None
                }
            })