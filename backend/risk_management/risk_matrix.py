"""
AuraQuant Advanced Risk Management System
==========================================
CRITICAL: Capital Protection is ABSOLUTE
The Infinity Money Synthetic Intelligence System

This module provides institutional-grade risk management with multiple
layers of protection to ensure capital preservation at all costs.

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import json
import time
from collections import defaultdict, deque
from enum import Enum
import warnings

# Risk levels enum
class RiskLevel(Enum):
    """Risk severity levels"""
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"

# Risk event types
class RiskEventType(Enum):
    """Types of risk events"""
    DRAWDOWN = "DRAWDOWN"
    CORRELATION = "CORRELATION"
    VOLATILITY = "VOLATILITY"
    LIQUIDITY = "LIQUIDITY"
    MARGIN_CALL = "MARGIN_CALL"
    POSITION_SIZE = "POSITION_SIZE"
    DAILY_LOSS = "DAILY_LOSS"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    KILL_SWITCH = "KILL_SWITCH"

@dataclass
class RiskMetrics:
    """Real-time risk metrics"""
    timestamp: float
    var_95: float  # Value at Risk at 95% confidence
    var_99: float  # Value at Risk at 99% confidence
    cvar: float  # Conditional VaR (Expected Shortfall)
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    daily_pnl: float
    exposure: Dict[str, float]
    correlation_matrix: pd.DataFrame
    liquidity_score: float
    margin_usage: float
    risk_score: float  # Overall risk score 0-100

@dataclass
class RiskLimits:
    """Configurable risk limits"""
    max_daily_loss: float = 50000  # $50k default
    max_daily_loss_pct: float = 5.0  # 5% of capital
    warning_daily_loss_pct: float = 3.0  # 3% warning threshold
    max_drawdown: float = 10.0  # 10% maximum drawdown
    max_position_pct: float = 10.0  # Max 10% in single position
    max_sector_pct: float = 30.0  # Max 30% in single sector
    max_correlation: float = 0.7  # Max correlation between positions
    min_liquidity_ratio: float = 2.0  # Minimum liquidity ratio
    max_leverage: float = 2.0  # Maximum leverage allowed
    max_var_95: float = 2.0  # Max 2% VaR at 95% confidence
    margin_call_level: float = 30.0  # Margin call at 30%
    liquidation_level: float = 20.0  # Force liquidation at 20%

@dataclass
class RiskAlert:
    """Risk alert notification"""
    timestamp: float
    event_type: RiskEventType
    level: RiskLevel
    message: str
    metrics: Dict[str, Any]
    action_required: str
    auto_action_taken: bool = False

class RiskManagementMatrix:
    """
    Advanced Risk Management System for AuraQuant
    
    Features:
    - Value at Risk (VaR) calculations
    - Position sizing algorithms
    - Correlation matrix monitoring
    - Max drawdown locks
    - Daily loss limits with auto-pause
    - Exposure limits per asset/sector
    - Margin requirement tracking
    - Liquidity risk assessment
    - Kill switch integration
    - Circuit breaker mechanism
    """
    
    def __init__(self, mongodb_client=None, capital: float = 1000000):
        """
        Initialize Risk Management Matrix
        
        Args:
            mongodb_client: MongoDB connection for logging
            capital: Total capital under management
        """
        self.mongodb = mongodb_client
        self.capital = capital
        self.initial_capital = capital
        
        # Risk limits configuration
        self.limits = RiskLimits()
        
        # Risk state tracking
        self.risk_state = {
            'is_paused': False,
            'kill_switch_active': False,
            'circuit_breaker_triggered': False,
            'daily_loss': 0,
            'daily_loss_pct': 0,
            'current_drawdown': 0,
            'peak_equity': capital,
            'risk_level': RiskLevel.LOW,
            'last_risk_check': time.time()
        }
        
        # Position tracking
        self.positions = {}  # symbol -> position details
        self.position_history = defaultdict(list)
        
        # Risk metrics history
        self.metrics_history = deque(maxlen=1000)
        self.alert_history = deque(maxlen=100)
        
        # Correlation tracking
        self.correlation_window = 60  # days
        self.correlation_data = defaultdict(deque)
        
        # VaR calculation parameters
        self.var_confidence_levels = [0.95, 0.99]
        self.var_horizon = 1  # 1 day VaR
        self.var_window = 252  # Trading days for historical VaR
        
        # Liquidity tracking
        self.liquidity_scores = {}
        
        # Margin tracking
        self.margin_requirements = {}
        self.margin_usage = 0
        
        # Performance metrics
        self.performance_window = 252  # Trading days
        self.returns_history = deque(maxlen=self.performance_window)
        
        # Risk monitoring flags
        self.monitoring_active = True
        self.auto_risk_reduction = True
        self.immutable_logging = True
        
    async def calculate_var(self, 
                           portfolio_returns: pd.Series,
                           confidence_level: float = 0.95,
                           method: str = 'historical') -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            portfolio_returns: Historical portfolio returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            method: 'historical', 'parametric', or 'monte_carlo'
            
        Returns:
            VaR value (potential loss)
        """
        if len(portfolio_returns) < 20:
            return 0  # Not enough data
        
        if method == 'historical':
            # Historical VaR
            var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
            
        elif method == 'parametric':
            # Parametric VaR (assuming normal distribution)
            mean = portfolio_returns.mean()
            std = portfolio_returns.std()
            z_score = np.abs(np.percentile(np.random.standard_normal(10000), 
                                          (1 - confidence_level) * 100))
            var = mean - z_score * std
            
        elif method == 'monte_carlo':
            # Monte Carlo VaR
            simulations = 10000
            mean = portfolio_returns.mean()
            std = portfolio_returns.std()
            simulated_returns = np.random.normal(mean, std, simulations)
            var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
        
        else:
            raise ValueError(f"Unknown VaR method: {method}")
        
        # Convert to dollar amount
        var_dollars = abs(var) * self.capital
        
        return var_dollars
    
    async def calculate_cvar(self, 
                            portfolio_returns: pd.Series,
                            confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall)
        
        Args:
            portfolio_returns: Historical portfolio returns
            confidence_level: Confidence level
            
        Returns:
            CVaR value (expected loss beyond VaR)
        """
        if len(portfolio_returns) < 20:
            return 0
        
        # Get VaR threshold
        var_threshold = np.percentile(portfolio_returns, 
                                     (1 - confidence_level) * 100)
        
        # Calculate expected shortfall
        tail_losses = portfolio_returns[portfolio_returns <= var_threshold]
        
        if len(tail_losses) > 0:
            cvar = tail_losses.mean()
        else:
            cvar = var_threshold
        
        # Convert to dollar amount
        cvar_dollars = abs(cvar) * self.capital
        
        return cvar_dollars
    
    async def calculate_position_size(self,
                                     symbol: str,
                                     entry_price: float,
                                     stop_loss: float,
                                     strategy_confidence: float = 0.5) -> Dict[str, Any]:
        """
        Calculate optimal position size using multiple methods
        
        Args:
            symbol: Asset symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            strategy_confidence: Strategy confidence (0-1)
            
        Returns:
            Position sizing recommendation
        """
        # Calculate risk per trade
        max_risk_per_trade = self.capital * 0.02  # 2% max risk per trade
        
        # Method 1: Fixed Fractional
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share > 0:
            fixed_fractional_size = max_risk_per_trade / risk_per_share
        else:
            fixed_fractional_size = 0
        
        # Method 2: Kelly Criterion (capped at 25%)
        win_rate = 0.6 + (strategy_confidence * 0.2)  # 60-80% win rate
        avg_win = risk_per_share * 2  # 2:1 reward/risk
        avg_loss = risk_per_share
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_fraction = min(kelly_fraction, 0.25)  # Cap at 25%
        kelly_size = (self.capital * kelly_fraction) / entry_price
        
        # Method 3: Volatility-based sizing
        volatility = await self._get_volatility(symbol)
        if volatility > 0:
            volatility_size = (max_risk_per_trade / (volatility * entry_price))
        else:
            volatility_size = fixed_fractional_size
        
        # Method 4: Risk parity sizing
        correlations = await self._get_correlations(symbol)
        correlation_factor = 1 - (sum(correlations.values()) / max(len(correlations), 1))
        risk_parity_size = fixed_fractional_size * correlation_factor
        
        # Determine final position size (conservative approach)
        recommended_size = min(
            fixed_fractional_size,
            kelly_size,
            volatility_size,
            risk_parity_size
        )
        
        # Apply maximum position limits
        max_position_value = self.capital * (self.limits.max_position_pct / 100)
        max_shares = max_position_value / entry_price
        
        final_size = min(recommended_size, max_shares)
        
        # Check margin requirements
        margin_required = final_size * entry_price * 0.25  # 25% margin
        
        return {
            'symbol': symbol,
            'recommended_shares': int(final_size),
            'position_value': final_size * entry_price,
            'risk_amount': final_size * risk_per_share,
            'risk_pct': (final_size * risk_per_share) / self.capital * 100,
            'methods': {
                'fixed_fractional': int(fixed_fractional_size),
                'kelly': int(kelly_size),
                'volatility': int(volatility_size),
                'risk_parity': int(risk_parity_size)
            },
            'margin_required': margin_required,
            'stop_loss': stop_loss,
            'entry_price': entry_price
        }
    
    async def monitor_correlation_matrix(self) -> pd.DataFrame:
        """
        Monitor correlation between all positions
        
        Returns:
            Correlation matrix of positions
        """
        if len(self.positions) < 2:
            return pd.DataFrame()
        
        # Prepare data for correlation calculation
        symbols = list(self.positions.keys())
        price_data = {}
        
        for symbol in symbols:
            if symbol in self.correlation_data:
                price_data[symbol] = list(self.correlation_data[symbol])
        
        if not price_data:
            return pd.DataFrame()
        
        # Create DataFrame and calculate correlation
        df = pd.DataFrame(price_data)
        correlation_matrix = df.corr()
        
        # Check for high correlations
        high_correlations = []
        for i in range(len(correlation_matrix)):
            for j in range(i + 1, len(correlation_matrix)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > self.limits.max_correlation:
                    high_correlations.append({
                        'pair': (correlation_matrix.index[i], correlation_matrix.columns[j]),
                        'correlation': corr_value
                    })
        
        # Alert if high correlations found
        if high_correlations:
            await self._create_alert(
                event_type=RiskEventType.CORRELATION,
                level=RiskLevel.HIGH,
                message=f"High correlation detected: {high_correlations[0]}",
                metrics={'correlations': high_correlations}
            )
            
            # Auto-reduce positions if enabled
            if self.auto_risk_reduction:
                await self._reduce_correlated_positions(high_correlations)
        
        return correlation_matrix
    
    async def check_drawdown(self, current_equity: float) -> Dict[str, Any]:
        """
        Monitor and enforce maximum drawdown limits
        
        Args:
            current_equity: Current account equity
            
        Returns:
            Drawdown analysis
        """
        # Update peak equity if new high
        if current_equity > self.risk_state['peak_equity']:
            self.risk_state['peak_equity'] = current_equity
        
        # Calculate current drawdown
        drawdown_amount = self.risk_state['peak_equity'] - current_equity
        drawdown_pct = (drawdown_amount / self.risk_state['peak_equity']) * 100
        
        self.risk_state['current_drawdown'] = drawdown_pct
        
        # Check against limits
        if drawdown_pct >= self.limits.max_drawdown:
            # CRITICAL: Maximum drawdown reached
            await self._activate_kill_switch("Maximum drawdown limit reached")
            
        elif drawdown_pct >= self.limits.max_drawdown * 0.8:  # 80% of max
            # WARNING: Approaching maximum drawdown
            await self._create_alert(
                event_type=RiskEventType.DRAWDOWN,
                level=RiskLevel.HIGH,
                message=f"Approaching maximum drawdown: {drawdown_pct:.2f}%",
                metrics={'drawdown_pct': drawdown_pct, 'drawdown_amount': drawdown_amount}
            )
            
            # Reduce risk exposure
            if self.auto_risk_reduction:
                await self._reduce_all_positions(reduction_pct=50)
        
        return {
            'current_equity': current_equity,
            'peak_equity': self.risk_state['peak_equity'],
            'drawdown_amount': drawdown_amount,
            'drawdown_pct': drawdown_pct,
            'max_allowed': self.limits.max_drawdown,
            'risk_level': self._calculate_risk_level(drawdown_pct)
        }
    
    async def enforce_daily_loss_limit(self, current_pnl: float) -> Dict[str, Any]:
        """
        Monitor and enforce daily loss limits
        
        Args:
            current_pnl: Current daily P&L
            
        Returns:
            Daily loss status
        """
        self.risk_state['daily_loss'] = current_pnl
        self.risk_state['daily_loss_pct'] = (current_pnl / self.capital) * 100
        
        loss_pct = abs(self.risk_state['daily_loss_pct'])
        
        # Check absolute dollar limit
        if current_pnl <= -self.limits.max_daily_loss:
            # EMERGENCY: Max daily loss reached
            await self._activate_kill_switch("Maximum daily loss limit reached")
            return {
                'status': 'HALTED',
                'daily_loss': current_pnl,
                'limit': self.limits.max_daily_loss,
                'action': 'KILL_SWITCH_ACTIVATED'
            }
        
        # Check percentage limit
        if loss_pct >= self.limits.max_daily_loss_pct:
            # CRITICAL: 5% daily loss - activate kill switch
            await self._activate_kill_switch(f"Daily loss {loss_pct:.2f}% exceeds limit")
            return {
                'status': 'HALTED',
                'daily_loss_pct': loss_pct,
                'limit': self.limits.max_daily_loss_pct,
                'action': 'KILL_SWITCH_ACTIVATED'
            }
            
        elif loss_pct >= self.limits.warning_daily_loss_pct:
            # WARNING: 3% daily loss - pause trading
            await self._pause_trading(f"Daily loss {loss_pct:.2f}% - warning threshold")
            return {
                'status': 'PAUSED',
                'daily_loss_pct': loss_pct,
                'warning_level': self.limits.warning_daily_loss_pct,
                'action': 'TRADING_PAUSED'
            }
        
        return {
            'status': 'ACTIVE',
            'daily_loss': current_pnl,
            'daily_loss_pct': self.risk_state['daily_loss_pct'],
            'remaining_loss_capacity': self.limits.max_daily_loss + current_pnl
        }
    
    async def check_exposure_limits(self) -> Dict[str, Any]:
        """
        Check position and sector exposure limits
        
        Returns:
            Exposure analysis
        """
        total_exposure = sum(pos.get('value', 0) for pos in self.positions.values())
        
        # Check individual position limits
        violations = []
        for symbol, position in self.positions.items():
            position_pct = (position.get('value', 0) / self.capital) * 100
            
            if position_pct > self.limits.max_position_pct:
                violations.append({
                    'symbol': symbol,
                    'exposure_pct': position_pct,
                    'limit': self.limits.max_position_pct
                })
        
        # Check sector exposure (simplified - group by asset class)
        sector_exposure = defaultdict(float)
        for symbol, position in self.positions.items():
            sector = self._get_sector(symbol)
            sector_exposure[sector] += position.get('value', 0)
        
        sector_violations = []
        for sector, exposure in sector_exposure.items():
            sector_pct = (exposure / self.capital) * 100
            
            if sector_pct > self.limits.max_sector_pct:
                sector_violations.append({
                    'sector': sector,
                    'exposure_pct': sector_pct,
                    'limit': self.limits.max_sector_pct
                })
        
        # Take action if violations found
        if violations or sector_violations:
            await self._create_alert(
                event_type=RiskEventType.POSITION_SIZE,
                level=RiskLevel.HIGH,
                message="Exposure limit violations detected",
                metrics={'position_violations': violations, 'sector_violations': sector_violations}
            )
            
            if self.auto_risk_reduction:
                await self._rebalance_positions()
        
        return {
            'total_exposure': total_exposure,
            'exposure_pct': (total_exposure / self.capital) * 100,
            'position_violations': violations,
            'sector_violations': sector_violations,
            'sector_breakdown': dict(sector_exposure)
        }
    
    async def track_margin_requirements(self) -> Dict[str, Any]:
        """
        Track and monitor margin requirements
        
        Returns:
            Margin status
        """
        total_margin_required = 0
        margin_details = {}
        
        for symbol, position in self.positions.items():
            # Calculate margin based on position type and broker requirements
            position_value = position.get('value', 0)
            leverage = position.get('leverage', 1)
            
            if position.get('type') == 'futures':
                margin_req = position_value * 0.10  # 10% for futures
            elif position.get('type') == 'options':
                margin_req = position_value * 0.15  # 15% for options
            elif leverage > 1:
                margin_req = position_value / leverage
            else:
                margin_req = position_value * 0.25  # 25% for regular positions
            
            total_margin_required += margin_req
            margin_details[symbol] = margin_req
        
        # Calculate margin usage percentage
        available_margin = self.capital * 0.5  # 50% of capital available for margin
        margin_usage_pct = (total_margin_required / available_margin) * 100
        
        self.margin_usage = margin_usage_pct
        
        # Check margin levels
        if margin_usage_pct >= self.limits.liquidation_level:
            # EMERGENCY: Liquidation level
            await self._force_liquidation("Margin liquidation level reached")
            
        elif margin_usage_pct >= self.limits.margin_call_level:
            # CRITICAL: Margin call
            await self._create_alert(
                event_type=RiskEventType.MARGIN_CALL,
                level=RiskLevel.CRITICAL,
                message=f"Margin call: {margin_usage_pct:.2f}% usage",
                metrics={'margin_usage': margin_usage_pct, 'required': total_margin_required}
            )
            
            if self.auto_risk_reduction:
                await self._reduce_leveraged_positions()
        
        return {
            'total_margin_required': total_margin_required,
            'available_margin': available_margin,
            'margin_usage_pct': margin_usage_pct,
            'margin_details': margin_details,
            'margin_call_level': self.limits.margin_call_level,
            'liquidation_level': self.limits.liquidation_level
        }
    
    async def assess_liquidity_risk(self) -> Dict[str, Any]:
        """
        Assess liquidity risk for all positions
        
        Returns:
            Liquidity risk assessment
        """
        liquidity_issues = []
        total_illiquid_value = 0
        
        for symbol, position in self.positions.items():
            # Get average daily volume
            avg_volume = await self._get_average_volume(symbol)
            position_size = position.get('quantity', 0)
            
            if avg_volume > 0:
                # Calculate how many days to liquidate position
                days_to_liquidate = position_size / (avg_volume * 0.1)  # 10% of daily volume
                
                if days_to_liquidate > 1:
                    liquidity_issues.append({
                        'symbol': symbol,
                        'days_to_liquidate': days_to_liquidate,
                        'position_size': position_size,
                        'avg_volume': avg_volume
                    })
                    total_illiquid_value += position.get('value', 0)
                
                # Calculate liquidity score (0-100, higher is better)
                liquidity_score = min(100, (avg_volume / position_size) * 10)
                self.liquidity_scores[symbol] = liquidity_score
            else:
                self.liquidity_scores[symbol] = 0
                liquidity_issues.append({
                    'symbol': symbol,
                    'issue': 'No volume data available'
                })
        
        # Calculate overall liquidity ratio
        liquid_value = sum(
            pos.get('value', 0) 
            for sym, pos in self.positions.items() 
            if self.liquidity_scores.get(sym, 0) > 50
        )
        
        total_value = sum(pos.get('value', 0) for pos in self.positions.values())
        
        if total_value > 0:
            liquidity_ratio = liquid_value / total_value
        else:
            liquidity_ratio = 1
        
        # Check liquidity ratio
        if liquidity_ratio < self.limits.min_liquidity_ratio:
            await self._create_alert(
                event_type=RiskEventType.LIQUIDITY,
                level=RiskLevel.HIGH,
                message=f"Low liquidity ratio: {liquidity_ratio:.2f}",
                metrics={'liquidity_ratio': liquidity_ratio, 'issues': liquidity_issues}
            )
        
        return {
            'liquidity_ratio': liquidity_ratio,
            'liquid_value': liquid_value,
            'illiquid_value': total_illiquid_value,
            'liquidity_scores': self.liquidity_scores,
            'issues': liquidity_issues
        }
    
    async def calculate_risk_metrics(self) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics
        
        Returns:
            Current risk metrics
        """
        # Get portfolio returns
        returns = pd.Series(list(self.returns_history)) if self.returns_history else pd.Series([0])
        
        # Calculate VaR
        var_95 = await self.calculate_var(returns, 0.95)
        var_99 = await self.calculate_var(returns, 0.99)
        
        # Calculate CVaR
        cvar = await self.calculate_cvar(returns, 0.95)
        
        # Calculate performance ratios
        if len(returns) > 1:
            sharpe = self._calculate_sharpe_ratio(returns)
            sortino = self._calculate_sortino_ratio(returns)
            calmar = self._calculate_calmar_ratio(returns)
        else:
            sharpe = sortino = calmar = 0
        
        # Get correlation matrix
        correlation_matrix = await self.monitor_correlation_matrix()
        
        # Calculate overall risk score (0-100)
        risk_score = self._calculate_overall_risk_score({
            'var_95': var_95,
            'drawdown': self.risk_state['current_drawdown'],
            'margin_usage': self.margin_usage,
            'daily_loss_pct': abs(self.risk_state['daily_loss_pct']),
            'correlation': correlation_matrix.values.max() if not correlation_matrix.empty else 0
        })
        
        metrics = RiskMetrics(
            timestamp=time.time(),
            var_95=var_95,
            var_99=var_99,
            cvar=cvar,
            max_drawdown=self.limits.max_drawdown,
            current_drawdown=self.risk_state['current_drawdown'],
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            daily_pnl=self.risk_state['daily_loss'],
            exposure=self._get_exposure_breakdown(),
            correlation_matrix=correlation_matrix,
            liquidity_score=np.mean(list(self.liquidity_scores.values())) if self.liquidity_scores else 100,
            margin_usage=self.margin_usage,
            risk_score=risk_score
        )
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Log to MongoDB if available
        if self.mongodb and self.immutable_logging:
            await self._log_risk_metrics(metrics)
        
        return metrics
    
    async def execute_circuit_breaker(self, trigger_reason: str):
        """
        Execute circuit breaker to pause trading temporarily
        
        Args:
            trigger_reason: Reason for triggering circuit breaker
        """
        self.risk_state['circuit_breaker_triggered'] = True
        self.risk_state['is_paused'] = True
        
        await self._create_alert(
            event_type=RiskEventType.CIRCUIT_BREAKER,
            level=RiskLevel.CRITICAL,
            message=f"Circuit breaker triggered: {trigger_reason}",
            metrics={'timestamp': time.time(), 'reason': trigger_reason},
            auto_action_taken=True
        )
        
        # Auto-resume after cooldown period (5 minutes)
        await asyncio.sleep(300)
        
        # Re-evaluate conditions before resuming
        metrics = await self.calculate_risk_metrics()
        if metrics.risk_score < 70:  # Safe to resume
            self.risk_state['circuit_breaker_triggered'] = False
            self.risk_state['is_paused'] = False
            print("Circuit breaker released - trading resumed")
        else:
            print("Circuit breaker extended - conditions still risky")
    
    async def _activate_kill_switch(self, reason: str):
        """
        EMERGENCY: Activate kill switch to halt all trading
        
        Args:
            reason: Reason for activation
        """
        self.risk_state['kill_switch_active'] = True
        self.risk_state['is_paused'] = True
        
        await self._create_alert(
            event_type=RiskEventType.KILL_SWITCH,
            level=RiskLevel.EMERGENCY,
            message=f"KILL SWITCH ACTIVATED: {reason}",
            metrics={'timestamp': time.time(), 'reason': reason},
            auto_action_taken=True
        )
        
        # Close all positions immediately
        await self._emergency_close_all_positions()
        
        # Log to MongoDB
        if self.mongodb:
            await self.mongodb.risk_events.insert_one({
                'event': 'KILL_SWITCH_ACTIVATED',
                'reason': reason,
                'timestamp': time.time(),
                'capital_at_activation': self.capital,
                'positions_closed': len(self.positions)
            })
        
        print(f"🚨 KILL SWITCH ACTIVATED: {reason}")
        print("All positions closed. Manual intervention required to resume.")
    
    async def _pause_trading(self, reason: str):
        """
        Pause trading temporarily
        
        Args:
            reason: Reason for pause
        """
        self.risk_state['is_paused'] = True
        
        await self._create_alert(
            event_type=RiskEventType.DAILY_LOSS,
            level=RiskLevel.HIGH,
            message=f"Trading paused: {reason}",
            metrics={'timestamp': time.time(), 'reason': reason}
        )
        
        print(f"⚠️ Trading paused: {reason}")
    
    async def _create_alert(self, 
                           event_type: RiskEventType,
                           level: RiskLevel,
                           message: str,
                           metrics: Dict,
                           auto_action_taken: bool = False):
        """
        Create and store risk alert
        """
        alert = RiskAlert(
            timestamp=time.time(),
            event_type=event_type,
            level=level,
            message=message,
            metrics=metrics,
            action_required=self._determine_action(level),
            auto_action_taken=auto_action_taken
        )
        
        self.alert_history.append(alert)
        
        # Log to MongoDB
        if self.mongodb:
            await self.mongodb.risk_alerts.insert_one({
                'timestamp': alert.timestamp,
                'event_type': event_type.value,
                'level': level.value,
                'message': message,
                'metrics': metrics,
                'auto_action_taken': auto_action_taken
            })
    
    def _calculate_risk_level(self, metric_value: float) -> RiskLevel:
        """Calculate risk level based on metric value"""
        if metric_value < 20:
            return RiskLevel.LOW
        elif metric_value < 40:
            return RiskLevel.MODERATE
        elif metric_value < 60:
            return RiskLevel.HIGH
        elif metric_value < 80:
            return RiskLevel.CRITICAL
        else:
            return RiskLevel.EMERGENCY
    
    def _calculate_overall_risk_score(self, factors: Dict[str, float]) -> float:
        """
        Calculate overall risk score (0-100)
        
        Args:
            factors: Risk factors with their values
            
        Returns:
            Overall risk score
        """
        weights = {
            'var_95': 0.2,
            'drawdown': 0.25,
            'margin_usage': 0.2,
            'daily_loss_pct': 0.25,
            'correlation': 0.1
        }
        
        score = 0
        for factor, value in factors.items():
            if factor in weights:
                # Normalize to 0-100 scale
                if factor == 'var_95':
                    normalized = min(100, (value / self.capital) * 1000)
                elif factor == 'correlation':
                    normalized = abs(value) * 100
                else:
                    normalized = min(100, abs(value))
                
                score += normalized * weights[factor]
        
        return min(100, score)
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return 0
        
        # Annualized Sharpe ratio (assuming daily returns)
        sharpe = (mean_return / std_return) * np.sqrt(252)
        return sharpe
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        if len(returns) < 2:
            return 0
        
        mean_return = returns.mean()
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0
        
        # Annualized Sortino ratio
        sortino = (mean_return / downside_std) * np.sqrt(252)
        return sortino
    
    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio (return / max drawdown)"""
        if len(returns) < 2:
            return 0
        
        total_return = (1 + returns).prod() - 1
        
        if self.risk_state['current_drawdown'] == 0:
            return float('inf') if total_return > 0 else 0
        
        calmar = (total_return * 100) / self.risk_state['current_drawdown']
        return calmar
    
    def _get_sector(self, symbol: str) -> str:
        """Determine sector for a symbol"""
        # Simplified sector classification
        if symbol.endswith(('USD', 'EUR', 'GBP', 'JPY')):
            return 'FOREX'
        elif symbol in ['BTC', 'ETH', 'SOL', 'DOGE']:
            return 'CRYPTO'
        elif symbol in ['SPY', 'QQQ', 'IWM', 'DIA']:
            return 'ETF'
        else:
            return 'EQUITY'
    
    def _determine_action(self, level: RiskLevel) -> str:
        """Determine required action based on risk level"""
        actions = {
            RiskLevel.MINIMAL: "Monitor",
            RiskLevel.LOW: "Monitor closely",
            RiskLevel.MODERATE: "Review positions",
            RiskLevel.HIGH: "Reduce risk immediately",
            RiskLevel.CRITICAL: "Emergency risk reduction",
            RiskLevel.EMERGENCY: "Close all positions"
        }
        return actions.get(level, "Review immediately")
    
    async def _get_volatility(self, symbol: str) -> float:
        """Get historical volatility for a symbol"""
        # Placeholder - would fetch from market data
        return 0.02  # 2% daily volatility
    
    async def _get_correlations(self, symbol: str) -> Dict[str, float]:
        """Get correlations with existing positions"""
        correlations = {}
        # Placeholder - would calculate from correlation matrix
        for existing_symbol in self.positions.keys():
            if existing_symbol != symbol:
                correlations[existing_symbol] = np.random.uniform(-0.3, 0.3)
        return correlations
    
    async def _get_average_volume(self, symbol: str) -> float:
        """Get average daily volume for a symbol"""
        # Placeholder - would fetch from market data
        return 1000000  # 1M shares average volume
    
    def _get_exposure_breakdown(self) -> Dict[str, float]:
        """Get exposure breakdown by asset"""
        breakdown = {}
        for symbol, position in self.positions.items():
            breakdown[symbol] = position.get('value', 0)
        return breakdown
    
    async def _reduce_all_positions(self, reduction_pct: float):
        """Reduce all positions by specified percentage"""
        for symbol in list(self.positions.keys()):
            current_size = self.positions[symbol].get('quantity', 0)
            new_size = current_size * (1 - reduction_pct / 100)
            self.positions[symbol]['quantity'] = new_size
            print(f"Reduced {symbol} position by {reduction_pct}%")
    
    async def _reduce_correlated_positions(self, high_correlations: List[Dict]):
        """Reduce highly correlated positions"""
        for corr_data in high_correlations:
            pair = corr_data['pair']
            # Reduce the smaller position
            if pair[0] in self.positions and pair[1] in self.positions:
                if self.positions[pair[0]]['value'] < self.positions[pair[1]]['value']:
                    self.positions[pair[0]]['quantity'] *= 0.5
                    print(f"Reduced {pair[0]} position due to high correlation")
                else:
                    self.positions[pair[1]]['quantity'] *= 0.5
                    print(f"Reduced {pair[1]} position due to high correlation")
    
    async def _reduce_leveraged_positions(self):
        """Reduce leveraged positions to meet margin requirements"""
        for symbol, position in self.positions.items():
            if position.get('leverage', 1) > 1:
                position['leverage'] = 1
                print(f"Reduced leverage on {symbol} to 1x")
    
    async def _rebalance_positions(self):
        """Rebalance positions to meet exposure limits"""
        total_value = sum(pos.get('value', 0) for pos in self.positions.values())
        max_position_value = self.capital * (self.limits.max_position_pct / 100)
        
        for symbol, position in self.positions.items():
            if position['value'] > max_position_value:
                position['quantity'] = max_position_value / position.get('price', 1)
                print(f"Rebalanced {symbol} to meet exposure limits")
    
    async def _force_liquidation(self, reason: str):
        """Force liquidation of positions"""
        print(f"🚨 FORCED LIQUIDATION: {reason}")
        await self._emergency_close_all_positions()
    
    async def _emergency_close_all_positions(self):
        """Emergency close all positions"""
        for symbol in list(self.positions.keys()):
            print(f"Emergency closing position: {symbol}")
            del self.positions[symbol]
        print("All positions closed")
    
    async def _log_risk_metrics(self, metrics: RiskMetrics):
        """Log risk metrics to MongoDB (immutable)"""
        if self.mongodb:
            await self.mongodb.risk_metrics.insert_one({
                'timestamp': metrics.timestamp,
                'var_95': metrics.var_95,
                'var_99': metrics.var_99,
                'cvar': metrics.cvar,
                'current_drawdown': metrics.current_drawdown,
                'sharpe_ratio': metrics.sharpe_ratio,
                'sortino_ratio': metrics.sortino_ratio,
                'calmar_ratio': metrics.calmar_ratio,
                'daily_pnl': metrics.daily_pnl,
                'margin_usage': metrics.margin_usage,
                'risk_score': metrics.risk_score,
                'capital': self.capital
            })

# Risk Management API endpoints for integration
async def create_risk_manager(capital: float = 1000000) -> RiskManagementMatrix:
    """Factory function to create risk manager"""
    return RiskManagementMatrix(capital=capital)