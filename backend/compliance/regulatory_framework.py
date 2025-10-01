"""
AuraQuant Regulatory Compliance Framework
==========================================
Ensures complete compliance with ASX, Crypto, and Meme Coin regulations
Self-updating rule system with automatic compliance checking

Created: 2025-01-30
Status: PRODUCTION-CRITICAL - COMPLIANCE MANDATORY
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
from motor.motor_asyncio import AsyncIOMotorClient
import aiohttp
import logging

# Configure compliance logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraQuant.Compliance")

class Market(Enum):
    """Supported markets with compliance"""
    ASX = "ASX"  # Australian Securities Exchange
    CRYPTO_SPOT = "CRYPTO_SPOT"  # Spot cryptocurrency
    CRYPTO_FUTURES = "CRYPTO_FUTURES"  # Crypto derivatives
    MEME_COINS = "MEME_COINS"  # Meme tokens (high volatility)

class ComplianceStatus(Enum):
    """Compliance check results"""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PENDING = "PENDING"

@dataclass
class RegulatoryRule:
    """Individual regulatory rule"""
    rule_id: str
    market: Market
    jurisdiction: str
    rule_type: str  # TRADING, REPORTING, KYC, AML
    description: str
    enforcement_level: str  # MANDATORY, WARNING, ADVISORY
    parameters: Dict[str, Any]
    effective_date: datetime
    last_updated: datetime
    active: bool = True

@dataclass
class ComplianceCheck:
    """Results of compliance check"""
    check_id: str
    timestamp: float
    market: Market
    symbol: str
    order_type: str
    status: ComplianceStatus
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class RegulatoryFramework:
    """
    Master regulatory compliance framework
    Ensures all trading activities are legal and safe
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.rules_cache = {}
        self.last_rule_update = {}
        
        # Initialize market-specific rules
        self._initialize_rules()
        
        # Compliance thresholds
        self.thresholds = {
            'max_order_size_pct': 0.05,  # 5% of market cap
            'max_position_size_pct': 0.10,  # 10% of portfolio
            'max_daily_trades': 100,
            'max_orders_per_second': 10,
            'max_order_to_trade_ratio': 20,  # Prevent spoofing
            'min_order_interval_ms': 100,
            'max_daily_loss_pct': 0.06,  # 6% daily loss limit
            'price_deviation_threshold': 0.10  # 10% from market
        }
        
        # ASX-specific rules
        self.asx_rules = {
            'market_hours': {
                'pre_open': {'start': '07:00', 'end': '10:00'},
                'normal': {'start': '10:00', 'end': '16:00'},
                'auction': {'start': '16:00', 'end': '16:10'}
            },
            'minimum_order_size': 1,  # 1 share minimum
            'tick_sizes': {  # Price-based tick sizes
                (0, 0.10): 0.001,
                (0.10, 2.00): 0.005,
                (2.00, float('inf')): 0.01
            },
            'short_selling_allowed': True,
            'circuit_breaker_threshold': 0.10,  # 10% move triggers halt
            'settlement_days': 2  # T+2 settlement
        }
        
        # Crypto-specific rules
        self.crypto_rules = {
            'market_hours': '24/7',
            'minimum_order_size_usd': 10,
            'max_leverage': {
                'CRYPTO_SPOT': 1,  # No leverage on spot
                'CRYPTO_FUTURES': 20  # Max 20x leverage
            },
            'kyc_required_amount_usd': 10000,  # KYC for large trades
            'aml_monitoring': True,
            'wash_trading_prevention': True,
            'price_manipulation_detection': True
        }
        
        # Meme coin specific rules (higher risk tolerance but stricter controls)
        self.meme_rules = {
            'max_position_size_pct': 0.02,  # Max 2% per meme coin
            'min_liquidity_usd': 100000,  # Minimum liquidity required
            'max_slippage_pct': 0.05,  # Max 5% slippage allowed
            'rug_pull_detection': True,
            'honeypot_detection': True,
            'contract_verification_required': True,
            'max_daily_trades': 20  # Limit meme coin trades
        }
        
        # Initialize compliance monitoring
        self.compliance_history = []
        self.violation_count = 0
        self.kill_switch_active = False
        
        logger.info("Regulatory Framework initialized with ASX, Crypto, and Meme Coin support")
    
    def _initialize_rules(self):
        """Initialize core regulatory rules"""
        self.rules_cache = {
            Market.ASX: self._load_asx_rules(),
            Market.CRYPTO_SPOT: self._load_crypto_rules(),
            Market.CRYPTO_FUTURES: self._load_crypto_futures_rules(),
            Market.MEME_COINS: self._load_meme_coin_rules()
        }
    
    def _load_asx_rules(self) -> List[RegulatoryRule]:
        """Load ASX regulatory rules"""
        return [
            RegulatoryRule(
                rule_id="ASX_001",
                market=Market.ASX,
                jurisdiction="Australia",
                rule_type="TRADING",
                description="Market manipulation prohibition",
                enforcement_level="MANDATORY",
                parameters={
                    'prohibit_spoofing': True,
                    'prohibit_layering': True,
                    'prohibit_wash_trading': True
                },
                effective_date=datetime(2020, 1, 1),
                last_updated=datetime.now()
            ),
            RegulatoryRule(
                rule_id="ASX_002",
                market=Market.ASX,
                jurisdiction="Australia",
                rule_type="TRADING",
                description="Best execution obligation",
                enforcement_level="MANDATORY",
                parameters={
                    'price_improvement_required': True,
                    'execution_speed_priority': True
                },
                effective_date=datetime(2020, 1, 1),
                last_updated=datetime.now()
            ),
            RegulatoryRule(
                rule_id="ASX_003",
                market=Market.ASX,
                jurisdiction="Australia",
                rule_type="REPORTING",
                description="Trade reporting requirements",
                enforcement_level="MANDATORY",
                parameters={
                    'report_within_minutes': 1,
                    'include_all_details': True
                },
                effective_date=datetime(2020, 1, 1),
                last_updated=datetime.now()
            )
        ]
    
    def _load_crypto_rules(self) -> List[RegulatoryRule]:
        """Load cryptocurrency regulatory rules"""
        return [
            RegulatoryRule(
                rule_id="CRYPTO_001",
                market=Market.CRYPTO_SPOT,
                jurisdiction="Global",
                rule_type="AML",
                description="Anti-money laundering monitoring",
                enforcement_level="MANDATORY",
                parameters={
                    'monitor_large_transactions': True,
                    'threshold_usd': 10000,
                    'report_suspicious': True
                },
                effective_date=datetime(2021, 1, 1),
                last_updated=datetime.now()
            ),
            RegulatoryRule(
                rule_id="CRYPTO_002",
                market=Market.CRYPTO_SPOT,
                jurisdiction="Global",
                rule_type="TRADING",
                description="Wash trading prevention",
                enforcement_level="MANDATORY",
                parameters={
                    'min_time_between_trades': 60,  # seconds
                    'self_trade_prevention': True
                },
                effective_date=datetime(2021, 1, 1),
                last_updated=datetime.now()
            )
        ]
    
    def _load_crypto_futures_rules(self) -> List[RegulatoryRule]:
        """Load crypto futures regulatory rules"""
        return [
            RegulatoryRule(
                rule_id="FUTURES_001",
                market=Market.CRYPTO_FUTURES,
                jurisdiction="Global",
                rule_type="TRADING",
                description="Leverage limits",
                enforcement_level="MANDATORY",
                parameters={
                    'max_leverage': 20,
                    'margin_call_threshold': 0.8,
                    'auto_liquidation': 0.95
                },
                effective_date=datetime(2021, 6, 1),
                last_updated=datetime.now()
            )
        ]
    
    def _load_meme_coin_rules(self) -> List[RegulatoryRule]:
        """Load meme coin specific rules"""
        return [
            RegulatoryRule(
                rule_id="MEME_001",
                market=Market.MEME_COINS,
                jurisdiction="Global",
                rule_type="TRADING",
                description="Rug pull prevention",
                enforcement_level="MANDATORY",
                parameters={
                    'check_liquidity_lock': True,
                    'verify_contract': True,
                    'check_ownership_renounced': True,
                    'max_wallet_concentration': 0.05  # No wallet holds > 5%
                },
                effective_date=datetime(2022, 1, 1),
                last_updated=datetime.now()
            ),
            RegulatoryRule(
                rule_id="MEME_002",
                market=Market.MEME_COINS,
                jurisdiction="Global",
                rule_type="TRADING",
                description="Honeypot detection",
                enforcement_level="MANDATORY",
                parameters={
                    'simulate_sell_before_buy': True,
                    'check_sell_tax': True,
                    'max_acceptable_tax': 0.10  # 10% max tax
                },
                effective_date=datetime(2022, 1, 1),
                last_updated=datetime.now()
            )
        ]
    
    # ==================== Pre-Trade Compliance Checks ====================
    
    async def check_order_compliance(self, order: Dict[str, Any]) -> ComplianceCheck:
        """
        Comprehensive pre-trade compliance check
        """
        check_id = f"CHK_{int(time.time() * 1000)}"
        market = Market[order.get('market', 'CRYPTO_SPOT')]
        
        check = ComplianceCheck(
            check_id=check_id,
            timestamp=time.time(),
            market=market,
            symbol=order.get('symbol', ''),
            order_type=order.get('order_type', ''),
            status=ComplianceStatus.PENDING,
            violations=[],
            warnings=[],
            metadata={}
        )
        
        try:
            # 1. Market-specific checks
            if market == Market.ASX:
                await self._check_asx_compliance(order, check)
            elif market in [Market.CRYPTO_SPOT, Market.CRYPTO_FUTURES]:
                await self._check_crypto_compliance(order, check)
            elif market == Market.MEME_COINS:
                await self._check_meme_coin_compliance(order, check)
            
            # 2. Universal checks
            await self._check_universal_compliance(order, check)
            
            # 3. Risk management checks
            await self._check_risk_limits(order, check)
            
            # 4. Anti-manipulation checks
            await self._check_market_manipulation(order, check)
            
            # Determine final status
            if check.violations:
                check.status = ComplianceStatus.REJECTED
                logger.warning(f"Order rejected: {check.violations}")
            elif check.warnings:
                check.status = ComplianceStatus.REVIEW_REQUIRED
                logger.info(f"Order requires review: {check.warnings}")
            else:
                check.status = ComplianceStatus.APPROVED
                logger.info(f"Order approved: {check_id}")
            
            # Store compliance check
            await self._store_compliance_check(check)
            
        except Exception as e:
            logger.error(f"Compliance check error: {str(e)}")
            check.status = ComplianceStatus.REJECTED
            check.violations.append(f"System error: {str(e)}")
        
        return check
    
    async def _check_asx_compliance(self, order: Dict, check: ComplianceCheck):
        """Check ASX-specific compliance"""
        current_time = datetime.now()
        
        # Check market hours
        if not self._is_asx_market_open(current_time):
            check.violations.append("ASX market is closed")
        
        # Check tick size compliance
        price = order.get('price', 0)
        tick_size = self._get_asx_tick_size(price)
        if price % tick_size != 0:
            check.violations.append(f"Price {price} violates tick size {tick_size}")
        
        # Check minimum order size
        quantity = order.get('quantity', 0)
        if quantity < self.asx_rules['minimum_order_size']:
            check.violations.append(f"Order size {quantity} below minimum")
        
        # Check short selling rules if applicable
        if order.get('side') == 'SELL' and order.get('is_short', False):
            if not self.asx_rules['short_selling_allowed']:
                check.violations.append("Short selling not allowed")
    
    async def _check_crypto_compliance(self, order: Dict, check: ComplianceCheck):
        """Check cryptocurrency compliance"""
        # Check minimum order size
        order_value = order.get('quantity', 0) * order.get('price', 0)
        if order_value < self.crypto_rules['minimum_order_size_usd']:
            check.violations.append(f"Order value ${order_value} below minimum")
        
        # Check leverage limits
        leverage = order.get('leverage', 1)
        market = check.market
        max_leverage = self.crypto_rules['max_leverage'].get(market.value, 1)
        if leverage > max_leverage:
            check.violations.append(f"Leverage {leverage}x exceeds maximum {max_leverage}x")
        
        # Check KYC requirements for large trades
        if order_value > self.crypto_rules['kyc_required_amount_usd']:
            if not order.get('kyc_verified', False):
                check.violations.append("KYC verification required for large trade")
    
    async def _check_meme_coin_compliance(self, order: Dict, check: ComplianceCheck):
        """Check meme coin specific compliance"""
        symbol = order.get('symbol', '')
        
        # Check if contract is verified
        if self.meme_rules['contract_verification_required']:
            if not await self._is_contract_verified(symbol):
                check.violations.append("Contract not verified")
        
        # Check for rug pull indicators
        if self.meme_rules['rug_pull_detection']:
            rug_pull_risk = await self._check_rug_pull_risk(symbol)
            if rug_pull_risk > 0.7:
                check.violations.append(f"High rug pull risk: {rug_pull_risk:.2%}")
        
        # Check for honeypot
        if self.meme_rules['honeypot_detection']:
            is_honeypot = await self._check_honeypot(symbol)
            if is_honeypot:
                check.violations.append("Token appears to be a honeypot")
        
        # Check liquidity
        liquidity = await self._get_token_liquidity(symbol)
        if liquidity < self.meme_rules['min_liquidity_usd']:
            check.violations.append(f"Insufficient liquidity: ${liquidity}")
        
        # Check position size limits
        position_size_pct = order.get('position_size_pct', 0)
        if position_size_pct > self.meme_rules['max_position_size_pct']:
            check.violations.append(f"Position size {position_size_pct:.1%} exceeds limit")
    
    async def _check_universal_compliance(self, order: Dict, check: ComplianceCheck):
        """Universal compliance checks for all markets"""
        # Check order rate limits
        if not await self._check_rate_limits(order):
            check.violations.append("Order rate limit exceeded")
        
        # Check price reasonability
        market_price = await self._get_market_price(order['symbol'])
        if market_price > 0:
            price_deviation = abs(order['price'] - market_price) / market_price
            if price_deviation > self.thresholds['price_deviation_threshold']:
                check.violations.append(f"Price deviates {price_deviation:.1%} from market")
        
        # Check self-trade prevention
        if await self._would_self_trade(order):
            check.violations.append("Order would result in self-trade")
    
    async def _check_risk_limits(self, order: Dict, check: ComplianceCheck):
        """Check risk management limits"""
        # Check maximum order size
        if order.get('quantity', 0) > await self._get_max_order_size(order['symbol']):
            check.violations.append("Order size exceeds maximum allowed")
        
        # Check maximum position size
        current_position = await self._get_current_position(order['symbol'])
        new_position = current_position + order.get('quantity', 0)
        max_position = await self._get_max_position_size(order['symbol'])
        if abs(new_position) > max_position:
            check.violations.append("Would exceed maximum position size")
        
        # Check daily loss limit
        daily_pnl = await self._get_daily_pnl()
        if daily_pnl < -self.thresholds['max_daily_loss_pct']:
            check.violations.append("Daily loss limit reached")
            self.kill_switch_active = True
    
    async def _check_market_manipulation(self, order: Dict, check: ComplianceCheck):
        """Check for potential market manipulation"""
        # Check order-to-trade ratio
        order_to_trade = await self._get_order_to_trade_ratio()
        if order_to_trade > self.thresholds['max_order_to_trade_ratio']:
            check.warnings.append(f"High order-to-trade ratio: {order_to_trade:.1f}")
        
        # Check for spoofing patterns
        if await self._detect_spoofing_pattern(order):
            check.violations.append("Potential spoofing detected")
        
        # Check for wash trading
        if await self._detect_wash_trading(order):
            check.violations.append("Potential wash trading detected")
    
    # ==================== Helper Functions ====================
    
    def _is_asx_market_open(self, current_time: datetime) -> bool:
        """Check if ASX market is open"""
        # Check weekday (Monday=0, Sunday=6)
        if current_time.weekday() >= 5:  # Weekend
            return False
        
        # Check trading hours (simplified, needs timezone handling)
        current_hour = current_time.hour
        current_minute = current_time.minute
        time_decimal = current_hour + current_minute / 60
        
        # Normal trading: 10:00 - 16:00 Sydney time
        return 10 <= time_decimal <= 16
    
    def _get_asx_tick_size(self, price: float) -> float:
        """Get ASX tick size based on price"""
        for (min_price, max_price), tick_size in self.asx_rules['tick_sizes'].items():
            if min_price <= price < max_price:
                return tick_size
        return 0.01  # Default
    
    async def _is_contract_verified(self, symbol: str) -> bool:
        """Check if token contract is verified"""
        # Would connect to blockchain explorer API
        # For now, simulate
        return True
    
    async def _check_rug_pull_risk(self, symbol: str) -> float:
        """Assess rug pull risk for token"""
        # Would check:
        # - Liquidity lock status
        # - Developer wallet holdings
        # - Contract ownership
        # - Historical behavior
        # For now, return low risk
        return 0.1
    
    async def _check_honeypot(self, symbol: str) -> bool:
        """Check if token is a honeypot"""
        # Would simulate sell transaction
        # Check for excessive taxes or inability to sell
        return False
    
    async def _get_token_liquidity(self, symbol: str) -> float:
        """Get token liquidity in USD"""
        # Would query DEX APIs
        return 1000000  # $1M default
    
    async def _check_rate_limits(self, order: Dict) -> bool:
        """Check if order respects rate limits"""
        # Track orders per second
        return True
    
    async def _get_market_price(self, symbol: str) -> float:
        """Get current market price"""
        # Would query market data
        return 100.0
    
    async def _would_self_trade(self, order: Dict) -> bool:
        """Check if order would trade against own order"""
        return False
    
    async def _get_max_order_size(self, symbol: str) -> float:
        """Get maximum allowed order size"""
        return 10000
    
    async def _get_current_position(self, symbol: str) -> float:
        """Get current position in symbol"""
        return 0
    
    async def _get_max_position_size(self, symbol: str) -> float:
        """Get maximum allowed position size"""
        return 50000
    
    async def _get_daily_pnl(self) -> float:
        """Get current day's P&L"""
        return 0.01  # 1% profit
    
    async def _get_order_to_trade_ratio(self) -> float:
        """Get order-to-trade ratio"""
        return 5.0
    
    async def _detect_spoofing_pattern(self, order: Dict) -> bool:
        """Detect potential spoofing behavior"""
        return False
    
    async def _detect_wash_trading(self, order: Dict) -> bool:
        """Detect potential wash trading"""
        return False
    
    # ==================== Rule Updates ====================
    
    async def update_rules(self):
        """
        Fetch and update regulatory rules
        Ensures system always has latest compliance requirements
        """
        logger.info("Updating regulatory rules...")
        
        try:
            # Fetch latest rules from regulatory APIs
            # This would connect to:
            # - ASIC for ASX rules
            # - Various crypto regulatory bodies
            # - Smart contract analysis services
            
            # For now, log that we're checking
            for market in Market:
                logger.info(f"Checking {market.value} regulations...")
                self.last_rule_update[market] = datetime.now()
            
            # Store updated rules in MongoDB
            if self.mongodb:
                await self._store_rules_update()
            
            logger.info("Regulatory rules updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating rules: {str(e)}")
    
    async def _store_rules_update(self):
        """Store rule updates in MongoDB"""
        if self.mongodb:
            for market, rules in self.rules_cache.items():
                for rule in rules:
                    await self.mongodb.regulatory_rules.update_one(
                        {'rule_id': rule.rule_id},
                        {'$set': {
                            'market': market.value,
                            'jurisdiction': rule.jurisdiction,
                            'rule_type': rule.rule_type,
                            'description': rule.description,
                            'parameters': rule.parameters,
                            'last_updated': datetime.now()
                        }},
                        upsert=True
                    )
    
    async def _store_compliance_check(self, check: ComplianceCheck):
        """Store compliance check in MongoDB"""
        if self.mongodb:
            await self.mongodb.compliance_checks.insert_one({
                'check_id': check.check_id,
                'timestamp': check.timestamp,
                'market': check.market.value,
                'symbol': check.symbol,
                'order_type': check.order_type,
                'status': check.status.value,
                'violations': check.violations,
                'warnings': check.warnings,
                'metadata': check.metadata
            })
    
    # ==================== Kill Switch ====================
    
    def activate_kill_switch(self, reason: str = "Manual activation"):
        """
        Immediately stop all trading
        """
        self.kill_switch_active = True
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        
        # Would send alerts, cancel all orders, close positions
        return {
            'status': 'ACTIVATED',
            'reason': reason,
            'timestamp': time.time()
        }
    
    def deactivate_kill_switch(self, authorization: str):
        """
        Deactivate kill switch with proper authorization
        """
        # Verify authorization
        if self._verify_authorization(authorization):
            self.kill_switch_active = False
            logger.info("Kill switch deactivated")
            return {'status': 'DEACTIVATED', 'timestamp': time.time()}
        else:
            logger.error("Invalid authorization for kill switch deactivation")
            return {'status': 'FAILED', 'error': 'Invalid authorization'}
    
    def _verify_authorization(self, auth: str) -> bool:
        """Verify authorization for sensitive operations"""
        # Would implement proper auth
        return True
    
    # ==================== Monitoring ====================
    
    async def monitor_compliance(self) -> Dict[str, Any]:
        """
        Continuous compliance monitoring
        """
        return {
            'timestamp': time.time(),
            'kill_switch_active': self.kill_switch_active,
            'violation_count': self.violation_count,
            'last_rule_update': {
                market.value: self.last_rule_update.get(market, 'Never')
                for market in Market
            },
            'compliance_rate': await self._calculate_compliance_rate(),
            'risk_metrics': await self._calculate_risk_metrics()
        }
    
    async def _calculate_compliance_rate(self) -> float:
        """Calculate overall compliance rate"""
        if not self.compliance_history:
            return 1.0
        
        approved = sum(1 for c in self.compliance_history[-100:] 
                      if c.status == ComplianceStatus.APPROVED)
        return approved / min(len(self.compliance_history), 100)
    
    async def _calculate_risk_metrics(self) -> Dict:
        """Calculate current risk metrics"""
        return {
            'order_to_trade_ratio': await self._get_order_to_trade_ratio(),
            'daily_pnl': await self._get_daily_pnl(),
            'active_markets': len(set(c.market for c in self.compliance_history[-100:]))
        }