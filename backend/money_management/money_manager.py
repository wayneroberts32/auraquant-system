"""
AuraQuant Money Management System
==================================
CRITICAL: Capital Growth with Absolute Protection
The Infinity Money Synthetic Intelligence System

This module provides advanced money management strategies to maximize
growth while ensuring capital preservation and tax compliance.

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
import math

# Money management strategies
class ManagementStrategy(Enum):
    """Available money management strategies"""
    FIXED_FRACTIONAL = "FIXED_FRACTIONAL"
    KELLY_CRITERION = "KELLY_CRITERION"
    ANTI_MARTINGALE = "ANTI_MARTINGALE"
    PROFIT_LOCK = "PROFIT_LOCK"
    COMPOUND_GROWTH = "COMPOUND_GROWTH"
    RISK_PARITY = "RISK_PARITY"
    VOLATILITY_TARGETING = "VOLATILITY_TARGETING"

@dataclass
class MoneyMetrics:
    """Money management metrics"""
    timestamp: float
    total_capital: float
    trading_capital: float
    protected_capital: float
    tax_reserve: float
    profit_locked: float
    current_allocation: Dict[str, float]
    kelly_fraction: float
    risk_per_trade: float
    compound_rate: float
    diversification_score: float
    strategy_performance: Dict[str, float]

@dataclass
class TaxAllocation:
    """Tax reserve allocation"""
    total_profit: float
    tax_rate: float
    tax_reserve: float
    short_term_gains: float
    long_term_gains: float
    wash_sales: float
    estimated_quarterly: float
    year_end_liability: float

@dataclass
class ProfitTarget:
    """Profit target configuration"""
    symbol: str
    entry_price: float
    current_price: float
    target_price: float
    stop_loss: float
    trail_stop: Optional[float]
    profit_locked: float
    status: str  # ACTIVE, LOCKED, CLOSED

class MoneyManagementSystem:
    """
    Advanced Money Management System for AuraQuant
    
    Features:
    - Kelly Criterion (capped at 25%)
    - Fixed Fractional positioning
    - Anti-Martingale strategy
    - Compound growth governor
    - Profit locking mechanisms
    - Diversification enforcement
    - Tax allocation reserves
    - Trail stop implementation
    """
    
    def __init__(self, mongodb_client=None, initial_capital: float = 1000000):
        """
        Initialize Money Management System
        
        Args:
            mongodb_client: MongoDB connection for persistence
            initial_capital: Starting capital
        """
        self.mongodb = mongodb_client
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Capital allocation
        self.capital_allocation = {
            'trading': initial_capital * 0.7,  # 70% for trading
            'protected': initial_capital * 0.2,  # 20% protected reserve
            'tax_reserve': initial_capital * 0.1  # 10% tax reserve
        }
        
        # Money management parameters
        self.parameters = {
            'max_risk_per_trade': 0.02,  # 2% max risk per trade
            'kelly_cap': 0.25,  # 25% Kelly cap
            'profit_lock_trigger': 0.20,  # Lock profits at 20% gain
            'trail_stop_activation': 0.10,  # Activate trail stop at 10% gain
            'trail_stop_distance': 0.05,  # 5% trailing distance
            'tax_rate': 0.30,  # 30% tax rate assumption
            'compound_frequency': 'monthly',  # Compound frequency
            'min_diversification': 5,  # Minimum 5 positions for diversification
            'max_concentration': 0.20,  # Max 20% in single position
            'martingale_prevention': True,  # Prevent doubling down on losses
            'profit_reinvestment_rate': 0.50,  # Reinvest 50% of profits
        }
        
        # Performance tracking
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'total_loss': 0,
            'peak_capital': initial_capital,
            'current_drawdown': 0,
            'compound_growth_rate': 0,
            'realized_tax_liability': 0
        }
        
        # Position tracking
        self.positions = {}  # symbol -> position details
        self.profit_targets = {}  # symbol -> ProfitTarget
        self.locked_profits = defaultdict(float)
        
        # Historical data
        self.trade_history = deque(maxlen=1000)
        self.capital_history = deque(maxlen=365)
        self.tax_history = deque(maxlen=100)
        
        # Strategy weights (for ensemble approach)
        self.strategy_weights = {
            ManagementStrategy.KELLY_CRITERION: 0.30,
            ManagementStrategy.FIXED_FRACTIONAL: 0.25,
            ManagementStrategy.ANTI_MARTINGALE: 0.20,
            ManagementStrategy.PROFIT_LOCK: 0.15,
            ManagementStrategy.RISK_PARITY: 0.10
        }
        
        # Tax tracking
        self.tax_tracker = {
            'short_term_gains': 0,
            'long_term_gains': 0,
            'wash_sales': [],
            'quarterly_payments': [],
            'year_to_date': 0
        }
        
        # Diversification tracking
        self.diversification = {
            'asset_classes': defaultdict(float),
            'sectors': defaultdict(float),
            'correlations': pd.DataFrame(),
            'concentration_index': 0
        }
        
    async def calculate_kelly_fraction(self,
                                      win_rate: float,
                                      avg_win: float,
                                      avg_loss: float,
                                      confidence: float = 1.0) -> float:
        """
        Calculate Kelly Criterion for optimal position sizing
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return
            confidence: Confidence in the edge (0-1)
            
        Returns:
            Kelly fraction (capped at 25%)
        """
        if avg_loss == 0:
            return 0
        
        # Basic Kelly formula: f = (p*b - q)/b
        # where p = win_rate, q = 1-p, b = avg_win/avg_loss
        win_prob = win_rate
        loss_prob = 1 - win_rate
        odds = avg_win / abs(avg_loss)
        
        # Calculate raw Kelly fraction
        kelly_fraction = (win_prob * odds - loss_prob) / odds
        
        # Apply confidence adjustment
        kelly_fraction *= confidence
        
        # Apply safety factor (use fractional Kelly)
        kelly_fraction *= 0.5  # Half Kelly for safety
        
        # Cap at maximum allowed
        kelly_fraction = min(kelly_fraction, self.parameters['kelly_cap'])
        
        # Ensure non-negative
        kelly_fraction = max(0, kelly_fraction)
        
        return kelly_fraction
    
    async def calculate_fixed_fractional(self,
                                        stop_loss_pct: float,
                                        account_balance: Optional[float] = None) -> float:
        """
        Calculate fixed fractional position size
        
        Args:
            stop_loss_pct: Stop loss percentage
            account_balance: Current account balance
            
        Returns:
            Position size in dollars
        """
        if account_balance is None:
            account_balance = self.capital_allocation['trading']
        
        # Risk amount per trade
        risk_amount = account_balance * self.parameters['max_risk_per_trade']
        
        # Position size based on stop loss
        if stop_loss_pct > 0:
            position_size = risk_amount / stop_loss_pct
        else:
            position_size = risk_amount
        
        # Cap at maximum concentration
        max_position = account_balance * self.parameters['max_concentration']
        position_size = min(position_size, max_position)
        
        return position_size
    
    async def apply_anti_martingale(self,
                                   recent_performance: List[float],
                                   base_size: float) -> float:
        """
        Apply anti-martingale strategy (increase size after wins, decrease after losses)
        
        Args:
            recent_performance: List of recent trade returns
            base_size: Base position size
            
        Returns:
            Adjusted position size
        """
        if not recent_performance:
            return base_size
        
        # Calculate recent win rate
        wins = sum(1 for r in recent_performance if r > 0)
        win_rate = wins / len(recent_performance)
        
        # Calculate streak
        current_streak = 0
        for result in reversed(recent_performance):
            if result > 0:
                if current_streak >= 0:
                    current_streak += 1
                else:
                    break
            else:
                if current_streak <= 0:
                    current_streak -= 1
                else:
                    break
        
        # Adjust size based on streak and win rate
        if current_streak > 0:  # Winning streak
            # Increase size gradually (max 50% increase)
            multiplier = 1 + min(current_streak * 0.1, 0.5)
        elif current_streak < 0:  # Losing streak
            # Decrease size more aggressively (max 50% decrease)
            multiplier = max(1 + current_streak * 0.15, 0.5)
        else:
            multiplier = 1.0
        
        # Additional adjustment based on overall win rate
        if win_rate > 0.6:
            multiplier *= 1.1
        elif win_rate < 0.4:
            multiplier *= 0.9
        
        # Apply martingale prevention
        if self.parameters['martingale_prevention'] and current_streak < -2:
            # Prevent increasing size after consecutive losses
            multiplier = min(multiplier, 0.7)
        
        adjusted_size = base_size * multiplier
        
        # Ensure within bounds
        min_size = base_size * 0.5
        max_size = base_size * 1.5
        adjusted_size = max(min_size, min(adjusted_size, max_size))
        
        return adjusted_size
    
    async def calculate_compound_growth(self,
                                       current_balance: float,
                                       returns_history: List[float]) -> Dict[str, float]:
        """
        Calculate compound growth metrics and optimal reinvestment
        
        Args:
            current_balance: Current account balance
            returns_history: Historical returns
            
        Returns:
            Compound growth metrics
        """
        if not returns_history:
            return {
                'compound_rate': 0,
                'optimal_reinvestment': 0,
                'projected_growth': 0
            }
        
        # Calculate geometric mean return
        total_return = np.prod([1 + r for r in returns_history]) - 1
        periods = len(returns_history)
        
        if periods > 0:
            geometric_mean = (1 + total_return) ** (1/periods) - 1
        else:
            geometric_mean = 0
        
        # Calculate volatility
        volatility = np.std(returns_history) if len(returns_history) > 1 else 0
        
        # Optimal growth rate (using growth-optimal portfolio theory)
        if volatility > 0:
            optimal_fraction = geometric_mean / (volatility ** 2)
            optimal_fraction = min(optimal_fraction, 1.0)
        else:
            optimal_fraction = self.parameters['profit_reinvestment_rate']
        
        # Calculate compound rate based on frequency
        if self.parameters['compound_frequency'] == 'daily':
            compound_periods = 252
        elif self.parameters['compound_frequency'] == 'weekly':
            compound_periods = 52
        elif self.parameters['compound_frequency'] == 'monthly':
            compound_periods = 12
        else:
            compound_periods = 4  # Quarterly
        
        # Annual compound rate
        annual_compound_rate = (1 + geometric_mean) ** compound_periods - 1
        
        # Optimal reinvestment amount
        available_profits = max(0, current_balance - self.initial_capital)
        optimal_reinvestment = available_profits * optimal_fraction
        
        # Projected growth (1 year)
        projected_balance = current_balance * (1 + annual_compound_rate)
        
        return {
            'compound_rate': annual_compound_rate,
            'geometric_mean': geometric_mean,
            'optimal_fraction': optimal_fraction,
            'optimal_reinvestment': optimal_reinvestment,
            'projected_balance': projected_balance,
            'volatility': volatility
        }
    
    async def implement_profit_lock(self,
                                   symbol: str,
                                   entry_price: float,
                                   current_price: float,
                                   position_size: float) -> Dict[str, Any]:
        """
        Implement profit locking mechanism
        
        Args:
            symbol: Asset symbol
            entry_price: Entry price
            current_price: Current price
            position_size: Position size
            
        Returns:
            Profit lock status and adjustments
        """
        # Calculate current profit
        profit_pct = (current_price - entry_price) / entry_price
        profit_amount = (current_price - entry_price) * position_size
        
        # Check if profit target exists
        if symbol not in self.profit_targets:
            self.profit_targets[symbol] = ProfitTarget(
                symbol=symbol,
                entry_price=entry_price,
                current_price=current_price,
                target_price=entry_price * (1 + self.parameters['profit_lock_trigger']),
                stop_loss=entry_price * 0.98,  # 2% initial stop loss
                trail_stop=None,
                profit_locked=0,
                status='ACTIVE'
            )
        
        target = self.profit_targets[symbol]
        target.current_price = current_price
        
        actions = {
            'lock_profits': False,
            'activate_trail_stop': False,
            'adjust_stop_loss': False,
            'partial_close': False,
            'full_close': False
        }
        
        # Check profit lock trigger
        if profit_pct >= self.parameters['profit_lock_trigger']:
            if target.profit_locked == 0:
                # Lock in profits by closing partial position
                lock_size = position_size * 0.5  # Lock 50% of position
                locked_amount = profit_amount * 0.5
                
                target.profit_locked = locked_amount
                self.locked_profits[symbol] += locked_amount
                
                # Move to protected capital
                self.capital_allocation['protected'] += locked_amount * 0.7
                self.capital_allocation['tax_reserve'] += locked_amount * 0.3
                
                actions['lock_profits'] = True
                actions['partial_close'] = True
                
                target.status = 'LOCKED'
        
        # Check trail stop activation
        if profit_pct >= self.parameters['trail_stop_activation']:
            if target.trail_stop is None:
                # Activate trailing stop
                target.trail_stop = current_price * (1 - self.parameters['trail_stop_distance'])
                actions['activate_trail_stop'] = True
            else:
                # Update trailing stop
                new_trail = current_price * (1 - self.parameters['trail_stop_distance'])
                if new_trail > target.trail_stop:
                    target.trail_stop = new_trail
                    actions['adjust_stop_loss'] = True
        
        # Check if trailing stop hit
        if target.trail_stop and current_price <= target.trail_stop:
            actions['full_close'] = True
            target.status = 'CLOSED'
        
        return {
            'symbol': symbol,
            'profit_pct': profit_pct,
            'profit_amount': profit_amount,
            'profit_locked': target.profit_locked,
            'trail_stop': target.trail_stop,
            'actions': actions,
            'status': target.status
        }
    
    async def enforce_diversification(self,
                                     portfolio: Dict[str, float]) -> Dict[str, Any]:
        """
        Enforce portfolio diversification requirements
        
        Args:
            portfolio: Current portfolio allocations
            
        Returns:
            Diversification analysis and adjustments
        """
        total_value = sum(portfolio.values())
        
        if total_value == 0:
            return {
                'diversified': True,
                'concentration_index': 0,
                'adjustments_needed': []
            }
        
        # Calculate concentration metrics
        positions_count = len(portfolio)
        concentrations = {k: v/total_value for k, v in portfolio.items()}
        
        # Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(c**2 for c in concentrations.values())
        
        # Check diversification requirements
        adjustments = []
        
        # Minimum positions check
        if positions_count < self.parameters['min_diversification']:
            adjustments.append({
                'issue': 'Insufficient diversification',
                'current_positions': positions_count,
                'required_positions': self.parameters['min_diversification'],
                'action': 'Add more positions'
            })
        
        # Maximum concentration check
        for symbol, concentration in concentrations.items():
            if concentration > self.parameters['max_concentration']:
                excess = concentration - self.parameters['max_concentration']
                reduce_amount = excess * total_value
                
                adjustments.append({
                    'issue': 'Over-concentrated position',
                    'symbol': symbol,
                    'current_pct': concentration * 100,
                    'max_allowed': self.parameters['max_concentration'] * 100,
                    'action': f'Reduce by ${reduce_amount:.2f}'
                })
        
        # Calculate diversification score (0-100)
        # Lower HHI = better diversification
        max_hhi = 1.0  # Worst case: single position
        min_hhi = 1.0 / max(positions_count, 1)  # Best case: equal weights
        
        if max_hhi > min_hhi:
            diversification_score = 100 * (1 - (hhi - min_hhi) / (max_hhi - min_hhi))
        else:
            diversification_score = 100
        
        # Asset class diversification
        asset_classes = self._classify_assets(portfolio)
        asset_concentration = defaultdict(float)
        
        for asset_class, symbols in asset_classes.items():
            asset_concentration[asset_class] = sum(portfolio.get(s, 0) for s in symbols) / total_value
        
        # Check if too concentrated in one asset class
        for asset_class, concentration in asset_concentration.items():
            if concentration > 0.5:  # Max 50% in one asset class
                adjustments.append({
                    'issue': 'Asset class concentration',
                    'asset_class': asset_class,
                    'concentration': concentration * 100,
                    'action': 'Rebalance across asset classes'
                })
        
        self.diversification['concentration_index'] = hhi
        
        return {
            'diversified': len(adjustments) == 0,
            'diversification_score': diversification_score,
            'concentration_index': hhi,
            'positions_count': positions_count,
            'asset_distribution': dict(asset_concentration),
            'adjustments_needed': adjustments
        }
    
    async def allocate_tax_reserve(self,
                                  realized_gains: float,
                                  holding_periods: Dict[str, int]) -> TaxAllocation:
        """
        Allocate appropriate tax reserves
        
        Args:
            realized_gains: Total realized gains
            holding_periods: Holding periods in days for each position
            
        Returns:
            Tax allocation details
        """
        # Separate short-term and long-term gains
        short_term_gains = 0
        long_term_gains = 0
        
        for symbol, gain in self.trade_history:
            if symbol in holding_periods:
                if holding_periods[symbol] < 365:
                    short_term_gains += max(0, gain)
                else:
                    long_term_gains += max(0, gain)
        
        # Calculate tax liability
        short_term_tax = short_term_gains * 0.35  # Higher rate for short-term
        long_term_tax = long_term_gains * 0.20   # Lower rate for long-term
        
        total_tax_liability = short_term_tax + long_term_tax
        
        # Add buffer for safety
        tax_reserve_needed = total_tax_liability * 1.1  # 10% buffer
        
        # Update tax reserve allocation
        current_reserve = self.capital_allocation['tax_reserve']
        
        if tax_reserve_needed > current_reserve:
            # Need to allocate more to tax reserve
            shortfall = tax_reserve_needed - current_reserve
            
            # Take from trading capital
            if self.capital_allocation['trading'] >= shortfall:
                self.capital_allocation['trading'] -= shortfall
                self.capital_allocation['tax_reserve'] += shortfall
            else:
                # Take what we can from trading, rest from protected
                available = self.capital_allocation['trading']
                self.capital_allocation['trading'] -= available
                self.capital_allocation['tax_reserve'] += available
                
                remaining = shortfall - available
                self.capital_allocation['protected'] -= remaining
                self.capital_allocation['tax_reserve'] += remaining
        
        # Calculate quarterly estimates
        quarterly_payment = total_tax_liability / 4
        
        # Check for wash sales
        wash_sales_amount = await self._check_wash_sales()
        
        allocation = TaxAllocation(
            total_profit=realized_gains,
            tax_rate=self.parameters['tax_rate'],
            tax_reserve=self.capital_allocation['tax_reserve'],
            short_term_gains=short_term_gains,
            long_term_gains=long_term_gains,
            wash_sales=wash_sales_amount,
            estimated_quarterly=quarterly_payment,
            year_end_liability=total_tax_liability
        )
        
        # Store tax allocation
        self.tax_tracker['year_to_date'] = total_tax_liability
        self.tax_tracker['quarterly_payments'].append(quarterly_payment)
        
        # Log to MongoDB
        if self.mongodb:
            await self._log_tax_allocation(allocation)
        
        return allocation
    
    async def calculate_position_size_ensemble(self,
                                              symbol: str,
                                              entry_price: float,
                                              stop_loss: float,
                                              market_conditions: Dict) -> Dict[str, Any]:
        """
        Calculate position size using ensemble of strategies
        
        Args:
            symbol: Asset symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            market_conditions: Current market conditions
            
        Returns:
            Ensemble position sizing recommendation
        """
        stop_loss_pct = abs(entry_price - stop_loss) / entry_price
        
        # Get recent performance
        recent_trades = list(self.trade_history)[-20:] if self.trade_history else []
        recent_performance = [t[1] for t in recent_trades]  # Extract returns
        
        # Calculate win rate and averages
        if recent_performance:
            wins = [r for r in recent_performance if r > 0]
            losses = [r for r in recent_performance if r < 0]
            
            win_rate = len(wins) / len(recent_performance) if recent_performance else 0.5
            avg_win = np.mean(wins) if wins else stop_loss_pct * 2
            avg_loss = abs(np.mean(losses)) if losses else stop_loss_pct
        else:
            win_rate = 0.5
            avg_win = stop_loss_pct * 2
            avg_loss = stop_loss_pct
        
        # Strategy 1: Kelly Criterion
        kelly_fraction = await self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
        kelly_size = self.capital_allocation['trading'] * kelly_fraction
        
        # Strategy 2: Fixed Fractional
        fixed_size = await self.calculate_fixed_fractional(stop_loss_pct)
        
        # Strategy 3: Anti-Martingale
        anti_mart_size = await self.apply_anti_martingale(recent_performance, fixed_size)
        
        # Strategy 4: Volatility Targeting
        volatility = market_conditions.get('volatility', 0.02)
        target_volatility = 0.15  # 15% annual target
        vol_scalar = min(target_volatility / (volatility * np.sqrt(252)), 1.5)
        volatility_size = fixed_size * vol_scalar
        
        # Strategy 5: Risk Parity
        correlations = market_conditions.get('correlations', {})
        avg_correlation = np.mean(list(correlations.values())) if correlations else 0
        risk_parity_scalar = 1 - (avg_correlation * 0.5)  # Reduce size for high correlation
        risk_parity_size = fixed_size * risk_parity_scalar
        
        # Calculate weighted ensemble size
        sizes = {
            ManagementStrategy.KELLY_CRITERION: kelly_size,
            ManagementStrategy.FIXED_FRACTIONAL: fixed_size,
            ManagementStrategy.ANTI_MARTINGALE: anti_mart_size,
            ManagementStrategy.VOLATILITY_TARGETING: volatility_size,
            ManagementStrategy.RISK_PARITY: risk_parity_size
        }
        
        # Weighted average
        ensemble_size = sum(
            sizes.get(strategy, 0) * weight
            for strategy, weight in self.strategy_weights.items()
        )
        
        # Apply final constraints
        min_size = self.capital_allocation['trading'] * 0.01  # Min 1% position
        max_size = self.capital_allocation['trading'] * self.parameters['max_concentration']
        
        final_size = max(min_size, min(ensemble_size, max_size))
        
        # Calculate position details
        shares = int(final_size / entry_price)
        actual_size = shares * entry_price
        risk_amount = shares * (entry_price - stop_loss)
        risk_pct = risk_amount / self.capital_allocation['trading']
        
        return {
            'symbol': symbol,
            'recommended_shares': shares,
            'position_value': actual_size,
            'risk_amount': risk_amount,
            'risk_pct': risk_pct * 100,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'strategy_sizes': {str(k): v for k, v in sizes.items()},
            'ensemble_size': ensemble_size,
            'final_size': final_size,
            'kelly_fraction': kelly_fraction,
            'volatility_scalar': vol_scalar,
            'risk_parity_scalar': risk_parity_scalar
        }
    
    async def update_capital_allocation(self, pnl: float, symbol: str = None):
        """
        Update capital allocation based on P&L
        
        Args:
            pnl: Profit/Loss amount
            symbol: Symbol of the trade
        """
        self.current_capital += pnl
        
        if pnl > 0:
            # Profit allocation
            tax_allocation = pnl * self.parameters['tax_rate']
            protected_allocation = pnl * 0.2  # 20% to protected
            trading_allocation = pnl - tax_allocation - protected_allocation
            
            self.capital_allocation['tax_reserve'] += tax_allocation
            self.capital_allocation['protected'] += protected_allocation
            self.capital_allocation['trading'] += trading_allocation
            
            self.performance['total_profit'] += pnl
            self.performance['winning_trades'] += 1
        else:
            # Loss - deduct from trading capital
            self.capital_allocation['trading'] += pnl  # pnl is negative
            self.performance['total_loss'] += abs(pnl)
            self.performance['losing_trades'] += 1
        
        # Update performance metrics
        self.performance['total_trades'] += 1
        
        # Update peak and drawdown
        if self.current_capital > self.performance['peak_capital']:
            self.performance['peak_capital'] = self.current_capital
        
        drawdown = (self.performance['peak_capital'] - self.current_capital) / self.performance['peak_capital']
        self.performance['current_drawdown'] = drawdown
        
        # Store in history
        if symbol:
            self.trade_history.append((symbol, pnl / self.current_capital))
        
        self.capital_history.append({
            'timestamp': time.time(),
            'capital': self.current_capital,
            'allocation': dict(self.capital_allocation)
        })
    
    async def get_money_metrics(self) -> MoneyMetrics:
        """
        Get comprehensive money management metrics
        
        Returns:
            Current money metrics
        """
        # Calculate Kelly fraction for current conditions
        recent_trades = list(self.trade_history)[-50:] if self.trade_history else []
        if recent_trades:
            wins = [t[1] for t in recent_trades if t[1] > 0]
            losses = [abs(t[1]) for t in recent_trades if t[1] < 0]
            
            win_rate = len(wins) / len(recent_trades) if recent_trades else 0.5
            avg_win = np.mean(wins) if wins else 0.02
            avg_loss = np.mean(losses) if losses else 0.01
            
            kelly = await self.calculate_kelly_fraction(win_rate, avg_win, avg_loss)
        else:
            kelly = 0
        
        # Get compound growth metrics
        returns = [t[1] for t in recent_trades] if recent_trades else []
        compound_metrics = await self.calculate_compound_growth(self.current_capital, returns)
        
        # Get diversification score
        current_positions = {k: v.get('value', 0) for k, v in self.positions.items()}
        div_analysis = await self.enforce_diversification(current_positions)
        
        metrics = MoneyMetrics(
            timestamp=time.time(),
            total_capital=self.current_capital,
            trading_capital=self.capital_allocation['trading'],
            protected_capital=self.capital_allocation['protected'],
            tax_reserve=self.capital_allocation['tax_reserve'],
            profit_locked=sum(self.locked_profits.values()),
            current_allocation=dict(self.capital_allocation),
            kelly_fraction=kelly,
            risk_per_trade=self.parameters['max_risk_per_trade'],
            compound_rate=compound_metrics['compound_rate'],
            diversification_score=div_analysis['diversification_score'],
            strategy_performance={
                'win_rate': self.performance['winning_trades'] / max(self.performance['total_trades'], 1),
                'profit_factor': self.performance['total_profit'] / max(abs(self.performance['total_loss']), 1),
                'drawdown': self.performance['current_drawdown']
            }
        )
        
        # Log metrics
        if self.mongodb:
            await self._log_money_metrics(metrics)
        
        return metrics
    
    def _classify_assets(self, portfolio: Dict[str, float]) -> Dict[str, List[str]]:
        """Classify assets into categories"""
        classifications = {
            'crypto': [],
            'forex': [],
            'equity': [],
            'etf': [],
            'commodity': []
        }
        
        for symbol in portfolio.keys():
            if symbol in ['BTC', 'ETH', 'SOL'] or 'USD' in symbol and len(symbol) > 6:
                classifications['crypto'].append(symbol)
            elif any(curr in symbol for curr in ['EUR', 'GBP', 'JPY', 'AUD']):
                classifications['forex'].append(symbol)
            elif symbol in ['SPY', 'QQQ', 'IWM', 'DIA']:
                classifications['etf'].append(symbol)
            elif symbol in ['GLD', 'SLV', 'USO']:
                classifications['commodity'].append(symbol)
            else:
                classifications['equity'].append(symbol)
        
        return classifications
    
    async def _check_wash_sales(self) -> float:
        """Check for wash sale violations"""
        wash_sales_amount = 0
        
        # Simple wash sale detection (would be more complex in production)
        recent_sells = [(t[0], t[1]) for t in self.trade_history if t[1] < 0]
        
        for symbol, loss in recent_sells[-30:]:  # Last 30 days
            # Check if repurchased within 30 days
            repurchases = [t for t in self.trade_history if t[0] == symbol and t[1] > 0]
            if repurchases:
                wash_sales_amount += abs(loss)
        
        self.tax_tracker['wash_sales'].append(wash_sales_amount)
        return wash_sales_amount
    
    async def _log_tax_allocation(self, allocation: TaxAllocation):
        """Log tax allocation to MongoDB"""
        if self.mongodb:
            await self.mongodb.tax_allocations.insert_one({
                'timestamp': time.time(),
                'total_profit': allocation.total_profit,
                'tax_reserve': allocation.tax_reserve,
                'short_term_gains': allocation.short_term_gains,
                'long_term_gains': allocation.long_term_gains,
                'wash_sales': allocation.wash_sales,
                'quarterly_payment': allocation.estimated_quarterly,
                'year_end_liability': allocation.year_end_liability
            })
    
    async def _log_money_metrics(self, metrics: MoneyMetrics):
        """Log money metrics to MongoDB"""
        if self.mongodb:
            await self.mongodb.money_metrics.insert_one({
                'timestamp': metrics.timestamp,
                'total_capital': metrics.total_capital,
                'trading_capital': metrics.trading_capital,
                'protected_capital': metrics.protected_capital,
                'tax_reserve': metrics.tax_reserve,
                'profit_locked': metrics.profit_locked,
                'kelly_fraction': metrics.kelly_fraction,
                'compound_rate': metrics.compound_rate,
                'diversification_score': metrics.diversification_score
            })

# Factory function
async def create_money_manager(initial_capital: float = 1000000) -> MoneyManagementSystem:
    """Create money management system"""
    return MoneyManagementSystem(initial_capital=initial_capital)