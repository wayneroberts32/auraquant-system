"""
AuraQuant Risk Metrics Library
Auto-registering risk metrics with MongoDB integration
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import db_config

class RiskMetricsRegistry:
    """Auto-registering risk metrics system"""
    
    _metrics: Dict[str, Dict] = {}
    _db_synced = False
    
    @classmethod
    def register(cls, name: str, metric_type: str = 'custom', description: str = ''):
        """Decorator to register risk metrics"""
        def decorator(func):
            cls._metrics[name] = {
                'function': func,
                'type': metric_type,
                'description': description or func.__doc__ or f'{name} metric',
                'auto_registered': True,
                'created_at': datetime.utcnow()
            }
            # Mark for MongoDB sync but don't do it during import
            cls._db_synced = False
            return func
        return decorator
    
    @classmethod
    async def _sync_to_mongodb(cls):
        """Sync registered metrics to MongoDB"""
        try:
            client = AsyncIOMotorClient(db_config.mongodb_uri)
            db = client[db_config.database_name]
            
            for name, info in cls._metrics.items():
                await db.risk_metrics.update_one(
                    {'name': name},
                    {'$set': {
                        'name': name,
                        'type': info['type'],
                        'description': info['description'],
                        'auto_registered': True,
                        'created_at': info['created_at']
                    }},
                    upsert=True
                )
            
            cls._db_synced = True
            client.close()
        except Exception as e:
            print(f"Warning: Could not sync risk metrics to MongoDB: {e}")
    
    @classmethod
    def get_all(cls) -> Dict:
        return cls._metrics
    
    @classmethod
    def get_metric(cls, name: str) -> Optional[Callable]:
        return cls._metrics.get(name, {}).get('function')
    
    @classmethod
    async def sync_all(cls):
        """Sync all risk metrics to MongoDB - call this on app startup"""
        if not cls._db_synced:
            await cls._sync_to_mongodb()

# Risk Metrics with auto-registration

@RiskMetricsRegistry.register('MaxDrawdown', 'risk', 'Maximum Drawdown')
def max_drawdown(returns: pd.Series) -> float:
    """Calculate maximum drawdown"""
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min() * 100)

@RiskMetricsRegistry.register('SharpeRatio', 'risk_adjusted_return', 'Sharpe Ratio')
def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe Ratio"""
    excess_returns = returns - risk_free_rate/252
    if returns.std() == 0:
        return 0
    return float(excess_returns.mean() / returns.std() * np.sqrt(252))

@RiskMetricsRegistry.register('SortinoRatio', 'risk_adjusted_return', 'Sortino Ratio')
def sortino_ratio(returns: pd.Series, target_return: float = 0) -> float:
    """Calculate Sortino Ratio"""
    downside_returns = returns[returns < target_return]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    return float((returns.mean() - target_return) / downside_returns.std() * np.sqrt(252))

@RiskMetricsRegistry.register('ProfitFactor', 'performance', 'Profit Factor')
def profit_factor(returns: pd.Series) -> float:
    """Calculate Profit Factor"""
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses == 0:
        return float('inf') if gains > 0 else 0
    return float(gains / losses)

@RiskMetricsRegistry.register('WinRate', 'performance', 'Win Rate')
def win_rate(returns: pd.Series) -> float:
    """Calculate Win Rate"""
    positive_returns = returns[returns > 0]
    total_trades = len(returns[returns != 0])
    if total_trades == 0:
        return 0
    return float(len(positive_returns) / total_trades * 100)

@RiskMetricsRegistry.register('ExpectedReturn', 'performance', 'Expected Return')
def expected_return(returns: pd.Series) -> float:
    """Calculate Expected Return (annualized)"""
    return float(returns.mean() * 252 * 100)

@RiskMetricsRegistry.register('VaR', 'risk', 'Value at Risk')
def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """Calculate Value at Risk"""
    return float(np.percentile(returns, (1 - confidence) * 100) * 100)

@RiskMetricsRegistry.register('CVaR', 'risk', 'Conditional Value at Risk')
def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Calculate Conditional Value at Risk (Expected Shortfall)"""
    var = np.percentile(returns, (1 - confidence) * 100)
    return float(returns[returns <= var].mean() * 100)

@RiskMetricsRegistry.register('CalmarRatio', 'risk_adjusted_return', 'Calmar Ratio')
def calmar_ratio(returns: pd.Series) -> float:
    """Calculate Calmar Ratio"""
    annual_return = returns.mean() * 252
    max_dd = abs(max_drawdown(returns) / 100)
    if max_dd == 0:
        return 0
    return float(annual_return / max_dd)

@RiskMetricsRegistry.register('Volatility', 'risk', 'Annualized Volatility')
def volatility(returns: pd.Series) -> float:
    """Calculate annualized volatility"""
    return float(returns.std() * np.sqrt(252) * 100)

@RiskMetricsRegistry.register('Skewness', 'distribution', 'Return Distribution Skewness')
def skewness(returns: pd.Series) -> float:
    """Calculate skewness of returns"""
    return float(returns.skew())

@RiskMetricsRegistry.register('Kurtosis', 'distribution', 'Return Distribution Kurtosis')
def kurtosis(returns: pd.Series) -> float:
    """Calculate kurtosis of returns"""
    return float(returns.kurtosis())

@RiskMetricsRegistry.register('OmegaRatio', 'risk_adjusted_return', 'Omega Ratio')
def omega_ratio(returns: pd.Series, threshold: float = 0) -> float:
    """Calculate Omega Ratio"""
    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns <= threshold]
    
    if losses.sum() == 0:
        return float('inf') if gains.sum() > 0 else 0
    return float(gains.sum() / losses.sum())

@RiskMetricsRegistry.register('UlcerIndex', 'risk', 'Ulcer Index')
def ulcer_index(returns: pd.Series) -> float:
    """Calculate Ulcer Index (measures downside volatility)"""
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = ((cumulative - running_max) / running_max * 100) ** 2
    return float(np.sqrt(drawdown.mean()))

# Utility functions

def calculate_all_metrics(returns: pd.Series) -> Dict[str, float]:
    """Calculate all registered risk metrics"""
    results = {}
    
    for name, info in RiskMetricsRegistry.get_all().items():
        func = info['function']
        try:
            results[name] = func(returns)
        except Exception as e:
            print(f"Warning: Could not calculate {name}: {e}")
            results[name] = None
    
    return results

def get_risk_metrics_list() -> List[Dict[str, str]]:
    """Get list of all available risk metrics"""
    return [
        {
            'name': name,
            'type': info['type'],
            'description': info['description']
        }
        for name, info in RiskMetricsRegistry.get_all().items()
    ]

# Export registry
registry = RiskMetricsRegistry