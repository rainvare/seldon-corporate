"""
seldon-corporate: Organizational Resilience Framework v3.0
Q(t) = R_scalar(t) - Pe(t)*(1 + gamma*Pe(t))
"""
from .model import ResilienceVector, EnvironmentalPressure, Period, EWSCalculator, derive_weights

__version__ = "3.0.0"
