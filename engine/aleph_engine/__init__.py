"""`aleph_engine` — motor financiero PURO de ALEPH (fuente única de verdad, capa /engine).

La lógica financiera (solo imports relativos, sin Streamlit/pandas/numpy; deps: scipy con fallback,
dateutil, pydantic) es la fuente ÚNICA de verdad. El harness dorado (`tests/test_golden_harness.py`)
re-ejecuta `calcular()` sobre la entrada congelada y exige paridad de cifras (tol. 0.1%).
(Streamlit fue retirado en jun-2026; el stack productivo es engine + api + web.)
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
from . import goal_seek
from . import simulacion
from . import portfolio
from . import metrics
from . import checks
from . import tipologias
from .schema import parse, Proyecto

# Versión HEREDADA del motor extraído (= cg_engine 2.39.0). El dorado compara CIFRAS, no la versión.
__version__ = "2.39.0"
