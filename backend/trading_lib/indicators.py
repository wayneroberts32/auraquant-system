"""
AuraQuant Trading Indicators Library
Auto-registering technical indicators with MongoDB integration
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent directory for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import db_config

class IndicatorRegistry:
    """Auto-registering indicator system"""
    
    _indicators: Dict[str, Callable] = {}
    _db_synced = False
    
    @classmethod
    def register(cls, name: str, category: str = 'custom', description: str = ''):
        """Decorator to register indicators"""
        def decorator(func):
            cls._indicators[name] = {
                'function': func,
                'category': category,
                'description': description or func.__doc__ or f'{name} indicator',
                'auto_registered': True,
                'created_at': datetime.utcnow()
            }
            # Sync to MongoDB will be done lazily when needed
            # Removed async task creation here to avoid runtime error
            return func
        return decorator
    
    @classmethod
    async def _sync_to_mongodb(cls):
        """Sync registered indicators to MongoDB"""
        try:
            client = AsyncIOMotorClient(db_config.mongodb_uri)
            db = client[db_config.database_name]
            
            for name, info in cls._indicators.items():
                await db.indicators.update_one(
                    {'name': name},
                    {'$set': {
                        'name': name,
                        'category': info['category'],
                        'description': info['description'],
                        'auto_registered': True,
                        'created_at': info['created_at']
                    }},
                    upsert=True
                )
            
            cls._db_synced = True
            client.close()
        except Exception as e:
            print(f"Warning: Could not sync indicators to MongoDB: {e}")
    
    @classmethod
    def get_all(cls) -> Dict:
        """Get all registered indicators"""
        return cls._indicators
    
    @classmethod
    def get_indicator(cls, name: str) -> Optional[Callable]:
        """Get specific indicator function"""
        return cls._indicators.get(name, {}).get('function')

# Technical Indicators with auto-registration

@IndicatorRegistry.register('SMA', 'trend', 'Simple Moving Average')
def sma(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Simple Moving Average"""
    return data.rolling(window=period).mean()

@IndicatorRegistry.register('EMA', 'trend', 'Exponential Moving Average')
def ema(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return data.ewm(span=period, adjust=False).mean()

@IndicatorRegistry.register('WMA', 'trend', 'Weighted Moving Average')
def wma(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Weighted Moving Average"""
    weights = np.arange(1, period + 1)
    return data.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

@IndicatorRegistry.register('RSI', 'momentum', 'Relative Strength Index')
def rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

@IndicatorRegistry.register('MACD', 'momentum', 'Moving Average Convergence Divergence')
def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """Calculate MACD"""
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }

@IndicatorRegistry.register('StochRSI', 'momentum', 'Stochastic RSI')
def stoch_rsi(data: pd.Series, period: int = 14, smooth_k: int = 3, smooth_d: int = 3) -> Dict[str, pd.Series]:
    """Calculate Stochastic RSI"""
    rsi_values = rsi(data, period)
    
    stoch = (rsi_values - rsi_values.rolling(period).min()) / (
        rsi_values.rolling(period).max() - rsi_values.rolling(period).min()
    ) * 100
    
    k = stoch.rolling(smooth_k).mean()
    d = k.rolling(smooth_d).mean()
    
    return {'k': k, 'd': d}

@IndicatorRegistry.register('BollingerBands', 'volatility', 'Bollinger Bands')
def bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
    """Calculate Bollinger Bands"""
    middle = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower,
        'bandwidth': (upper - lower) / middle
    }

@IndicatorRegistry.register('ATR', 'volatility', 'Average True Range')
def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

@IndicatorRegistry.register('OBV', 'volume', 'On Balance Volume')
def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On Balance Volume"""
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv

@IndicatorRegistry.register('VWAP', 'volume', 'Volume Weighted Average Price')
def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate Volume Weighted Average Price"""
    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / volume.cumsum()

# Advanced Indicators (auto-discovered)

@IndicatorRegistry.register('SuperTrend', 'trend', 'SuperTrend Indicator')
def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> Dict[str, pd.Series]:
    """Calculate SuperTrend indicator"""
    hl_avg = (high + low) / 2
    atr_value = atr(high, low, close, period)
    
    upper_band = hl_avg + (multiplier * atr_value)
    lower_band = hl_avg - (multiplier * atr_value)
    
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    for i in range(period, len(close)):
        if close.iloc[i] <= upper_band.iloc[i]:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1
        else:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
    
    return {'supertrend': supertrend, 'direction': direction}

@IndicatorRegistry.register('IchimokuCloud', 'trend', 'Ichimoku Cloud')
def ichimoku_cloud(high: pd.Series, low: pd.Series, close: pd.Series, 
                   tenkan: int = 9, kijun: int = 26, senkou_b: int = 52) -> Dict[str, pd.Series]:
    """Calculate Ichimoku Cloud components"""
    # Tenkan-sen (Conversion Line)
    tenkan_sen = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    
    # Kijun-sen (Base Line)
    kijun_sen = (high.rolling(kijun).max() + low.rolling(kijun).min()) / 2
    
    # Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun)
    
    # Senkou Span B (Leading Span B)
    senkou_span_b = ((high.rolling(senkou_b).max() + low.rolling(senkou_b).min()) / 2).shift(kijun)
    
    # Chikou Span (Lagging Span)
    chikou_span = close.shift(-kijun)
    
    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }

@IndicatorRegistry.register('FibonacciRetracement', 'support_resistance', 'Fibonacci Retracement Levels')
def fibonacci_retracement(high: pd.Series, low: pd.Series) -> Dict[str, float]:
    """Calculate Fibonacci Retracement levels"""
    max_price = high.max()
    min_price = low.min()
    diff = max_price - min_price
    
    levels = {
        'level_0': max_price,
        'level_236': max_price - diff * 0.236,
        'level_382': max_price - diff * 0.382,
        'level_500': max_price - diff * 0.500,
        'level_618': max_price - diff * 0.618,
        'level_786': max_price - diff * 0.786,
        'level_100': min_price
    }
    
    return levels

# Utility functions

def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all registered indicators for a DataFrame"""
    result = df.copy()
    
    for name, info in IndicatorRegistry.get_all().items():
        func = info['function']
        try:
            if name in ['SMA', 'EMA', 'WMA', 'RSI']:
                result[f'{name}'] = func(df['close'])
            elif name == 'MACD':
                macd_result = func(df['close'])
                for key, value in macd_result.items():
                    result[f'MACD_{key}'] = value
            elif name == 'BollingerBands':
                bb_result = func(df['close'])
                for key, value in bb_result.items():
                    result[f'BB_{key}'] = value
            elif name in ['ATR', 'SuperTrend', 'IchimokuCloud']:
                if all(col in df.columns for col in ['high', 'low', 'close']):
                    if name == 'ATR':
                        result[name] = func(df['high'], df['low'], df['close'])
                    else:
                        indicator_result = func(df['high'], df['low'], df['close'])
                        if isinstance(indicator_result, dict):
                            for key, value in indicator_result.items():
                                result[f'{name}_{key}'] = value
            elif name in ['OBV', 'VWAP']:
                if 'volume' in df.columns:
                    if name == 'OBV':
                        result[name] = func(df['close'], df['volume'])
                    else:
                        result[name] = func(df['high'], df['low'], df['close'], df['volume'])
        except Exception as e:
            print(f"Warning: Could not calculate {name}: {e}")
    
    return result

def get_indicator_list() -> List[Dict[str, str]]:
    """Get list of all available indicators"""
    return [
        {
            'name': name,
            'category': info['category'],
            'description': info['description']
        }
        for name, info in IndicatorRegistry.get_all().items()
    ]

# Export registry for external access
registry = IndicatorRegistry