"""
Business Data Layer for AuraQuant Trading System
Engineer's Note: This adds comprehensive business logic and data management
to your existing system WITHOUT modifying existing code
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import json
from dataclasses import dataclass, asdict
from enum import Enum
from dotenv import load_dotenv

# Load environment
load_dotenv()

class OrderType(Enum):
    """Trading order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class OrderStatus(Enum):
    """Order status states"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PositionSide(Enum):
    """Position sides"""
    LONG = "long"
    SHORT = "short"

@dataclass
class TradingOrder:
    """Trading order data structure"""
    order_id: str
    symbol: str
    side: str  # buy/sell
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    timestamp: datetime
    status: OrderStatus
    filled_quantity: float = 0
    average_fill_price: float = 0
    commission: float = 0
    notes: str = ""

@dataclass
class Position:
    """Trading position data structure"""
    position_id: str
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: datetime
    closed_at: Optional[datetime] = None
    pnl: float = 0
    pnl_percentage: float = 0

@dataclass
class Portfolio:
    """Portfolio data structure"""
    portfolio_id: str
    user_id: str
    total_value: float
    cash_balance: float
    positions_value: float
    total_pnl: float
    daily_pnl: float
    positions: List[Position]
    pending_orders: List[TradingOrder]
    risk_metrics: Dict[str, float]
    last_updated: datetime

class BusinessDataManager:
    """
    Manages all business data operations for the trading system
    Integrates with MongoDB for persistence
    """
    
    def __init__(self):
        """Initialize business data manager"""
        # Risk management parameters
        self.max_position_size = float(os.getenv("MAX_POSITION_SIZE", "10000"))
        self.max_portfolio_risk = float(os.getenv("MAX_PORTFOLIO_RISK", "0.02"))  # 2%
        self.max_daily_loss = float(os.getenv("MAX_DAILY_LOSS", "500"))
        self.leverage_limit = float(os.getenv("LEVERAGE_LIMIT", "2.0"))
        
        # Performance tracking
        self.performance_cache = {}
        self.risk_cache = {}
        
        # Get MongoDB service
        self._init_mongodb()
        
        print("📊 Business Data Layer Initialized")
        
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            from brain.mongodb_persistence import get_persistence_service
            self.persistence = get_persistence_service()
            
            if self.persistence and self.persistence.db:
                # Create business collections
                self._setup_collections()
                
        except Exception as e:
            print(f"⚠️ MongoDB not available for business data: {e}")
            self.persistence = None
            
    def _setup_collections(self):
        """Setup business data collections in MongoDB"""
        if not self.persistence or not self.persistence.db:
            return
            
        db = self.persistence.db
        
        # Create indexes for business collections
        collections = {
            'portfolios': [('user_id', 1), ('portfolio_id', 1)],
            'positions': [('symbol', 1), ('status', 1), ('opened_at', -1)],
            'orders': [('symbol', 1), ('status', 1), ('timestamp', -1)],
            'transactions': [('user_id', 1), ('timestamp', -1)],
            'risk_metrics': [('portfolio_id', 1), ('timestamp', -1)],
            'performance': [('portfolio_id', 1), ('date', -1)]
        }
        
        for collection_name, indexes in collections.items():
            collection = db[collection_name]
            for index in indexes:
                try:
                    collection.create_index([index])
                except:
                    pass  # Index might exist
                    
    def create_portfolio(self, user_id: str, initial_balance: float) -> Portfolio:
        """
        Create new portfolio for user
        
        Args:
            user_id: User identifier
            initial_balance: Starting cash balance
            
        Returns:
            Portfolio object
        """
        import uuid
        
        portfolio = Portfolio(
            portfolio_id=str(uuid.uuid4()),
            user_id=user_id,
            total_value=initial_balance,
            cash_balance=initial_balance,
            positions_value=0,
            total_pnl=0,
            daily_pnl=0,
            positions=[],
            pending_orders=[],
            risk_metrics={
                'var_95': 0,  # Value at Risk
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'risk_score': 0
            },
            last_updated=datetime.now()
        )
        
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            self.persistence.db.portfolios.insert_one(asdict(portfolio))
            
        return portfolio
        
    def submit_order(self, portfolio_id: str, symbol: str, side: str, 
                    quantity: float, order_type: OrderType = OrderType.MARKET,
                    price: Optional[float] = None, 
                    stop_price: Optional[float] = None) -> Optional[TradingOrder]:
        """
        Submit trading order with risk validation
        
        Args:
            portfolio_id: Portfolio identifier
            symbol: Trading symbol
            side: Buy or sell
            quantity: Order quantity
            order_type: Type of order
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            
        Returns:
            TradingOrder if successful, None if rejected
        """
        import uuid
        
        # Validate order against risk rules
        if not self._validate_order_risk(portfolio_id, symbol, side, quantity, price):
            print(f"❌ Order rejected: Risk validation failed")
            return None
            
        order = TradingOrder(
            order_id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            timestamp=datetime.now(),
            status=OrderStatus.PENDING
        )
        
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            # Encrypt sensitive order data
            from brain.security_layer import encrypt_data
            encrypted_order = encrypt_data(asdict(order))
            
            self.persistence.db.orders.insert_one({
                'order_id': order.order_id,
                'portfolio_id': portfolio_id,
                'encrypted_data': encrypted_order,
                'timestamp': order.timestamp
            })
            
        # Log for audit
        self._log_business_event('order_submitted', {
            'order_id': order.order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity
        })
        
        return order
        
    def _validate_order_risk(self, portfolio_id: str, symbol: str, 
                           side: str, quantity: float, 
                           price: Optional[float]) -> bool:
        """
        Validate order against risk management rules
        
        Returns:
            True if order passes risk checks
        """
        # Get portfolio
        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            return False
            
        # Calculate order value
        order_value = quantity * (price if price else self._get_current_price(symbol))
        
        # Check position size limit
        if order_value > self.max_position_size:
            print(f"⚠️ Order exceeds max position size: ${order_value:.2f} > ${self.max_position_size:.2f}")
            return False
            
        # Check portfolio risk limit
        portfolio_risk = order_value / portfolio.total_value
        if portfolio_risk > self.max_portfolio_risk:
            print(f"⚠️ Order exceeds portfolio risk limit: {portfolio_risk:.2%} > {self.max_portfolio_risk:.2%}")
            return False
            
        # Check daily loss limit
        if portfolio.daily_pnl < -self.max_daily_loss:
            print(f"⚠️ Daily loss limit reached: ${portfolio.daily_pnl:.2f}")
            return False
            
        # Check leverage
        total_exposure = portfolio.positions_value + order_value
        leverage = total_exposure / portfolio.total_value
        if leverage > self.leverage_limit:
            print(f"⚠️ Leverage limit exceeded: {leverage:.2f}x > {self.leverage_limit:.2f}x")
            return False
            
        return True
        
    def open_position(self, order: TradingOrder, fill_price: float) -> Position:
        """
        Open new position from filled order
        
        Args:
            order: Filled order
            fill_price: Execution price
            
        Returns:
            Position object
        """
        import uuid
        
        position = Position(
            position_id=str(uuid.uuid4()),
            symbol=order.symbol,
            side=PositionSide.LONG if order.side == 'buy' else PositionSide.SHORT,
            quantity=order.quantity,
            entry_price=fill_price,
            current_price=fill_price,
            stop_loss=None,
            take_profit=None,
            opened_at=datetime.now()
        )
        
        # Calculate initial stop loss and take profit
        position.stop_loss = self._calculate_stop_loss(position)
        position.take_profit = self._calculate_take_profit(position)
        
        # Save to MongoDB
        if self.persistence and self.persistence.db:
            from brain.security_layer import encrypt_data
            encrypted_position = encrypt_data(asdict(position))
            
            self.persistence.db.positions.insert_one({
                'position_id': position.position_id,
                'encrypted_data': encrypted_position,
                'opened_at': position.opened_at
            })
            
        return position
        
    def update_position_prices(self, position_id: str, current_price: float):
        """
        Update position with current market price
        
        Args:
            position_id: Position identifier
            current_price: Current market price
        """
        if not self.persistence or not self.persistence.db:
            return
            
        # Get position
        position_doc = self.persistence.db.positions.find_one({'position_id': position_id})
        if not position_doc:
            return
            
        from brain.security_layer import decrypt_data
        position_data = decrypt_data(position_doc['encrypted_data'])
        
        # Update prices and P&L
        position_data['current_price'] = current_price
        
        if position_data['side'] == 'long':
            position_data['pnl'] = (current_price - position_data['entry_price']) * position_data['quantity']
        else:  # short
            position_data['pnl'] = (position_data['entry_price'] - current_price) * position_data['quantity']
            
        position_data['pnl_percentage'] = (position_data['pnl'] / (position_data['entry_price'] * position_data['quantity'])) * 100
        
        # Update in MongoDB
        from brain.security_layer import encrypt_data
        encrypted_update = encrypt_data(position_data)
        
        self.persistence.db.positions.update_one(
            {'position_id': position_id},
            {'$set': {
                'encrypted_data': encrypted_update,
                'last_updated': datetime.now()
            }}
        )
        
    def close_position(self, position_id: str, close_price: float) -> Dict[str, float]:
        """
        Close position and calculate final P&L
        
        Args:
            position_id: Position identifier
            close_price: Closing price
            
        Returns:
            Final P&L details
        """
        if not self.persistence or not self.persistence.db:
            return {}
            
        # Get position
        position_doc = self.persistence.db.positions.find_one({'position_id': position_id})
        if not position_doc:
            return {}
            
        from brain.security_layer import decrypt_data
        position_data = decrypt_data(position_doc['encrypted_data'])
        
        # Calculate final P&L
        if position_data['side'] == 'long':
            pnl = (close_price - position_data['entry_price']) * position_data['quantity']
        else:  # short
            pnl = (position_data['entry_price'] - close_price) * position_data['quantity']
            
        pnl_percentage = (pnl / (position_data['entry_price'] * position_data['quantity'])) * 100
        
        # Update position as closed
        position_data['closed_at'] = datetime.now().isoformat()
        position_data['pnl'] = pnl
        position_data['pnl_percentage'] = pnl_percentage
        position_data['current_price'] = close_price
        
        from brain.security_layer import encrypt_data
        encrypted_update = encrypt_data(position_data)
        
        self.persistence.db.positions.update_one(
            {'position_id': position_id},
            {'$set': {
                'encrypted_data': encrypted_update,
                'status': 'closed',
                'closed_at': datetime.now()
            }}
        )
        
        # Log trade completion
        self._log_business_event('position_closed', {
            'position_id': position_id,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage
        })
        
        return {
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'entry_price': position_data['entry_price'],
            'close_price': close_price,
            'quantity': position_data['quantity']
        }
        
    def calculate_portfolio_metrics(self, portfolio_id: str) -> Dict[str, float]:
        """
        Calculate comprehensive portfolio metrics
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Dictionary of metrics
        """
        if not self.persistence or not self.persistence.db:
            return {}
            
        # Get all positions
        positions = list(self.persistence.db.positions.find({
            'portfolio_id': portfolio_id,
            'status': {'$ne': 'closed'}
        }))
        
        # Calculate metrics
        total_value = 0
        total_pnl = 0
        winning_trades = 0
        losing_trades = 0
        
        for pos_doc in positions:
            from brain.security_layer import decrypt_data
            pos = decrypt_data(pos_doc['encrypted_data'])
            
            total_value += pos['quantity'] * pos['current_price']
            total_pnl += pos['pnl']
            
            if pos['pnl'] > 0:
                winning_trades += 1
            elif pos['pnl'] < 0:
                losing_trades += 1
                
        # Calculate advanced metrics
        total_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        metrics = {
            'total_positions': len(positions),
            'total_value': total_value,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'calculated_at': datetime.now().isoformat()
        }
        
        # Save metrics to MongoDB
        self.persistence.db.performance.insert_one({
            'portfolio_id': portfolio_id,
            'metrics': metrics,
            'timestamp': datetime.now()
        })
        
        return metrics
        
    def get_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """
        Get portfolio by ID
        
        Args:
            portfolio_id: Portfolio identifier
            
        Returns:
            Portfolio object or None
        """
        if not self.persistence or not self.persistence.db:
            return None
            
        portfolio_doc = self.persistence.db.portfolios.find_one({'portfolio_id': portfolio_id})
        
        if portfolio_doc:
            # Convert document to Portfolio object
            portfolio_doc.pop('_id', None)
            return Portfolio(**portfolio_doc)
            
        return None
        
    def _calculate_stop_loss(self, position: Position) -> float:
        """Calculate stop loss for position"""
        # 2% stop loss by default
        if position.side == PositionSide.LONG:
            return position.entry_price * 0.98
        else:  # SHORT
            return position.entry_price * 1.02
            
    def _calculate_take_profit(self, position: Position) -> float:
        """Calculate take profit for position"""
        # 5% take profit by default
        if position.side == PositionSide.LONG:
            return position.entry_price * 1.05
        else:  # SHORT
            return position.entry_price * 0.95
            
    def _get_current_price(self, symbol: str) -> float:
        """Get current market price for symbol"""
        # This would connect to your market data source
        # For now, return a placeholder
        return 100.0
        
    def _log_business_event(self, event_type: str, details: Dict):
        """Log business events for audit"""
        if self.persistence and self.persistence.db:
            self.persistence.db.business_events.insert_one({
                'timestamp': datetime.now(),
                'event_type': event_type,
                'details': details
            })
            
    def get_risk_metrics(self, portfolio_id: str, days: int = 30) -> Dict[str, float]:
        """
        Calculate risk metrics for portfolio
        
        Args:
            portfolio_id: Portfolio identifier
            days: Number of days for calculation
            
        Returns:
            Risk metrics dictionary
        """
        if not self.persistence or not self.persistence.db:
            return {}
            
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get historical data
        performance = list(self.persistence.db.performance.find({
            'portfolio_id': portfolio_id,
            'timestamp': {'$gte': cutoff_date}
        }).sort('timestamp', 1))
        
        if len(performance) < 2:
            return {}
            
        # Calculate daily returns
        returns = []
        for i in range(1, len(performance)):
            prev_value = performance[i-1]['metrics']['total_value']
            curr_value = performance[i]['metrics']['total_value']
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)
                
        if not returns:
            return {}
            
        import statistics
        
        # Calculate metrics
        avg_return = statistics.mean(returns)
        std_dev = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        sharpe_ratio = (avg_return / std_dev * (252 ** 0.5)) if std_dev > 0 else 0
        
        # Value at Risk (95% confidence)
        sorted_returns = sorted(returns)
        var_index = int(len(sorted_returns) * 0.05)
        var_95 = sorted_returns[var_index] if var_index < len(sorted_returns) else 0
        
        # Maximum drawdown
        cumulative = 1
        peak = 1
        max_drawdown = 0
        
        for ret in returns:
            cumulative *= (1 + ret)
            if cumulative > peak:
                peak = cumulative
            drawdown = (peak - cumulative) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                
        risk_metrics = {
            'sharpe_ratio': sharpe_ratio,
            'var_95': var_95,
            'max_drawdown': max_drawdown,
            'volatility': std_dev * (252 ** 0.5),  # Annualized
            'avg_daily_return': avg_return,
            'calculated_at': datetime.now().isoformat()
        }
        
        # Cache and save
        self.risk_cache[portfolio_id] = risk_metrics
        
        if self.persistence and self.persistence.db:
            self.persistence.db.risk_metrics.insert_one({
                'portfolio_id': portfolio_id,
                'metrics': risk_metrics,
                'timestamp': datetime.now()
            })
            
        return risk_metrics

# Global instance
_business_manager = None

def get_business_manager():
    """Get or create business data manager instance"""
    global _business_manager
    if _business_manager is None:
        _business_manager = BusinessDataManager()
    return _business_manager

# Helper functions for easy integration
def create_portfolio(user_id: str, initial_balance: float) -> Portfolio:
    """Create new portfolio"""
    manager = get_business_manager()
    return manager.create_portfolio(user_id, initial_balance)

def submit_order(portfolio_id: str, symbol: str, side: str, quantity: float, **kwargs):
    """Submit trading order"""
    manager = get_business_manager()
    return manager.submit_order(portfolio_id, symbol, side, quantity, **kwargs)

def get_portfolio_metrics(portfolio_id: str) -> Dict[str, float]:
    """Get portfolio metrics"""
    manager = get_business_manager()
    return manager.calculate_portfolio_metrics(portfolio_id)

def get_risk_metrics(portfolio_id: str, days: int = 30) -> Dict[str, float]:
    """Get risk metrics"""
    manager = get_business_manager()
    return manager.get_risk_metrics(portfolio_id, days)