"""Constantes de dominio del motor (esqueleto · PROMPT 2.3).

Hoy contiene SOLO lo que el contrato de datos (`models.py`) necesita para validar: el ciclo de vida
del proyecto. El resto de la configuración del motor (defaults de costos/recaudo/WACC, umbrales de
aprobación, números sin magia) se EXTRAE desde `app_streamlit/cg_engine/config.py` en PROMPT 3.

`aleph_engine` es PURO y autónomo: NO importa de `cg_engine`. Estos valores son una RÉPLICA EXACTA
de los de `cg_engine.config` (mismo conjunto, mismas cadenas) para que el snapshot dorado siga
validando sin cambios cuando se extraiga la lógica.
"""
from __future__ import annotations

# --- Ciclo de vida del proyecto (estados del pipeline / embudo) ---
# Eje rector de la UI; NO afecta el cálculo financiero. Réplica de cg_engine.config.
ESTADO_PREFACT = "prefactibilidad"    # candidato en evaluación; lote = supuesto; decisión ir/no-ir
ESTADO_APROBADO = "aprobado"          # evaluado + lote adquirido; obra aún no inicia
ESTADO_CONSTRUCCION = "construccion"  # en ejecución / obra; con seguimiento plan vs real
ESTADO_ENTREGADO = "entregado"        # proyecto cerrado / entregado

# Orden del embudo (de candidato a cerrado). Es también el conjunto válido del contrato (models.py).
ESTADOS = (ESTADO_PREFACT, ESTADO_APROBADO, ESTADO_CONSTRUCCION, ESTADO_ENTREGADO)

ESTADO_LABEL = {
    ESTADO_PREFACT: "Pre-factibilidad",
    ESTADO_APROBADO: "Aprobado",
    ESTADO_CONSTRUCCION: "Construcción",
    ESTADO_ENTREGADO: "Entregado",
}
ESTADO_DEFAULT = ESTADO_CONSTRUCCION   # respaldo si un proyecto no declara estado
