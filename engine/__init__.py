"""Motor financiero de factibilidad CG — fuente única de verdad."""
from .modelo import calcular, pyg, flujo_caja, escenarios, sensibilidades, calcular_wacc, tir
from . import curvas

__version__ = "1.5.0"
