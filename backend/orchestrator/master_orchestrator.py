"""
AuraQuant Master System Orchestrator
=====================================
Central nervous system that wires all components together
Integrates indicators, patterns, strategies with MongoDB persistence

Created: 2025-01-30
Status: PRODUCTION-CRITICAL
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time
import json
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraQuant.Orchestrator")

# Import all system components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.technical_indicators import TechnicalIndicators
from indicators.extended_indicators import ExtendedIndicators  
from indicators.pattern_recognition import PatternRecognition
from strategies.professional_strategies import ProfessionalStrategies
from money_management.money_manager import MoneyManager
from brain.quantum_brain import QuantumBrain

@dataclass
class SystemState:
    """Current state of the entire system"""
    timestamp: float
    market_phase: str  # TRENDING, RANGING, VOLATILE, UNCERTAIN
    risk_level: str  # LOW, MODERATE, HIGH, EXTREME
    active_positions: int
    total_exposure: float
    daily_pnl: float
    system_health: str  # HEALTHY, WARNING, CRITICAL
    signals_generated: int
    signals_executed: int
    learning_cycles: int

@dataclass
class MarketSnapshot:
    """Complete market analysis snapshot"""
    symbol: str
    timeframe: str
    timestamp: float
    price_current: float
    price_change_24h: float
    volume_24h: float
    volatility: float
    trend_direction: str
    trend_strength: float
    market_phase: str

class MasterOrchestrator:
    """
    The Master Orchestrator - Brain of AuraQuant
    Coordinates all components, makes decisions, learns and evolves
    """
    
    def __init__(self, mongodb_uri: str = None):
        # Initialize MongoDB connection
        self.mongodb_client = None
        self.db = None
        if mongodb_uri:
            self.mongodb_client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.mongodb_client.auraquant
        
        # Initialize all components with MongoDB
        self.technical = TechnicalIndicators(self.db)
        self.extended = ExtendedIndicators(self.db)
        self.patterns = PatternRecognition(self.db)
        self.strategies = ProfessionalStrategies(self.db)
        self.money_manager = MoneyManager(self.db)
        self.quantum_brain = QuantumBrain(self.db) if self.db else None
        
        # System state
        self.system_state = SystemState(
            timestamp=time.time(),
            market_phase="UNCERTAIN",
            risk_level="MODERATE",
            active_positions=0,
            total_exposure=0.0,
            daily_pnl=0.0,
            system_health="HEALTHY",
            signals_generated=0,
            signals_executed=0,
            learning_cycles=0
        )
        
        # Market snapshots cache
        self.market_snapshots = {}
        
        # Signal queue
        self.signal_queue = []
        
        # Performance tracking
        self.performance_history = []
        
        logger.info("AuraQuant Master Orchestrator initialized")
    
    # ==================== Main Analysis Pipeline ====================
    
    async def analyze_market(self, symbol: str, ohlcv_data: pd.DataFrame,
                           timeframe: str = "1H") -> Dict[str, Any]:
        """
        Complete market analysis pipeline
        Runs all indicators, patterns, and strategies
        """
        logger.info(f"Starting market analysis for {symbol} on {timeframe}")
        
        analysis_start = time.time()
        
        # Create market snapshot
        snapshot = self._create_market_snapshot(symbol, ohlcv_data, timeframe)
        self.market_snapshots[symbol] = snapshot
        
        # Initialize results
        analysis_results = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': time.time(),
            'snapshot': asdict(snapshot),
            'indicators': {},
            'patterns': {},
            'strategies': {},
            'signals': [],
            'risk_assessment': {},
            'recommendations': []
        }
        
        try:
            # 1. Run Technical Indicators
            logger.info("Running technical indicators...")
            tech_analysis = await self.technical.analyze_complete(symbol, ohlcv_data)
            analysis_results['indicators']['technical'] = self._serialize_analysis(tech_analysis)
            
            # 2. Run Extended Indicators
            logger.info("Running extended indicators...")
            extended_analysis = await self.extended.analyze_extended(symbol, ohlcv_data)
            analysis_results['indicators']['extended'] = self._serialize_analysis(extended_analysis)
            
            # 3. Run Pattern Recognition
            logger.info("Running pattern recognition...")
            pattern_analysis = await self.patterns.analyze_all_patterns(symbol, ohlcv_data)
            analysis_results['patterns'] = self._serialize_patterns(pattern_analysis)
            
            # 4. Run Professional Strategies
            logger.info("Running professional strategies...")
            strategy_analysis = await self.strategies.analyze_all_strategies(
                ohlcv_data, symbol, timeframe
            )
            analysis_results['strategies'] = self._serialize_strategies(strategy_analysis)
            
            # 5. Combine all signals
            logger.info("Combining signals...")
            combined_signals = await self._combine_signals(
                tech_analysis, extended_analysis, pattern_analysis, strategy_analysis
            )
            analysis_results['signals'] = combined_signals
            
            # 6. Risk Assessment
            logger.info("Assessing risk...")
            risk_assessment = await self._assess_risk(combined_signals, ohlcv_data)
            analysis_results['risk_assessment'] = risk_assessment
            
            # 7. Generate Recommendations
            logger.info("Generating recommendations...")
            recommendations = await self._generate_recommendations(
                combined_signals, risk_assessment, snapshot
            )
            analysis_results['recommendations'] = recommendations
            
            # 8. Update System State
            await self._update_system_state(analysis_results)
            
            # 9. Store in MongoDB
            if self.db:
                await self._store_analysis(analysis_results)
            
            # 10. Trigger Learning if Quantum Brain available
            if self.quantum_brain:
                await self.quantum_brain.learn_from_analysis(analysis_results)
                self.system_state.learning_cycles += 1
            
            analysis_time = time.time() - analysis_start
            logger.info(f"Analysis completed in {analysis_time:.2f} seconds")
            
            analysis_results['analysis_time'] = analysis_time
            analysis_results['system_state'] = asdict(self.system_state)
            
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            analysis_results['error'] = str(e)
            self.system_state.system_health = "WARNING"
        
        return analysis_results
    
    # ==================== Signal Combination & Scoring ====================
    
    async def _combine_signals(self, tech_analysis: Dict, extended_analysis: Dict,
                              pattern_analysis: Dict, strategy_analysis: Dict) -> List[Dict]:
        """
        Combine signals from all sources and score them
        """
        combined_signals = []
        
        # Extract technical indicator signals
        if 'signals' in tech_analysis:
            for signal in tech_analysis['signals']:
                combined_signals.append({
                    'source': 'TECHNICAL',
                    'type': signal.get('type'),
                    'strength': signal.get('strength', 0),
                    'confidence': signal.get('confidence', 0),
                    'timestamp': signal.get('timestamp', time.time())
                })
        
        # Extract extended indicator signals
        if 'master_signal' in extended_analysis:
            master = extended_analysis['master_signal']
            if master['action'] != 'NEUTRAL':
                combined_signals.append({
                    'source': 'EXTENDED',
                    'type': master['action'],
                    'strength': master['strength'],
                    'confidence': master['confidence'],
                    'conditions': master.get('conditions', []),
                    'risk_level': master.get('risk_level'),
                    'timestamp': time.time()
                })
        
        # Extract pattern signals
        if 'pattern_signals' in pattern_analysis:
            for signal in pattern_analysis['pattern_signals']:
                combined_signals.append({
                    'source': 'PATTERN',
                    'type': signal.get('type'),
                    'pattern': signal.get('pattern'),
                    'direction': signal.get('direction'),
                    'confidence': signal.get('confidence', 0),
                    'timestamp': signal.get('timestamp', time.time())
                })
        
        # Extract strategy signals
        if 'high_confidence_signals' in strategy_analysis:
            for signal in strategy_analysis['high_confidence_signals']:
                combined_signals.append({
                    'source': 'STRATEGY',
                    'strategy': signal.strategy_name,
                    'direction': signal.direction.value,
                    'entry': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit_2,
                    'position_size': signal.position_size,
                    'confidence': signal.confidence,
                    'risk_reward': signal.risk_reward_ratio,
                    'conditions': signal.conditions_met,
                    'timestamp': signal.timestamp
                })
        
        # Score and rank signals
        scored_signals = self._score_signals(combined_signals)
        
        # Filter high-quality signals
        high_quality = [s for s in scored_signals if s['final_score'] >= 0.7]
        high_quality.sort(key=lambda x: x['final_score'], reverse=True)
        
        return high_quality
    
    def _score_signals(self, signals: List[Dict]) -> List[Dict]:
        """
        Score signals based on multiple factors
        """
        for signal in signals:
            score = 0
            weight = 0
            
            # Base confidence score
            if 'confidence' in signal:
                score += signal['confidence'] * 0.3
                weight += 0.3
            
            # Source weight
            source_weights = {
                'STRATEGY': 0.35,
                'PATTERN': 0.25,
                'TECHNICAL': 0.2,
                'EXTENDED': 0.2
            }
            if 'source' in signal:
                score += source_weights.get(signal['source'], 0.1)
                weight += source_weights.get(signal['source'], 0.1)
            
            # Risk-reward bonus
            if 'risk_reward' in signal:
                if signal['risk_reward'] >= 3:
                    score += 0.2
                elif signal['risk_reward'] >= 2:
                    score += 0.1
                weight += 0.2
            
            # Strength factor
            if 'strength' in signal:
                score += signal['strength'] * 0.15
                weight += 0.15
            
            # Calculate final score
            signal['final_score'] = score / weight if weight > 0 else 0
        
        return signals
    
    # ==================== Risk Assessment ====================
    
    async def _assess_risk(self, signals: List[Dict], ohlcv_data: pd.DataFrame) -> Dict:
        """
        Comprehensive risk assessment
        """
        risk_assessment = {
            'overall_risk': 'MODERATE',
            'factors': {},
            'warnings': [],
            'max_position_size': 0.1,
            'recommended_stops': {}
        }
        
        # Calculate volatility risk
        atr_data = self.extended.calculate_atr(ohlcv_data)
        current_atr = atr_data['atr'].iloc[-1] if not atr_data['atr'].empty else 0
        atr_percent = atr_data['atr_percent'].iloc[-1] if not atr_data['atr_percent'].empty else 0
        
        if atr_percent > 5:
            risk_assessment['factors']['volatility'] = 'EXTREME'
            risk_assessment['warnings'].append("Extreme volatility detected")
            risk_assessment['max_position_size'] = 0.02
        elif atr_percent > 3:
            risk_assessment['factors']['volatility'] = 'HIGH'
            risk_assessment['warnings'].append("High volatility")
            risk_assessment['max_position_size'] = 0.05
        else:
            risk_assessment['factors']['volatility'] = 'NORMAL'
            risk_assessment['max_position_size'] = 0.1
        
        # Signal correlation risk
        if len(signals) > 3:
            risk_assessment['factors']['signal_correlation'] = 'HIGH'
            risk_assessment['warnings'].append(f"Multiple correlated signals ({len(signals)})")
        
        # Position sizing recommendations
        risk_assessment['recommended_stops'] = {
            'conservative': current_atr * 2,
            'moderate': current_atr * 1.5,
            'aggressive': current_atr * 1
        }
        
        # Overall risk calculation
        risk_factors = []
        if risk_assessment['factors'].get('volatility') in ['HIGH', 'EXTREME']:
            risk_factors.append('HIGH')
        if risk_assessment['factors'].get('signal_correlation') == 'HIGH':
            risk_factors.append('HIGH')
        
        if 'EXTREME' in str(risk_assessment['factors'].values()):
            risk_assessment['overall_risk'] = 'EXTREME'
        elif len([f for f in risk_factors if f == 'HIGH']) >= 2:
            risk_assessment['overall_risk'] = 'HIGH'
        elif 'HIGH' in risk_factors:
            risk_assessment['overall_risk'] = 'MODERATE'
        else:
            risk_assessment['overall_risk'] = 'LOW'
        
        return risk_assessment
    
    # ==================== Recommendations ====================
    
    async def _generate_recommendations(self, signals: List[Dict],
                                       risk_assessment: Dict,
                                       snapshot: MarketSnapshot) -> List[Dict]:
        """
        Generate actionable trading recommendations
        """
        recommendations = []
        
        # Check if we have high-confidence signals
        if not signals:
            recommendations.append({
                'action': 'WAIT',
                'reason': 'No high-confidence signals detected',
                'confidence': 0.9
            })
            return recommendations
        
        # Get top signal
        top_signal = signals[0] if signals else None
        
        if top_signal and top_signal['final_score'] >= 0.8:
            # Strong signal recommendation
            rec = {
                'action': 'EXECUTE',
                'signal': top_signal,
                'position_size': min(
                    top_signal.get('position_size', 0.05),
                    risk_assessment['max_position_size']
                ),
                'risk_level': risk_assessment['overall_risk'],
                'confidence': top_signal['final_score']
            }
            
            # Add stop-loss recommendation
            if 'stop_loss' in top_signal:
                rec['stop_loss'] = top_signal['stop_loss']
            else:
                rec['stop_loss'] = snapshot.price_current - risk_assessment['recommended_stops']['moderate']
            
            recommendations.append(rec)
            
        elif top_signal and top_signal['final_score'] >= 0.7:
            # Moderate signal - suggest waiting for confirmation
            recommendations.append({
                'action': 'PREPARE',
                'signal': top_signal,
                'reason': 'Signal needs additional confirmation',
                'watch_levels': {
                    'entry': top_signal.get('entry', snapshot.price_current),
                    'confirmation': snapshot.price_current * 1.005  # 0.5% move
                },
                'confidence': top_signal['final_score']
            })
        
        # Add risk warnings
        for warning in risk_assessment.get('warnings', []):
            recommendations.append({
                'action': 'WARNING',
                'message': warning,
                'type': 'RISK'
            })
        
        # Market phase recommendations
        if snapshot.market_phase == 'VOLATILE':
            recommendations.append({
                'action': 'ADJUST',
                'type': 'POSITION_SIZE',
                'recommendation': 'Reduce position sizes due to high volatility',
                'max_size': risk_assessment['max_position_size']
            })
        
        return recommendations
    
    # ==================== System State Management ====================
    
    async def _update_system_state(self, analysis: Dict):
        """
        Update the overall system state
        """
        self.system_state.timestamp = time.time()
        
        # Update market phase
        if 'snapshot' in analysis:
            self.system_state.market_phase = analysis['snapshot'].get('market_phase', 'UNCERTAIN')
        
        # Update risk level
        if 'risk_assessment' in analysis:
            self.system_state.risk_level = analysis['risk_assessment'].get('overall_risk', 'MODERATE')
        
        # Update signal counts
        if 'signals' in analysis:
            self.system_state.signals_generated += len(analysis['signals'])
        
        # Check system health
        if self.system_state.risk_level == 'EXTREME':
            self.system_state.system_health = 'WARNING'
        elif len(analysis.get('signals', [])) == 0 and self.system_state.signals_generated > 100:
            # No signals despite many attempts
            self.system_state.system_health = 'WARNING'
        else:
            self.system_state.system_health = 'HEALTHY'
    
    # ==================== Helper Functions ====================
    
    def _create_market_snapshot(self, symbol: str, ohlcv_data: pd.DataFrame,
                               timeframe: str) -> MarketSnapshot:
        """
        Create a market snapshot from OHLCV data
        """
        close = ohlcv_data['close']
        volume = ohlcv_data['volume']
        
        # Current price and 24h change
        current_price = close.iloc[-1]
        price_24h_ago = close.iloc[-24] if len(close) > 24 else close.iloc[0]
        price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        
        # Volume
        volume_24h = volume.iloc[-24:].sum() if len(volume) > 24 else volume.sum()
        
        # Volatility (using standard deviation)
        volatility = close.pct_change().std() * np.sqrt(252) * 100  # Annualized
        
        # Trend analysis
        sma_20 = close.rolling(20).mean().iloc[-1] if len(close) > 20 else current_price
        sma_50 = close.rolling(50).mean().iloc[-1] if len(close) > 50 else current_price
        
        if current_price > sma_20 > sma_50:
            trend_direction = 'BULLISH'
            trend_strength = min((current_price - sma_50) / sma_50 * 10, 1.0)
        elif current_price < sma_20 < sma_50:
            trend_direction = 'BEARISH'
            trend_strength = min((sma_50 - current_price) / sma_50 * 10, 1.0)
        else:
            trend_direction = 'NEUTRAL'
            trend_strength = 0.0
        
        # Market phase detection
        if volatility > 50:
            market_phase = 'VOLATILE'
        elif abs(trend_strength) > 0.5:
            market_phase = 'TRENDING'
        else:
            market_phase = 'RANGING'
        
        return MarketSnapshot(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=time.time(),
            price_current=current_price,
            price_change_24h=price_change_24h,
            volume_24h=volume_24h,
            volatility=volatility,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            market_phase=market_phase
        )
    
    def _serialize_analysis(self, analysis: Dict) -> Dict:
        """
        Serialize analysis results for storage/transmission
        """
        serialized = {}
        for key, value in analysis.items():
            if isinstance(value, pd.Series):
                serialized[key] = value.iloc[-1] if not value.empty else None
            elif isinstance(value, pd.DataFrame):
                serialized[key] = value.iloc[-1].to_dict() if not value.empty else {}
            elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        return serialized
    
    def _serialize_patterns(self, pattern_analysis: Dict) -> Dict:
        """
        Serialize pattern analysis results
        """
        serialized = {
            'harmonic_count': len(pattern_analysis.get('harmonic_patterns', [])),
            'support_resistance_count': len(pattern_analysis.get('support_resistance', [])),
            'candlestick_count': len(pattern_analysis.get('candlestick_patterns', [])),
            'pattern_signals': pattern_analysis.get('pattern_signals', [])
        }
        
        # Add top patterns
        if pattern_analysis.get('harmonic_patterns'):
            serialized['top_harmonic'] = {
                'type': pattern_analysis['harmonic_patterns'][0].pattern_type,
                'direction': pattern_analysis['harmonic_patterns'][0].direction,
                'confidence': pattern_analysis['harmonic_patterns'][0].confidence
            }
        
        return serialized
    
    def _serialize_strategies(self, strategy_analysis: Dict) -> Dict:
        """
        Serialize strategy analysis results
        """
        return {
            'total_signals': strategy_analysis.get('total_signals', 0),
            'actionable_signals': strategy_analysis.get('actionable_signals', 0),
            'risk_assessment': strategy_analysis.get('risk_assessment', {}),
            'top_signals': [
                {
                    'strategy': s.strategy_name,
                    'direction': s.direction.value,
                    'confidence': s.confidence,
                    'risk_reward': s.risk_reward_ratio
                }
                for s in strategy_analysis.get('high_confidence_signals', [])[:3]
            ]
        }
    
    # ==================== MongoDB Storage ====================
    
    async def _store_analysis(self, analysis: Dict):
        """
        Store complete analysis in MongoDB
        """
        if not self.db:
            return
        
        try:
            # Store in main analysis collection
            await self.db.market_analysis.insert_one({
                'timestamp': analysis['timestamp'],
                'symbol': analysis['symbol'],
                'timeframe': analysis['timeframe'],
                'snapshot': analysis['snapshot'],
                'signal_count': len(analysis.get('signals', [])),
                'risk_level': analysis.get('risk_assessment', {}).get('overall_risk'),
                'recommendations': analysis.get('recommendations', []),
                'system_state': asdict(self.system_state)
            })
            
            # Store signals separately for quick access
            if analysis.get('signals'):
                for signal in analysis['signals']:
                    await self.db.trading_signals.insert_one({
                        'timestamp': time.time(),
                        'symbol': analysis['symbol'],
                        'signal': signal,
                        'executed': False
                    })
            
            logger.info(f"Analysis stored in MongoDB for {analysis['symbol']}")
            
        except Exception as e:
            logger.error(f"Error storing analysis in MongoDB: {str(e)}")
    
    # ==================== Execution & Monitoring ====================
    
    async def execute_recommendations(self, recommendations: List[Dict]) -> Dict:
        """
        Execute trading recommendations
        """
        execution_results = {
            'timestamp': time.time(),
            'executed': [],
            'skipped': [],
            'errors': []
        }
        
        for rec in recommendations:
            if rec['action'] == 'EXECUTE':
                try:
                    # Here would connect to actual trading API
                    # For now, we'll simulate
                    result = {
                        'recommendation': rec,
                        'status': 'SIMULATED',
                        'order_id': f"SIM_{int(time.time()*1000)}",
                        'timestamp': time.time()
                    }
                    execution_results['executed'].append(result)
                    self.system_state.signals_executed += 1
                    
                except Exception as e:
                    execution_results['errors'].append({
                        'recommendation': rec,
                        'error': str(e)
                    })
            else:
                execution_results['skipped'].append(rec)
        
        # Store execution results
        if self.db:
            await self.db.executions.insert_one(execution_results)
        
        return execution_results
    
    async def monitor_positions(self) -> Dict:
        """
        Monitor all active positions
        """
        monitoring_results = {
            'timestamp': time.time(),
            'positions': [],
            'alerts': [],
            'adjustments': []
        }
        
        # This would connect to actual position tracking
        # For now, return system state
        monitoring_results['system_state'] = asdict(self.system_state)
        
        return monitoring_results
    
    # ==================== Main Run Loop ====================
    
    async def run_continuous(self, symbols: List[str], interval_seconds: int = 300):
        """
        Run continuous analysis on multiple symbols
        """
        logger.info(f"Starting continuous analysis for {symbols}")
        
        while True:
            try:
                for symbol in symbols:
                    # Fetch latest data (would connect to real data source)
                    # For now, using placeholder
                    logger.info(f"Analyzing {symbol}...")
                    
                    # Run analysis
                    # analysis = await self.analyze_market(symbol, ohlcv_data)
                    
                    # Execute if needed
                    # if analysis.get('recommendations'):
                    #     await self.execute_recommendations(analysis['recommendations'])
                    
                    await asyncio.sleep(5)  # Small delay between symbols
                
                # Monitor positions
                await self.monitor_positions()
                
                # Sleep until next interval
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Stopping continuous analysis...")
                break
            except Exception as e:
                logger.error(f"Error in continuous run: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying