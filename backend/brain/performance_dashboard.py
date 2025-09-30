"""
Performance Analytics Dashboard for AuraQuant Trading System
Professor/Engineer's Note: Real-time analytics and visualization APIs
WITHOUT modifying existing code - Task 10/12
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import asyncio
import threading
from collections import deque

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from brain.mongodb_persistence import get_persistence_service
from brain.evolution_monitor import get_evolution_monitor
from brain.learning_feedback import get_learning_feedback
from brain.decision_logger import get_decision_logger
from brain.memory_sync import get_memory_synchronizer

class PerformanceAnalyticsDashboard:
    """
    Comprehensive performance analytics with real-time updates
    Provides MongoDB aggregation pipelines and API endpoints
    """
    
    def __init__(self):
        """Initialize performance analytics dashboard"""
        # MongoDB persistence
        self.persistence = get_persistence_service()
        
        # Component references
        self.evolution_monitor = get_evolution_monitor()
        self.learning_feedback = get_learning_feedback()
        self.decision_logger = get_decision_logger()
        self.memory_sync = get_memory_synchronizer()
        
        # Analytics cache
        self.analytics_cache = {}
        self.cache_ttl = 60  # Cache for 60 seconds
        self.last_cache_update = {}
        
        # Real-time metrics
        self.real_time_metrics = {
            'current_generation': 1,
            'total_decisions': 0,
            'win_rate': 0,
            'consciousness_level': 0.5,
            'learning_rate': 0.001,
            'total_pnl': 0,
            'active_positions': 0,
            'risk_score': 0,
            'memory_usage': 0,
            'patterns_discovered': 0
        }
        
        # WebSocket connections for real-time updates
        self.websocket_connections = []
        
        # Aggregation pipelines
        self.aggregation_pipelines = self._init_aggregation_pipelines()
        
        # Background update thread
        self.update_thread = None
        self.running = True
        
        print("📊 Performance Analytics Dashboard Initialized")
        self._start_real_time_updates()
        
    def _init_aggregation_pipelines(self) -> Dict[str, List[Dict]]:
        """Initialize MongoDB aggregation pipelines"""
        pipelines = {
            'learning_curve': [
                {
                    '$match': {
                        'timestamp': {'$gte': datetime.now() - timedelta(days=30)}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': '$timestamp'
                            }
                        },
                        'avg_fitness': {'$avg': '$fitness_score'},
                        'avg_win_rate': {'$avg': '$win_rate'},
                        'total_trades': {'$sum': '$total_trades'}
                    }
                },
                {'$sort': {'_id': 1}}
            ],
            
            'strategy_performance': [
                {
                    '$match': {
                        'timestamp': {'$gte': datetime.now() - timedelta(days=7)}
                    }
                },
                {
                    '$group': {
                        '_id': '$strategy_name',
                        'avg_effectiveness': {'$avg': '$effectiveness'},
                        'total_trades': {'$sum': '$total_trades'},
                        'last_update': {'$max': '$timestamp'}
                    }
                },
                {'$sort': {'avg_effectiveness': -1}}
            ],
            
            'memory_utilization': [
                {
                    '$facet': {
                        'by_type': [
                            {
                                '$group': {
                                    '_id': '$memory_type',
                                    'count': {'$sum': 1},
                                    'avg_importance': {'$avg': '$importance'}
                                }
                            }
                        ],
                        'by_date': [
                            {
                                '$group': {
                                    '_id': {
                                        '$dateToString': {
                                            'format': '%Y-%m-%d',
                                            'date': '$timestamp'
                                        }
                                    },
                                    'count': {'$sum': 1}
                                }
                            },
                            {'$sort': {'_id': 1}},
                            {'$limit': 7}
                        ]
                    }
                }
            ],
            
            'evolution_progress': [
                {
                    '$match': {
                        'generation': {'$exists': True}
                    }
                },
                {
                    '$group': {
                        '_id': '$generation',
                        'fitness': {'$avg': '$fitness_score'},
                        'consciousness': {'$avg': '$consciousness_level'},
                        'patterns': {'$sum': '$patterns_discovered'}
                    }
                },
                {'$sort': {'_id': 1}},
                {'$limit': 100}
            ],
            
            'risk_analysis': [
                {
                    '$match': {
                        'risk_score': {'$exists': True}
                    }
                },
                {
                    '$bucket': {
                        'groupBy': '$risk_score',
                        'boundaries': [0, 0.2, 0.4, 0.6, 0.8, 1.0],
                        'default': 'other',
                        'output': {
                            'count': {'$sum': 1},
                            'avg_pnl': {'$avg': '$pnl'}
                        }
                    }
                }
            ],
            
            'pattern_discovery': [
                {
                    '$match': {
                        'success_rate': {'$gt': 0}
                    }
                },
                {
                    '$group': {
                        '_id': '$pattern_type',
                        'avg_success_rate': {'$avg': '$success_rate'},
                        'total_occurrences': {'$sum': '$occurrences'},
                        'top_patterns': {
                            '$push': {
                                'pattern_id': '$pattern_id',
                                'success_rate': '$success_rate'
                            }
                        }
                    }
                },
                {
                    '$project': {
                        'avg_success_rate': 1,
                        'total_occurrences': 1,
                        'top_patterns': {'$slice': ['$top_patterns', 5]}
                    }
                }
            ],
            
            'hourly_performance': [
                {
                    '$match': {
                        'timestamp': {
                            '$gte': datetime.now() - timedelta(hours=24)
                        }
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d %H:00',
                                'date': '$timestamp'
                            }
                        },
                        'decisions': {'$sum': 1},
                        'successful': {
                            '$sum': {
                                '$cond': [{'$gt': ['$outcome', 0]}, 1, 0]
                            }
                        },
                        'total_pnl': {'$sum': '$pnl'}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
        }
        
        return pipelines
        
    def _start_real_time_updates(self):
        """Start real-time metrics updates"""
        self.update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self.update_thread.start()
        print("🔄 Real-time updates started")
        
    def _update_loop(self):
        """Background loop for real-time updates"""
        while self.running:
            try:
                # Update real-time metrics
                self._update_real_time_metrics()
                
                # Broadcast to WebSocket connections
                self._broadcast_updates()
                
                import time
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Error in update loop: {e}")
                import time
                time.sleep(10)
                
    def _update_real_time_metrics(self):
        """Update real-time metrics"""
        # Evolution metrics
        if self.evolution_monitor:
            summary = self.evolution_monitor.get_evolution_summary()
            self.real_time_metrics['current_generation'] = summary.get('current_generation', 1)
            self.real_time_metrics['patterns_discovered'] = summary.get('total_patterns_discovered', 0)
            
        # Learning metrics
        if self.learning_feedback:
            learning = self.learning_feedback.get_learning_metrics()
            self.real_time_metrics['consciousness_level'] = learning.get('consciousness_level', 0.5)
            self.real_time_metrics['learning_rate'] = learning.get('learning_rate', 0.001)
            
        # Trading metrics
        if self.decision_logger:
            trading = self.decision_logger.get_statistics()
            self.real_time_metrics['total_decisions'] = trading.get('total', 0)
            self.real_time_metrics['total_pnl'] = trading.get('total_pnl', 0)
            self.real_time_metrics['active_positions'] = trading.get('pending', 0)
            
            # Calculate win rate
            successful = trading.get('successful', 0)
            failed = trading.get('failed', 0)
            total_completed = successful + failed
            if total_completed > 0:
                self.real_time_metrics['win_rate'] = successful / total_completed
                
        # Memory metrics
        if self.memory_sync:
            sync_status = self.memory_sync.get_sync_status()
            stats = sync_status.get('stats', {})
            self.real_time_metrics['memory_usage'] = stats.get('data_volume_mb', 0)
            
    def get_learning_curve(self, days: int = 30) -> List[Dict]:
        """
        Get learning curve data
        
        Args:
            days: Number of days to look back
            
        Returns:
            Learning curve data points
        """
        cache_key = f'learning_curve_{days}'
        
        # Check cache
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        # Run aggregation
        if self.persistence and self.persistence.db:
            try:
                pipeline = self.aggregation_pipelines['learning_curve'].copy()
                pipeline[0]['$match']['timestamp']['$gte'] = datetime.now() - timedelta(days=days)
                
                result = list(self.persistence.db.evolution_metrics.aggregate(pipeline))
                
                # Cache result
                self._cache_result(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error getting learning curve: {e}")
                
        return []
        
    def get_strategy_performance(self) -> List[Dict]:
        """Get strategy performance metrics"""
        cache_key = 'strategy_performance'
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        if self.persistence and self.persistence.db:
            try:
                result = list(self.persistence.db.strategy_performance.aggregate(
                    self.aggregation_pipelines['strategy_performance']
                ))
                
                self._cache_result(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error getting strategy performance: {e}")
                
        return []
        
    def get_memory_utilization(self) -> Dict[str, List]:
        """Get memory utilization statistics"""
        cache_key = 'memory_utilization'
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        if self.persistence and self.persistence.db:
            try:
                result = list(self.persistence.db.brain_memories.aggregate(
                    self.aggregation_pipelines['memory_utilization']
                ))
                
                if result:
                    data = result[0]
                    self._cache_result(cache_key, data)
                    return data
                    
            except Exception as e:
                print(f"Error getting memory utilization: {e}")
                
        return {'by_type': [], 'by_date': []}
        
    def get_evolution_progress(self) -> List[Dict]:
        """Get evolution progress over generations"""
        cache_key = 'evolution_progress'
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        if self.persistence and self.persistence.db:
            try:
                result = list(self.persistence.db.evolution_metrics.aggregate(
                    self.aggregation_pipelines['evolution_progress']
                ))
                
                self._cache_result(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error getting evolution progress: {e}")
                
        return []
        
    def get_risk_analysis(self) -> List[Dict]:
        """Get risk analysis breakdown"""
        cache_key = 'risk_analysis'
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        if self.persistence and self.persistence.db:
            try:
                result = list(self.persistence.db.risk_assessments.aggregate(
                    self.aggregation_pipelines['risk_analysis']
                ))
                
                self._cache_result(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error getting risk analysis: {e}")
                
        return []
        
    def get_pattern_discovery_stats(self) -> List[Dict]:
        """Get pattern discovery statistics"""
        cache_key = 'pattern_discovery'
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        if self.persistence and self.persistence.db:
            try:
                result = list(self.persistence.db.discovered_patterns.aggregate(
                    self.aggregation_pipelines['pattern_discovery']
                ))
                
                self._cache_result(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error getting pattern discovery: {e}")
                
        return []
        
    def get_hourly_performance(self) -> List[Dict]:
        """Get hourly performance for last 24 hours"""
        cache_key = 'hourly_performance'
        
        if self._is_cache_valid(cache_key):
            return self.analytics_cache[cache_key]
            
        if self.persistence and self.persistence.db:
            try:
                result = list(self.persistence.db.trading_decisions.aggregate(
                    self.aggregation_pipelines['hourly_performance']
                ))
                
                self._cache_result(cache_key, result)
                return result
                
            except Exception as e:
                print(f"Error getting hourly performance: {e}")
                
        return []
        
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        return self.real_time_metrics.copy()
        
    def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Get all dashboard data in one call"""
        return {
            'real_time': self.get_real_time_metrics(),
            'learning_curve': self.get_learning_curve(7),
            'strategy_performance': self.get_strategy_performance(),
            'memory_utilization': self.get_memory_utilization(),
            'evolution_progress': self.get_evolution_progress()[:20],  # Last 20 generations
            'risk_analysis': self.get_risk_analysis(),
            'pattern_discovery': self.get_pattern_discovery_stats(),
            'hourly_performance': self.get_hourly_performance(),
            'timestamp': datetime.now().isoformat()
        }
        
    def create_api_endpoints(self):
        """
        Create FastAPI endpoints for dashboard
        This would be integrated with your existing API
        """
        endpoints = {
            '/api/dashboard/realtime': {
                'method': 'GET',
                'handler': self.get_real_time_metrics,
                'description': 'Get real-time metrics'
            },
            '/api/dashboard/learning-curve': {
                'method': 'GET',
                'handler': self.get_learning_curve,
                'params': ['days'],
                'description': 'Get learning curve data'
            },
            '/api/dashboard/strategies': {
                'method': 'GET',
                'handler': self.get_strategy_performance,
                'description': 'Get strategy performance'
            },
            '/api/dashboard/memory': {
                'method': 'GET',
                'handler': self.get_memory_utilization,
                'description': 'Get memory utilization'
            },
            '/api/dashboard/evolution': {
                'method': 'GET',
                'handler': self.get_evolution_progress,
                'description': 'Get evolution progress'
            },
            '/api/dashboard/risk': {
                'method': 'GET',
                'handler': self.get_risk_analysis,
                'description': 'Get risk analysis'
            },
            '/api/dashboard/patterns': {
                'method': 'GET',
                'handler': self.get_pattern_discovery_stats,
                'description': 'Get pattern discovery stats'
            },
            '/api/dashboard/hourly': {
                'method': 'GET',
                'handler': self.get_hourly_performance,
                'description': 'Get hourly performance'
            },
            '/api/dashboard/comprehensive': {
                'method': 'GET',
                'handler': self.get_comprehensive_dashboard,
                'description': 'Get all dashboard data'
            },
            '/api/dashboard/websocket': {
                'method': 'WEBSOCKET',
                'handler': self.handle_websocket,
                'description': 'WebSocket for real-time updates'
            }
        }
        
        return endpoints
        
    async def handle_websocket(self, websocket):
        """
        Handle WebSocket connection for real-time updates
        
        Args:
            websocket: WebSocket connection
        """
        # Add connection
        self.websocket_connections.append(websocket)
        
        try:
            # Send initial data
            await websocket.send_json({
                'type': 'initial',
                'data': self.get_real_time_metrics()
            })
            
            # Keep connection alive
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"WebSocket error: {e}")
            
        finally:
            # Remove connection
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
                
    def _broadcast_updates(self):
        """Broadcast updates to all WebSocket connections"""
        if not self.websocket_connections:
            return
            
        update_data = {
            'type': 'update',
            'data': self.get_real_time_metrics(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to all connections
        for websocket in self.websocket_connections[:]:
            try:
                asyncio.create_task(websocket.send_json(update_data))
            except:
                # Remove dead connections
                self.websocket_connections.remove(websocket)
                
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.analytics_cache:
            return False
            
        if cache_key not in self.last_cache_update:
            return False
            
        age = (datetime.now() - self.last_cache_update[cache_key]).seconds
        return age < self.cache_ttl
        
    def _cache_result(self, cache_key: str, data: Any):
        """Cache analytics result"""
        self.analytics_cache[cache_key] = data
        self.last_cache_update[cache_key] = datetime.now()
        
    def export_analytics_report(self, format: str = 'json') -> str:
        """
        Export comprehensive analytics report
        
        Args:
            format: Export format (json, csv, html)
            
        Returns:
            Exported data as string
        """
        data = self.get_comprehensive_dashboard()
        
        if format == 'json':
            return json.dumps(data, indent=2, default=str)
            
        elif format == 'html':
            # Generate HTML report
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>AuraQuant Performance Report</title>
                <style>
                    body {{ font-family: Arial; margin: 20px; }}
                    .metric {{ padding: 10px; margin: 5px; background: #f0f0f0; }}
                    .chart {{ width: 100%; height: 300px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1>AuraQuant Trading System Performance Report</h1>
                <h2>Generated: {datetime.now().isoformat()}</h2>
                
                <div class="section">
                    <h3>Real-Time Metrics</h3>
                    <div class="metric">Generation: {data['real_time']['current_generation']}</div>
                    <div class="metric">Win Rate: {data['real_time']['win_rate']:.2%}</div>
                    <div class="metric">Total P&L: ${data['real_time']['total_pnl']:.2f}</div>
                    <div class="metric">Consciousness: {data['real_time']['consciousness_level']:.3f}</div>
                </div>
                
                <div class="section">
                    <h3>Strategy Performance</h3>
                    {self._format_strategy_table(data['strategy_performance'])}
                </div>
                
                <script>
                    // Add charts using Chart.js or similar
                </script>
            </body>
            </html>
            """
            return html
            
        return json.dumps(data, default=str)
        
    def _format_strategy_table(self, strategies: List[Dict]) -> str:
        """Format strategy data as HTML table"""
        if not strategies:
            return "<p>No strategy data available</p>"
            
        html = "<table border='1'><tr><th>Strategy</th><th>Effectiveness</th><th>Trades</th></tr>"
        for strategy in strategies:
            html += f"<tr><td>{strategy['_id']}</td>"
            html += f"<td>{strategy['avg_effectiveness']:.2%}</td>"
            html += f"<td>{strategy['total_trades']}</td></tr>"
        html += "</table>"
        
        return html
        
    def shutdown(self):
        """Graceful shutdown"""
        print("Shutting down Performance Dashboard...")
        self.running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=5)
            
        print("✅ Performance Dashboard shutdown complete")


# Global instance
_dashboard = None

def get_performance_dashboard():
    """Get or create performance dashboard"""
    global _dashboard
    if _dashboard is None:
        _dashboard = PerformanceAnalyticsDashboard()
    return _dashboard

# Helper functions for API integration
def get_real_time_metrics():
    """Get real-time metrics"""
    dashboard = get_performance_dashboard()
    return dashboard.get_real_time_metrics()

def get_comprehensive_dashboard():
    """Get comprehensive dashboard data"""
    dashboard = get_performance_dashboard()
    return dashboard.get_comprehensive_dashboard()

def export_report(format: str = 'json'):
    """Export analytics report"""
    dashboard = get_performance_dashboard()
    return dashboard.export_analytics_report(format)

def get_api_endpoints():
    """Get API endpoint definitions"""
    dashboard = get_performance_dashboard()
    return dashboard.create_api_endpoints()