"""`aleph_engine` — motor financiero PURO de ALEPH (fuente única de verdad, capa /engine).

PROMPT 3 · bloque 1: la lógica se MOVIÓ **tal cual** desde `app_streamlit/cg_engine` (solo imports
relativos, sin Streamlit/pandas/numpy; deps: scipy con fallback, dateutil, pydantic). El harness
dorado (`tests/test_golden_harness.py`) ya re-ejecuta `calcular()` sobre la entrada congelada y exige
paridad de cifras (tol. 0.1%). `app_streamlit` sigue usando su `cg_engine` (INTACTO) hasta el bloque 2,
que repunta los imports y elimina la copia.
"""
from .modelo import (
    calcular,
    pyg,
    flujo_caja,
    escenarios,
    sensibilidades,
    montecarlo,
    montecarlo_tir,
    calcular_wacc,
    tir,
    directos_total,
    indirectos_total,
    normalizar_tipologias,
    gastos_fijos_total,
)
from . import curvas
from . import schema
from .schema import parse, Proyecto

# Versión HEREDADA del motor extraído (= cg_engine 2.39.0). El dorado compara CIFRAS, no la versión.
__version__ = "2.39.0"
