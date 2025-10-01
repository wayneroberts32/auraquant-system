"""
AuraQuant Professional Trading Strategies
==========================================
Institutional-grade strategies combining multiple indicators
Trend-Following Pullback, Mean Reversion, Breakout Confirmation

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import asyncio
from enum import Enum

# Import our indicators
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.technical_indicators import TechnicalIndicators
from indicators.extended_indicators import ExtendedIndicators
from indicators.pattern_recognition import PatternRecognition

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"

class RiskLevel(Enum):
    CONSERVATIVE = "CONSERVATIVE"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"

@dataclass
class StrategySignal:
    """Comprehensive strategy signal"""
    strategy_name: str
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit_1: float  # First target
    take_profit_2: float  # Second target
    take_profit_3: float  # Third target
    position_size: float  # As percentage of capital
    confidence: float  # 0-1
    risk_reward_ratio: float
    conditions_met: List[str]
    timestamp: float
    expiry_time: float  # Signal expiry

@dataclass
class RiskManagement:
    """Risk management parameters"""
    max_risk_per_trade: float = 0.02  # 2% max risk
    max_positions: int = 5
    max_correlation: float = 0.7
    max_daily_loss: float = 0.06  # 6% daily loss limit
    position_scaling: bool = True
    use_trailing_stop: bool = True
    partial_profits: bool = True  # Take partial profits at targets

class ProfessionalStrategies:
    """
    Professional trading strategies for AuraQuant
    Combining multiple indicators for high-probability setups
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.technical = TechnicalIndicators(mongodb_client)
        self.extended = ExtendedIndicators(mongodb_client)
        self.patterns = PatternRecognition(mongodb_client)
        self.risk_mgmt = RiskManagement()
        self.active_signals = []
        
    # ==================== Strategy 1: Trend-Following Pullback ====================
    
    async def trend_pullback_strategy(self, ohlcv_data: pd.DataFrame,
                                     symbol: str = "",
                                     timeframe: str = "4H") -> List[StrategySignal]:
        """
        The Classic Trend-Following Pullback Strategy
        Buy pullbacks in uptrends, sell rallies in downtrends
        """
        signals = []
        
        # Calculate required indicators
        close = ohlcv_data['close']
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        volume = ohlcv_data['volume']
        
        # Moving Averages
        ema_200 = close.ewm(span=200, adjust=False).mean()
        ema_50 = close.ewm(span=50, adjust=False).mean()
        ema_20 = close.ewm(span=20, adjust=False).mean()
        
        # RSI for momentum
        rsi_data = self.technical.calculate_rsi(close, period=14)
        rsi = rsi_data['rsi'] if isinstance(rsi_data, pd.DataFrame) else rsi_data
        
        # ADX for trend strength
        adx_data = self.extended.calculate_adx(ohlcv_data)
        adx = adx_data['adx']
        plus_di = adx_data['plus_di']
        minus_di = adx_data['minus_di']
        
        # ATR for volatility
        atr_data = self.extended.calculate_atr(ohlcv_data)
        atr = atr_data['atr']
        
        # Bollinger Bands for volatility context
        bb_data = self.extended.calculate_bollinger_bands(ohlcv_data)
        bb_lower = bb_data['lower_band']
        bb_upper = bb_data['upper_band']
        
        # Check each bar for setup conditions
        for i in range(201, len(close)):  # Need 200 bars for EMA 200
            conditions_met = []
            
            # === LONG SETUP ===
            # 1. Primary trend confirmation
            uptrend = (close.iloc[i] > ema_200.iloc[i] and 
                      ema_50.iloc[i] > ema_200.iloc[i] and
                      ema_20.iloc[i] > ema_50.iloc[i])
            
            if uptrend:
                conditions_met.append("UPTREND_CONFIRMED")
                
                # 2. ADX confirms strong trend
                if adx.iloc[i] > 25 and plus_di.iloc[i] > minus_di.iloc[i]:
                    conditions_met.append("ADX_STRONG_TREND")
                    
                    # 3. Pullback to support (50 EMA or 20 EMA)
                    pullback_to_50 = abs(low.iloc[i] - ema_50.iloc[i]) / ema_50.iloc[i] < 0.005
                    pullback_to_20 = abs(low.iloc[i] - ema_20.iloc[i]) / ema_20.iloc[i] < 0.005
                    
                    if pullback_to_50 or pullback_to_20:
                        conditions_met.append("PULLBACK_TO_EMA")
                        
                        # 4. RSI momentum check (not oversold but recovering)
                        if 30 <= rsi.iloc[i] <= 50 and rsi.iloc[i] > rsi.iloc[i-1]:
                            conditions_met.append("RSI_MOMENTUM_POSITIVE")
                            
                            # 5. Volume confirmation (increasing on bounce)
                            if volume.iloc[i] > volume.rolling(20).mean().iloc[i]:
                                conditions_met.append("VOLUME_CONFIRMATION")
                                
                                # 6. Candlestick pattern confirmation
                                bullish_reversal = self._check_bullish_reversal(ohlcv_data, i)
                                if bullish_reversal:
                                    conditions_met.append("BULLISH_REVERSAL_PATTERN")
                                    
                                    # Generate LONG signal
                                    entry = close.iloc[i]
                                    stop_loss = low.iloc[i] - (atr.iloc[i] * 1.5)
                                    
                                    # Multiple targets based on R:R
                                    risk = entry - stop_loss
                                    tp1 = entry + (risk * 1.5)  # 1.5:1 R:R
                                    tp2 = entry + (risk * 2.5)  # 2.5:1 R:R
                                    tp3 = entry + (risk * 4.0)  # 4:1 R:R
                                    
                                    # Position sizing based on ATR
                                    position_size = self._calculate_position_size(
                                        atr.iloc[i], close.iloc[i], self.risk_mgmt.max_risk_per_trade
                                    )
                                    
                                    signals.append(StrategySignal(
                                        strategy_name="TREND_PULLBACK_LONG",
                                        direction=TradeDirection.LONG,
                                        entry_price=entry,
                                        stop_loss=stop_loss,
                                        take_profit_1=tp1,
                                        take_profit_2=tp2,
                                        take_profit_3=tp3,
                                        position_size=position_size,
                                        confidence=min(len(conditions_met) / 6, 1.0),
                                        risk_reward_ratio=2.5,
                                        conditions_met=conditions_met,
                                        timestamp=time.time(),
                                        expiry_time=time.time() + (3600 * 24)  # 24 hour expiry
                                    ))
            
            # === SHORT SETUP ===
            # 1. Primary trend confirmation
            downtrend = (close.iloc[i] < ema_200.iloc[i] and 
                        ema_50.iloc[i] < ema_200.iloc[i] and
                        ema_20.iloc[i] < ema_50.iloc[i])
            
            if downtrend:
                conditions_met = ["DOWNTREND_CONFIRMED"]
                
                # 2. ADX confirms strong trend
                if adx.iloc[i] > 25 and minus_di.iloc[i] > plus_di.iloc[i]:
                    conditions_met.append("ADX_STRONG_TREND")
                    
                    # 3. Rally to resistance (50 EMA or 20 EMA)
                    rally_to_50 = abs(high.iloc[i] - ema_50.iloc[i]) / ema_50.iloc[i] < 0.005
                    rally_to_20 = abs(high.iloc[i] - ema_20.iloc[i]) / ema_20.iloc[i] < 0.005
                    
                    if rally_to_50 or rally_to_20:
                        conditions_met.append("RALLY_TO_EMA")
                        
                        # 4. RSI momentum check
                        if 50 <= rsi.iloc[i] <= 70 and rsi.iloc[i] < rsi.iloc[i-1]:
                            conditions_met.append("RSI_MOMENTUM_NEGATIVE")
                            
                            # 5. Volume confirmation
                            if volume.iloc[i] > volume.rolling(20).mean().iloc[i]:
                                conditions_met.append("VOLUME_CONFIRMATION")
                                
                                # 6. Candlestick pattern confirmation
                                bearish_reversal = self._check_bearish_reversal(ohlcv_data, i)
                                if bearish_reversal:
                                    conditions_met.append("BEARISH_REVERSAL_PATTERN")
                                    
                                    # Generate SHORT signal
                                    entry = close.iloc[i]
                                    stop_loss = high.iloc[i] + (atr.iloc[i] * 1.5)
                                    
                                    risk = stop_loss - entry
                                    tp1 = entry - (risk * 1.5)
                                    tp2 = entry - (risk * 2.5)
                                    tp3 = entry - (risk * 4.0)
                                    
                                    position_size = self._calculate_position_size(
                                        atr.iloc[i], close.iloc[i], self.risk_mgmt.max_risk_per_trade
                                    )
                                    
                                    signals.append(StrategySignal(
                                        strategy_name="TREND_PULLBACK_SHORT",
                                        direction=TradeDirection.SHORT,
                                        entry_price=entry,
                                        stop_loss=stop_loss,
                                        take_profit_1=tp1,
                                        take_profit_2=tp2,
                                        take_profit_3=tp3,
                                        position_size=position_size,
                                        confidence=min(len(conditions_met) / 6, 1.0),
                                        risk_reward_ratio=2.5,
                                        conditions_met=conditions_met,
                                        timestamp=time.time(),
                                        expiry_time=time.time() + (3600 * 24)
                                    ))
        
        return signals
    
    # ==================== Strategy 2: Mean Reversion / Range Trading ====================
    
    async def mean_reversion_strategy(self, ohlcv_data: pd.DataFrame,
                                     symbol: str = "",
                                     timeframe: str = "1H") -> List[StrategySignal]:
        """
        Mean Reversion Strategy for Range-Bound Markets
        Buy at support, sell at resistance within defined ranges
        """
        signals = []
        
        # Calculate indicators
        close = ohlcv_data['close']
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        volume = ohlcv_data['volume']
        
        # RSI for oversold/overbought
        rsi_data = self.technical.calculate_rsi(close)
        rsi = rsi_data['rsi'] if isinstance(rsi_data, pd.DataFrame) else rsi_data
        
        # Stochastic for momentum
        stoch_data = self.extended.calculate_stochastic(ohlcv_data)
        stoch_k = stoch_data['slow_k']
        stoch_d = stoch_data['slow_d']
        
        # Bollinger Bands for range boundaries
        bb_data = self.extended.calculate_bollinger_bands(ohlcv_data)
        bb_upper = bb_data['upper_band']
        bb_lower = bb_data['lower_band']
        bb_middle = bb_data['middle_band']
        pct_b = bb_data['pct_b']
        
        # ADX to confirm ranging market
        adx_data = self.extended.calculate_adx(ohlcv_data)
        adx = adx_data['adx']
        
        # ATR for stops
        atr_data = self.extended.calculate_atr(ohlcv_data)
        atr = atr_data['atr']
        
        # Support/Resistance levels
        sr_levels = self.patterns.detect_support_resistance(ohlcv_data, min_touches=3)
        
        # Identify ranging periods (ADX < 25)
        for i in range(50, len(close)):  # Need history for indicators
            if adx.iloc[i] < 25:  # Confirming range-bound market
                conditions_met = ["RANGE_MARKET_CONFIRMED"]
                
                # === LONG SETUP (Buy at Support) ===
                # 1. Price at lower Bollinger Band
                at_lower_band = close.iloc[i] <= bb_lower.iloc[i] * 1.01
                
                # 2. Check if near support level
                near_support = False
                support_level = None
                for level in sr_levels:
                    if level.level_type == "SUPPORT":
                        if abs(close.iloc[i] - level.level) / level.level < 0.01:  # Within 1%
                            near_support = True
                            support_level = level.level
                            break
                
                if at_lower_band or near_support:
                    if at_lower_band:
                        conditions_met.append("AT_LOWER_BAND")
                    if near_support:
                        conditions_met.append("AT_SUPPORT_LEVEL")
                    
                    # 3. RSI oversold
                    if rsi.iloc[i] < 30:
                        conditions_met.append("RSI_OVERSOLD")
                        
                        # 4. Stochastic oversold and turning up
                        if stoch_k.iloc[i] < 20 and stoch_k.iloc[i] > stoch_k.iloc[i-1]:
                            conditions_met.append("STOCH_OVERSOLD_REVERSAL")
                            
                            # 5. %B near 0 (price at lower band)
                            if pct_b.iloc[i] < 0.2:
                                conditions_met.append("PERCENT_B_OVERSOLD")
                                
                                # 6. Volume spike (capitulation)
                                if volume.iloc[i] > volume.rolling(20).mean().iloc[i] * 1.5:
                                    conditions_met.append("VOLUME_SPIKE")
                                    
                                    # Generate LONG signal
                                    entry = close.iloc[i]
                                    
                                    # Stop below support or lower band
                                    if support_level:
                                        stop_loss = support_level - (atr.iloc[i] * 0.5)
                                    else:
                                        stop_loss = bb_lower.iloc[i] - (atr.iloc[i] * 0.5)
                                    
                                    # Targets at middle and upper band
                                    tp1 = bb_middle.iloc[i]
                                    tp2 = bb_upper.iloc[i] * 0.98
                                    tp3 = bb_upper.iloc[i] + (atr.iloc[i] * 0.5)
                                    
                                    risk = entry - stop_loss
                                    rr_ratio = (tp2 - entry) / risk if risk > 0 else 0
                                    
                                    position_size = self._calculate_position_size(
                                        atr.iloc[i], close.iloc[i], self.risk_mgmt.max_risk_per_trade
                                    )
                                    
                                    signals.append(StrategySignal(
                                        strategy_name="MEAN_REVERSION_LONG",
                                        direction=TradeDirection.LONG,
                                        entry_price=entry,
                                        stop_loss=stop_loss,
                                        take_profit_1=tp1,
                                        take_profit_2=tp2,
                                        take_profit_3=tp3,
                                        position_size=position_size,
                                        confidence=min(len(conditions_met) / 6, 1.0),
                                        risk_reward_ratio=rr_ratio,
                                        conditions_met=conditions_met,
                                        timestamp=time.time(),
                                        expiry_time=time.time() + (3600 * 12)  # 12 hour expiry
                                    ))
                
                # === SHORT SETUP (Sell at Resistance) ===
                # 1. Price at upper Bollinger Band
                at_upper_band = close.iloc[i] >= bb_upper.iloc[i] * 0.99
                
                # 2. Check if near resistance level
                near_resistance = False
                resistance_level = None
                for level in sr_levels:
                    if level.level_type == "RESISTANCE":
                        if abs(close.iloc[i] - level.level) / level.level < 0.01:
                            near_resistance = True
                            resistance_level = level.level
                            break
                
                if at_upper_band or near_resistance:
                    conditions_met = ["RANGE_MARKET_CONFIRMED"]
                    if at_upper_band:
                        conditions_met.append("AT_UPPER_BAND")
                    if near_resistance:
                        conditions_met.append("AT_RESISTANCE_LEVEL")
                    
                    # 3. RSI overbought
                    if rsi.iloc[i] > 70:
                        conditions_met.append("RSI_OVERBOUGHT")
                        
                        # 4. Stochastic overbought and turning down
                        if stoch_k.iloc[i] > 80 and stoch_k.iloc[i] < stoch_k.iloc[i-1]:
                            conditions_met.append("STOCH_OVERBOUGHT_REVERSAL")
                            
                            # 5. %B near 1 (price at upper band)
                            if pct_b.iloc[i] > 0.8:
                                conditions_met.append("PERCENT_B_OVERBOUGHT")
                                
                                # 6. Volume spike
                                if volume.iloc[i] > volume.rolling(20).mean().iloc[i] * 1.5:
                                    conditions_met.append("VOLUME_SPIKE")
                                    
                                    # Generate SHORT signal
                                    entry = close.iloc[i]
                                    
                                    if resistance_level:
                                        stop_loss = resistance_level + (atr.iloc[i] * 0.5)
                                    else:
                                        stop_loss = bb_upper.iloc[i] + (atr.iloc[i] * 0.5)
                                    
                                    tp1 = bb_middle.iloc[i]
                                    tp2 = bb_lower.iloc[i] * 1.02
                                    tp3 = bb_lower.iloc[i] - (atr.iloc[i] * 0.5)
                                    
                                    risk = stop_loss - entry
                                    rr_ratio = (entry - tp2) / risk if risk > 0 else 0
                                    
                                    position_size = self._calculate_position_size(
                                        atr.iloc[i], close.iloc[i], self.risk_mgmt.max_risk_per_trade
                                    )
                                    
                                    signals.append(StrategySignal(
                                        strategy_name="MEAN_REVERSION_SHORT",
                                        direction=TradeDirection.SHORT,
                                        entry_price=entry,
                                        stop_loss=stop_loss,
                                        take_profit_1=tp1,
                                        take_profit_2=tp2,
                                        take_profit_3=tp3,
                                        position_size=position_size,
                                        confidence=min(len(conditions_met) / 6, 1.0),
                                        risk_reward_ratio=rr_ratio,
                                        conditions_met=conditions_met,
                                        timestamp=time.time(),
                                        expiry_time=time.time() + (3600 * 12)
                                    ))
        
        return signals
    
    # ==================== Strategy 3: Breakout with Confirmation ====================
    
    async def breakout_strategy(self, ohlcv_data: pd.DataFrame,
                               symbol: str = "",
                               timeframe: str = "1H") -> List[StrategySignal]:
        """
        Breakout Strategy with Multiple Confirmations
        Enter on breakouts from consolidation with volume and momentum confirmation
        """
        signals = []
        
        # Calculate indicators
        close = ohlcv_data['close']
        high = ohlcv_data['high']
        low = ohlcv_data['low']
        volume = ohlcv_data['volume']
        
        # Bollinger Bands for squeeze detection
        bb_data = self.extended.calculate_bollinger_bands(ohlcv_data, period=20)
        bb_upper = bb_data['upper_band']
        bb_lower = bb_data['lower_band']
        bb_width = bb_data['band_width']
        squeeze = bb_data['squeeze']
        
        # MACD for momentum
        macd_data = self.technical.calculate_macd(close)
        macd = macd_data['macd']
        macd_signal = macd_data['signal']
        macd_histogram = macd_data['histogram']
        
        # RSI for momentum confirmation
        rsi_data = self.technical.calculate_rsi(close)
        rsi = rsi_data['rsi'] if isinstance(rsi_data, pd.DataFrame) else rsi_data
        
        # ATR for volatility and stops
        atr_data = self.extended.calculate_atr(ohlcv_data)
        atr = atr_data['atr']
        
        # Volume analysis
        volume_sma = volume.rolling(window=20).mean()
        volume_ratio = volume / volume_sma
        
        # Identify consolidation patterns
        for i in range(50, len(close)):
            conditions_met = []
            
            # Check for Bollinger Band squeeze (consolidation)
            if squeeze.iloc[i-1] and not squeeze.iloc[i]:  # Squeeze just ended
                conditions_met.append("SQUEEZE_BREAKOUT")
                
                # === LONG BREAKOUT ===
                # 1. Price breaks above upper band
                if close.iloc[i] > bb_upper.iloc[i] and close.iloc[i-1] <= bb_upper.iloc[i-1]:
                    conditions_met.append("UPPER_BAND_BREAKOUT")
                    
                    # 2. Volume confirmation (50% above average)
                    if volume_ratio.iloc[i] > 1.5:
                        conditions_met.append("VOLUME_SURGE")
                        
                        # 3. MACD bullish (above signal and positive)
                        if macd.iloc[i] > macd_signal.iloc[i] and macd.iloc[i] > 0:
                            conditions_met.append("MACD_BULLISH")
                            
                            # 4. RSI strong but not overbought (50-70)
                            if 50 < rsi.iloc[i] < 70:
                                conditions_met.append("RSI_STRONG")
                                
                                # 5. Price above recent high
                                recent_high = high.iloc[i-20:i].max()
                                if close.iloc[i] > recent_high:
                                    conditions_met.append("NEW_HIGH_BREAKOUT")
                                    
                                    # 6. ATR expanding (volatility increasing)
                                    if atr.iloc[i] > atr.iloc[i-5]:
                                        conditions_met.append("VOLATILITY_EXPANSION")
                                        
                                        # Generate LONG signal
                                        entry = close.iloc[i]
                                        
                                        # Stop below breakout level or recent low
                                        stop_loss = min(bb_upper.iloc[i] - atr.iloc[i],
                                                      low.iloc[i-20:i].min())
                                        
                                        # Targets using ATR projection
                                        tp1 = entry + (atr.iloc[i] * 1.5)
                                        tp2 = entry + (atr.iloc[i] * 3)
                                        tp3 = entry + (atr.iloc[i] * 5)
                                        
                                        risk = entry - stop_loss
                                        rr_ratio = (tp2 - entry) / risk if risk > 0 else 0
                                        
                                        position_size = self._calculate_position_size(
                                            atr.iloc[i], close.iloc[i], 
                                            self.risk_mgmt.max_risk_per_trade * 0.8  # Smaller size for breakouts
                                        )
                                        
                                        signals.append(StrategySignal(
                                            strategy_name="BREAKOUT_LONG",
                                            direction=TradeDirection.LONG,
                                            entry_price=entry,
                                            stop_loss=stop_loss,
                                            take_profit_1=tp1,
                                            take_profit_2=tp2,
                                            take_profit_3=tp3,
                                            position_size=position_size,
                                            confidence=min(len(conditions_met) / 6, 1.0),
                                            risk_reward_ratio=rr_ratio,
                                            conditions_met=conditions_met,
                                            timestamp=time.time(),
                                            expiry_time=time.time() + (3600 * 8)  # 8 hour expiry
                                        ))
                
                # === SHORT BREAKOUT ===
                # 1. Price breaks below lower band
                elif close.iloc[i] < bb_lower.iloc[i] and close.iloc[i-1] >= bb_lower.iloc[i-1]:
                    conditions_met.append("LOWER_BAND_BREAKOUT")
                    
                    # 2. Volume confirmation
                    if volume_ratio.iloc[i] > 1.5:
                        conditions_met.append("VOLUME_SURGE")
                        
                        # 3. MACD bearish
                        if macd.iloc[i] < macd_signal.iloc[i] and macd.iloc[i] < 0:
                            conditions_met.append("MACD_BEARISH")
                            
                            # 4. RSI weak but not oversold (30-50)
                            if 30 < rsi.iloc[i] < 50:
                                conditions_met.append("RSI_WEAK")
                                
                                # 5. Price below recent low
                                recent_low = low.iloc[i-20:i].min()
                                if close.iloc[i] < recent_low:
                                    conditions_met.append("NEW_LOW_BREAKOUT")
                                    
                                    # 6. ATR expanding
                                    if atr.iloc[i] > atr.iloc[i-5]:
                                        conditions_met.append("VOLATILITY_EXPANSION")
                                        
                                        # Generate SHORT signal
                                        entry = close.iloc[i]
                                        
                                        stop_loss = max(bb_lower.iloc[i] + atr.iloc[i],
                                                      high.iloc[i-20:i].max())
                                        
                                        tp1 = entry - (atr.iloc[i] * 1.5)
                                        tp2 = entry - (atr.iloc[i] * 3)
                                        tp3 = entry - (atr.iloc[i] * 5)
                                        
                                        risk = stop_loss - entry
                                        rr_ratio = (entry - tp2) / risk if risk > 0 else 0
                                        
                                        position_size = self._calculate_position_size(
                                            atr.iloc[i], close.iloc[i],
                                            self.risk_mgmt.max_risk_per_trade * 0.8
                                        )
                                        
                                        signals.append(StrategySignal(
                                            strategy_name="BREAKOUT_SHORT",
                                            direction=TradeDirection.SHORT,
                                            entry_price=entry,
                                            stop_loss=stop_loss,
                                            take_profit_1=tp1,
                                            take_profit_2=tp2,
                                            take_profit_3=tp3,
                                            position_size=position_size,
                                            confidence=min(len(conditions_met) / 6, 1.0),
                                            risk_reward_ratio=rr_ratio,
                                            conditions_met=conditions_met,
                                            timestamp=time.time(),
                                            expiry_time=time.time() + (3600 * 8)
                                        ))
        
        return signals
    
    # ==================== Helper Functions ====================
    
    def _check_bullish_reversal(self, ohlcv_data: pd.DataFrame, idx: int) -> bool:
        """Check for bullish reversal candlestick patterns"""
        if idx < 2:
            return False
        
        open_price = ohlcv_data['open'].iloc[idx]
        close = ohlcv_data['close'].iloc[idx]
        high = ohlcv_data['high'].iloc[idx]
        low = ohlcv_data['low'].iloc[idx]
        
        prev_close = ohlcv_data['close'].iloc[idx-1]
        prev_open = ohlcv_data['open'].iloc[idx-1]
        
        # Hammer pattern
        body = abs(close - open_price)
        lower_shadow = min(open_price, close) - low
        upper_shadow = high - max(open_price, close)
        
        if lower_shadow >= body * 2 and upper_shadow <= body * 0.3:
            return True
        
        # Bullish engulfing
        if (prev_close < prev_open and  # Previous bearish
            close > open_price and  # Current bullish
            open_price <= prev_close and  # Opens below prev close
            close >= prev_open):  # Closes above prev open
            return True
        
        return False
    
    def _check_bearish_reversal(self, ohlcv_data: pd.DataFrame, idx: int) -> bool:
        """Check for bearish reversal candlestick patterns"""
        if idx < 2:
            return False
        
        open_price = ohlcv_data['open'].iloc[idx]
        close = ohlcv_data['close'].iloc[idx]
        high = ohlcv_data['high'].iloc[idx]
        low = ohlcv_data['low'].iloc[idx]
        
        prev_close = ohlcv_data['close'].iloc[idx-1]
        prev_open = ohlcv_data['open'].iloc[idx-1]
        
        # Shooting star pattern
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        
        if upper_shadow >= body * 2 and lower_shadow <= body * 0.3:
            return True
        
        # Bearish engulfing
        if (prev_close > prev_open and  # Previous bullish
            close < open_price and  # Current bearish
            open_price >= prev_close and  # Opens above prev close
            close <= prev_open):  # Closes below prev open
            return True
        
        return False
    
    def _calculate_position_size(self, atr: float, price: float, 
                                max_risk: float) -> float:
        """Calculate position size based on ATR and risk management"""
        if atr <= 0 or price <= 0:
            return 0.01  # Minimum position
        
        # Stop distance as multiple of ATR
        stop_distance = atr * 2
        stop_distance_pct = stop_distance / price
        
        # Position size to risk max_risk of capital
        position_size = max_risk / stop_distance_pct
        
        # Cap position size
        position_size = min(position_size, 0.2)  # Max 20% per position
        position_size = max(position_size, 0.01)  # Min 1% per position
        
        return round(position_size, 4)
    
    # ==================== Master Strategy Combiner ====================
    
    async def analyze_all_strategies(self, ohlcv_data: pd.DataFrame,
                                    symbol: str = "",
                                    timeframe: str = "1H") -> Dict[str, Any]:
        """
        Run all strategies and combine signals
        """
        analysis = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': time.time(),
            'strategies': {}
        }
        
        # Run all strategies
        trend_signals = await self.trend_pullback_strategy(ohlcv_data, symbol, timeframe)
        mean_signals = await self.mean_reversion_strategy(ohlcv_data, symbol, timeframe)
        breakout_signals = await self.breakout_strategy(ohlcv_data, symbol, timeframe)
        
        # Store signals
        analysis['strategies']['trend_pullback'] = trend_signals
        analysis['strategies']['mean_reversion'] = mean_signals
        analysis['strategies']['breakout'] = breakout_signals
        
        # Combine and rank signals
        all_signals = trend_signals + mean_signals + breakout_signals
        
        # Filter and rank by confidence
        high_confidence_signals = [s for s in all_signals if s.confidence >= 0.7]
        high_confidence_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        analysis['high_confidence_signals'] = high_confidence_signals
        analysis['total_signals'] = len(all_signals)
        analysis['actionable_signals'] = len(high_confidence_signals)
        
        # Risk assessment
        analysis['risk_assessment'] = self._assess_portfolio_risk(high_confidence_signals)
        
        # Store in MongoDB
        if self.mongodb:
            await self._store_strategy_analysis(analysis)
        
        return analysis
    
    def _assess_portfolio_risk(self, signals: List[StrategySignal]) -> Dict:
        """Assess overall portfolio risk from signals"""
        if not signals:
            return {'risk_level': 'LOW', 'open_risk': 0, 'correlation_risk': 'LOW'}
        
        total_position_size = sum(s.position_size for s in signals)
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        risk_assessment = {
            'total_exposure': total_position_size,
            'signal_count': len(signals),
            'avg_confidence': avg_confidence,
            'max_position_size': max(s.position_size for s in signals),
            'risk_level': 'MODERATE'
        }
        
        if total_position_size > 0.5:
            risk_assessment['risk_level'] = 'HIGH'
        elif total_position_size < 0.2:
            risk_assessment['risk_level'] = 'LOW'
        
        return risk_assessment
    
    async def _store_strategy_analysis(self, analysis: Dict):
        """Store strategy analysis in MongoDB"""
        if self.mongodb:
            # Convert signals to storable format
            stored_analysis = {
                'symbol': analysis['symbol'],
                'timeframe': analysis['timeframe'],
                'timestamp': analysis['timestamp'],
                'total_signals': analysis['total_signals'],
                'actionable_signals': analysis['actionable_signals'],
                'risk_assessment': analysis['risk_assessment'],
                'signal_summary': []
            }
            
            for signal in analysis.get('high_confidence_signals', []):
                stored_analysis['signal_summary'].append({
                    'strategy': signal.strategy_name,
                    'direction': signal.direction.value,
                    'entry': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit_2': signal.take_profit_2,
                    'confidence': signal.confidence,
                    'risk_reward': signal.risk_reward_ratio,
                    'position_size': signal.position_size
                })
            
            await self.mongodb.strategy_signals.insert_one(stored_analysis)