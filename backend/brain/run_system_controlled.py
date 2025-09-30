"""
AuraQuant AI Trading System - Controlled Startup
Professor/Engineer's Note: Runs the complete system WITHOUT hanging
Provides interactive control and monitoring
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
import signal

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Global control flag
SYSTEM_RUNNING = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global SYSTEM_RUNNING
    print("\n[!] Shutdown signal received...")
    SYSTEM_RUNNING = False

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

class ControlledAuraQuantSystem:
    """
    Controlled system runner that prevents hanging
    """
    
    def __init__(self):
        self.mongodb_process = None
        self.orchestrator = None
        self.dashboard = None
        self.components_loaded = False
        self.monitoring_active = False
        
    def start_mongodb(self):
        """Start MongoDB if not running"""
        print("\n[1/4] Checking MongoDB...")
        
        try:
            from pymongo import MongoClient
            client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
            client.server_info()
            print("[OK] MongoDB is already running")
            return True
        except:
            print("[!] MongoDB not running, attempting to start...")
            
        # Try to start MongoDB
        mongo_paths = [
            r"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
            r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe",
            r"C:\Program Files\MongoDB\Server\5.0\bin\mongod.exe",
            r"C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe",
            "mongod"  # If in PATH
        ]
        
        data_dir = r"D:\New AuraQuant\mongodb_data"
        os.makedirs(data_dir, exist_ok=True)
        
        for mongo_path in mongo_paths:
            try:
                if mongo_path == "mongod" or os.path.exists(mongo_path):
                    cmd = f'"{mongo_path}" --dbpath "{data_dir}" --port 27017' if mongo_path != "mongod" else f'mongod --dbpath "{data_dir}" --port 27017'
                    
                    # Start MongoDB in background
                    self.mongodb_process = subprocess.Popen(
                        cmd, 
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    
                    print(f"[*] MongoDB starting with data directory: {data_dir}")
                    time.sleep(5)  # Wait for MongoDB to start
                    
                    # Verify it started
                    try:
                        from pymongo import MongoClient
                        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
                        client.server_info()
                        print("[OK] MongoDB started successfully")
                        return True
                    except:
                        continue
            except:
                continue
                
        print("[WARNING] Could not start MongoDB automatically")
        print("Please start MongoDB manually: mongod --dbpath \"D:\\New AuraQuant\\mongodb_data\"")
        return False
        
    def initialize_orchestrator(self):
        """Initialize system orchestrator with controlled threading"""
        print("\n[2/4] Initializing System Orchestrator...")
        
        try:
            from brain.system_orchestrator import SystemIntegrationOrchestrator
            
            # Create orchestrator with auto-start disabled
            self.orchestrator = SystemIntegrationOrchestrator()
            
            # Disable automatic background threads
            self.orchestrator.config['auto_start'] = False
            self.orchestrator.orchestration_enabled = False
            self.orchestrator.running = False
            
            # Manually load components
            print("[*] Loading components (background threads disabled)...")
            
            # Check component status
            status = self.orchestrator.get_system_status()
            print(f"[OK] System State: {status['state']}")
            print(f"[OK] Components Loaded: {len(status['components'])}")
            
            # Show component status
            active_count = 0
            for name, comp_status in status['components'].items():
                if comp_status['status'] == 'active':
                    active_count += 1
                    
            print(f"[OK] Active Components: {active_count}/{len(status['components'])}")
            
            self.components_loaded = True
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize orchestrator: {e}")
            return False
            
    def setup_dashboard(self):
        """Setup performance dashboard without background threads"""
        print("\n[3/4] Setting up Performance Dashboard...")
        
        try:
            from brain.performance_dashboard import PerformanceAnalyticsDashboard
            
            # Create dashboard with background threads disabled
            self.dashboard = PerformanceAnalyticsDashboard()
            self.dashboard.running = False  # Disable background updates
            
            # Get initial metrics
            metrics = self.dashboard.get_real_time_metrics()
            
            print("[OK] Dashboard initialized")
            print(f"    Win Rate: {metrics['win_rate']:.2%}")
            print(f"    Consciousness: {metrics['consciousness_level']:.3f}")
            print(f"    Patterns: {metrics['patterns_discovered']}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to setup dashboard: {e}")
            return False
            
    def start_controlled_monitoring(self):
        """Start controlled monitoring that won't hang"""
        print("\n[4/4] Starting Controlled Monitoring...")
        
        def monitor_loop():
            """Controlled monitoring loop"""
            iteration = 0
            
            while SYSTEM_RUNNING and self.monitoring_active:
                try:
                    iteration += 1
                    
                    # Get system status
                    if self.orchestrator:
                        status = self.orchestrator.get_system_status()
                        
                        # Get performance metrics
                        if self.dashboard:
                            metrics = self.dashboard.get_real_time_metrics()
                            
                            # Print status line (overwrite previous)
                            print(f"\r[{iteration:04d}] State: {status['state']:12} | "
                                  f"Gen: {metrics['current_generation']:3} | "
                                  f"Decisions: {metrics['total_decisions']:5} | "
                                  f"Patterns: {metrics['patterns_discovered']:4} | "
                                  f"Win Rate: {metrics['win_rate']:6.2%} | "
                                  f"Consciousness: {metrics['consciousness_level']:.3f}", 
                                  end="", flush=True)
                    
                    # Controlled sleep
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"\n[ERROR] Monitor error: {e}")
                    time.sleep(10)
                    
        # Start monitoring in a separate thread
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        print("[OK] Monitoring started (updates every 5 seconds)")
        print("\n" + "="*60)
        print("SYSTEM CONTROL PANEL")
        print("="*60)
        
        return True
        
    def enable_evolution(self):
        """Enable controlled evolution"""
        if self.orchestrator and 'evolution_monitor' in self.orchestrator.components:
            print("\n[*] Enabling Evolution...")
            
            # Trigger one evolution cycle
            evolution = self.orchestrator.components['evolution_monitor']
            generation = evolution.trigger_evolution_cycle()
            print(f"[OK] Evolution enabled - Generation {generation}")
            
            return True
        return False
        
    def enable_learning(self):
        """Enable controlled learning"""
        if self.orchestrator and 'learning_feedback' in self.orchestrator.components:
            print("\n[*] Enabling Learning...")
            
            learning = self.orchestrator.components['learning_feedback']
            metrics = learning.get_learning_metrics()
            print(f"[OK] Learning enabled - Consciousness: {metrics['consciousness_level']:.3f}")
            
            return True
        return False
        
    def process_command(self, command):
        """Process user commands"""
        command = command.lower().strip()
        
        if command == 'help':
            print("\nAvailable Commands:")
            print("  status    - Show system status")
            print("  evolve    - Trigger evolution cycle")
            print("  learn     - Enable learning")
            print("  metrics   - Show performance metrics")
            print("  auto      - Enable autonomous mode (careful!)")
            print("  stop      - Stop monitoring")
            print("  quit      - Shutdown system")
            print("  help      - Show this help")
            
        elif command == 'status':
            if self.orchestrator:
                status = self.orchestrator.get_system_status()
                print(f"\nSystem Status:")
                print(f"  State: {status['state']}")
                print(f"  Mode: {status['integration_mode']}")
                print(f"  Components: {len(status['components'])}")
                print(f"  Uptime: {status['metrics']['uptime']:.0f} seconds")
                
        elif command == 'evolve':
            self.enable_evolution()
            
        elif command == 'learn':
            self.enable_learning()
            
        elif command == 'metrics':
            if self.dashboard:
                metrics = self.dashboard.get_real_time_metrics()
                print(f"\nPerformance Metrics:")
                print(f"  Generation: {metrics['current_generation']}")
                print(f"  Win Rate: {metrics['win_rate']:.2%}")
                print(f"  Consciousness: {metrics['consciousness_level']:.3f}")
                print(f"  Total Decisions: {metrics['total_decisions']}")
                print(f"  Patterns Found: {metrics['patterns_discovered']}")
                print(f"  Risk Score: {metrics['risk_score']:.3f}")
                
        elif command == 'auto':
            print("\n[WARNING] Autonomous mode will enable automatic trading!")
            confirm = input("Are you sure? (yes/no): ").lower()
            if confirm == 'yes':
                if self.orchestrator:
                    self.orchestrator.config['enable_learning'] = True
                    self.orchestrator.config['enable_evolution'] = True
                    print("[OK] Autonomous features enabled (trading still in simulation)")
                    
        elif command == 'stop':
            self.monitoring_active = False
            print("\n[OK] Monitoring stopped")
            
        elif command in ['quit', 'exit']:
            return False
            
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")
            
        return True
        
    def run(self):
        """Main run method"""
        print("="*60)
        print("AURAQUANT AI TRADING SYSTEM - CONTROLLED STARTUP")
        print("="*60)
        
        # Step 1: Start MongoDB
        mongodb_ok = self.start_mongodb()
        
        # Step 2: Initialize Orchestrator
        if not self.initialize_orchestrator():
            print("\n[ERROR] Failed to initialize system")
            return
            
        # Step 3: Setup Dashboard
        self.setup_dashboard()
        
        # Step 4: Start Monitoring
        self.start_controlled_monitoring()
        
        # Interactive command loop
        print("\nType 'help' for available commands")
        print("Press Ctrl+C or type 'quit' to shutdown\n")
        
        try:
            while SYSTEM_RUNNING:
                try:
                    command = input("\nAuraQuant> ")
                    if not self.process_command(command):
                        break
                except EOFError:
                    break
                except KeyboardInterrupt:
                    break
                    
        except Exception as e:
            print(f"\n[ERROR] System error: {e}")
            
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Graceful shutdown"""
        global SYSTEM_RUNNING
        SYSTEM_RUNNING = False
        
        print("\n[*] Initiating graceful shutdown...")
        
        # Stop monitoring
        self.monitoring_active = False
        time.sleep(1)
        
        # Shutdown orchestrator
        if self.orchestrator:
            try:
                print("[*] Shutting down orchestrator...")
                self.orchestrator.shutdown()
            except:
                pass
                
        # Stop MongoDB if we started it
        if self.mongodb_process:
            try:
                print("[*] Stopping MongoDB...")
                self.mongodb_process.terminate()
                self.mongodb_process.wait(timeout=5)
            except:
                pass
                
        print("[OK] System shutdown complete")
        print("\n" + "="*60)
        print("Thank you for using AuraQuant AI Trading System")
        print("="*60)


def main():
    """Main entry point"""
    system = ControlledAuraQuantSystem()
    
    try:
        system.run()
    except Exception as e:
        print(f"\n[FATAL] System error: {e}")
        system.shutdown()
        
    sys.exit(0)


if __name__ == "__main__":
    main()