"""
IBKR Integration Module for AuraQuant
Handles all Interactive Brokers connectivity and operations
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from ib_insync import *
import pandas as pd
from collections import defaultdict
import logging
from .risk_manager import risk_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBKRBroker:
    """Interactive Brokers integration for AuraQuant"""
    
    def __init__(self, 
                 host: str = "127.0.0.1",
                 port: int = 4002,  # Default to paper trading
                 client_id: int = 1):
        """Initialize IBKR broker connection"""
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = IB()
        self.connected = False
        self.account_info = {}
        self.positions = []
        self.orders = []
        self.market_data_streams = {}
        self.callbacks = defaultdict(list)
        
    async def connect(self) -> bool:
        """Connect to IBKR Gateway/TWS"""
        try:
            # Connect to IB Gateway
            await self.ib.connectAsync(self.host, self.port, self.client_id)
            self.connected = True
            
            # Set up event handlers
            self._setup_event_handlers()
            
            # Get initial account info
            await self.refresh_account_info()
            
            logger.info(f"✅ Connected to IBKR at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to IBKR: {e}")
            self.connected = False
            return False
    
    def _setup_event_handlers(self):
        """Set up IBKR event handlers"""
        self.ib.orderStatusEvent += self._on_order_status
        self.ib.execDetailsEvent += self._on_exec_details
        self.ib.errorEvent += self._on_error
        self.ib.positionEvent += self._on_position
        
    def _on_order_status(self, trade):
        """Handle order status updates"""
        logger.info(f"Order status: {trade.order.orderId} - {trade.orderStatus.status}")
        # Trigger callbacks
        for callback in self.callbacks['order_status']:
            asyncio.create_task(callback(trade))
    
    def _on_exec_details(self, trade, fill):
        """Handle execution details"""
        logger.info(f"Execution: {fill.contract.symbol} - {fill.execution.side} {fill.execution.shares} @ {fill.execution.price}")
        # Trigger callbacks
        for callback in self.callbacks['execution']:
            asyncio.create_task(callback(trade, fill))
    
    def _on_error(self, reqId, errorCode, errorString, contract):
        """Handle errors"""
        if errorCode > 2000:  # Warnings
            logger.warning(f"Warning {errorCode}: {errorString}")
        else:
            logger.error(f"Error {errorCode}: {errorString}")
    
    def _on_position(self, position):
        """Handle position updates"""
        logger.info(f"Position update: {position.contract.symbol} - {position.position} @ {position.avgCost}")
        # Trigger callbacks
        for callback in self.callbacks['position']:
            asyncio.create_task(callback(position))
    
    async def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            logger.info("Disconnected from IBKR")
    
    async def refresh_account_info(self) -> Dict:
        """Get account information"""
        if not self.connected:
            return {}
        
        try:
            # Get account summary
            account_summary = self.ib.accountSummary()
            self.account_info = {
                item.tag: item.value 
                for item in account_summary
            }
            
            # Get positions
            self.positions = self.ib.positions()
            
            # Get open orders
            self.orders = self.ib.openOrders()
            
            return self.account_info
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {}
    
    async def get_account_balance(self) -> Dict:
        """Get account balance information"""
        await self.refresh_account_info()
        
        return {
            'total_cash': float(self.account_info.get('TotalCashValue', 0)),
            'net_liquidation': float(self.account_info.get('NetLiquidation', 0)),
            'buying_power': float(self.account_info.get('BuyingPower', 0)),
            'available_funds': float(self.account_info.get('AvailableFunds', 0)),
            'maintenance_margin': float(self.account_info.get('MaintMarginReq', 0)),
            'cushion': float(self.account_info.get('Cushion', 0))
        }
    
    async def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.connected:
            return []
        
        positions = self.ib.positions()
        return [
            {
                'symbol': pos.contract.symbol,
                'quantity': pos.position,
                'avg_cost': pos.avgCost,
                'market_value': pos.position * pos.avgCost,  # Will be updated with market price
                'unrealized_pnl': 0,  # Will be calculated
                'exchange': pos.contract.exchange
            }
            for pos in positions
        ]
    
    async def place_order(self, 
                          symbol: str,
                          action: str,  # BUY or SELL
                          quantity: int,
                          order_type: str = 'MARKET',
                          limit_price: float = None,
                          stop_price: float = None) -> Dict:
        """Place an order with safety checks"""
        if not self.connected:
            return {'error': 'Not connected to IBKR'}
        
        # RISK MANAGEMENT: Comprehensive pre-trade checks
        # Get current positions for concentration check
        positions = await self.get_positions()
        positions_dict = {pos['symbol']: pos for pos in positions}
        
        # Get account balance for risk checks
        balance_info = await self.get_account_balance()
        account_balance = balance_info.get('net_liquidation', 0)
        buying_power = balance_info.get('buying_power', 0)
        
        # Estimate price for risk check
        if limit_price:
            estimated_price = limit_price
        else:
            market_data = await self.get_market_data(symbol)
            estimated_price = market_data.get('ask') if action.upper() == 'BUY' else market_data.get('bid', 0)
            if not estimated_price:
                estimated_price = market_data.get('last', 0)
        
        # Run risk management checks
        risk_check = risk_manager.check_pre_trade(
            action=action,
            symbol=symbol,
            quantity=quantity,
            price=estimated_price,
            account_balance=account_balance,
            buying_power=buying_power,
            existing_positions=positions_dict
        )
        
        # If risk check fails, return error
        if not risk_check['allowed']:
            logger.error(f"❌ Risk check failed: {risk_check['reason']}")
            return {'error': f"Risk Management: {risk_check['reason']}"}
        
        # Log any warnings
        for warning in risk_check.get('warnings', []):
            logger.warning(warning)
        
        # Additional SAFETY CHECK for BUY orders
        if action.upper() == 'BUY':
            balance = await self.get_account_balance()
            available_funds = balance.get('available_funds', 0)
            buying_power = balance.get('buying_power', 0)
            
            # Estimate required funds (use limit price or fetch current price)
            if limit_price:
                estimated_cost = limit_price * quantity
            else:
                # For market orders, fetch current price
                market_data = await self.get_market_data(symbol)
                current_price = market_data.get('ask') or market_data.get('last', 0)
                estimated_cost = current_price * quantity * 1.02  # Add 2% buffer
            
            # Check if funds are sufficient
            if available_funds <= 0:
                logger.error(f"❌ SAFETY: Cannot place order - No available funds (${available_funds})")
                return {'error': 'Insufficient funds: Account balance is $0'}
            
            if estimated_cost > available_funds:
                logger.error(f"❌ SAFETY: Order rejected - Cost ${estimated_cost:.2f} > Available ${available_funds:.2f}")
                return {'error': f'Insufficient funds: Need ${estimated_cost:.2f}, have ${available_funds:.2f}'}
            
            # Additional safety for buying power
            if estimated_cost > buying_power:
                logger.warning(f"⚠️ Order exceeds buying power: ${estimated_cost:.2f} > ${buying_power:.2f}")
                return {'error': f'Exceeds buying power: Need ${estimated_cost:.2f}, have ${buying_power:.2f}'}
        
        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Create order based on type
            if order_type == 'MARKET':
                order = MarketOrder(action, quantity)
            elif order_type == 'LIMIT':
                order = LimitOrder(action, quantity, limit_price)
            elif order_type == 'STOP':
                order = StopOrder(action, quantity, stop_price)
            elif order_type == 'STOP_LIMIT':
                order = StopLimitOrder(action, quantity, stop_price, limit_price)
            else:
                return {'error': f'Unsupported order type: {order_type}'}
            
            # Place the order
            trade = self.ib.placeOrder(contract, order)
            
            # Wait a moment for order to be acknowledged
            await asyncio.sleep(0.5)
            
            return {
                'order_id': trade.order.orderId,
                'status': trade.orderStatus.status,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'order_type': order_type,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {'error': str(e)}
    
    async def cancel_order(self, order_id: int) -> bool:
        """Cancel an order"""
        if not self.connected:
            return False
        
        try:
            # Find the order
            for order in self.ib.openOrders():
                if order.orderId == order_id:
                    self.ib.cancelOrder(order)
                    logger.info(f"Cancelled order {order_id}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return False
    
    async def get_market_data(self, symbol: str) -> Dict:
        """Get current market data for a symbol"""
        if not self.connected:
            return {}
        
        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            
            # Wait for data
            await asyncio.sleep(2)
            
            return {
                'symbol': symbol,
                'last': ticker.last if not pd.isna(ticker.last) else None,
                'bid': ticker.bid if not pd.isna(ticker.bid) else None,
                'ask': ticker.ask if not pd.isna(ticker.ask) else None,
                'volume': ticker.volume if not pd.isna(ticker.volume) else None,
                'high': ticker.high if not pd.isna(ticker.high) else None,
                'low': ticker.low if not pd.isna(ticker.low) else None,
                'close': ticker.close if not pd.isna(ticker.close) else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return {}
    
    async def stream_market_data(self, symbol: str, callback):
        """Stream real-time market data for a symbol"""
        if not self.connected:
            return
        
        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request streaming market data
            ticker = self.ib.reqMktData(contract, '', False, False)
            
            # Store the ticker for later access
            self.market_data_streams[symbol] = ticker
            
            # Set up the callback
            def on_tick(ticker, tickType):
                asyncio.create_task(callback({
                    'symbol': symbol,
                    'last': ticker.last if not pd.isna(ticker.last) else None,
                    'bid': ticker.bid if not pd.isna(ticker.bid) else None,
                    'ask': ticker.ask if not pd.isna(ticker.ask) else None,
                    'volume': ticker.volume if not pd.isna(ticker.volume) else None,
                    'timestamp': datetime.now().isoformat()
                }))
            
            ticker.updateEvent += on_tick
            logger.info(f"Started streaming market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to stream market data for {symbol}: {e}")
    
    async def stop_market_data_stream(self, symbol: str):
        """Stop streaming market data for a symbol"""
        if symbol in self.market_data_streams:
            ticker = self.market_data_streams[symbol]
            self.ib.cancelMktData(ticker.contract)
            del self.market_data_streams[symbol]
            logger.info(f"Stopped streaming market data for {symbol}")
    
    async def get_historical_data(self,
                                  symbol: str,
                                  duration: str = "1 D",
                                  bar_size: str = "1 min",
                                  what_to_show: str = "TRADES") -> pd.DataFrame:
        """Get historical data for a symbol"""
        if not self.connected:
            return pd.DataFrame()
        
        try:
            # Create contract
            contract = Stock(symbol, 'SMART', 'USD')
            
            # Request historical data
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,
                formatDate=1
            )
            
            # Convert to DataFrame
            if bars:
                df = pd.DataFrame([{
                    'date': bar.date,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                } for bar in bars])
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                return df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def register_callback(self, event_type: str, callback):
        """Register a callback for specific events"""
        self.callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback):
        """Unregister a callback"""
        if callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)


# Singleton instance
_broker_instance = None

def get_ibkr_broker(host: str = None, port: int = None, client_id: int = None) -> IBKRBroker:
    """Get or create the IBKR broker singleton instance"""
    global _broker_instance
    
    if _broker_instance is None:
        # Use environment variables or defaults
        host = host or os.getenv('IBKR_HOST', '127.0.0.1')
        port = port or int(os.getenv('IBKR_PORT', '4002'))
        client_id = client_id or int(os.getenv('IBKR_CLIENT_ID', '1'))
        
        _broker_instance = IBKRBroker(host, port, client_id)
    
    return _broker_instance