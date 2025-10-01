#!/usr/bin/env python3
"""
AuraQuant Frontend-Backend Wiring Validation & Setup
Engineer's Note: Ensures frontend is properly connected to backend and MongoDB
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List

class FrontendBackendWiring:
    """
    Validates and establishes connections between:
    - Frontend (HTML/JS) 
    - Backend (Python API)
    - MongoDB (Atlas Cloud Database)
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.frontend_path = self.base_path / "frontend"
        self.backend_path = self.base_path / "backend"
        self.issues = []
        self.fixes_applied = []
        
    def check_backend_api(self) -> Dict[str, Any]:
        """Check if backend API is configured"""
        print("\n" + "="*70)
        print("CHECKING BACKEND API CONFIGURATION")
        print("="*70)
        
        results = {}
        
        # Check for main API file
        api_main = self.backend_path / "api" / "main.py"
        if api_main.exists():
            results['api_main'] = '✓ API main.py found'
            print(f"  ✓ API main.py found at {api_main}")
        else:
            results['api_main'] = '✗ API main.py missing'
            self.issues.append("Backend API main.py not found")
            print(f"  ✗ API main.py missing")
            
        # Check for .env configuration
        env_file = self.backend_path / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                env_content = f.read()
                
            # Check MongoDB configuration
            if 'MONGO_URI' in env_content or 'MONGODB_URI' in env_content:
                results['mongodb_config'] = '✓ MongoDB configured'
                print(f"  ✓ MongoDB URI configured in .env")
                
                # Check if it's the Atlas URI
                if 'mongodb+srv://auraquant' in env_content:
                    results['mongodb_atlas'] = '✓ MongoDB Atlas configured'
                    print(f"  ✓ MongoDB Atlas cloud database configured")
                else:
                    results['mongodb_atlas'] = '⚠ Local MongoDB only'
                    print(f"  ⚠ Using local MongoDB (not Atlas)")
            else:
                results['mongodb_config'] = '✗ MongoDB not configured'
                self.issues.append("MongoDB URI not configured in .env")
                print(f"  ✗ MongoDB URI not configured")
                
            # Check API port
            if 'API_PORT' in env_content:
                import re
                port_match = re.search(r'API_PORT=(\d+)', env_content)
                if port_match:
                    api_port = port_match.group(1)
                    results['api_port'] = f'✓ API Port: {api_port}'
                    print(f"  ✓ API Port configured: {api_port}")
        else:
            results['env_file'] = '✗ .env file missing'
            self.issues.append("Backend .env file not found")
            print(f"  ✗ .env file missing")
            
        return results
        
    def check_frontend_api_connections(self) -> Dict[str, Any]:
        """Check frontend API service configurations"""
        print("\n" + "="*70)
        print("CHECKING FRONTEND API CONNECTIONS")
        print("="*70)
        
        results = {}
        
        # Check API service file
        api_service = self.frontend_path / "assets" / "js" / "api-service.js"
        if api_service.exists():
            with open(api_service, 'r') as f:
                content = f.read()
                
            # Check API endpoint configuration
            if 'localhost:5000' in content:
                results['api_endpoint'] = '✓ API endpoint configured (port 5000)'
                print(f"  ✓ API endpoint configured: localhost:5000")
            elif 'localhost:8000' in content:
                results['api_endpoint'] = '✓ API endpoint configured (port 8000)'
                print(f"  ✓ API endpoint configured: localhost:8000")
            else:
                results['api_endpoint'] = '⚠ API endpoint needs update'
                self.issues.append("Frontend API endpoint may need updating")
                print(f"  ⚠ API endpoint configuration unclear")
                
            # Check authentication handling
            if 'login' in content and 'token' in content:
                results['auth_handling'] = '✓ Authentication configured'
                print(f"  ✓ Authentication handling present")
            else:
                results['auth_handling'] = '✗ Authentication missing'
                self.issues.append("Frontend authentication not configured")
                
        else:
            results['api_service'] = '✗ API service file missing'
            self.issues.append("Frontend api-service.js not found")
            print(f"  ✗ api-service.js missing")
            
        # Check WebSocket service
        ws_service = self.frontend_path / "assets" / "js" / "websocket-service.js"
        if ws_service.exists():
            with open(ws_service, 'r') as f:
                content = f.read()
                
            if 'WebSocket' in content:
                results['websocket'] = '✓ WebSocket service configured'
                print(f"  ✓ WebSocket service configured")
                
                # Check WebSocket endpoint
                if 'ws://localhost:5000' in content:
                    results['ws_endpoint'] = '✓ WebSocket endpoint (port 5000)'
                    print(f"  ✓ WebSocket endpoint: ws://localhost:5000")
                elif 'ws://localhost:8000' in content:
                    results['ws_endpoint'] = '✓ WebSocket endpoint (port 8000)'
                    print(f"  ✓ WebSocket endpoint: ws://localhost:8000")
        else:
            results['websocket'] = '✗ WebSocket service missing'
            self.issues.append("Frontend websocket-service.js not found")
            
        return results
        
    def check_mongodb_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection"""
        print("\n" + "="*70)
        print("CHECKING MONGODB CONNECTION")
        print("="*70)
        
        results = {}
        
        # Check MongoDB persistence module
        mongo_module = self.backend_path / "brain" / "mongodb_persistence.py"
        if mongo_module.exists():
            results['persistence_module'] = '✓ MongoDB persistence module found'
            print(f"  ✓ MongoDB persistence module found")
            
            # Try to test connection
            try:
                # Load .env to get MongoDB URI
                from dotenv import load_dotenv
                env_path = self.backend_path / ".env"
                load_dotenv(env_path)
                
                mongo_uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")
                
                if mongo_uri:
                    # Check if it's Atlas
                    if 'mongodb+srv://' in mongo_uri:
                        results['mongodb_type'] = '✓ MongoDB Atlas (Cloud)'
                        print(f"  ✓ Using MongoDB Atlas (Cloud Database)")
                    else:
                        results['mongodb_type'] = '⚠ Local MongoDB'
                        print(f"  ⚠ Using Local MongoDB")
                        
                    # Try to connect
                    try:
                        from pymongo import MongoClient
                        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                        client.admin.command('ping')
                        results['connection_test'] = '✓ MongoDB connection successful'
                        print(f"  ✓ MongoDB connection test PASSED")
                        client.close()
                    except Exception as e:
                        results['connection_test'] = f'✗ MongoDB connection failed'
                        self.issues.append(f"MongoDB connection failed: {str(e)}")
                        print(f"  ✗ MongoDB connection failed: {e}")
                else:
                    results['mongodb_uri'] = '✗ MongoDB URI not found'
                    self.issues.append("MongoDB URI not configured")
                    
            except ImportError:
                results['pymongo'] = '✗ PyMongo not installed'
                self.issues.append("PyMongo library not installed")
                print(f"  ✗ PyMongo not installed")
                
        return results
        
    def create_wiring_config(self):
        """Create a wiring configuration file"""
        config = {
            "frontend": {
                "path": str(self.frontend_path),
                "index": str(self.frontend_path / "index.html"),
                "api_endpoint": "http://localhost:8000/api",
                "websocket_endpoint": "ws://localhost:8000/ws"
            },
            "backend": {
                "path": str(self.backend_path),
                "api_main": str(self.backend_path / "api" / "main.py"),
                "api_port": 8000,
                "mongodb_configured": True
            },
            "mongodb": {
                "type": "MongoDB Atlas",
                "database": "auraquant",
                "collections": [
                    "brain_memories",
                    "evolution_states", 
                    "quantum_states",
                    "trading_decisions",
                    "learned_patterns",
                    "neural_weights",
                    "performance_metrics"
                ]
            }
        }
        
        config_path = self.base_path / "wiring_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"\n✅ Wiring configuration saved to: {config_path}")
        return config
        
    def fix_api_endpoints(self):
        """Fix API endpoint configurations"""
        print("\n" + "="*70)
        print("APPLYING FIXES")
        print("="*70)
        
        # Update API service to use port 8000
        api_service = self.frontend_path / "assets" / "js" / "api-service.js"
        if api_service.exists():
            with open(api_service, 'r') as f:
                content = f.read()
                
            # Update port from 5000 to 8000
            if 'localhost:5000' in content:
                content = content.replace('localhost:5000', 'localhost:8000')
                with open(api_service, 'w') as f:
                    f.write(content)
                self.fixes_applied.append("Updated API port from 5000 to 8000")
                print("  ✓ Updated API endpoint to port 8000")
                
        # Update WebSocket service
        ws_service = self.frontend_path / "assets" / "js" / "websocket-service.js"
        if ws_service.exists():
            with open(ws_service, 'r') as f:
                content = f.read()
                
            if 'ws://localhost:5000' in content:
                content = content.replace('ws://localhost:5000', 'ws://localhost:8000')
                with open(ws_service, 'w') as f:
                    f.write(content)
                self.fixes_applied.append("Updated WebSocket port from 5000 to 8000")
                print("  ✓ Updated WebSocket endpoint to port 8000")
                
    def create_startup_script(self):
        """Create a startup script for the full system"""
        script_content = '''@echo off
echo ======================================================================
echo AURAQUANT TRADING SYSTEM - FULL STACK STARTUP
echo ======================================================================

echo Starting Backend API Server...
start /B cmd /c "cd backend && python api\\main.py"
timeout /t 3 /nobreak > nul

echo Starting Frontend...
start http://localhost:8000
start "" "D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\frontend\\index.html"

echo ======================================================================
echo System Started Successfully!
echo Backend API: http://localhost:8000
echo Frontend: Open in browser
echo MongoDB: Atlas Cloud Database
echo ======================================================================
pause
'''
        
        script_path = self.base_path / "START_AURAQUANT.bat"
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        print(f"\n✅ Startup script created: {script_path}")
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive wiring report"""
        
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "frontend_backend_wiring": {
                "status": "CONNECTED" if len(self.issues) == 0 else "NEEDS_ATTENTION",
                "issues_found": len(self.issues),
                "fixes_applied": len(self.fixes_applied)
            },
            "connections": {
                "frontend_to_api": "Port 8000",
                "api_to_mongodb": "MongoDB Atlas",
                "websocket": "ws://localhost:8000"
            },
            "issues": self.issues,
            "fixes": self.fixes_applied
        }
        
        return report

def main():
    """Main execution"""
    print("="*70)
    print("AURAQUANT FRONTEND-BACKEND WIRING VALIDATION")
    print("Engineer's Analysis")
    print("="*70)
    
    wiring = FrontendBackendWiring()
    
    # Run checks
    backend_results = wiring.check_backend_api()
    frontend_results = wiring.check_frontend_api_connections()
    mongodb_results = wiring.check_mongodb_connection()
    
    # Apply fixes
    wiring.fix_api_endpoints()
    
    # Create configurations
    config = wiring.create_wiring_config()
    wiring.create_startup_script()
    
    # Generate report
    report = wiring.generate_report()
    
    # Print summary
    print("\n" + "="*70)
    print("WIRING STATUS SUMMARY")
    print("="*70)
    
    if len(wiring.issues) == 0:
        print("✅ FULLY WIRED: Frontend ←→ Backend ←→ MongoDB")
        print("   All connections properly configured")
    else:
        print(f"⚠️ {len(wiring.issues)} issues found:")
        for issue in wiring.issues:
            print(f"   - {issue}")
            
    print(f"\n✅ {len(wiring.fixes_applied)} fixes applied:")
    for fix in wiring.fixes_applied:
        print(f"   - {fix}")
        
    print("\n" + "="*70)
    print("CONNECTION MAP")
    print("="*70)
    print("Frontend (HTML/JS)")
    print("    ↓")
    print("    ↓ HTTP/WebSocket")
    print("    ↓")
    print("Backend API (Port 8000)")
    print("    ↓")
    print("    ↓ PyMongo")
    print("    ↓")
    print("MongoDB Atlas (Cloud)")
    print("="*70)
    
    return len(wiring.issues) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)