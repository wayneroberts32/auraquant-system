"""
AuraQuant Trading Strategies Library
Auto-registering trading strategies with MongoDB integration
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import db_config
from trading_lib.indicators import *

class StrategyRegistry:
    """Auto-registering strategy system"""
    
    _strategies: Dict[str, Dict] = {}
    _db_synced = False
    
    @classmethod
    def register(cls, name: str, strategy_type: str = 'custom', description: str = ''):
        """Decorator to register strategies"""
        def decorator(func):
            cls._strategies[name] = {
                'function': func,
                'type': strategy_type,
                'description': description or func.__doc__ or f'{name} strategy',
                'auto_registered': True,
                'status': 'active',
                'created_at': datetime.utcnow()
            }
            # Sync to MongoDB on registration
            if not cls._db_synced:
                asyncio.create_task(cls._sync_to_mongodb())
            return func
        return decorator
    
    @classmethod
    async def _sync_to_mongodb(cls):
        """Sync registered strategies to MongoDB"""
        try:
            client = AsyncIOMotorClient(db_config.mongodb_uri)
            db = client[db_config.database_name]
            
            for name, info in cls._strategies.items():
                await db.strategies.update_one(
                    {'name': name},
                    {'$set': {
                        'name': name,
                        'type': info['type'],
                        'description': info['description'],
                        'auto_registered': True,
                        'status': info['status'],
                        'created_at': info['created_at']
                    }},
                    upsert=True
                )
            
            cls._db_synced = True
            client.close()
        except Exception as e:
            print(f"Warning: Could not sync strategies to MongoDB: {e}")
    
    @classmethod
    def get_all(cls) -> Dict:
        """Get all registered strategies"""
        return cls._strategies
    
    @classmethod
    def get_strategy(cls, name: str) -> Optional[Callable]:
        """Get specific strategy function"""
        return cls._strategies.get(name, {}).get('function')

# Base Strategy Class
class BaseStrategy:
    """Base class for trading strategies"""
    
    def __init__(self, df: pd.DataFrame, **params):
        self.df = df
        self.params = params
        self.signals = pd.Series(index=df.index, dtype=float).fillna(0)
        
    def generate_signals(self) -> pd.Series:
        """Generate trading signals (to be implemented by subclasses)"""
        raise NotImplementedError
        
    def backtest(self, initial_capital: float = 10000) -> Dict:
        """Run backtest on generated signals"""
        signals = self.generate_signals()
        
        # Calculate returns
        returns = self.df['close'].pct_change()
        strategy_returns = signals.shift(1) * returns
        
        # Calculate cumulative returns
        cum_returns = (1 + strategy_returns).cumprod()
        equity_curve = initial_capital * cum_returns
        
        # Calculate metrics
        total_return = (equity_curve.iloc[-1] / initial_capital - 1) * 100
        trades = signals.diff().fillna(0) != 0
        num_trades = trades.sum()
        
        winning_trades = strategy_returns[strategy_returns > 0]
        losing_trades = strategy_returns[strategy_returns < 0]
        
        win_rate = len(winning_trades) / len(strategy_returns[strategy_returns != 0]) * 100 if len(strategy_returns[strategy_returns != 0]) > 0 else 0
        
        return {
            'total_return': total_return,
            'num_trades': int(num_trades),
            'win_rate': win_rate,
            'equity_curve': equity_curve,
            'signals': signals
        }

# Trading Strategies with auto-registration

@StrategyRegistry.register('SMA_Crossover', 'trend_following', 'Simple Moving Average Crossover')
def sma_crossover(df: pd.DataFrame, fast_period: int = 10, slow_period: int = 20) -> pd.Series:
    """SMA Crossover Strategy"""
    fast_sma = sma(df['close'], fast_period)
    slow_sma = sma(df['close'], slow_period)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[fast_sma > slow_sma] = 1.0  # Buy signal
    signals[fast_sma < slow_sma] = -1.0  # Sell signal
    
    return signals

@StrategyRegistry.register('EMA_Crossover', 'trend_following', 'Exponential Moving Average Crossover')
def ema_crossover(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26) -> pd.Series:
    """EMA Crossover Strategy"""
    fast_ema = ema(df['close'], fast_period)
    slow_ema = ema(df['close'], slow_period)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[fast_ema > slow_ema] = 1.0
    signals[fast_ema < slow_ema] = -1.0
    
    return signals

@StrategyRegistry.register('RSI_Oversold_Overbought', 'mean_reversion', 'RSI Mean Reversion')
def rsi_strategy(df: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70) -> pd.Series:
    """RSI Oversold/Overbought Strategy"""
    rsi_values = rsi(df['close'], period)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[rsi_values < oversold] = 1.0  # Buy when oversold
    signals[rsi_values > overbought] = -1.0  # Sell when overbought
    
    return signals

@StrategyRegistry.register('MACD_Signal', 'momentum', 'MACD Signal Line Crossover')
def macd_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    """MACD Signal Line Crossover Strategy"""
    macd_result = macd(df['close'], fast, slow, signal)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[macd_result['macd'] > macd_result['signal']] = 1.0
    signals[macd_result['macd'] < macd_result['signal']] = -1.0
    
    return signals

@StrategyRegistry.register('Bollinger_Breakout', 'breakout', 'Bollinger Bands Breakout')
def bollinger_breakout(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.Series:
    """Bollinger Bands Breakout Strategy"""
    bb = bollinger_bands(df['close'], period, std_dev)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[df['close'] > bb['upper']] = 1.0  # Buy on upper band breakout
    signals[df['close'] < bb['lower']] = -1.0  # Sell on lower band breakdown
    
    return signals

@StrategyRegistry.register('Bollinger_MeanReversion', 'mean_reversion', 'Bollinger Bands Mean Reversion')
def bollinger_mean_reversion(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.Series:
    """Bollinger Bands Mean Reversion Strategy"""
    bb = bollinger_bands(df['close'], period, std_dev)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[df['close'] < bb['lower']] = 1.0  # Buy at lower band
    signals[df['close'] > bb['upper']] = -1.0  # Sell at upper band
    
    return signals

@StrategyRegistry.register('Volume_Momentum', 'volume', 'Volume-based Momentum')
def volume_momentum(df: pd.DataFrame, volume_ma: int = 20, price_ma: int = 10) -> pd.Series:
    """Volume Momentum Strategy"""
    if 'volume' not in df.columns:
        return pd.Series(index=df.index, dtype=float).fillna(0)
    
    volume_sma = sma(df['volume'], volume_ma)
    price_sma = sma(df['close'], price_ma)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    
    # Buy when volume and price are above their moving averages
    signals[(df['volume'] > volume_sma) & (df['close'] > price_sma)] = 1.0
    signals[(df['volume'] < volume_sma) & (df['close'] < price_sma)] = -1.0
    
    return signals

@StrategyRegistry.register('StochRSI_Strategy', 'momentum', 'Stochastic RSI Strategy')
def stochrsi_strategy(df: pd.DataFrame, period: int = 14, oversold: int = 20, overbought: int = 80) -> pd.Series:
    """Stochastic RSI Strategy"""
    stoch = stoch_rsi(df['close'], period)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[stoch['k'] < oversold] = 1.0
    signals[stoch['k'] > overbought] = -1.0
    
    return signals

@StrategyRegistry.register('MultiIndicator_Composite', 'composite', 'Multiple Indicator Composite Strategy')
def multi_indicator_strategy(df: pd.DataFrame, rsi_period: int = 14, sma_fast: int = 10, sma_slow: int = 30) -> pd.Series:
    """Composite strategy using multiple indicators"""
    rsi_values = rsi(df['close'], rsi_period)
    fast_sma = sma(df['close'], sma_fast)
    slow_sma = sma(df['close'], sma_slow)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    
    # Buy when RSI is oversold AND price is above slow SMA (trend filter)
    buy_condition = (rsi_values < 30) & (df['close'] > slow_sma)
    sell_condition = (rsi_values > 70) & (df['close'] < slow_sma)
    
    signals[buy_condition] = 1.0
    signals[sell_condition] = -1.0
    
    return signals

@StrategyRegistry.register('ATR_Breakout', 'volatility', 'ATR-based Breakout Strategy')
def atr_breakout(df: pd.DataFrame, atr_period: int = 14, multiplier: float = 2.0) -> pd.Series:
    """ATR Breakout Strategy"""
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return pd.Series(index=df.index, dtype=float).fillna(0)
    
    atr_values = atr(df['high'], df['low'], df['close'], atr_period)
    sma_values = sma(df['close'], 20)
    
    upper_band = sma_values + (atr_values * multiplier)
    lower_band = sma_values - (atr_values * multiplier)
    
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    signals[df['close'] > upper_band] = 1.0
    signals[df['close'] < lower_band] = -1.0
    
    return signals

@StrategyRegistry.register('SuperTrend_Strategy', 'trend', 'SuperTrend Following Strategy')
def supertrend_strategy(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """SuperTrend Strategy"""
    if not all(col in df.columns for col in ['high', 'low', 'close']):
        return pd.Series(index=df.index, dtype=float).fillna(0)
    
    st = supertrend(df['high'], df['low'], df['close'], period, multiplier)
    
    signals = st['direction'].copy()
    return signals

# Advanced ML-Ready Strategy Template
@StrategyRegistry.register('ML_Predictive', 'machine_learning', 'Machine Learning Predictive Strategy')
def ml_predictive_strategy(df: pd.DataFrame, lookback: int = 20, threshold: float = 0.02) -> pd.Series:
    """ML-ready strategy template using feature engineering"""
    signals = pd.Series(index=df.index, dtype=float).fillna(0)
    
    # Feature engineering
    features = pd.DataFrame(index=df.index)
    features['returns'] = df['close'].pct_change()
    features['sma_ratio'] = df['close'] / sma(df['close'], 20)
    features['rsi'] = rsi(df['close'], 14)
    
    if 'volume' in df.columns:
        features['volume_ratio'] = df['volume'] / sma(df['volume'], 20)
    
    # Simple momentum-based prediction (placeholder for ML model)
    momentum = features['returns'].rolling(lookback).mean()
    
    signals[momentum > threshold] = 1.0
    signals[momentum < -threshold] = -1.0
    
    return signals

# Utility functions

def run_strategy(df: pd.DataFrame, strategy_name: str, **params) -> Tuple[pd.Series, Dict]:
    """Run a registered strategy and return signals and metrics"""
    strategy_func = StrategyRegistry.get_strategy(strategy_name)
    
    if not strategy_func:
        raise ValueError(f"Strategy '{strategy_name}' not found")
    
    signals = strategy_func(df, **params)
    
    # Calculate basic metrics
    returns = df['close'].pct_change()
    strategy_returns = signals.shift(1) * returns
    
    metrics = {
        'total_trades': int((signals.diff() != 0).sum()),
        'long_trades': int((signals == 1).sum()),
        'short_trades': int((signals == -1).sum()),
        'avg_return': float(strategy_returns.mean() * 100),
        'total_return': float((strategy_returns + 1).prod() - 1) * 100,
        'volatility': float(strategy_returns.std() * np.sqrt(252) * 100),
        'sharpe_ratio': float(strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)) if strategy_returns.std() > 0 else 0
    }
    
    return signals, metrics

def get_strategy_list() -> List[Dict[str, str]]:
    """Get list of all available strategies"""
    return [
        {
            'name': name,
            'type': info['type'],
            'description': info['description'],
            'status': info['status']
        }
        for name, info in StrategyRegistry.get_all().items()
    ]

# Export registry for external access
registry = StrategyRegistry