"""
AuraQuant Advanced Money Management System
The Infinity Money Synthetic Intelligence System
Kelly Criterion, Optimal F, Position Sizing, Capital Preservation
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import json
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_db_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AllocationStrategy(Enum):
    """Capital allocation strategies"""
    EQUAL_WEIGHT = "equal_weight"
    RISK_PARITY = "risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    OPTIMAL_F = "optimal_f"
    VOLATILITY_SCALED = "volatility_scaled"
    MOMENTUM_WEIGHTED = "momentum_weighted"
    CORRELATION_ADJUSTED = "correlation_adjusted"

class CompoundingMode(Enum):
    """Profit compounding strategies"""
    NONE = "none"  # No compounding
    CONSERVATIVE = "conservative"  # Compound 25% of profits
    MODERATE = "moderate"  # Compound 50% of profits
    AGGRESSIVE = "aggressive"  # Compound 75% of profits
    FULL = "full"  # Compound 100% of profits
    ADAPTIVE = "adaptive"  # Based on win rate stability

@dataclass
class CapitalAllocation:
    """Capital allocation for a position"""
    symbol: str
    allocation_pct: float  # Percentage of total capital
    position_size: float  # Number of units/shares
    dollar_amount: float  # Dollar value
    stop_loss: float  # Stop loss price
    take_profit: float  # Take profit price
    risk_amount: float  # Dollar risk
    reward_amount: float  # Dollar reward
    risk_reward_ratio: float
    confidence_score: float
    strategy: str
    timestamp: datetime
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'allocation_pct': self.allocation_pct,
            'position_size': self.position_size,
            'dollar_amount': self.dollar_amount,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_amount': self.risk_amount,
            'reward_amount': self.reward_amount,
            'risk_reward_ratio': self.risk_reward_ratio,
            'confidence_score': self.confidence_score,
            'strategy': self.strategy,
            'timestamp': self.timestamp
        }

@dataclass
class MoneyManagementRules:
    """Money management rules and limits"""
    max_position_size_pct: float = 10.0  # Max % per position
    max_sector_exposure_pct: float = 30.0  # Max % per sector
    max_correlation_exposure: float = 50.0  # Max % in correlated assets
    min_position_size_pct: float = 0.5  # Min % per position
    max_daily_risk_pct: float = 2.0  # Max daily risk %
    max_open_positions: int = 20  # Maximum concurrent positions
    min_risk_reward_ratio: float = 1.5  # Minimum R:R ratio
    kelly_cap: float = 0.25  # Maximum Kelly fraction
    profit_lock_threshold: float = 0.2  # Lock profits at 20% gain
    trailing_stop_activation: float = 0.15  # Activate trailing at 15% gain
    trailing_stop_distance: float = 0.05  # Trail by 5%

class AdvancedMoneyManager:
    """
    Advanced Money Management System with:
    - Kelly Criterion optimization
    - Optimal F calculation
    - Dynamic position sizing
    - Risk parity allocation
    - Profit compounding strategies
    - Capital preservation
    """
    
    def __init__(self):
        """Initialize the Advanced Money Manager"""
        self.db_config = get_db_config()
        self.db = None
        
        # Management rules
        self.rules = MoneyManagementRules()
        
        # Capital tracking
        self.total_capital = 100000.0  # Starting capital
        self.available_capital = 100000.0
        self.allocated_capital = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        
        # Position tracking
        self.active_positions = {}
        self.position_history = []
        
        # Performance metrics
        self.win_rate = 0.5
        self.avg_win = 0.0
        self.avg_loss = 0.0
        self.profit_factor = 1.0
        self.kelly_fraction = 0.02
        self.optimal_f = 0.02
        
        # Compounding settings
        self.compounding_mode = CompoundingMode.MODERATE
        self.compound_threshold = 10000  # Compound after $10k profit
        
        # Sector and correlation tracking
        self.sector_exposures = {}
        self.correlation_matrix = pd.DataFrame()
        
        logger.info("💰 Advanced Money Manager initialized")
    
    async def connect(self):
        """Connect to MongoDB"""
        if self.db_config.async_client:
            self.db = self.db_config.async_db
            logger.info("✅ Money Manager connected to MongoDB")
            
            # Load saved state
            await self._load_state()
    
    async def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence_score: float,
        strategy: AllocationStrategy = AllocationStrategy.KELLY_CRITERION
    ) -> CapitalAllocation:
        """
        Calculate optimal position size based on strategy
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit target
            confidence_score: Strategy confidence (0-1)
            strategy: Allocation strategy to use
            
        Returns:
            CapitalAllocation object with position details
        """
        
        # Calculate risk and reward
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = abs(take_profit - entry_price)
        risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0
        
        # Check minimum R:R ratio
        if risk_reward_ratio < self.rules.min_risk_reward_ratio:
            logger.warning(f"R:R ratio {risk_reward_ratio:.2f} below minimum {self.rules.min_risk_reward_ratio}")
            return self._create_zero_allocation(symbol)
        
        # Calculate allocation percentage based on strategy
        if strategy == AllocationStrategy.KELLY_CRITERION:
            allocation_pct = await self._calculate_kelly_allocation(
                symbol, confidence_score, risk_reward_ratio
            )
        elif strategy == AllocationStrategy.OPTIMAL_F:
            allocation_pct = await self._calculate_optimal_f_allocation(
                symbol, risk_per_unit
            )
        elif strategy == AllocationStrategy.RISK_PARITY:
            allocation_pct = await self._calculate_risk_parity_allocation(
                symbol, risk_per_unit
            )
        elif strategy == AllocationStrategy.VOLATILITY_SCALED:
            allocation_pct = await self._calculate_volatility_scaled_allocation(
                symbol
            )
        elif strategy == AllocationStrategy.MOMENTUM_WEIGHTED:
            allocation_pct = await self._calculate_momentum_weighted_allocation(
                symbol, confidence_score
            )
        else:  # EQUAL_WEIGHT
            allocation_pct = min(
                self.rules.max_position_size_pct,
                100.0 / max(1, len(self.active_positions) + 1)
            )
        
        # Apply position size limits
        allocation_pct = self._apply_position_limits(allocation_pct)
        
        # Check sector exposure
        allocation_pct = await self._check_sector_exposure(symbol, allocation_pct)
        
        # Check correlation exposure
        allocation_pct = await self._check_correlation_exposure(symbol, allocation_pct)
        
        # Calculate actual position size
        dollar_amount = self.available_capital * (allocation_pct / 100.0)
        position_size = dollar_amount / entry_price
        
        # Calculate risk and reward amounts
        risk_amount = position_size * risk_per_unit
        reward_amount = position_size * reward_per_unit
        
        # Create allocation object
        allocation = CapitalAllocation(
            symbol=symbol,
            allocation_pct=allocation_pct,
            position_size=position_size,
            dollar_amount=dollar_amount,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward_ratio,
            confidence_score=confidence_score,
            strategy=strategy.value,
            timestamp=datetime.now()
        )
        
        logger.info(f"📊 Position Size Calculated: {symbol} - ${dollar_amount:.2f} ({allocation_pct:.2f}%)")
        
        return allocation
    
    async def _calculate_kelly_allocation(
        self,
        symbol: str,
        confidence_score: float,
        risk_reward_ratio: float
    ) -> float:
        """
        Calculate position size using Kelly Criterion
        
        Kelly Formula: f = (p*b - q) / b
        where:
        f = fraction of capital to bet
        p = probability of winning
        b = ratio of win to loss
        q = probability of losing (1-p)
        """
        
        # Get historical performance for this symbol
        win_rate, avg_win_ratio = await self._get_symbol_performance(symbol)
        
        # Adjust win rate by confidence score
        adjusted_win_rate = win_rate * confidence_score
        
        # Calculate Kelly fraction
        if risk_reward_ratio > 0:
            kelly = (adjusted_win_rate * risk_reward_ratio - (1 - adjusted_win_rate)) / risk_reward_ratio
        else:
            kelly = 0
        
        # Apply Kelly cap for safety
        kelly = min(kelly, self.rules.kelly_cap)
        
        # Convert to percentage
        allocation_pct = max(0, kelly * 100)
        
        # Store for analysis
        self.kelly_fraction = kelly
        
        return allocation_pct
    
    async def _calculate_optimal_f_allocation(
        self,
        symbol: str,
        risk_per_unit: float
    ) -> float:
        """
        Calculate position size using Optimal F
        
        Optimal F maximizes geometric growth rate
        """
        
        # Get trade history
        trades = await self._get_trade_history(symbol)
        
        if len(trades) < 10:
            # Not enough history, use conservative allocation
            return self.rules.min_position_size_pct
        
        # Calculate optimal F using iterative method
        best_f = 0.01
        best_growth = 0
        
        for f in np.arange(0.01, 0.5, 0.01):
            growth = self._calculate_geometric_growth(trades, f)
            if growth > best_growth:
                best_growth = growth
                best_f = f
        
        # Apply safety cap
        best_f = min(best_f, self.rules.kelly_cap)
        
        # Store for analysis
        self.optimal_f = best_f
        
        return best_f * 100
    
    async def _calculate_risk_parity_allocation(
        self,
        symbol: str,
        risk_per_unit: float
    ) -> float:
        """
        Calculate allocation using Risk Parity
        
        Each position contributes equally to portfolio risk
        """
        
        # Calculate volatility
        volatility = await self._get_symbol_volatility(symbol)
        
        if volatility == 0:
            return self.rules.min_position_size_pct
        
        # Target risk contribution
        target_risk_contribution = self.rules.max_daily_risk_pct / max(1, len(self.active_positions) + 1)
        
        # Calculate allocation
        allocation_pct = target_risk_contribution / volatility * 100
        
        return allocation_pct
    
    async def _calculate_volatility_scaled_allocation(
        self,
        symbol: str
    ) -> float:
        """
        Scale position size inversely to volatility
        """
        
        volatility = await self._get_symbol_volatility(symbol)
        
        if volatility == 0:
            return self.rules.min_position_size_pct
        
        # Base allocation
        base_allocation = self.rules.max_position_size_pct
        
        # Scale by inverse volatility (lower vol = larger position)
        target_vol = 0.15  # 15% annual volatility target
        allocation_pct = base_allocation * min(2, target_vol / volatility)
        
        return allocation_pct
    
    async def _calculate_momentum_weighted_allocation(
        self,
        symbol: str,
        confidence_score: float
    ) -> float:
        """
        Weight allocation by momentum strength
        """
        
        momentum_score = await self._get_momentum_score(symbol)
        
        # Combine momentum and confidence
        combined_score = (momentum_score + confidence_score) / 2
        
        # Scale allocation
        allocation_pct = self.rules.max_position_size_pct * combined_score
        
        return allocation_pct
    
    def _apply_position_limits(self, allocation_pct: float) -> float:
        """Apply position size limits"""
        
        # Apply max and min limits
        allocation_pct = max(self.rules.min_position_size_pct, allocation_pct)
        allocation_pct = min(self.rules.max_position_size_pct, allocation_pct)
        
        # Check if we have room for new position
        if len(self.active_positions) >= self.rules.max_open_positions:
            logger.warning(f"Maximum positions reached: {self.rules.max_open_positions}")
            return 0.0
        
        # Check available capital
        max_available_pct = (self.available_capital / self.total_capital) * 100
        allocation_pct = min(allocation_pct, max_available_pct)
        
        return allocation_pct
    
    async def _check_sector_exposure(self, symbol: str, allocation_pct: float) -> float:
        """Check and limit sector exposure"""
        
        sector = await self._get_symbol_sector(symbol)
        
        if not sector:
            return allocation_pct
        
        # Calculate current sector exposure
        current_exposure = self.sector_exposures.get(sector, 0.0)
        
        # Check if adding this position would exceed limit
        total_exposure = current_exposure + allocation_pct
        
        if total_exposure > self.rules.max_sector_exposure_pct:
            # Reduce allocation to fit within limit
            max_additional = self.rules.max_sector_exposure_pct - current_exposure
            allocation_pct = max(0, max_additional)
            logger.warning(f"Sector exposure limit: {sector} reduced to {allocation_pct:.2f}%")
        
        return allocation_pct
    
    async def _check_correlation_exposure(self, symbol: str, allocation_pct: float) -> float:
        """Check and limit correlation exposure"""
        
        if len(self.active_positions) == 0:
            return allocation_pct
        
        # Calculate correlation with existing positions
        total_correlated_exposure = 0.0
        
        for pos_symbol in self.active_positions:
            correlation = await self._get_correlation(symbol, pos_symbol)
            
            if abs(correlation) > 0.7:  # High correlation threshold
                pos_allocation = self.active_positions[pos_symbol].get('allocation_pct', 0)
                total_correlated_exposure += pos_allocation * abs(correlation)
        
        # Check limit
        if total_correlated_exposure + allocation_pct > self.rules.max_correlation_exposure:
            max_additional = self.rules.max_correlation_exposure - total_correlated_exposure
            allocation_pct = max(0, max_additional)
            logger.warning(f"Correlation exposure limit: {symbol} reduced to {allocation_pct:.2f}%")
        
        return allocation_pct
    
    async def execute_position(self, allocation: CapitalAllocation) -> bool:
        """
        Execute a position based on allocation
        
        Args:
            allocation: CapitalAllocation object
            
        Returns:
            bool: Success status
        """
        
        try:
            # Update capital
            self.allocated_capital += allocation.dollar_amount
            self.available_capital -= allocation.dollar_amount
            
            # Store position
            self.active_positions[allocation.symbol] = {
                'allocation': allocation,
                'entry_time': datetime.now(),
                'status': 'active',
                'trailing_stop_active': False,
                'highest_price': allocation.dollar_amount / allocation.position_size
            }
            
            # Update sector exposure
            sector = await self._get_symbol_sector(allocation.symbol)
            if sector:
                self.sector_exposures[sector] = self.sector_exposures.get(sector, 0) + allocation.allocation_pct
            
            # Store in database
            await self._store_position(allocation)
            
            logger.info(f"✅ Position executed: {allocation.symbol} - ${allocation.dollar_amount:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute position: {e}")
            return False
    
    async def update_position(
        self,
        symbol: str,
        current_price: float,
        high_price: float = None
    ):
        """
        Update position with current price and check for profit locks/trailing stops
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            high_price: Highest price since entry
        """
        
        if symbol not in self.active_positions:
            return
        
        position = self.active_positions[symbol]
        allocation = position['allocation']
        
        # Calculate current P&L
        entry_price = allocation.dollar_amount / allocation.position_size
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Update highest price
        if high_price:
            position['highest_price'] = max(position['highest_price'], high_price)
        
        # Check for profit lock
        if pnl_pct >= self.rules.profit_lock_threshold:
            if not position.get('profit_locked', False):
                await self._lock_profits(symbol, current_price)
                position['profit_locked'] = True
        
        # Check for trailing stop activation
        if pnl_pct >= self.rules.trailing_stop_activation:
            if not position['trailing_stop_active']:
                position['trailing_stop_active'] = True
                position['trailing_stop_price'] = current_price * (1 - self.rules.trailing_stop_distance)
                logger.info(f"📈 Trailing stop activated for {symbol} at ${position['trailing_stop_price']:.2f}")
        
        # Update trailing stop
        if position['trailing_stop_active']:
            new_trailing_stop = current_price * (1 - self.rules.trailing_stop_distance)
            if new_trailing_stop > position.get('trailing_stop_price', 0):
                position['trailing_stop_price'] = new_trailing_stop
                
                # Check if trailing stop hit
                if current_price <= position['trailing_stop_price']:
                    await self.close_position(symbol, current_price, 'trailing_stop')
    
    async def close_position(
        self,
        symbol: str,
        exit_price: float,
        reason: str = 'manual'
    ) -> float:
        """
        Close a position and update capital
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Reason for closing
            
        Returns:
            float: Realized P&L
        """
        
        if symbol not in self.active_positions:
            logger.warning(f"Position not found: {symbol}")
            return 0.0
        
        position = self.active_positions[symbol]
        allocation = position['allocation']
        
        # Calculate P&L
        entry_price = allocation.dollar_amount / allocation.position_size
        pnl = (exit_price - entry_price) * allocation.position_size
        pnl_pct = pnl / allocation.dollar_amount * 100
        
        # Update capital
        exit_value = exit_price * allocation.position_size
        self.available_capital += exit_value
        self.allocated_capital -= allocation.dollar_amount
        self.realized_pnl += pnl
        
        # Update sector exposure
        sector = await self._get_symbol_sector(symbol)
        if sector:
            self.sector_exposures[sector] -= allocation.allocation_pct
        
        # Store trade history
        trade = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': allocation.position_size,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'reason': reason,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now()
        }
        self.position_history.append(trade)
        await self._store_trade(trade)
        
        # Update performance metrics
        await self._update_performance_metrics()
        
        # Handle compounding
        await self._handle_compounding()
        
        # Remove from active positions
        del self.active_positions[symbol]
        
        logger.info(f"📊 Position closed: {symbol} - P&L: ${pnl:.2f} ({pnl_pct:.2f}%) - Reason: {reason}")
        
        return pnl
    
    async def _handle_compounding(self):
        """Handle profit compounding based on mode"""
        
        if self.compounding_mode == CompoundingMode.NONE:
            return
        
        # Check if we meet compound threshold
        if self.realized_pnl < self.compound_threshold:
            return
        
        # Calculate compound amount based on mode
        if self.compounding_mode == CompoundingMode.CONSERVATIVE:
            compound_pct = 0.25
        elif self.compounding_mode == CompoundingMode.MODERATE:
            compound_pct = 0.50
        elif self.compounding_mode == CompoundingMode.AGGRESSIVE:
            compound_pct = 0.75
        elif self.compounding_mode == CompoundingMode.FULL:
            compound_pct = 1.0
        elif self.compounding_mode == CompoundingMode.ADAPTIVE:
            # Base on win rate stability
            compound_pct = min(1.0, self.win_rate * self.profit_factor / 2)
        else:
            compound_pct = 0.5
        
        # Compound profits
        compound_amount = self.realized_pnl * compound_pct
        self.total_capital += compound_amount
        self.available_capital += compound_amount
        self.realized_pnl -= compound_amount
        
        logger.info(f"💰 Compounded ${compound_amount:.2f} into capital (Total: ${self.total_capital:.2f})")
    
    async def _lock_profits(self, symbol: str, current_price: float):
        """Lock in partial profits"""
        
        position = self.active_positions[symbol]
        allocation = position['allocation']
        
        # Move stop loss to breakeven or higher
        entry_price = allocation.dollar_amount / allocation.position_size
        new_stop = entry_price * 1.01  # 1% above entry
        
        allocation.stop_loss = new_stop
        
        logger.info(f"🔒 Profits locked for {symbol} - Stop moved to ${new_stop:.2f}")
    
    async def _update_performance_metrics(self):
        """Update performance metrics from trade history"""
        
        if len(self.position_history) == 0:
            return
        
        # Calculate win rate
        wins = [t for t in self.position_history if t['pnl'] > 0]
        losses = [t for t in self.position_history if t['pnl'] < 0]
        
        self.win_rate = len(wins) / len(self.position_history) if self.position_history else 0
        
        # Calculate average win/loss
        self.avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        self.avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 0
        
        # Calculate profit factor
        total_wins = sum([t['pnl'] for t in wins])
        total_losses = abs(sum([t['pnl'] for t in losses]))
        self.profit_factor = total_wins / total_losses if total_losses > 0 else 1.0
    
    def _calculate_geometric_growth(self, trades: List[Dict], f: float) -> float:
        """Calculate geometric growth rate for Optimal F"""
        
        if not trades:
            return 0
        
        twr = 1.0  # Terminal wealth relative
        
        for trade in trades:
            pnl_pct = trade.get('pnl_pct', 0) / 100
            twr *= (1 + f * pnl_pct)
        
        # Calculate geometric mean
        n = len(trades)
        geometric_mean = twr ** (1/n) - 1 if n > 0 else 0
        
        return geometric_mean
    
    def _create_zero_allocation(self, symbol: str) -> CapitalAllocation:
        """Create zero allocation when position should not be taken"""
        return CapitalAllocation(
            symbol=symbol,
            allocation_pct=0,
            position_size=0,
            dollar_amount=0,
            stop_loss=0,
            take_profit=0,
            risk_amount=0,
            reward_amount=0,
            risk_reward_ratio=0,
            confidence_score=0,
            strategy="none",
            timestamp=datetime.now()
        )
    
    async def _get_symbol_performance(self, symbol: str) -> Tuple[float, float]:
        """Get historical performance for symbol"""
        # Implement based on actual trade history
        # This is a placeholder
        return 0.55, 2.0  # 55% win rate, 2:1 avg win ratio
    
    async def _get_trade_history(self, symbol: str) -> List[Dict]:
        """Get trade history for symbol"""
        if self.db:
            trades = await self.db.trades.find({'symbol': symbol}).to_list(100)
            return trades
        return []
    
    async def _get_symbol_volatility(self, symbol: str) -> float:
        """Get symbol volatility"""
        # Implement based on actual price data
        # This is a placeholder
        return 0.20  # 20% annual volatility
    
    async def _get_momentum_score(self, symbol: str) -> float:
        """Get momentum score for symbol"""
        # Implement based on actual price data
        # This is a placeholder
        return 0.7  # 70% momentum score
    
    async def _get_symbol_sector(self, symbol: str) -> str:
        """Get sector for symbol"""
        # Implement based on symbol mapping
        # This is a placeholder
        sectors = {
            'AAPL': 'Technology',
            'GOOGL': 'Technology',
            'JPM': 'Financials',
            'XOM': 'Energy',
            'BTCUSD': 'Crypto',
            'ETHUSD': 'Crypto'
        }
        return sectors.get(symbol, 'Unknown')
    
    async def _get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols"""
        # Implement based on actual price data
        # This is a placeholder
        if symbol1 == symbol2:
            return 1.0
        
        # Simplified correlation logic
        sector1 = await self._get_symbol_sector(symbol1)
        sector2 = await self._get_symbol_sector(symbol2)
        
        if sector1 == sector2:
            return 0.7  # High correlation within sector
        else:
            return 0.3  # Low correlation across sectors
    
    async def _store_position(self, allocation: CapitalAllocation):
        """Store position in MongoDB"""
        if self.db:
            await self.db.positions.insert_one(allocation.to_dict())
    
    async def _store_trade(self, trade: Dict):
        """Store completed trade in MongoDB"""
        if self.db:
            await self.db.trades.insert_one(trade)
    
    async def _load_state(self):
        """Load saved state from MongoDB"""
        if self.db:
            # Load capital state
            state = await self.db.money_management_state.find_one(sort=[('timestamp', -1)])
            if state:
                self.total_capital = state.get('total_capital', 100000)
                self.available_capital = state.get('available_capital', 100000)
                self.realized_pnl = state.get('realized_pnl', 0)
                self.win_rate = state.get('win_rate', 0.5)
                self.profit_factor = state.get('profit_factor', 1.0)
    
    async def save_state(self):
        """Save current state to MongoDB"""
        if self.db:
            state = {
                'total_capital': self.total_capital,
                'available_capital': self.available_capital,
                'allocated_capital': self.allocated_capital,
                'realized_pnl': self.realized_pnl,
                'unrealized_pnl': self.unrealized_pnl,
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'kelly_fraction': self.kelly_fraction,
                'optimal_f': self.optimal_f,
                'active_positions': len(self.active_positions),
                'timestamp': datetime.now()
            }
            await self.db.money_management_state.insert_one(state)

# Export the money manager
money_manager = AdvancedMoneyManager()