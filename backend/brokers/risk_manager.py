"""
Risk Management Module for AuraQuant
Ensures safe trading practices and protects capital
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RiskManager:
    """Comprehensive risk management for trading operations"""
    
    def __init__(self):
        # Risk limits (configurable)
        self.max_position_size_pct = 0.10  # Max 10% of portfolio per position
        self.max_daily_loss_pct = 0.02  # Max 2% daily loss
        self.max_trades_per_day = 50  # Maximum trades per day
        self.min_account_balance = 500  # Minimum $500 AUD for paper trading
        self.max_leverage = 2.0  # Maximum leverage allowed
        self.currency = 'AUD'  # Australian Dollars
        
        # Tracking
        self.daily_trades = 0
        self.daily_pnl = 0
        self.last_reset = datetime.now().date()
        self.consecutive_losses = 0
        self.is_locked = False
        
    def check_pre_trade(self, 
                       action: str,
                       symbol: str,
                       quantity: int,
                       price: float,
                       account_balance: float,
                       buying_power: float,
                       existing_positions: Dict) -> Dict:
        """
        Pre-trade risk checks
        Returns: {'allowed': bool, 'reason': str, 'warnings': list}
        """
        result = {
            'allowed': True,
            'reason': None,
            'warnings': []
        }
        
        # Reset daily counters if new day
        self._reset_daily_counters()
        
        # Check 1: Account locked due to risk
        if self.is_locked:
            result['allowed'] = False
            result['reason'] = "Trading locked due to risk limits exceeded"
            return result
        
        # Check 2: Minimum account balance
        if account_balance < self.min_account_balance:
            result['allowed'] = False
            result['reason'] = f"Account balance ${account_balance:.2f} below minimum ${self.min_account_balance}"
            logger.error(f"❌ RISK: Insufficient balance - ${account_balance:.2f}")
            return result
        
        # Check 3: Zero balance protection
        if account_balance <= 0:
            result['allowed'] = False
            result['reason'] = "Cannot trade with zero or negative balance"
            logger.error("❌ RISK: Zero balance - trading disabled")
            return result
        
        # Check 4: Position size limit
        position_value = quantity * price
        max_position_value = account_balance * self.max_position_size_pct
        
        if position_value > max_position_value:
            result['allowed'] = False
            result['reason'] = f"Position size ${position_value:.2f} exceeds limit ${max_position_value:.2f}"
            logger.error(f"❌ RISK: Position too large - {position_value/account_balance:.1%} of account")
            return result
        
        # Check 5: Daily trade limit
        if self.daily_trades >= self.max_trades_per_day:
            result['allowed'] = False
            result['reason'] = f"Daily trade limit ({self.max_trades_per_day}) reached"
            return result
        
        # Check 6: Daily loss limit
        max_daily_loss = account_balance * self.max_daily_loss_pct
        if self.daily_pnl < -max_daily_loss:
            result['allowed'] = False
            result['reason'] = f"Daily loss limit reached: ${self.daily_pnl:.2f}"
            self.is_locked = True  # Lock trading for the day
            logger.error(f"❌ RISK: Daily loss limit hit - trading locked")
            return result
        
        # Check 7: Leverage check
        if action == 'BUY' and buying_power > 0:
            leverage = position_value / buying_power
            if leverage > self.max_leverage:
                result['allowed'] = False
                result['reason'] = f"Leverage {leverage:.1f}x exceeds limit {self.max_leverage}x"
                return result
        
        # Check 8: Consecutive losses (warning only)
        if self.consecutive_losses >= 3:
            result['warnings'].append(f"⚠️ {self.consecutive_losses} consecutive losses - consider pausing")
        
        # Check 9: Concentration risk
        if symbol in existing_positions:
            existing_value = existing_positions[symbol].get('market_value', 0)
            total_exposure = existing_value + position_value
            concentration = total_exposure / account_balance
            
            if concentration > 0.2:  # More than 20% in one symbol
                result['warnings'].append(f"⚠️ High concentration in {symbol}: {concentration:.1%}")
                if concentration > 0.3:  # Hard limit at 30%
                    result['allowed'] = False
                    result['reason'] = f"Position concentration too high: {concentration:.1%}"
                    return result
        
        # Check 10: Market hours (warning)
        current_hour = datetime.now().hour
        if current_hour < 9 or current_hour > 16:
            result['warnings'].append("⚠️ Trading outside market hours")
        
        # Log successful pre-trade check
        if result['allowed']:
            logger.info(f"✅ RISK: Pre-trade checks passed for {action} {quantity} {symbol}")
            if result['warnings']:
                for warning in result['warnings']:
                    logger.warning(warning)
        
        return result
    
    def update_post_trade(self, 
                         trade_result: Dict,
                         pnl: float = 0):
        """Update risk metrics after trade execution"""
        self.daily_trades += 1
        self.daily_pnl += pnl
        
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        logger.info(f"📊 RISK: Daily trades: {self.daily_trades}, Daily P&L: ${self.daily_pnl:.2f}")
    
    def _reset_daily_counters(self):
        """Reset daily counters at start of new trading day"""
        current_date = datetime.now().date()
        if current_date > self.last_reset:
            self.daily_trades = 0
            self.daily_pnl = 0
            self.is_locked = False
            self.last_reset = current_date
            logger.info("🔄 RISK: Daily counters reset")
    
    def get_risk_status(self) -> Dict:
        """Get current risk management status"""
        return {
            'is_locked': self.is_locked,
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'consecutive_losses': self.consecutive_losses,
            'max_position_size_pct': self.max_position_size_pct,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'max_trades_per_day': self.max_trades_per_day,
            'min_account_balance': self.min_account_balance,
            'last_reset': self.last_reset.isoformat()
        }
    
    def emergency_stop(self):
        """Emergency stop - lock all trading"""
        self.is_locked = True
        logger.error("🚨 RISK: EMERGENCY STOP ACTIVATED - All trading locked")
    
    def unlock_trading(self, override_code: str = None):
        """Unlock trading (requires override code in production)"""
        if override_code == "UNLOCK_RISK_2025":  # In production, use secure method
            self.is_locked = False
            self.consecutive_losses = 0
            logger.warning("🔓 RISK: Trading unlocked by manual override")
            return True
        return False

# Global risk manager instance
risk_manager = RiskManager()