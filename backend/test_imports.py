#!/usr/bin/env python3
"""
Test AuraQuant imports to ensure deployment will work
"""
import sys
print(f"Python version: {sys.version}")

# Test critical imports
errors = []

try:
    import email_validator
    print("✅ email_validator installed")
except ImportError as e:
    print(f"❌ email_validator missing: {e}")
    errors.append("email_validator")

try:
    from api.routes.auth import UserCreate
    print("✅ Auth routes import OK")
except ImportError as e:
    print(f"❌ Auth import error: {e}")
    errors.append("auth")

try:
    from trading_lib.strategies import StrategyRegistry
    print("✅ Strategies import OK")
except ImportError as e:
    print(f"❌ Strategies import error: {e}")
    errors.append("strategies")

try:
    from trading_lib.risk import RiskMetricsRegistry
    print("✅ Risk metrics import OK")
except ImportError as e:
    print(f"❌ Risk metrics import error: {e}")
    errors.append("risk")

try:
    from api.main import app
    print("✅ API main import OK")
except ImportError as e:
    print(f"❌ API main import error: {e}")
    errors.append("api.main")

if errors:
    print(f"\n❌ Found {len(errors)} import errors: {errors}")
    sys.exit(1)
else:
    print("\n✅ All imports successful - ready for deployment!")