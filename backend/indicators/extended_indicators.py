"""
AuraQuant Extended Technical Indicators
========================================
Ichimoku Cloud, ADX, Stochastic, Bollinger Bands, ATR
Professional-grade implementations with MongoDB persistence

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import asyncio
from scipy import stats

@dataclass
class IchimokuSignal:
    """Ichimoku trading signal"""
    signal_type: str  # TK_CROSS, KUMO_BREAKOUT, CHIKOU_SPAN_CROSS
    direction: str  # BULLISH, BEARISH
    strength: float
    kumo_thickness: float
    future_kumo_trend: str  # BULLISH, BEARISH, NEUTRAL
    timestamp: float

@dataclass
class ADXSignal:
    """ADX trend strength signal"""
    adx_value: float
    plus_di: float
    minus_di: float
    trend_strength: str  # STRONG, MODERATE, WEAK, NO_TREND
    trend_direction: str  # BULLISH, BEARISH, NEUTRAL
    timestamp: float

class ExtendedIndicators:
    """
    Extended technical indicators for AuraQuant
    Institutional-grade implementations
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.cache = {}
        
    # ==================== Ichimoku Cloud ====================
    
    def calculate_ichimoku(self, ohlcv_data: pd.DataFrame,
                          tenkan_period: int = 9,
                          kijun_period: int = 26,
                          senkou_b_period: int = 52,
                          displacement: int = 26) -> Dict[str, pd.Series]:
        """
        Calculate Ichimoku Cloud (Ichimoku Kinko Hyo)
        The complete "one glance equilibrium chart"
        """
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        close = ohlcv_data['close']
        
        # Tenkan-sen (Conversion Line) = (9-period high + 9-period low) / 2
        tenkan_sen = (high.rolling(window=tenkan_period).max() + 
                     low.rolling(window=tenkan_period).min()) / 2
        
        # Kijun-sen (Base Line) = (26-period high + 26-period low) / 2
        kijun_sen = (high.rolling(window=kijun_period).max() + 
                    low.rolling(window=kijun_period).min()) / 2
        
        # Senkou Span A (Leading Span A) = (Tenkan-sen + Kijun-sen) / 2, displaced 26 periods
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        
        # Senkou Span B (Leading Span B) = (52-period high + 52-period low) / 2, displaced 26
        senkou_span_b = ((high.rolling(window=senkou_b_period).max() + 
                         low.rolling(window=senkou_b_period).min()) / 2).shift(displacement)
        
        # Chikou Span (Lagging Span) = Close price, displaced 26 periods backward
        chikou_span = close.shift(-displacement)
        
        # Kumo (Cloud) thickness and trend
        kumo_thickness = abs(senkou_span_a - senkou_span_b)
        kumo_trend = pd.Series('NEUTRAL', index=close.index)
        kumo_trend[senkou_span_a > senkou_span_b] = 'BULLISH'
        kumo_trend[senkou_span_a < senkou_span_b] = 'BEARISH'
        
        # Generate trading signals
        ichimoku_signals = self._generate_ichimoku_signals(
            close, tenkan_sen, kijun_sen, senkou_span_a, 
            senkou_span_b, chikou_span, kumo_thickness, kumo_trend
        )
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span,
            'kumo_thickness': kumo_thickness,
            'kumo_trend': kumo_trend,
            'signals': ichimoku_signals
        }
    
    def _generate_ichimoku_signals(self, close: pd.Series, 
                                  tenkan: pd.Series, kijun: pd.Series,
                                  span_a: pd.Series, span_b: pd.Series,
                                  chikou: pd.Series, thickness: pd.Series,
                                  trend: pd.Series) -> List[IchimokuSignal]:
        """Generate Ichimoku trading signals"""
        signals = []
        
        # TK Cross (Tenkan-Kijun Cross)
        tk_cross_bull = (tenkan > kijun) & (tenkan.shift(1) <= kijun.shift(1))
        tk_cross_bear = (tenkan < kijun) & (tenkan.shift(1) >= kijun.shift(1))
        
        # Kumo Breakout
        kumo_top = pd.DataFrame({'a': span_a, 'b': span_b}).max(axis=1)
        kumo_bottom = pd.DataFrame({'a': span_a, 'b': span_b}).min(axis=1)
        
        kumo_break_bull = (close > kumo_top) & (close.shift(1) <= kumo_top.shift(1))
        kumo_break_bear = (close < kumo_bottom) & (close.shift(1) >= kumo_bottom.shift(1))
        
        # Chikou Span Cross
        chikou_bull = (chikou > close.shift(26)) & (chikou.shift(1) <= close.shift(27))
        chikou_bear = (chikou < close.shift(26)) & (chikou.shift(1) >= close.shift(27))
        
        # Strong signals (multiple confirmations)
        for i in range(len(close)):
            signal_strength = 0
            signal_types = []
            
            # Check TK Cross
            if i > 0 and tk_cross_bull.iloc[i]:
                signal_strength += 0.3
                signal_types.append('TK_CROSS')
            elif i > 0 and tk_cross_bear.iloc[i]:
                signal_strength -= 0.3
                signal_types.append('TK_CROSS')
            
            # Check Kumo Breakout
            if i > 0 and kumo_break_bull.iloc[i]:
                signal_strength += 0.4
                signal_types.append('KUMO_BREAKOUT')
            elif i > 0 and kumo_break_bear.iloc[i]:
                signal_strength -= 0.4
                signal_types.append('KUMO_BREAKOUT')
            
            # Check price position relative to cloud
            if not pd.isna(kumo_top.iloc[i]) and not pd.isna(kumo_bottom.iloc[i]):
                if close.iloc[i] > kumo_top.iloc[i]:
                    signal_strength += 0.2
                elif close.iloc[i] < kumo_bottom.iloc[i]:
                    signal_strength -= 0.2
            
            # Check cloud trend
            if trend.iloc[i] == 'BULLISH':
                signal_strength += 0.1
            elif trend.iloc[i] == 'BEARISH':
                signal_strength -= 0.1
            
            # Generate signal if strength threshold met
            if abs(signal_strength) >= 0.5:
                signals.append(IchimokuSignal(
                    signal_type=','.join(signal_types) if signal_types else 'COMPLEX',
                    direction='BULLISH' if signal_strength > 0 else 'BEARISH',
                    strength=abs(signal_strength),
                    kumo_thickness=thickness.iloc[i] if not pd.isna(thickness.iloc[i]) else 0,
                    future_kumo_trend=trend.iloc[i] if i < len(trend) else 'NEUTRAL',
                    timestamp=time.time()
                ))
        
        return signals
    
    # ==================== Average Directional Index (ADX) ====================
    
    def calculate_adx(self, ohlcv_data: pd.DataFrame, 
                     period: int = 14) -> Dict[str, pd.Series]:
        """
        Calculate Average Directional Index (ADX)
        Measures trend strength regardless of direction
        """
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        close = ohlcv_data['close']
        
        # Calculate True Range (TR)
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = pd.Series(0.0, index=high.index)
        minus_dm = pd.Series(0.0, index=low.index)
        
        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move[(up_move > down_move) & (up_move > 0)]
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move[(down_move > up_move) & (down_move > 0)]
        
        # Calculate smoothed averages (Wilder's smoothing)
        atr = self._wilder_smoothing(tr, period)
        plus_dm_smooth = self._wilder_smoothing(plus_dm, period)
        minus_dm_smooth = self._wilder_smoothing(minus_dm, period)
        
        # Calculate Directional Indicators
        plus_di = 100 * plus_dm_smooth / atr
        minus_di = 100 * minus_dm_smooth / atr
        
        # Calculate DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = self._wilder_smoothing(dx, period)
        
        # Generate ADX signals
        adx_signals = self._generate_adx_signals(adx, plus_di, minus_di)
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di,
            'atr': atr,
            'signals': adx_signals
        }
    
    def _wilder_smoothing(self, series: pd.Series, period: int) -> pd.Series:
        """Wilder's smoothing method (used in ADX, ATR, RSI)"""
        alpha = 1.0 / period
        return series.ewm(alpha=alpha, adjust=False).mean()
    
    def _generate_adx_signals(self, adx: pd.Series, 
                             plus_di: pd.Series, 
                             minus_di: pd.Series) -> List[ADXSignal]:
        """Generate ADX trend strength signals"""
        signals = []
        
        for i in range(len(adx)):
            if pd.isna(adx.iloc[i]):
                continue
            
            adx_value = adx.iloc[i]
            plus_value = plus_di.iloc[i] if not pd.isna(plus_di.iloc[i]) else 0
            minus_value = minus_di.iloc[i] if not pd.isna(minus_di.iloc[i]) else 0
            
            # Determine trend strength
            if adx_value >= 50:
                trend_strength = 'VERY_STRONG'
            elif adx_value >= 25:
                trend_strength = 'STRONG'
            elif adx_value >= 20:
                trend_strength = 'MODERATE'
            else:
                trend_strength = 'WEAK'
            
            # Determine trend direction
            if plus_value > minus_value:
                trend_direction = 'BULLISH'
            elif minus_value > plus_value:
                trend_direction = 'BEARISH'
            else:
                trend_direction = 'NEUTRAL'
            
            # Only generate signal for significant conditions
            if adx_value >= 25 or (i > 0 and abs(adx.iloc[i] - adx.iloc[i-1]) > 5):
                signals.append(ADXSignal(
                    adx_value=adx_value,
                    plus_di=plus_value,
                    minus_di=minus_value,
                    trend_strength=trend_strength,
                    trend_direction=trend_direction,
                    timestamp=time.time()
                ))
        
        return signals
    
    # ==================== Stochastic Oscillator ====================
    
    def calculate_stochastic(self, ohlcv_data: pd.DataFrame,
                            k_period: int = 14,
                            d_period: int = 3,
                            smooth_k: int = 3) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic Oscillator
        Momentum indicator comparing closing price to price range
        """
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        close = ohlcv_data['close']
        
        # Calculate %K (Fast Stochastic)
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        fast_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        
        # Smooth %K to get Slow %K
        slow_k = fast_k.rolling(window=smooth_k).mean()
        
        # Calculate %D (Signal line)
        slow_d = slow_k.rolling(window=d_period).mean()
        
        # Identify overbought/oversold conditions
        overbought = slow_k > 80
        oversold = slow_k < 20
        
        # Detect divergences
        divergences = self._detect_stochastic_divergence(close, slow_k)
        
        # Generate crossover signals
        k_cross_d_bull = (slow_k > slow_d) & (slow_k.shift(1) <= slow_d.shift(1))
        k_cross_d_bear = (slow_k < slow_d) & (slow_k.shift(1) >= slow_d.shift(1))
        
        return {
            'fast_k': fast_k,
            'slow_k': slow_k,
            'slow_d': slow_d,
            'overbought': overbought,
            'oversold': oversold,
            'bullish_crossover': k_cross_d_bull,
            'bearish_crossover': k_cross_d_bear,
            'divergences': divergences
        }
    
    def _detect_stochastic_divergence(self, prices: pd.Series, 
                                     stochastic: pd.Series,
                                     lookback: int = 20) -> pd.Series:
        """Detect bullish and bearish divergences"""
        divergence = pd.Series('NONE', index=prices.index)
        
        if len(prices) < lookback * 2:
            return divergence
        
        for i in range(lookback, len(prices)):
            window_prices = prices.iloc[i-lookback:i]
            window_stoch = stochastic.iloc[i-lookback:i]
            
            if window_prices.isna().any() or window_stoch.isna().any():
                continue
            
            # Find local extrema
            price_peaks = (window_prices == window_prices.rolling(5, center=True).max())
            price_troughs = (window_prices == window_prices.rolling(5, center=True).min())
            
            stoch_peaks = (window_stoch == window_stoch.rolling(5, center=True).max())
            stoch_troughs = (window_stoch == window_stoch.rolling(5, center=True).min())
            
            # Check for bearish divergence (price higher high, stoch lower high)
            if price_peaks.any() and stoch_peaks.any():
                price_peak_vals = window_prices[price_peaks].values
                stoch_peak_vals = window_stoch[stoch_peaks].values
                
                if len(price_peak_vals) >= 2 and len(stoch_peak_vals) >= 2:
                    if (price_peak_vals[-1] > price_peak_vals[-2] and 
                        stoch_peak_vals[-1] < stoch_peak_vals[-2]):
                        divergence.iloc[i] = 'BEARISH_DIVERGENCE'
            
            # Check for bullish divergence (price lower low, stoch higher low)
            if price_troughs.any() and stoch_troughs.any():
                price_trough_vals = window_prices[price_troughs].values
                stoch_trough_vals = window_stoch[stoch_troughs].values
                
                if len(price_trough_vals) >= 2 and len(stoch_trough_vals) >= 2:
                    if (price_trough_vals[-1] < price_trough_vals[-2] and 
                        stoch_trough_vals[-1] > stoch_trough_vals[-2]):
                        divergence.iloc[i] = 'BULLISH_DIVERGENCE'
        
        return divergence
    
    # ==================== Bollinger Bands ====================
    
    def calculate_bollinger_bands(self, ohlcv_data: pd.DataFrame,
                                 period: int = 20,
                                 std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands
        Volatility bands based on standard deviation
        """
        close = ohlcv_data['close']
        volume = ohlcv_data['volume']
        
        # Calculate middle band (SMA)
        middle_band = close.rolling(window=period).mean()
        
        # Calculate standard deviation
        std = close.rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        # Calculate band width and %B
        band_width = upper_band - lower_band
        pct_b = (close - lower_band) / (upper_band - lower_band)
        
        # Detect squeeze (low volatility)
        band_width_sma = band_width.rolling(window=period).mean()
        squeeze = band_width < band_width_sma * 0.75  # Band width below 75% of average
        
        # Detect band touches and walks
        upper_touch = close >= upper_band * 0.98  # Within 2% of upper band
        lower_touch = close <= lower_band * 1.02  # Within 2% of lower band
        
        # Band walk detection (consecutive touches)
        upper_walk = upper_touch.rolling(window=3).sum() >= 2  # 2+ touches in 3 bars
        lower_walk = lower_touch.rolling(window=3).sum() >= 2
        
        # Volume confirmation
        volume_surge = volume > volume.rolling(window=20).mean() * 1.5
        
        # Generate signals
        bb_signals = {
            'squeeze_signal': squeeze & squeeze.shift(1) & ~squeeze.shift(2),  # Squeeze start
            'breakout_signal': ~squeeze & squeeze.shift(1),  # Squeeze end (potential breakout)
            'overbought': (pct_b > 1) & volume_surge,
            'oversold': (pct_b < 0) & volume_surge,
            'upper_band_walk': upper_walk,
            'lower_band_walk': lower_walk
        }
        
        return {
            'upper_band': upper_band,
            'middle_band': middle_band,
            'lower_band': lower_band,
            'band_width': band_width,
            'pct_b': pct_b,
            'squeeze': squeeze,
            'signals': bb_signals
        }
    
    # ==================== Average True Range (ATR) ====================
    
    def calculate_atr(self, ohlcv_data: pd.DataFrame, 
                     period: int = 14) -> Dict[str, Any]:
        """
        Calculate Average True Range (ATR)
        Volatility indicator for position sizing and stop-loss
        """
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        close = ohlcv_data['close']
        
        # Calculate True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        # True Range is the maximum of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR using Wilder's smoothing
        atr = self._wilder_smoothing(true_range, period)
        
        # Calculate ATR percentage (ATR as % of price)
        atr_percent = (atr / close) * 100
        
        # Volatility classification
        volatility_level = pd.Series('NORMAL', index=close.index)
        volatility_level[atr_percent > 5] = 'VERY_HIGH'
        volatility_level[(atr_percent > 3) & (atr_percent <= 5)] = 'HIGH'
        volatility_level[(atr_percent > 1.5) & (atr_percent <= 3)] = 'MODERATE'
        volatility_level[atr_percent <= 1.5] = 'LOW'
        
        # Calculate position sizing suggestions
        position_sizing = self._calculate_position_sizing(atr, close)
        
        # Calculate dynamic stop-loss levels
        stop_loss_levels = self._calculate_stop_loss_levels(atr, close, high, low)
        
        return {
            'atr': atr,
            'atr_percent': atr_percent,
            'true_range': true_range,
            'volatility_level': volatility_level,
            'position_sizing': position_sizing,
            'stop_loss_levels': stop_loss_levels
        }
    
    def _calculate_position_sizing(self, atr: pd.Series, 
                                  close: pd.Series,
                                  risk_per_trade: float = 0.02) -> pd.DataFrame:
        """Calculate position sizing based on ATR"""
        # Standard position sizing: Risk / (ATR * multiplier)
        conservative_stop = atr * 2
        moderate_stop = atr * 1.5
        aggressive_stop = atr * 1
        
        # Position size as percentage of capital
        conservative_size = risk_per_trade / (conservative_stop / close)
        moderate_size = risk_per_trade / (moderate_stop / close)
        aggressive_size = risk_per_trade / (aggressive_stop / close)
        
        return pd.DataFrame({
            'conservative_size': conservative_size.clip(upper=0.1),  # Max 10% position
            'moderate_size': moderate_size.clip(upper=0.15),  # Max 15% position
            'aggressive_size': aggressive_size.clip(upper=0.2),  # Max 20% position
            'stop_distance_conservative': conservative_stop,
            'stop_distance_moderate': moderate_stop,
            'stop_distance_aggressive': aggressive_stop
        })
    
    def _calculate_stop_loss_levels(self, atr: pd.Series, 
                                   close: pd.Series,
                                   high: pd.Series,
                                   low: pd.Series) -> pd.DataFrame:
        """Calculate dynamic stop-loss levels"""
        # Chandelier Exit style stops
        long_stop_atr = high.rolling(window=22).max() - (atr * 3)
        short_stop_atr = low.rolling(window=22).min() + (atr * 3)
        
        # Percentage-based stops
        long_stop_pct = close * 0.98  # 2% stop
        short_stop_pct = close * 1.02  # 2% stop
        
        # Volatility-adjusted stops
        long_stop_vol = close - (atr * 2)
        short_stop_vol = close + (atr * 2)
        
        return pd.DataFrame({
            'long_stop_atr': long_stop_atr,
            'short_stop_atr': short_stop_atr,
            'long_stop_pct': long_stop_pct,
            'short_stop_pct': short_stop_pct,
            'long_stop_volatility': long_stop_vol,
            'short_stop_volatility': short_stop_vol,
            'trailing_stop_long': pd.concat([long_stop_atr, long_stop_vol], axis=1).max(axis=1),
            'trailing_stop_short': pd.concat([short_stop_atr, short_stop_vol], axis=1).min(axis=1)
        })
    
    # ==================== Complete Analysis ====================
    
    async def analyze_extended(self, symbol: str, 
                              ohlcv_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Complete extended indicator analysis
        """
        analysis = {
            'symbol': symbol,
            'timestamp': time.time(),
            'indicators': {}
        }
        
        # Calculate all extended indicators
        analysis['indicators']['ichimoku'] = self.calculate_ichimoku(ohlcv_data)
        analysis['indicators']['adx'] = self.calculate_adx(ohlcv_data)
        analysis['indicators']['stochastic'] = self.calculate_stochastic(ohlcv_data)
        analysis['indicators']['bollinger'] = self.calculate_bollinger_bands(ohlcv_data)
        analysis['indicators']['atr'] = self.calculate_atr(ohlcv_data)
        
        # Generate master signal
        analysis['master_signal'] = self._generate_master_signal(analysis['indicators'])
        
        # Store in MongoDB if available
        if self.mongodb:
            await self._store_extended_analysis(analysis)
        
        return analysis
    
    def _generate_master_signal(self, indicators: Dict) -> Dict:
        """Generate master trading signal from all indicators"""
        signal = {
            'action': 'NEUTRAL',
            'strength': 0,
            'confidence': 0,
            'conditions': [],
            'risk_level': 'MODERATE'
        }
        
        bullish_count = 0
        bearish_count = 0
        total_weight = 0
        
        # Check Ichimoku
        if 'ichimoku' in indicators and 'signals' in indicators['ichimoku']:
            for ich_signal in indicators['ichimoku']['signals']:
                if ich_signal.direction == 'BULLISH':
                    bullish_count += ich_signal.strength
                else:
                    bearish_count += ich_signal.strength
                total_weight += 1
        
        # Check ADX
        if 'adx' in indicators and 'signals' in indicators['adx']:
            for adx_signal in indicators['adx']['signals']:
                if adx_signal.trend_strength in ['STRONG', 'VERY_STRONG']:
                    if adx_signal.trend_direction == 'BULLISH':
                        bullish_count += 0.8
                    elif adx_signal.trend_direction == 'BEARISH':
                        bearish_count += 0.8
                    total_weight += 0.8
        
        # Check Stochastic
        if 'stochastic' in indicators:
            stoch = indicators['stochastic']
            if not stoch['oversold'].empty and stoch['oversold'].iloc[-1]:
                bullish_count += 0.5
                total_weight += 0.5
            elif not stoch['overbought'].empty and stoch['overbought'].iloc[-1]:
                bearish_count += 0.5
                total_weight += 0.5
        
        # Check Bollinger Bands
        if 'bollinger' in indicators and 'signals' in indicators['bollinger']:
            bb_signals = indicators['bollinger']['signals']
            if 'squeeze_signal' in bb_signals and not bb_signals['squeeze_signal'].empty:
                if bb_signals['squeeze_signal'].iloc[-1]:
                    signal['conditions'].append('BOLLINGER_SQUEEZE')
            if 'upper_band_walk' in bb_signals and not bb_signals['upper_band_walk'].empty:
                if bb_signals['upper_band_walk'].iloc[-1]:
                    bullish_count += 0.6
                    total_weight += 0.6
        
        # Calculate final signal
        if total_weight > 0:
            net_signal = (bullish_count - bearish_count) / total_weight
            
            if net_signal > 0.3:
                signal['action'] = 'BUY'
                signal['strength'] = min(net_signal, 1.0)
            elif net_signal < -0.3:
                signal['action'] = 'SELL'
                signal['strength'] = min(abs(net_signal), 1.0)
            
            signal['confidence'] = min(total_weight / 5, 1.0)  # Max confidence at 5+ indicators
        
        # Set risk level based on ATR
        if 'atr' in indicators and 'volatility_level' in indicators['atr']:
            vol_level = indicators['atr']['volatility_level']
            if not vol_level.empty:
                latest_vol = vol_level.iloc[-1]
                if latest_vol in ['VERY_HIGH', 'HIGH']:
                    signal['risk_level'] = 'HIGH'
                elif latest_vol == 'LOW':
                    signal['risk_level'] = 'LOW'
        
        return signal
    
    async def _store_extended_analysis(self, analysis: Dict):
        """Store extended analysis in MongoDB"""
        if self.mongodb:
            # Prepare data for MongoDB (convert non-serializable types)
            stored_analysis = {
                'symbol': analysis['symbol'],
                'timestamp': analysis['timestamp'],
                'master_signal': analysis['master_signal'],
                'indicator_summary': {
                    'ichimoku_trend': analysis['indicators']['ichimoku'].get('kumo_trend', pd.Series()).iloc[-1] if 'ichimoku' in analysis['indicators'] else None,
                    'adx_value': analysis['indicators']['adx'].get('adx', pd.Series()).iloc[-1] if 'adx' in analysis['indicators'] else None,
                    'stochastic_k': analysis['indicators']['stochastic'].get('slow_k', pd.Series()).iloc[-1] if 'stochastic' in analysis['indicators'] else None,
                    'bollinger_squeeze': analysis['indicators']['bollinger'].get('squeeze', pd.Series()).iloc[-1] if 'bollinger' in analysis['indicators'] else None,
                    'atr_value': analysis['indicators']['atr'].get('atr', pd.Series()).iloc[-1] if 'atr' in analysis['indicators'] else None
                }
            }
            
            await self.mongodb.extended_indicators.insert_one(stored_analysis)