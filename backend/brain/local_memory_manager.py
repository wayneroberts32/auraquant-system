"""
AuraQuant Local Memory Manager - Alias for Memory Manager
This file provides backward compatibility
"""

# Import everything from memory_manager
from .memory_manager import *

# Alias the main class for backward compatibility
LocalMemoryManager = LocalMemoryStorage

print("✅ Local Memory Manager loaded via alias")