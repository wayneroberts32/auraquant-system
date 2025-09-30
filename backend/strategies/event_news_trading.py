"""
Event-Driven & News-Based Trading Module  
AuraQuant Infinity Money Synthetic Intelligence System
ADD-ONLY • NO REBUILD • REAL-TIME NEWS REACTION
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import json

@dataclass
class NewsEvent:
    """Represents a market-moving news event"""
    event_id: str
    timestamp: float
    source: str
    headline: str
    content: str
    symbols: List[str]
    sentiment_score: float  # -1 to 1
    impact_level: str  # HIGH, MEDIUM, LOW
    event_type: str  # EARNINGS, ECONOMIC, REGULATORY, MERGER, etc
    metadata: Dict

@dataclass 
class EventTrade:
    """Trade triggered by news event"""
    event_id: str
    symbol: str
    direction: str  # LONG/SHORT
    entry_price: float
    size: int
    stop_loss: float
    take_profit: float
    time_horizon: int  # seconds
    confidence: float  # 0-1

class EventDrivenEngine:
    """
    Real-time news analysis and event-driven trading
    Processes news, earnings, economic data for instant trading decisions
    """
    
    def __init__(self, mongodb_client=None):
        self.mongodb = mongodb_client
        self.news_queue = asyncio.Queue(maxsize=1000)
        self.active_trades = {}
        self.event_history = []
        
        # Event patterns for different news types
        self.event_patterns = {
            'EARNINGS_BEAT': {
                'keywords': ['beats', 'exceeds', 'surpasses', 'earnings'],
                'impact': 'POSITIVE',
                'confidence': 0.8
            },
            'EARNINGS_MISS': {
                'keywords': ['misses', 'disappoints', 'below', 'earnings'],
                'impact': 'NEGATIVE', 
                'confidence': 0.8
            },
            'FDA_APPROVAL': {
                'keywords': ['FDA', 'approved', 'clearance', 'authorization'],
                'impact': 'POSITIVE',
                'confidence': 0.9
            },
            'MERGER_ANNOUNCEMENT': {
                'keywords': ['merger', 'acquisition', 'buyout', 'deal'],
                'impact': 'MIXED',
                'confidence': 0.7
            },
            'REGULATORY_ACTION': {
                'keywords': ['SEC', 'investigation', 'probe', 'lawsuit'],
                'impact': 'NEGATIVE',
                'confidence': 0.75
            },
            'PRODUCT_LAUNCH': {
                'keywords': ['launches', 'unveils', 'announces', 'new product'],
                'impact': 'POSITIVE',
                'confidence': 0.6
            }
        }
        
        # Trading parameters by event type
        self.trading_params = {
            'EARNINGS': {
                'position_size_pct': 2.0,
                'stop_loss_pct': 2.0,
                'take_profit_pct': 5.0,
                'hold_time': 3600  # 1 hour
            },
            'FDA_APPROVAL': {
                'position_size_pct': 3.0,
                'stop_loss_pct': 3.0,
                'take_profit_pct': 10.0,
                'hold_time': 7200  # 2 hours
            },
            'MERGER': {
                'position_size_pct': 1.5,
                'stop_loss_pct': 1.5,
                'take_profit_pct': 3.0,
                'hold_time': 86400  # 24 hours
            },
            'DEFAULT': {
                'position_size_pct': 1.0,
                'stop_loss_pct': 1.0,
                'take_profit_pct': 2.0,
                'hold_time': 1800  # 30 minutes
            }
        }
        
        # Performance metrics
        self.metrics = {
            'events_processed': 0,
            'trades_executed': 0,
            'winning_trades': 0,
            'total_pnl': 0,
            'avg_reaction_time_ms': 0
        }
    
    async def process_news_stream(self, news_item: Dict) -> Optional[NewsEvent]:
        """
        Process incoming news and convert to tradeable event
        """
        start_time = time.perf_counter()
        
        try:
            # Parse news item
            event = self._parse_news_item(news_item)
            
            if not event:
                return None
            
            # Analyze sentiment and impact
            event.sentiment_score = await self._analyze_sentiment(event.content)
            event.impact_level = self._assess_impact_level(event)
            
            # Extract affected symbols
            event.symbols = self._extract_symbols(event.headline, event.content)
            
            # Add to queue for processing
            await self.news_queue.put(event)
            
            # Update metrics
            reaction_time = (time.perf_counter() - start_time) * 1000
            self._update_reaction_metrics(reaction_time)
            
            self.metrics['events_processed'] += 1
            
            return event
            
        except Exception as e:
            print(f"Error processing news: {e}")
            return None
    
    def _parse_news_item(self, news_item: Dict) -> Optional[NewsEvent]:
        """
        Parse raw news item into NewsEvent
        """
        try:
            # Determine event type
            event_type = self._classify_event_type(news_item.get('headline', ''))
            
            event = NewsEvent(
                event_id=f"NEWS_{time.time()}_{hash(news_item.get('headline', ''))}",
                timestamp=time.time(),
                source=news_item.get('source', 'unknown'),
                headline=news_item.get('headline', ''),
                content=news_item.get('content', news_item.get('summary', '')),
                symbols=[],
                sentiment_score=0,
                impact_level='UNKNOWN',
                event_type=event_type,
                metadata=news_item.get('metadata', {})
            )
            
            return event
            
        except Exception:
            return None
    
    def _classify_event_type(self, headline: str) -> str:
        """
        Classify news event type based on headline
        """
        headline_lower = headline.lower()
        
        if any(word in headline_lower for word in ['earnings', 'revenue', 'profit']):
            return 'EARNINGS'
        elif any(word in headline_lower for word in ['fda', 'approval', 'drug']):
            return 'FDA_APPROVAL'
        elif any(word in headline_lower for word in ['merger', 'acquisition', 'buyout']):
            return 'MERGER'
        elif any(word in headline_lower for word in ['fed', 'interest rate', 'inflation']):
            return 'ECONOMIC'
        elif any(word in headline_lower for word in ['sec', 'lawsuit', 'investigation']):
            return 'REGULATORY'
        else:
            return 'GENERAL'
    
    async def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of news text
        Returns score between -1 (very negative) and 1 (very positive)
        """
        # Simple keyword-based sentiment (would use NLP model in production)
        positive_words = ['surge', 'soar', 'jump', 'rally', 'gain', 'beat', 'exceed', 
                         'record', 'breakthrough', 'success', 'upgrade', 'positive']
        negative_words = ['plunge', 'crash', 'fall', 'drop', 'loss', 'miss', 'fail',
                         'lawsuit', 'investigation', 'downgrade', 'negative', 'concern']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0
        
        sentiment = (positive_count - negative_count) / total
        return max(-1, min(1, sentiment))
    
    def _assess_impact_level(self, event: NewsEvent) -> str:
        """
        Assess market impact level of event
        """
        # High impact indicators
        high_impact_keywords = ['bankruptcy', 'merger', 'fda', 'fed', 'earnings beat', 
                               'earnings miss', 'ceo', 'acquisition']
        
        text_combined = f"{event.headline} {event.content}".lower()
        
        if any(keyword in text_combined for keyword in high_impact_keywords):
            return 'HIGH'
        
        # Check sentiment extremes
        if abs(event.sentiment_score) > 0.7:
            return 'HIGH'
        elif abs(event.sentiment_score) > 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _extract_symbols(self, headline: str, content: str) -> List[str]:
        """
        Extract stock symbols from text
        """
        # Pattern for stock symbols (1-5 uppercase letters)
        symbol_pattern = r'\b[A-Z]{1,5}\b'
        
        text = f"{headline} {content}"
        potential_symbols = re.findall(symbol_pattern, text)
        
        # Filter out common words that match pattern
        common_words = {'CEO', 'CFO', 'FDA', 'SEC', 'NYSE', 'USA', 'UK', 'EU', 
                       'AI', 'IT', 'HR', 'PR', 'IPO', 'ETF'}
        
        symbols = [s for s in potential_symbols if s not in common_words]
        
        # Return unique symbols
        return list(set(symbols))[:10]  # Limit to 10 symbols
    
    async def generate_trade_signals(self, event: NewsEvent) -> List[EventTrade]:
        """
        Generate trade signals from news event
        """
        trades = []
        
        # Skip if low impact
        if event.impact_level == 'LOW':
            return trades
        
        # Get trading parameters for event type
        params = self.trading_params.get(event.event_type, self.trading_params['DEFAULT'])
        
        for symbol in event.symbols[:3]:  # Limit to top 3 symbols
            # Determine trade direction based on sentiment
            if event.sentiment_score > 0.3:
                direction = 'LONG'
                multiplier = 1
            elif event.sentiment_score < -0.3:
                direction = 'SHORT'
                multiplier = -1
            else:
                continue  # Skip neutral sentiment
            
            # Get current price (simulated)
            current_price = await self._get_current_price(symbol)
            
            # Calculate trade parameters
            confidence = abs(event.sentiment_score) * 0.8
            
            if event.impact_level == 'HIGH':
                confidence *= 1.2
            elif event.impact_level == 'MEDIUM':
                confidence *= 1.0
            
            confidence = min(1.0, confidence)
            
            # Create trade signal
            trade = EventTrade(
                event_id=event.event_id,
                symbol=symbol,
                direction=direction,
                entry_price=current_price,
                size=int(10000 * params['position_size_pct'] / 100 * confidence),
                stop_loss=current_price * (1 - multiplier * params['stop_loss_pct'] / 100),
                take_profit=current_price * (1 + multiplier * params['take_profit_pct'] / 100),
                time_horizon=params['hold_time'],
                confidence=confidence
            )
            
            trades.append(trade)
        
        return trades
    
    async def execute_event_trade(self, trade: EventTrade) -> Dict[str, Any]:
        """
        Execute trade based on news event
        """
        execution_result = {
            'trade_id': f"EVT_{trade.symbol}_{time.time()}",
            'event_id': trade.event_id,
            'status': 'PENDING',
            'entry_price': 0,
            'exit_price': 0,
            'pnl': 0
        }
        
        try:
            # Place order (simulated)
            order_result = await self._place_event_order(trade)
            
            if order_result['status'] == 'FILLED':
                execution_result['status'] = 'ACTIVE'
                execution_result['entry_price'] = order_result['fill_price']
                
                # Store active trade
                self.active_trades[execution_result['trade_id']] = {
                    'trade': trade,
                    'entry_time': time.time(),
                    'entry_price': order_result['fill_price'],
                    'status': 'ACTIVE'
                }
                
                # Schedule exit monitoring
                asyncio.create_task(self._monitor_trade_exit(execution_result['trade_id'], trade))
                
                self.metrics['trades_executed'] += 1
                
            else:
                execution_result['status'] = 'REJECTED'
            
            # Store in MongoDB
            if self.mongodb:
                await self._store_event_trade(trade, execution_result)
                
        except Exception as e:
            execution_result['status'] = 'ERROR'
            execution_result['error'] = str(e)
        
        return execution_result
    
    async def _monitor_trade_exit(self, trade_id: str, trade: EventTrade):
        """
        Monitor trade for exit conditions
        """
        start_time = time.time()
        
        while trade_id in self.active_trades:
            current_trade = self.active_trades[trade_id]
            
            # Check time horizon
            if time.time() - start_time > trade.time_horizon:
                await self._exit_trade(trade_id, 'TIME_EXIT')
                break
            
            # Check stop loss and take profit
            current_price = await self._get_current_price(trade.symbol)
            
            if trade.direction == 'LONG':
                if current_price <= trade.stop_loss:
                    await self._exit_trade(trade_id, 'STOP_LOSS')
                    break
                elif current_price >= trade.take_profit:
                    await self._exit_trade(trade_id, 'TAKE_PROFIT')
                    break
            else:  # SHORT
                if current_price >= trade.stop_loss:
                    await self._exit_trade(trade_id, 'STOP_LOSS')
                    break
                elif current_price <= trade.take_profit:
                    await self._exit_trade(trade_id, 'TAKE_PROFIT')
                    break
            
            # Check every second
            await asyncio.sleep(1)
    
    async def _exit_trade(self, trade_id: str, exit_reason: str):
        """
        Exit active trade
        """
        if trade_id not in self.active_trades:
            return
        
        trade_info = self.active_trades[trade_id]
        trade = trade_info['trade']
        
        # Get exit price
        exit_price = await self._get_current_price(trade.symbol)
        
        # Calculate PnL
        if trade.direction == 'LONG':
            pnl = (exit_price - trade_info['entry_price']) * trade.size
        else:
            pnl = (trade_info['entry_price'] - exit_price) * trade.size
        
        # Update metrics
        self.metrics['total_pnl'] += pnl
        if pnl > 0:
            self.metrics['winning_trades'] += 1
        
        # Remove from active trades
        del self.active_trades[trade_id]
        
        # Store exit in MongoDB
        if self.mongodb:
            await self._store_trade_exit(trade_id, exit_price, pnl, exit_reason)
    
    async def backtest_news_strategy(self, historical_news: List[Dict], 
                                    historical_prices: Dict[str, List[float]]) -> Dict:
        """
        Backtest news trading strategy on historical data
        """
        results = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'trades': []
        }
        
        for news_item in historical_news:
            # Process news event
            event = await self.process_news_stream(news_item)
            
            if not event:
                continue
            
            # Generate trade signals
            trades = await self.generate_trade_signals(event)
            
            for trade in trades:
                # Simulate trade execution
                if trade.symbol in historical_prices:
                    prices = historical_prices[trade.symbol]
                    
                    # Simulate entry
                    entry_idx = int(len(prices) * 0.3)  # Entry point
                    exit_idx = min(entry_idx + 100, len(prices) - 1)  # Exit point
                    
                    entry_price = prices[entry_idx]
                    exit_price = prices[exit_idx]
                    
                    # Calculate PnL
                    if trade.direction == 'LONG':
                        pnl = (exit_price - entry_price) * trade.size
                    else:
                        pnl = (entry_price - exit_price) * trade.size
                    
                    results['total_trades'] += 1
                    results['total_pnl'] += pnl
                    
                    if pnl > 0:
                        results['winning_trades'] += 1
                    
                    results['trades'].append({
                        'event_id': event.event_id,
                        'symbol': trade.symbol,
                        'direction': trade.direction,
                        'pnl': pnl
                    })
        
        # Calculate statistics
        if results['total_trades'] > 0:
            results['win_rate'] = results['winning_trades'] / results['total_trades'] * 100
            results['avg_pnl'] = results['total_pnl'] / results['total_trades']
        
        return results
    
    def _update_reaction_metrics(self, reaction_time_ms: float):
        """
        Update reaction time metrics
        """
        alpha = 0.1  # EMA factor
        if self.metrics['avg_reaction_time_ms'] == 0:
            self.metrics['avg_reaction_time_ms'] = reaction_time_ms
        else:
            self.metrics['avg_reaction_time_ms'] = (
                alpha * reaction_time_ms + 
                (1 - alpha) * self.metrics['avg_reaction_time_ms']
            )
    
    # Placeholder methods
    async def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        # Simulated price
        import random
        return 100.0 * (1 + random.uniform(-0.02, 0.02))
    
    async def _place_event_order(self, trade: EventTrade) -> Dict:
        """Place order for event-driven trade"""
        # Simulated order placement
        import random
        success = random.random() > 0.1
        
        return {
            'status': 'FILLED' if success else 'REJECTED',
            'fill_price': trade.entry_price * (1 + random.uniform(-0.001, 0.001))
        }
    
    async def _store_event_trade(self, trade: EventTrade, result: Dict):
        """Store event trade in MongoDB"""
        if not self.mongodb:
            return
        
        doc = {
            'timestamp': time.time(),
            'event_id': trade.event_id,
            'trade': {
                'symbol': trade.symbol,
                'direction': trade.direction,
                'size': trade.size,
                'confidence': trade.confidence
            },
            'execution': result,
            'strategy': 'EVENT_DRIVEN'
        }
        
        await self.mongodb.trades.insert_one(doc)
    
    async def _store_trade_exit(self, trade_id: str, exit_price: float, pnl: float, reason: str):
        """Store trade exit in MongoDB"""
        if not self.mongodb:
            return
        
        await self.mongodb.trades.update_one(
            {'trade_id': trade_id},
            {'$set': {
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': reason,
                'exit_timestamp': time.time(),
                'status': 'CLOSED'
            }}
        )

# QA/QC Test
async def qa_news_trading_test():
    """
    QA: Test news processing and event-driven trading
    """
    engine = EventDrivenEngine()
    
    # Test news items
    test_news = [
        {
            'headline': 'AAPL Beats Earnings Expectations by 20%',
            'content': 'Apple Inc reported strong Q4 earnings, beating analyst estimates...',
            'source': 'Bloomberg',
            'timestamp': time.time()
        },
        {
            'headline': 'FDA Approves New Drug for BIOTECH Company XYZ',
            'content': 'The FDA has granted approval for revolutionary treatment...',
            'source': 'Reuters',
            'timestamp': time.time()
        },
        {
            'headline': 'TSLA Under SEC Investigation for Accounting Practices',
            'content': 'Securities and Exchange Commission launches probe into Tesla...',
            'source': 'WSJ',
            'timestamp': time.time()
        }
    ]
    
    results = {
        'events_processed': 0,
        'trades_generated': 0,
        'trades_executed': 0,
        'avg_confidence': 0,
        'reaction_times': []
    }
    
    # Process each news item
    for news_item in test_news:
        start = time.perf_counter()
        
        # Process news
        event = await engine.process_news_stream(news_item)
        
        if event:
            results['events_processed'] += 1
            
            # Generate trades
            trades = await engine.generate_trade_signals(event)
            results['trades_generated'] += len(trades)
            
            # Execute trades
            for trade in trades:
                execution = await engine.execute_event_trade(trade)
                if execution['status'] in ['ACTIVE', 'FILLED']:
                    results['trades_executed'] += 1
                
                results['avg_confidence'] += trade.confidence
            
            # Track reaction time
            reaction_time = (time.perf_counter() - start) * 1000
            results['reaction_times'].append(reaction_time)
    
    # Calculate averages
    if results['trades_generated'] > 0:
        results['avg_confidence'] /= results['trades_generated']
    
    if results['reaction_times']:
        results['avg_reaction_time_ms'] = sum(results['reaction_times']) / len(results['reaction_times'])
        results['max_reaction_time_ms'] = max(results['reaction_times'])
        results['min_reaction_time_ms'] = min(results['reaction_times'])
    
    # Get engine metrics
    results['engine_metrics'] = engine.metrics
    
    return results