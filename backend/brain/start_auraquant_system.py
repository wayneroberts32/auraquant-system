"""
AuraQuant AI Trading System - Complete Startup Script
Professor/Engineer's Note: Automated system initialization and monitoring
"""

import os
import sys
import time
import subprocess
import platform
from pathlib import Path

# Disable emojis on Windows to avoid encoding issues
USE_EMOJIS = platform.system() != 'Windows'

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

def check_mongodb():
    """Check if MongoDB is running"""
    try:
        # Try to connect to MongoDB
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        print("[OK] MongoDB is running" if not USE_EMOJIS else "âœ… MongoDB is running")
        return True
    except Exception as e:
        print(f"[ERROR] MongoDB is not running: {e}" if not USE_EMOJIS else f"âŒ MongoDB is not running: {e}")
        return False

def start_mongodb_windows():
    """Start MongoDB on Windows"""
    print("[>>] Attempting to start MongoDB..." if not USE_EMOJIS else "ðŸš€ Attempting to start MongoDB...")
    
    # Common MongoDB paths on Windows
    mongo_paths = [
        r"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe",
        r"C:\mongodb\bin\mongod.exe",
    ]
    
    # Check if mongod is in PATH
    try:
        result = subprocess.run(['where', 'mongod'], capture_output=True, text=True)
        if result.returncode == 0:
            mongo_paths.insert(0, 'mongod')
    except:
        pass
    
    # Try to start MongoDB
    for mongo_path in mongo_paths:
        if os.path.exists(mongo_path) or mongo_path == 'mongod':
            try:
                # Create data directory if it doesn't exist
                data_dir = r"D:\New AuraQuant\mongodb_data"
                os.makedirs(data_dir, exist_ok=True)
                
                # Start MongoDB
                if mongo_path == 'mongod':
                    cmd = f'mongod --dbpath "{data_dir}" --port 27017'
                else:
                    cmd = f'"{mongo_path}" --dbpath "{data_dir}" --port 27017'
                
                # Start in background
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[DIR] MongoDB starting with data directory: {data_dir}" if not USE_EMOJIS else f"ðŸ“‚ MongoDB starting with data directory: {data_dir}")
                
                # Wait for MongoDB to start
                time.sleep(5)
                
                if check_mongodb():
                    return True
                    
            except Exception as e:
                print(f"Failed to start with {mongo_path}: {e}")
                continue
    
    return False

def start_auraquant_system():
    """Start the complete AuraQuant system"""
    print("="*60)
    print("*** AuraQuant AI Trading System - Automated Startup ***" if not USE_EMOJIS else "ðŸŒŸ AuraQuant AI Trading System - Automated Startup")
    print("ðŸ’¼ Professor/Engineer's Complete System Initialization")
    print("="*60)
    
    # Step 1: Check/Start MongoDB
    print("\nðŸ“‹ Step 1: Checking MongoDB...")
    if not check_mongodb():
        print("MongoDB not running, attempting to start...")
        if platform.system() == 'Windows':
            if not start_mongodb_windows():
                print("\nâš ï¸ WARNING: MongoDB could not be started automatically.")
                print("Please start MongoDB manually:")
                print("  1. Open a new terminal")
                print("  2. Run: mongod --dbpath D:\\New AuraQuant\\mongodb_data")
                print("\nSystem will continue with limited functionality...")
                time.sleep(3)
        else:
            print("Please start MongoDB manually on your system")
            
    # Step 2: Initialize System Orchestrator
    print("\nðŸ“‹ Step 2: Initializing System Orchestrator...")
    try:
        from brain.system_orchestrator import get_system_orchestrator
        orchestrator = get_system_orchestrator()
        print("âœ… System Orchestrator initialized")
        
        # Get initial status
        status = orchestrator.get_system_status()
        print(f"\nðŸ“Š System Status:")
        print(f"  State: {status['state']}")
        print(f"  Mode: {status['integration_mode']}")
        print(f"  Components: {len(status['components'])} loaded")
        
        # Show component status
        print("\nðŸ”§ Component Status:")
        for name, comp_status in status['components'].items():
            status_icon = "âœ…" if comp_status['status'] == 'active' else "âŒ"
            print(f"  {status_icon} {name}: {comp_status['status']}")
            
    except Exception as e:
        print(f"âŒ Failed to initialize System Orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    # Step 3: Enable Autonomous Mode (with user confirmation)
    print("\nðŸ“‹ Step 3: Autonomous Mode Configuration...")
    print("âš ï¸ Autonomous Mode will enable:")
    print("  - Self-learning from market patterns")
    print("  - Automatic strategy evolution")
    print("  - Simulated trading execution")
    print("\nWould you like to enable Autonomous Mode? (y/n): ", end="")
    
    # Auto-enable for now (you can change this)
    enable_auto = True  # Set to False if you want manual confirmation
    
    if enable_auto:
        print("y (auto-enabled)")
        try:
            orchestrator.enable_autonomous_mode()
            print("âœ… Autonomous Mode ENABLED")
        except Exception as e:
            print(f"âš ï¸ Could not enable autonomous mode: {e}")
    else:
        print("n (skipped)")
        print("â„¹ï¸ System running in orchestrated mode")
        
    # Step 4: Start Performance Monitoring
    print("\nðŸ“‹ Step 4: Starting Performance Dashboard...")
    try:
        from brain.performance_dashboard import get_performance_dashboard
        dashboard = get_performance_dashboard()
        
        # Get initial metrics
        metrics = dashboard.get_real_time_metrics()
        
        print("âœ… Performance Dashboard Active")
        print("\nðŸ“ˆ Real-Time Metrics:")
        print(f"  Generation: {metrics['current_generation']}")
        print(f"  Consciousness Level: {metrics['consciousness_level']:.3f}")
        print(f"  Learning Rate: {metrics['learning_rate']:.4f}")
        print(f"  Win Rate: {metrics['win_rate']:.2%}")
        print(f"  Total P&L: ${metrics['total_pnl']:.2f}")
        print(f"  Active Positions: {metrics['active_positions']}")
        print(f"  Memory Usage: {metrics['memory_usage']:.2f} MB")
        print(f"  Patterns Discovered: {metrics['patterns_discovered']}")
        
        # API endpoints
        print("\nðŸŒ Dashboard API Endpoints Available:")
        print("  http://localhost:8000/api/dashboard/realtime")
        print("  http://localhost:8000/api/dashboard/comprehensive")
        print("  http://localhost:8000/api/dashboard/evolution")
        print("  http://localhost:8000/api/dashboard/strategies")
        
    except Exception as e:
        print(f"âš ï¸ Dashboard initialization warning: {e}")
        
    # System is running
    print("\n" + "="*60)
    print("ðŸš€ AURAQUANT SYSTEM IS NOW OPERATIONAL!")
    print("="*60)
    
    print("\nðŸ’¡ System Commands:")
    print("  Press Ctrl+C to stop the system")
    print("  System is continuously:")
    print("    - Learning from patterns")
    print("    - Evolving strategies")
    print("    - Monitoring performance")
    print("    - Recovering from errors")
    
    # Monitor system
    print("\nðŸ“Š Live System Monitor (updates every 10 seconds):")
    print("-" * 50)
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Get current status
            current_status = orchestrator.get_system_status()
            
            # Get performance metrics
            if 'performance_dashboard' in orchestrator.components:
                perf_metrics = dashboard.get_real_time_metrics()
                
                # Display live updates
                print(f"\r[{iteration:04d}] State: {current_status['state']:12} | "
                      f"Gen: {perf_metrics['current_generation']:3} | "
                      f"Decisions: {perf_metrics['total_decisions']:5} | "
                      f"Patterns: {perf_metrics['patterns_discovered']:4} | "
                      f"Win Rate: {perf_metrics['win_rate']:6.2%} | "
                      f"P&L: ${perf_metrics['total_pnl']:8.2f}", end="")
                      
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\nâŒ¨ï¸ Shutdown signal received...")
        print("ðŸ“´ Initiating graceful shutdown...")
        
        # Shutdown system
        orchestrator.shutdown()
        
        print("\nâœ… System shutdown complete")
        print("Thank you for using AuraQuant AI Trading System!")
        
    return True

if __name__ == "__main__":
    # Run the startup sequence
    success = start_auraquant_system()
    
    if not success:
        print("\nâŒ System startup failed")
        sys.exit(1)

