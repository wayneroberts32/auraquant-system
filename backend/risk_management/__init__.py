"""
AuraQuant Risk Management Module
=================================
Advanced risk management and capital protection system
"""

from .risk_matrix import (
    RiskManagementMatrix,
    RiskMetrics,
    RiskLimits,
    RiskAlert,
    RiskLevel,
    RiskEventType,
    create_risk_manager
)

__all__ = [
    'RiskManagementMatrix',
    'RiskMetrics',
    'RiskLimits',
    'RiskAlert',
    'RiskLevel',
    'RiskEventType',
    'create_risk_manager'
]

__version__ = '1.0.0'