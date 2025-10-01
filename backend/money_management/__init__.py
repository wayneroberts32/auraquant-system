"""
AuraQuant Money Management Module
==================================
Advanced money management strategies for capital growth and protection
"""

from .money_manager import (
    MoneyManagementSystem,
    MoneyMetrics,
    TaxAllocation,
    ProfitTarget,
    ManagementStrategy,
    create_money_manager
)

__all__ = [
    'MoneyManagementSystem',
    'MoneyMetrics',
    'TaxAllocation', 
    'ProfitTarget',
    'ManagementStrategy',
    'create_money_manager'
]

__version__ = '1.0.0'