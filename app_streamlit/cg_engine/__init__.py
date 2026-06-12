"""Motor financiero de factibilidad CG — fuente única de verdad."""
from .modelo import calcular, pyg, flujo_caja, escenarios, sensibilidades, montecarlo, montecarlo_tir, calcular_wacc, tir, directos_total, indirectos_total, normalizar_tipologias, gastos_fijos_total
from . import curvas

# FUENTE ÚNICA de versión del proyecto. La leen pyproject.toml (dynamic) y el pie de la app.
__version__ = "2.39.0"
