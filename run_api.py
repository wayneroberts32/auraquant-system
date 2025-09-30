"""
AuraQuant API Runner
This script properly sets up the Python path and runs the API
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path (where packages are installed)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'Lib' / 'site-packages'))
sys.path.insert(0, str(project_root / 'backend'))

# Set working directory
os.chdir(project_root / 'backend')

# Now import and run the API
try:
    from api.main import app
    import uvicorn
    
    print("🚀 Starting AuraQuant Quantum Brain API...")
    print("📚 Documentation will be available at: http://localhost:8000/docs")
    print("🔐 Login: wayneroberts32@outlook.com.au / admin123")
    print("-" * 50)
    
    # Run the API
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("\nTrying simplified test mode...")
    
    # Fall back to test mode
    from test_api_simple import app as test_app
    import uvicorn
    
    print("🧪 Running in TEST MODE (without Quantum Brain)")
    uvicorn.run(
        test_app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )