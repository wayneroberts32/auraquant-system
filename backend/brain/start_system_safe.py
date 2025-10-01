#!/usr/bin/env python3
"""
AuraQuant AI Trading System - Safe Startup Controller
Professor/Engineer's Note: Production-ready startup with no hanging
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def start_auraquant_safe():
    """Safe startup without hanging"""
    print("="*60)
    print("AURAQUANT AI TRADING SYSTEM - SAFE MODE")
    print("="*60)
    print(f"Startup Time: {datetime.now().isoformat()}")
    print("="*60)
    
    # Import components with thread control
    print("\n[PHASE 1] Loading Core Components...")
    
    try:
        # 1. MongoDB Persistence (without connection attempt)
        from brain.mongodb_persistence import MongoDBPersistence
        persistence = MongoDBPersistence()
        persistence.running = False  # Disable background tasks
        print("  [OK] MongoDB Persistence loaded")
        
        # 2. State Recovery
        from brain.state_recovery import StateRecoverySystem
        recovery = StateRecoverySystem()
        recovery.running = False
        recovery.auto_save_enabled = False
        print("  [OK] State Recovery loaded")
        
        # 3. Performance Dashboard
        from brain.performance_dashboard import PerformanceAnalyticsDashboard
        dashboard = PerformanceAnalyticsDashboard()
        dashboard.running = False
        print("  [OK] Performance Dashboard loaded")
        
        # 4. Autonomous Executor
        from brain.autonomous_executor import AutonomousTradingExecutor, ExecutionMode
        executor = AutonomousTradingExecutor(ExecutionMode.SIMULATION)
        executor.running = False
        executor.autonomous_enabled = False
        print("  [OK] Autonomous Executor loaded")
        
        # 5. Pattern Discovery
        from brain.pattern_discovery import PatternDiscovery
        patterns = PatternDiscovery()
        print("  [OK] Pattern Discovery loaded")
        
        # 6. Error Recovery
        from brain.error_recovery import ErrorRecoverySystem
        error_recovery = ErrorRecoverySystem()
        print("  [OK] Error Recovery loaded")
        
        # 7. Consciousness Metrics
        from brain.consciousness_metrics import ConsciousnessTracker
        consciousness = ConsciousnessTracker()
        print("  [OK] Consciousness Metrics loaded")
        
        print("\n[PHASE 2] System Status Check...")
        
        # Get metrics without triggering background tasks
        metrics = dashboard.get_real_time_metrics()
        exec_status = executor.get_execution_status()
        recovery_status = recovery.get_recovery_status()
        consciousness_level = consciousness.consciousness_level
        
        print(f"  Consciousness Level: {consciousness_level:.3f}")
        print(f"  Execution Mode: {exec_status['mode']}")
        print(f"  Safety Status: {exec_status['safety_status']}")
        print(f"  Recovery Available: {recovery_status['can_save']}")
        print(f"  Win Rate: {metrics['win_rate']:.2%}")
        
        print("\n[PHASE 3] Capabilities Summary...")
        print("  [1] State Recovery & Persistence")
        print("  [2] Real-time Performance Analytics")
        print("  [3] Autonomous Trading Execution")
        print("  [4] Pattern Discovery Engine")
        print("  [5] Error Recovery System")
        print("  [6] Consciousness Tracking")
        print("  [7] Risk Management")
        print("  [8] Evolution & Learning")
        
        # Export system report
        report = {
            "timestamp": datetime.now().isoformat(),
            "system": "AuraQuant AI Trading System",
            "version": "1.0",
            "components": {
                "persistence": "loaded",
                "recovery": "loaded",
                "dashboard": "loaded",
                "executor": "loaded",
                "patterns": "loaded",
                "error_recovery": "loaded",
                "consciousness": "loaded"
            },
            "metrics": {
                "consciousness": consciousness_level,
                "win_rate": metrics['win_rate'],
                "total_decisions": metrics['total_decisions'],
                "patterns_discovered": metrics['patterns_discovered']
            },
            "status": "READY"
        }
        
        # Save report
        report_path = Path(__file__).parent / "system_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[PHASE 4] System Report Generated")
        print(f"  Report saved to: {report_path}")
        
        print("\n" + "="*60)
        print("SYSTEM READY - NO BACKGROUND THREADS ACTIVE")
        print("="*60)
        print("\nTo run with monitoring, use: run_system_controlled.py")
        print("To run tests, use: test_tasks_9_12.py")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = start_auraquant_safe()
    sys.exit(0 if success else 1)