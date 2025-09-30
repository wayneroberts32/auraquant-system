#!/usr/bin/env python3
"""
AuraQuant Complete Installation Script
Cross-platform installer for all Quantum Brain dependencies
Professor's Engineering Setup
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class AuraQuantInstaller:
    """Complete installer for AuraQuant Quantum Brain System"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.python_version = sys.version
        self.pip_cmd = [sys.executable, "-m", "pip"]
        self.failed_packages = []
        self.optional_packages = []
        
    def print_header(self):
        """Print installation header"""
        print("""
        ╔══════════════════════════════════════════════════════════════╗
        ║         AuraQuant Quantum Brain - Complete Installation      ║
        ║              Professor's Engineering Setup Script             ║
        ╚══════════════════════════════════════════════════════════════╝
        
        System Information:
        • Operating System: {}
        • Python Version: {}
        • Installation Path: {}
        """.format(self.os_type, self.python_version.split()[0], os.getcwd()))
        
    def check_python(self):
        """Check Python version"""
        print("\n[1/8] Checking Python version...")
        
        if sys.version_info < (3, 7):
            print("❌ Python 3.7+ is required. You have: {}".format(self.python_version))
            print("\nPlease upgrade Python from: https://www.python.org/downloads/")
            sys.exit(1)
        else:
            print("✅ Python version: {}".format(self.python_version.split()[0]))
            
    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        print("\n[2/8] Upgrading pip...")
        try:
            subprocess.check_call(self.pip_cmd + ["install", "--upgrade", "pip"])
            print("✅ pip upgraded successfully")
        except subprocess.CalledProcessError:
            print("⚠️ Could not upgrade pip, continuing...")
            
    def install_core_dependencies(self):
        """Install core Python packages"""
        print("\n[3/8] Installing core dependencies...")
        
        core_packages = [
            "numpy",
            "pandas",
            "scikit-learn",
            "python-dateutil",
            "pytz",
            "colorama",
            "tqdm",
            "ipython",
            "requests",
            "aiohttp",
            "aiofiles"
        ]
        
        for package in core_packages:
            self.install_package(package)
            
    def install_deep_learning(self):
        """Install deep learning frameworks"""
        print("\n[4/8] Installing deep learning frameworks...")
        print("⚠️ This may take several minutes and requires significant disk space...")
        
        # TensorFlow
        print("\nInstalling TensorFlow...")
        self.install_package("tensorflow")
        
        # PyTorch - different commands for different OS
        print("\nInstalling PyTorch...")
        if self.os_type == "Windows":
            # CPU version for Windows
            subprocess.call(self.pip_cmd + ["install", "torch", "torchvision", "torchaudio", 
                                           "--index-url", "https://download.pytorch.org/whl/cpu"])
        elif self.os_type == "Darwin":  # macOS
            self.install_package("torch")
            self.install_package("torchvision")
        else:  # Linux
            self.install_package("torch")
            self.install_package("torchvision")
            self.install_package("torchaudio")
            
        # Keras
        self.install_package("keras")
        
    def install_mongodb_drivers(self):
        """Install MongoDB drivers"""
        print("\n[5/8] Installing MongoDB drivers...")
        
        mongodb_packages = [
            "pymongo",
            "motor",
            "dnspython"  # Required for MongoDB Atlas connections
        ]
        
        for package in mongodb_packages:
            self.install_package(package)
            
    def install_technical_analysis(self):
        """Install technical analysis and market data libraries"""
        print("\n[6/8] Installing technical analysis libraries...")
        
        ta_packages = [
            "yfinance",
            "beautifulsoup4",
            "lxml",
            "html5lib"
        ]
        
        for package in ta_packages:
            self.install_package(package)
            
        # TA-Lib is special case - often fails on Windows
        print("\nAttempting to install TA-Lib...")
        try:
            subprocess.check_call(self.pip_cmd + ["install", "TA-Lib"], 
                                stderr=subprocess.DEVNULL)
            print("✅ TA-Lib installed")
        except:
            print("⚠️ TA-Lib installation failed (this is optional)")
            print("   For Windows: Download wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib")
            self.optional_packages.append("TA-Lib")
            
    def install_web_frameworks(self):
        """Install web and API frameworks"""
        print("\n[7/8] Installing web frameworks...")
        
        web_packages = [
            "fastapi",
            "uvicorn[standard]",
            "websockets",
            "python-dotenv",
            "pydantic"
        ]
        
        for package in web_packages:
            self.install_package(package)
            
    def install_optional(self):
        """Install optional packages"""
        print("\n[8/8] Installing optional packages...")
        
        optional = [
            "matplotlib",
            "plotly",
            "pytest",
            "pytest-asyncio",
            "black",
            "pylint"
        ]
        
        for package in optional:
            try:
                subprocess.check_call(self.pip_cmd + ["install", package],
                                    stderr=subprocess.DEVNULL)
                print(f"✅ {package} installed")
            except:
                self.optional_packages.append(package)
                
    def install_package(self, package):
        """Install a single package"""
        try:
            subprocess.check_call(self.pip_cmd + ["install", package],
                                stderr=subprocess.DEVNULL)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            self.failed_packages.append(package)
            
    def verify_installation(self):
        """Verify all packages are installed"""
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        
        critical_packages = {
            'numpy': 'Core computations',
            'pandas': 'Data manipulation',
            'sklearn': 'Machine learning',
            'tensorflow': 'Deep learning (TensorFlow)',
            'torch': 'Deep learning (PyTorch)',
            'pymongo': 'MongoDB driver',
            'motor': 'Async MongoDB',
            'yfinance': 'Market data',
            'bs4': 'Web scraping',
            'fastapi': 'API framework'
        }
        
        print("\nCritical Packages:")
        all_good = True
        for package, description in critical_packages.items():
            try:
                __import__(package)
                print(f"  ✅ {package:15} - {description}")
            except ImportError:
                print(f"  ❌ {package:15} - {description} [NOT INSTALLED]")
                all_good = False
                
        if self.failed_packages:
            print(f"\n⚠️ Failed to install: {', '.join(self.failed_packages)}")
            
        if self.optional_packages:
            print(f"\n📝 Optional packages skipped: {', '.join(self.optional_packages)}")
            
        return all_good
        
    def setup_mongodb_instructions(self):
        """Display MongoDB setup instructions"""
        print("\n" + "="*60)
        print("MONGODB SETUP")
        print("="*60)
        
        print("""
Option 1: Local MongoDB
------------------------
1. Download: https://www.mongodb.com/try/download/community
2. Install and start service
3. Connection: mongodb://localhost:27017/

Option 2: MongoDB Atlas (Cloud) - RECOMMENDED
----------------------------------------------
1. Create free account: https://cloud.mongodb.com
2. Create M0 cluster (free tier)
3. Get connection string from "Connect" button
4. Whitelist your IP address
5. Use connection string in migration script

MongoDB Atlas provides:
• 512MB free storage
• Automatic backups
• Built-in monitoring
• No local setup required
        """)
        
    def display_next_steps(self):
        """Display next steps after installation"""
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        
        print("""
1. Test the Demo
----------------
cd backend/brain
python test_scanner_demo.py

2. Run Full Scanner (requires packages)
----------------------------------------
python dashboard_scanner.py

3. Setup MongoDB
----------------
• Local: Install MongoDB Community Server
• Cloud: Create MongoDB Atlas account (free)

4. Migrate to Cloud
-------------------
python migrate_to_cloud.py

5. Start Continuous Learning
-----------------------------
The brain will scan markets and learn patterns continuously

Project Structure:
------------------
📁 D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\
├── 📁 Memory/              # Local brain memories
│   ├── trades/             # Trading decisions
│   ├── patterns/           # Market patterns
│   ├── evolution/          # Brain evolution
│   └── neural_weights/     # AI models
├── 📁 backend/brain/       # Brain system
│   ├── quantum_brain.py    # Main brain
│   ├── dashboard_scanner.py # Market scanner
│   └── migrate_to_cloud.py # Cloud migration
└── 📁 frontend/pages/      # Trading dashboard
        """)
        
    def run(self):
        """Run complete installation"""
        self.print_header()
        
        # Check Python version
        self.check_python()
        
        # Upgrade pip
        self.upgrade_pip()
        
        # Install packages
        self.install_core_dependencies()
        self.install_deep_learning()
        self.install_mongodb_drivers()
        self.install_technical_analysis()
        self.install_web_frameworks()
        self.install_optional()
        
        # Verify installation
        success = self.verify_installation()
        
        # Display MongoDB setup
        self.setup_mongodb_instructions()
        
        # Display next steps
        self.display_next_steps()
        
        if success:
            print("\n✅ INSTALLATION COMPLETE!")
            print("Your AuraQuant Quantum Brain is ready to learn and evolve!")
        else:
            print("\n⚠️ INSTALLATION COMPLETED WITH WARNINGS")
            print("Some packages failed to install. The system may still work with limited features.")
            print("Try installing failed packages manually or consult the documentation.")
            
        return success


def main():
    """Main entry point"""
    installer = AuraQuantInstaller()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--minimal":
            print("Installing minimal dependencies only...")
            installer.install_core_dependencies()
            installer.install_mongodb_drivers()
        elif sys.argv[1] == "--help":
            print("""
Usage: python install_everything.py [options]

Options:
  --minimal    Install only core dependencies
  --help       Show this help message
  
Default: Install all dependencies
            """)
            sys.exit(0)
    else:
        # Full installation
        installer.run()


if __name__ == "__main__":
    main()