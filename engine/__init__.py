"""Motor financiero de factibilidad CG — fuente única de verdad."""
from .modelo import calcular, pyg, flujo_caja, escenarios, sensibilidades, montecarlo, calcular_wacc, tir, directos_total, indirectos_total, normalizar_tipologias, gastos_fijos_total
from . import curvas

__version__ = "1.12.1"
