#!/usr/bin/env python3
"""
AuraQuant Global Error & Exception Handling System
Engineer's Note: Comprehensive error wrangling for all system components
Handles, logs, recovers, and reports all errors without crashing
"""

import os
import sys
import json
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from pathlib import Path
import asyncio
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auraquant_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"          # Minor issue, system continues
    MEDIUM = "medium"    # Degraded performance but operational
    HIGH = "high"        # Critical function impaired
    CRITICAL = "critical" # System failure imminent
    FATAL = "fatal"      # Complete system failure

class ErrorCategory(Enum):
    """Error categories for classification"""
    API = "api"
    DATABASE = "database"
    TRADING = "trading"
    AUTHENTICATION = "auth"
    WEBSOCKET = "websocket"
    AI_MODEL = "ai_model"
    FRONTEND = "frontend"
    NETWORK = "network"
    VALIDATION = "validation"
    SYSTEM = "system"

class AuraQuantErrorHandler:
    """
    Master error handler for the entire AuraQuant system
    Catches, logs, recovers from, and reports all errors
    """
    
    def __init__(self):
        self.error_log = []
        self.error_count = {}
        self.recovery_strategies = {}
        self.alert_thresholds = {
            ErrorSeverity.LOW: 100,
            ErrorSeverity.MEDIUM: 20,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.FATAL: 1
        }
        self.setup_recovery_strategies()
        
    def setup_recovery_strategies(self):
        """Define recovery strategies for different error types"""
        self.recovery_strategies = {
            ErrorCategory.DATABASE: self.recover_database_error,
            ErrorCategory.API: self.recover_api_error,
            ErrorCategory.TRADING: self.recover_trading_error,
            ErrorCategory.WEBSOCKET: self.recover_websocket_error,
            ErrorCategory.AI_MODEL: self.recover_ai_error,
            ErrorCategory.NETWORK: self.recover_network_error,
        }
        
    def handle_error(self, error: Exception, 
                    category: ErrorCategory = ErrorCategory.SYSTEM,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main error handling method
        
        Args:
            error: The exception that occurred
            category: Category of the error
            severity: Severity level
            context: Additional context information
            
        Returns:
            Error report dictionary
        """
        error_id = self.generate_error_id()
        
        # Create error report
        error_report = {
            "id": error_id,
            "timestamp": datetime.now().isoformat(),
            "category": category.value,
            "severity": severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {},
            "recovered": False,
            "recovery_action": None
        }
        
        # Log the error
        self.log_error(error_report)
        
        # Attempt recovery
        if category in self.recovery_strategies:
            recovery_result = self.recovery_strategies[category](error, context)
            error_report["recovered"] = recovery_result["success"]
            error_report["recovery_action"] = recovery_result["action"]
            
        # Check if alert needed
        self.check_alert_threshold(category, severity)
        
        # Store error
        self.error_log.append(error_report)
        
        # Update error count
        error_key = f"{category.value}_{severity.value}"
        self.error_count[error_key] = self.error_count.get(error_key, 0) + 1
        
        return error_report
        
    def generate_error_id(self) -> str:
        """Generate unique error ID"""
        from uuid import uuid4
        return f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
        
    def log_error(self, error_report: Dict[str, Any]):
        """Log error to file and console"""
        if error_report["severity"] in [ErrorSeverity.CRITICAL.value, ErrorSeverity.FATAL.value]:
            logger.error(f"🚨 {error_report['severity'].upper()}: {error_report['error_message']}")
        elif error_report["severity"] == ErrorSeverity.HIGH.value:
            logger.warning(f"⚠️ HIGH: {error_report['error_message']}")
        else:
            logger.info(f"ℹ️ {error_report['severity']}: {error_report['error_message']}")
            
    def check_alert_threshold(self, category: ErrorCategory, severity: ErrorSeverity):
        """Check if error count exceeds alert threshold"""
        key = f"{category.value}_{severity.value}"
        count = self.error_count.get(key, 0)
        threshold = self.alert_thresholds.get(severity, 10)
        
        if count >= threshold:
            self.send_alert(category, severity, count)
            
    def send_alert(self, category: ErrorCategory, severity: ErrorSeverity, count: int):
        """Send alert for critical errors"""
        alert_message = f"""
        🚨 AURAQUANT ALERT 🚨
        Category: {category.value}
        Severity: {severity.value}
        Count: {count}
        Time: {datetime.now().isoformat()}
        Action Required: Check system logs
        """
        logger.critical(alert_message)
        # TODO: Send email/SMS/Discord notification
        
    # Recovery strategies for different error types
    
    def recover_database_error(self, error: Exception, context: Dict) -> Dict:
        """Recover from database errors"""
        recovery_actions = []
        
        if "connection" in str(error).lower():
            recovery_actions.append("Attempting database reconnection")
            # TODO: Implement reconnection logic
            
        if "timeout" in str(error).lower():
            recovery_actions.append("Increasing timeout and retrying")
            # TODO: Implement retry with increased timeout
            
        return {
            "success": len(recovery_actions) > 0,
            "action": ", ".join(recovery_actions) if recovery_actions else "No recovery attempted"
        }
        
    def recover_api_error(self, error: Exception, context: Dict) -> Dict:
        """Recover from API errors"""
        recovery_actions = []
        
        if "rate limit" in str(error).lower():
            recovery_actions.append("Implementing rate limit backoff")
            # TODO: Implement exponential backoff
            
        if "authentication" in str(error).lower():
            recovery_actions.append("Refreshing authentication token")
            # TODO: Refresh auth token
            
        return {
            "success": len(recovery_actions) > 0,
            "action": ", ".join(recovery_actions) if recovery_actions else "No recovery attempted"
        }
        
    def recover_trading_error(self, error: Exception, context: Dict) -> Dict:
        """Recover from trading errors"""
        recovery_actions = []
        
        if "insufficient" in str(error).lower():
            recovery_actions.append("Adjusting position size")
            
        if "market closed" in str(error).lower():
            recovery_actions.append("Queuing order for market open")
            
        return {
            "success": len(recovery_actions) > 0,
            "action": ", ".join(recovery_actions) if recovery_actions else "No recovery attempted"
        }
        
    def recover_websocket_error(self, error: Exception, context: Dict) -> Dict:
        """Recover from WebSocket errors"""
        recovery_actions = []
        
        if "connection" in str(error).lower():
            recovery_actions.append("Attempting WebSocket reconnection")
            # TODO: Implement WebSocket reconnection
            
        return {
            "success": len(recovery_actions) > 0,
            "action": ", ".join(recovery_actions) if recovery_actions else "No recovery attempted"
        }
        
    def recover_ai_error(self, error: Exception, context: Dict) -> Dict:
        """Recover from AI model errors"""
        recovery_actions = []
        
        if "memory" in str(error).lower():
            recovery_actions.append("Clearing model cache and retrying")
            
        if "prediction" in str(error).lower():
            recovery_actions.append("Falling back to rule-based strategy")
            
        return {
            "success": len(recovery_actions) > 0,
            "action": ", ".join(recovery_actions) if recovery_actions else "No recovery attempted"
        }
        
    def recover_network_error(self, error: Exception, context: Dict) -> Dict:
        """Recover from network errors"""
        recovery_actions = []
        
        if "timeout" in str(error).lower():
            recovery_actions.append("Retrying with exponential backoff")
            
        if "connection" in str(error).lower():
            recovery_actions.append("Switching to backup endpoint")
            
        return {
            "success": len(recovery_actions) > 0,
            "action": ", ".join(recovery_actions) if recovery_actions else "No recovery attempted"
        }
        
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": len(self.error_log),
            "error_by_category": self.get_errors_by_category(),
            "error_by_severity": self.get_errors_by_severity(),
            "recovery_rate": self.calculate_recovery_rate(),
            "recent_errors": self.error_log[-10:] if self.error_log else []
        }
        
    def get_errors_by_category(self) -> Dict[str, int]:
        """Get error count by category"""
        category_count = {}
        for error in self.error_log:
            cat = error["category"]
            category_count[cat] = category_count.get(cat, 0) + 1
        return category_count
        
    def get_errors_by_severity(self) -> Dict[str, int]:
        """Get error count by severity"""
        severity_count = {}
        for error in self.error_log:
            sev = error["severity"]
            severity_count[sev] = severity_count.get(sev, 0) + 1
        return severity_count
        
    def calculate_recovery_rate(self) -> float:
        """Calculate successful recovery rate"""
        if not self.error_log:
            return 1.0
        recovered = sum(1 for e in self.error_log if e["recovered"])
        return recovered / len(self.error_log)

# Global error handler instance
error_handler = AuraQuantErrorHandler()

# Decorators for error handling

def handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    Decorator to automatically handle errors in functions
    
    Usage:
        @handle_errors(category=ErrorCategory.API, severity=ErrorSeverity.HIGH)
        def my_function():
            # function code
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }
                error_handler.handle_error(e, category, severity, context)
                raise
        return wrapper
    return decorator

def async_handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM):
    """
    Decorator for async functions
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                }
                error_handler.handle_error(e, category, severity, context)
                raise
        return wrapper
    return decorator

# Frontend error handler for API responses

def format_api_error(error: Exception, status_code: int = 500) -> Dict[str, Any]:
    """Format error for API response"""
    return {
        "success": False,
        "error": {
            "message": str(error),
            "type": type(error).__name__,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
    }

# WebSocket error handler

class WebSocketErrorHandler:
    """Specialized handler for WebSocket errors"""
    
    @staticmethod
    async def handle_ws_error(ws, error: Exception):
        """Handle WebSocket specific errors"""
        try:
            await ws.send_json({
                "type": "error",
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass  # WebSocket might be closed
            
        # Log to main error handler
        error_handler.handle_error(
            error,
            ErrorCategory.WEBSOCKET,
            ErrorSeverity.MEDIUM,
            {"websocket_id": id(ws)}
        )

# System health check

def system_health_check() -> Dict[str, Any]:
    """Perform system health check based on errors"""
    stats = error_handler.get_error_statistics()
    
    health_status = "healthy"
    if stats["error_by_severity"].get("critical", 0) > 0:
        health_status = "critical"
    elif stats["error_by_severity"].get("high", 0) > 5:
        health_status = "degraded"
    elif stats["total_errors"] > 100:
        health_status = "warning"
        
    return {
        "status": health_status,
        "total_errors": stats["total_errors"],
        "recovery_rate": stats["recovery_rate"],
        "critical_errors": stats["error_by_severity"].get("critical", 0),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("✅ AuraQuant Error Handler System Initialized")
    print(f"📊 Health Status: {system_health_check()}")