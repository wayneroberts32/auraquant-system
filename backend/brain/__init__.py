"""
AuraQuant Brain Module - Synthetic Intelligence Orchestrator
The world's most advanced, safest, self-evolving orchestrator of capital
"""

# Import and expose core brain components
try:
    from .quantum_brain_fixed import QuantumBrain, get_brain
    HAS_QUANTUM_BRAIN = True
except ImportError:
    try:
        from .quantum_brain_local import QuantumBrain
        get_brain = None
        HAS_QUANTUM_BRAIN = True
    except ImportError:
        QuantumBrain = None
        get_brain = None
        HAS_QUANTUM_BRAIN = False

# Dashboard scanner
try:
    from .dashboard_scanner import DashboardScanner
    HAS_SCANNER = True
except ImportError:
    DashboardScanner = None
    HAS_SCANNER = False

# Memory manager - try both names
try:
    from .memory_manager import LocalMemoryStorage as LocalMemoryManager
    HAS_MEMORY = True
except ImportError:
    try:
        from .local_memory_manager import LocalMemoryManager
        HAS_MEMORY = True
    except ImportError:
        LocalMemoryManager = None
        HAS_MEMORY = False

__all__ = [
    'QuantumBrain',
    'get_brain',
    'DashboardScanner',
    'LocalMemoryManager',
    'HAS_QUANTUM_BRAIN',
    'HAS_SCANNER',
    'HAS_MEMORY'
]

# Module status
print(f"🧠 Brain Module Status:")
print(f"  - Quantum Brain: {'✅' if HAS_QUANTUM_BRAIN else '❌'}")
print(f"  - Dashboard Scanner: {'✅' if HAS_SCANNER else '❌'}")
print(f"  - Memory Manager: {'✅' if HAS_MEMORY else '❌'}")