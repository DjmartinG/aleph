"""`aleph_engine` — motor financiero PURO de ALEPH (fuente única de verdad, capa /engine).

ESTADO: ESQUELETO (PROMPT 2.3). Hoy expone SOLO el contrato de datos del proyecto (modelos
Pydantic en `models.py`) y la lista válida de estados (`config.py`). La lógica financiera
(`calcular`, `pyg`, `flujo`, `wacc`, indicadores, EVM, escenarios, Monte Carlo) se EXTRAE TAL CUAL
desde `app_streamlit/cg_engine` en PROMPT 3 — no se reescribe de memoria.

Cuando se extraiga, el harness dorado (`tests/test_golden_harness.py`) detectará `aleph_engine.calcular`
automáticamente y empezará a exigir paridad de cifras contra el snapshot (tolerancia 0.1%).
"""
from . import config
from .models import (
    Areas,
    CostosPct,
    Cronograma,
    Etapa,
    Financiero,
    Meta,
    Proyecto,
    Wacc,
    parse,
)

# FUENTE ÚNICA de versión del paquete. La lee pyproject.toml (dynamic). Paquete nuevo → arranca en 0.x.
__version__ = "0.1.0"

__all__ = [
    "config",
    "Areas",
    "CostosPct",
    "Cronograma",
    "Etapa",
    "Financiero",
    "Meta",
    "Proyecto",
    "Wacc",
    "parse",
    "__version__",
]
