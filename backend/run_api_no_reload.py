#!/usr/bin/env python
"""
Run AuraQuant API without auto-reload
"""

import uvicorn
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting AuraQuant Backend API (No Auto-Reload)")
    print("="*60)
    print("\nAPI will be available at:")
    print("  📊 Documentation: http://localhost:8000/docs")
    print("  🏥 Health Check: http://localhost:8000/health")
    print("  🌐 Root: http://localhost:8000/")
    print("\nPress CTRL+C to stop the server\n")
    
    # Run without reload to avoid shutdown issues
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable auto-reload
        log_level="info"
    )