"""
AuraQuant Advanced Risk Management System
The Infinity Money Synthetic Intelligence System
Kill Switch, Max Drawdown Lock, Slippage Control, Liquidity Management
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.database import get_db_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level classification"""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    EXTREME = 5
    CRITICAL = 6

class SystemState(Enum):
    """System operational state"""
    NORMAL = "normal"
    CAUTION = "caution"
    RESTRICTED = "restricted"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"

@dataclass
class RiskMetrics:
    """Real-time risk metrics"""
    current_drawdown: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    sortino_ratio: float
    leverage: float
    concentration_risk: float
    liquidity_score: float
    correlation_risk: float
    timestamp: datetime
    
    def to_dict(self):
        return {
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'leverage': self.leverage,
            'concentration_risk': self.concentration_risk,
            'liquidity_score': self.liquidity_score,
            'correlation_risk': self.correlation_risk,
            'timestamp': self.timestamp
        }

@dataclass
class RiskLimit:
    """Risk limit configuration"""
    max_drawdown: float = -20.0  # Maximum allowed drawdown (%)
    max_position_size: float = 10.0  # Maximum position size (% of portfolio)
    max_leverage: float = 2.0  # Maximum leverage
    max_var_95: float = -5.0  # Maximum VaR at 95% confidence
    max_correlation: float = 0.8  # Maximum correlation between positions
    min_liquidity_ratio: float = 0.2  # Minimum cash/liquid assets ratio
    max_daily_loss: float = -3.0  # Maximum daily loss (%)
    max_consecutive_losses: int = 5  # Maximum consecutive losing trades
    max_slippage: float = 0.5  # Maximum acceptable slippage (%)
    min_sharpe: float = 0.5  # Minimum Sharpe ratio to continue trading

class AdvancedRiskManager:
    """
    Advanced Risk Management System with:
    - Real-time risk monitoring
    - Kill switch activation
    - Dynamic position sizing
    - Slippage control
    - Liquidity management
    - Correlation risk management
    """
    
    def __init__(self):
        """Initialize the Advanced Risk Manager"""
        self.db_config = get_db_config()
        self.db = None
        
        # Risk limits
        self.limits = RiskLimit()
        
        # System state
        self.system_state = SystemState.NORMAL
        self.kill_switch_active = False
        self.emergency_shutdown = False
        
        # Risk tracking
        self.current_metrics = None
        self.historical_metrics = []
        self.active_positions = {}
        self.trade_history = []
        
        # Risk counters
        self.consecutive_losses = 0
        self.daily_loss = 0.0
        self.high_water_mark = 100000  # Initial capital
        
        # Monitoring
        self.monitoring_active = False
        self.alert_callbacks = []
        
        logger.info("🛡️ Advanced Risk Manager initialized")
    
    async def connect(self):
        """Connect to MongoDB"""
        if self.db_config.async_client:
            self.db = self.db_config.async_db
            logger.info("✅ Risk Manager connected to MongoDB")
            
            # Load saved state
            await self._load_state()
    
    async def start_monitoring(self):
        """Start continuous risk monitoring"""
        self.monitoring_active = True
        logger.info("🔍 Risk monitoring started")
        
        while self.monitoring_active and not self.emergency_shutdown:
            try:
                # Calculate current risk metrics
                metrics = await self.calculate_risk_metrics()
                
                # Check risk limits
                await self.check_risk_limits(metrics)
                
                # Update system state
                await self.update_system_state(metrics)
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Sleep for monitoring interval
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(5)
    
    async def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate current risk metrics"""
        
        # Calculate portfolio value
        portfolio_value = await self._calculate_portfolio_value()
        
        # Calculate drawdown
        current_drawdown = ((portfolio_value - self.high_water_mark) / 
                           self.high_water_mark * 100)
        
        # Update high water mark
        if portfolio_value > self.high_water_mark:
            self.high_water_mark = portfolio_value
        
        # Calculate returns for metrics
        returns = await self._get_recent_returns()
        
        # Calculate VaR and CVaR
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        cvar_95 = np.mean(returns[returns <= var_95]) if len(returns) > 0 else 0
        
        # Calculate Sharpe and Sortino
        sharpe = self._calculate_sharpe(returns)
        sortino = self._calculate_sortino(returns)
        
        # Calculate leverage
        leverage = await self._calculate_leverage()
        
        # Calculate concentration risk
        concentration = await self._calculate_concentration_risk()
        
        # Calculate liquidity score
        liquidity = await self._calculate_liquidity_score()
        
        # Calculate correlation risk
        correlation = await self._calculate_correlation_risk()
        
        metrics = RiskMetrics(
            current_drawdown=current_drawdown,
            max_drawdown=min(current_drawdown, getattr(self.current_metrics, 'max_drawdown', 0) if self.current_metrics else 0),
            var_95=var_95,
            cvar_95=cvar_95,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            leverage=leverage,
            concentration_risk=concentration,
            liquidity_score=liquidity,
            correlation_risk=correlation,
            timestamp=datetime.now()
        )
        
        self.current_metrics = metrics
        return metrics
    
    async def check_risk_limits(self, metrics: RiskMetrics) -> List[str]:
        """Check if any risk limits are breached"""
        violations = []
        
        # Check drawdown limit
        if metrics.current_drawdown < self.limits.max_drawdown:
            violations.append(f"DRAWDOWN BREACH: {metrics.current_drawdown:.2f}% < {self.limits.max_drawdown:.2f}%")
            await self.trigger_kill_switch("Maximum drawdown exceeded")
        
        # Check VaR limit
        if metrics.var_95 < self.limits.max_var_95:
            violations.append(f"VaR BREACH: {metrics.var_95:.2f}% < {self.limits.max_var_95:.2f}%")
        
        # Check leverage limit
        if metrics.leverage > self.limits.max_leverage:
            violations.append(f"LEVERAGE BREACH: {metrics.leverage:.2f}x > {self.limits.max_leverage:.2f}x")
        
        # Check liquidity
        if metrics.liquidity_score < self.limits.min_liquidity_ratio:
            violations.append(f"LIQUIDITY WARNING: {metrics.liquidity_score:.2f} < {self.limits.min_liquidity_ratio:.2f}")
        
        # Check Sharpe ratio
        if metrics.sharpe_ratio < self.limits.min_sharpe:
            violations.append(f"SHARPE WARNING: {metrics.sharpe_ratio:.2f} < {self.limits.min_sharpe:.2f}")
        
        # Check daily loss
        if self.daily_loss < self.limits.max_daily_loss:
            violations.append(f"DAILY LOSS BREACH: {self.daily_loss:.2f}% < {self.limits.max_daily_loss:.2f}%")
            await self.trigger_kill_switch("Maximum daily loss exceeded")
        
        # Check consecutive losses
        if self.consecutive_losses >= self.limits.max_consecutive_losses:
            violations.append(f"CONSECUTIVE LOSSES: {self.consecutive_losses} >= {self.limits.max_consecutive_losses}")
            await self.trigger_kill_switch("Maximum consecutive losses exceeded")
        
        # Log violations
        for violation in violations:
            logger.warning(f"⚠️ RISK VIOLATION: {violation}")
            await self._send_alert(violation, RiskLevel.HIGH)
        
        return violations
    
    async def update_system_state(self, metrics: RiskMetrics):
        """Update system state based on risk metrics"""
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(metrics)
        
        # Determine system state
        if self.kill_switch_active:
            self.system_state = SystemState.SHUTDOWN
        elif risk_score > 80:
            self.system_state = SystemState.EMERGENCY
        elif risk_score > 60:
            self.system_state = SystemState.RESTRICTED
        elif risk_score > 40:
            self.system_state = SystemState.CAUTION
        else:
            self.system_state = SystemState.NORMAL
        
        logger.info(f"📊 System State: {self.system_state.value} (Risk Score: {risk_score:.1f})")
    
    async def trigger_kill_switch(self, reason: str):
        """Activate kill switch - emergency stop all trading"""
        logger.critical(f"🚨 KILL SWITCH ACTIVATED: {reason}")
        
        self.kill_switch_active = True
        self.system_state = SystemState.SHUTDOWN
        
        # Close all positions
        await self.close_all_positions()
        
        # Cancel all pending orders
        await self.cancel_all_orders()
        
        # Send emergency alert
        await self._send_alert(f"KILL SWITCH ACTIVATED: {reason}", RiskLevel.CRITICAL)
        
        # Store event
        await self._store_kill_switch_event(reason)
    
    async def reset_kill_switch(self, admin_override: str = None):
        """Reset kill switch (requires admin override)"""
        if not admin_override:
            logger.warning("Kill switch reset requires admin override")
            return False
        
        # Verify admin credentials (implement proper auth)
        if admin_override != "ADMIN_OVERRIDE_KEY":
            logger.warning("Invalid admin override key")
            return False
        
        self.kill_switch_active = False
        self.consecutive_losses = 0
        self.daily_loss = 0.0
        self.system_state = SystemState.NORMAL
        
        logger.info("✅ Kill switch reset by admin")
        await self._send_alert("Kill switch reset by admin", RiskLevel.LOW)
        
        return True
    
    async def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        account_balance: float
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion with safety cap
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            account_balance: Current account balance
            
        Returns:
            Optimal position size
        """
        
        # Check if trading is allowed
        if self.system_state in [SystemState.EMERGENCY, SystemState.SHUTDOWN]:
            return 0.0
        
        # Calculate risk per trade
        risk_per_trade = abs(entry_price - stop_loss) / entry_price
        
        # Get win rate and average win/loss from history
        win_rate, avg_win, avg_loss = await self._get_trade_statistics(symbol)
        
        # Kelly Criterion
        if avg_loss > 0:
            kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        else:
            kelly_fraction = 0.1  # Default conservative size
        
        # Cap Kelly at 25% (safety)
        kelly_fraction = min(kelly_fraction, 0.25)
        
        # Further reduce based on system state
        if self.system_state == SystemState.RESTRICTED:
            kelly_fraction *= 0.5
        elif self.system_state == SystemState.CAUTION:
            kelly_fraction *= 0.75
        
        # Calculate position size
        max_risk_amount = account_balance * kelly_fraction
        position_size = max_risk_amount / risk_per_trade
        
        # Apply maximum position size limit
        max_position = account_balance * (self.limits.max_position_size / 100)
        position_size = min(position_size, max_position)
        
        return position_size
    
    async def check_slippage(
        self,
        expected_price: float,
        actual_price: float,
        side: str
    ) -> bool:
        """
        Check if slippage is within acceptable limits
        
        Args:
            expected_price: Expected execution price
            actual_price: Actual execution price
            side: 'buy' or 'sell'
            
        Returns:
            bool: Whether slippage is acceptable
        """
        
        # Calculate slippage
        if side == 'buy':
            slippage = (actual_price - expected_price) / expected_price * 100
        else:
            slippage = (expected_price - actual_price) / expected_price * 100
        
        # Check against limit
        if abs(slippage) > self.limits.max_slippage:
            logger.warning(f"⚠️ Excessive slippage: {slippage:.2f}%")
            await self._send_alert(f"Excessive slippage: {slippage:.2f}%", RiskLevel.HIGH)
            return False
        
        return True
    
    async def check_liquidity(self, symbol: str, volume: float) -> bool:
        """
        Check if there's sufficient liquidity for trading
        
        Args:
            symbol: Trading symbol
            volume: Desired trade volume
            
        Returns:
            bool: Whether liquidity is sufficient
        """
        
        # Get market depth
        market_depth = await self._get_market_depth(symbol)
        
        if not market_depth:
            return False
        
        # Check if volume can be absorbed
        available_liquidity = market_depth.get('total_volume', 0)
        
        if volume > available_liquidity * 0.1:  # Don't take more than 10% of available liquidity
            logger.warning(f"⚠️ Insufficient liquidity for {symbol}")
            return False
        
        return True
    
    async def update_trade_result(self, symbol: str, pnl: float):
        """Update trade history and risk counters"""
        
        # Update consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Update daily P&L
        self.daily_loss += pnl
        
        # Store trade
        self.trade_history.append({
            'symbol': symbol,
            'pnl': pnl,
            'timestamp': datetime.now()
        })
        
        # Check if we need to trigger risk controls
        metrics = await self.calculate_risk_metrics()
        await self.check_risk_limits(metrics)
    
    def _calculate_risk_score(self, metrics: RiskMetrics) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0.0
        
        # Drawdown contribution (0-30)
        dd_score = min(30, abs(metrics.current_drawdown) / abs(self.limits.max_drawdown) * 30)
        score += dd_score
        
        # VaR contribution (0-20)
        var_score = min(20, abs(metrics.var_95) / abs(self.limits.max_var_95) * 20)
        score += var_score
        
        # Leverage contribution (0-20)
        lev_score = min(20, metrics.leverage / self.limits.max_leverage * 20)
        score += lev_score
        
        # Liquidity contribution (0-15)
        liq_score = max(0, 15 * (1 - metrics.liquidity_score / self.limits.min_liquidity_ratio))
        score += liq_score
        
        # Sharpe contribution (0-15)
        if metrics.sharpe_ratio < self.limits.min_sharpe:
            sharpe_score = 15 * (1 - metrics.sharpe_ratio / self.limits.min_sharpe)
            score += sharpe_score
        
        return min(100, score)
    
    async def _calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        # Implement based on actual positions
        # This is a placeholder
        return 100000.0
    
    async def _get_recent_returns(self) -> np.ndarray:
        """Get recent portfolio returns"""
        # Implement based on actual trade history
        # This is a placeholder
        return np.random.normal(0.001, 0.02, 100)
    
    def _calculate_sharpe(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0.0
        return np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    def _calculate_sortino(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        if len(returns) == 0:
            return 0.0
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0.0
        downside_std = np.std(downside_returns)
        return np.mean(returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0
    
    async def _calculate_leverage(self) -> float:
        """Calculate current leverage"""
        # Implement based on actual positions
        return 1.0
    
    async def _calculate_concentration_risk(self) -> float:
        """Calculate portfolio concentration risk"""
        # Implement based on actual positions
        return 0.2
    
    async def _calculate_liquidity_score(self) -> float:
        """Calculate portfolio liquidity score"""
        # Implement based on actual positions
        return 0.5
    
    async def _calculate_correlation_risk(self) -> float:
        """Calculate correlation risk between positions"""
        # Implement based on actual positions
        return 0.3
    
    async def _get_trade_statistics(self, symbol: str) -> Tuple[float, float, float]:
        """Get trade statistics for position sizing"""
        # Implement based on actual trade history
        return 0.55, 0.02, 0.01  # win_rate, avg_win, avg_loss
    
    async def _get_market_depth(self, symbol: str) -> Dict:
        """Get market depth for liquidity check"""
        # Implement based on actual market data
        return {'total_volume': 1000000}
    
    async def close_all_positions(self):
        """Emergency close all positions"""
        logger.critical("🚨 CLOSING ALL POSITIONS")
        # Implement actual position closing
        pass
    
    async def cancel_all_orders(self):
        """Cancel all pending orders"""
        logger.critical("🚨 CANCELLING ALL ORDERS")
        # Implement actual order cancellation
        pass
    
    async def _send_alert(self, message: str, level: RiskLevel):
        """Send risk alert"""
        alert = {
            'message': message,
            'level': level.name,
            'timestamp': datetime.now(),
            'system_state': self.system_state.value
        }
        
        # Execute callbacks
        for callback in self.alert_callbacks:
            await callback(alert)
        
        # Store alert
        if self.db:
            await self.db.risk_alerts.insert_one(alert)
    
    async def _store_metrics(self, metrics: RiskMetrics):
        """Store risk metrics in MongoDB"""
        if self.db:
            await self.db.risk_metrics.insert_one(metrics.to_dict())
    
    async def _store_kill_switch_event(self, reason: str):
        """Store kill switch event"""
        if self.db:
            await self.db.kill_switch_events.insert_one({
                'reason': reason,
                'timestamp': datetime.now(),
                'metrics': self.current_metrics.to_dict() if self.current_metrics else None
            })
    
    async def _load_state(self):
        """Load saved state from MongoDB"""
        if self.db:
            # Load latest metrics
            latest = await self.db.risk_metrics.find_one(sort=[('timestamp', -1)])
            if latest:
                self.high_water_mark = latest.get('high_water_mark', 100000)

# Export the risk manager
risk_manager = AdvancedRiskManager()