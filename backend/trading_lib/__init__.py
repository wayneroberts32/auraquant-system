"""
AuraQuant Trading Library
Auto-registering trading components with MongoDB integration
"""

from .indicators import (
    IndicatorRegistry,
    get_indicator_list,
    calculate_all_indicators,
    sma, ema, wma, rsi, macd, stoch_rsi,
    bollinger_bands, atr, obv, vwap,
    supertrend, ichimoku_cloud, fibonacci_retracement
)

from .strategies import (
    StrategyRegistry,
    get_strategy_list,
    run_strategy,
    BaseStrategy,
    sma_crossover, ema_crossover, rsi_strategy,
    macd_strategy, bollinger_breakout, bollinger_mean_reversion,
    volume_momentum, stochrsi_strategy, multi_indicator_strategy,
    atr_breakout, supertrend_strategy, ml_predictive_strategy
)

from .risk import (
    RiskMetricsRegistry,
    get_risk_metrics_list,
    calculate_all_metrics,
    max_drawdown, sharpe_ratio, sortino_ratio,
    profit_factor, win_rate, expected_return,
    value_at_risk, conditional_var, calmar_ratio,
    volatility, skewness, kurtosis,
    omega_ratio, ulcer_index
)

# Auto-register all components on import
import asyncio

async def sync_all_to_mongodb():
    """Sync all registries to MongoDB"""
    tasks = []
    
    if not IndicatorRegistry._db_synced:
        tasks.append(IndicatorRegistry._sync_to_mongodb())
    
    if not StrategyRegistry._db_synced:
        tasks.append(StrategyRegistry._sync_to_mongodb())
    
    if not RiskMetricsRegistry._db_synced:
        tasks.append(RiskMetricsRegistry._sync_to_mongodb())
    
    if tasks:
        await asyncio.gather(*tasks)
        print("✅ Trading library components synced to MongoDB")

# Sync will be called from main app startup to avoid async issues
# sync_all_to_mongodb() should be called from app startup event

__all__ = [
    # Registries
    'IndicatorRegistry',
    'StrategyRegistry',
    'RiskMetricsRegistry',
    
    # List functions
    'get_indicator_list',
    'get_strategy_list',
    'get_risk_metrics_list',
    
    # Calculation functions
    'calculate_all_indicators',
    'run_strategy',
    'calculate_all_metrics',
    
    # Classes
    'BaseStrategy',
    
    # Indicators
    'sma', 'ema', 'wma', 'rsi', 'macd', 'stoch_rsi',
    'bollinger_bands', 'atr', 'obv', 'vwap',
    'supertrend', 'ichimoku_cloud', 'fibonacci_retracement',
    
    # Strategies
    'sma_crossover', 'ema_crossover', 'rsi_strategy',
    'macd_strategy', 'bollinger_breakout', 'bollinger_mean_reversion',
    'volume_momentum', 'stochrsi_strategy', 'multi_indicator_strategy',
    'atr_breakout', 'supertrend_strategy', 'ml_predictive_strategy',
    
    # Risk Metrics
    'max_drawdown', 'sharpe_ratio', 'sortino_ratio',
    'profit_factor', 'win_rate', 'expected_return',
    'value_at_risk', 'conditional_var', 'calmar_ratio',
    'volatility', 'skewness', 'kurtosis',
    'omega_ratio', 'ulcer_index'
]

print("🚀 AuraQuant Trading Library loaded with auto-registration")