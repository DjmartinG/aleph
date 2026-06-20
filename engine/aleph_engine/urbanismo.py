# -*- coding: utf-8 -*-
"""Viabilidad urbanística (POT) — compara los índices que el motor YA calcula contra los límites POT.

Curso Camacol M1/M5 (localización y tamaño / impacto). El motor calcula índice de construcción,
densidad y aprovechamiento (`modelo._urbanistico`); aquí se contrastan con los MÁXIMOS del POT de la
zona (capturados por el analista en `par['pot']`) y se marca cumple / al límite / excede.

ADITIVO: agregación descriptiva, no toca `calcular()` (dorado intacto). Los límites POT viven en el
`par` del escenario (como el registro de due diligence); el motor financiero los ignora.
"""
from __future__ import annotations

# (clave en el `urbanistico` calculado, nombre, clave del máximo en par['pot'])
COMPARABLES = (
    ("indice_construccion", "Índice de construcción", "indice_construccion_max"),
    ("densidad_und_ha", "Densidad (und/ha)", "densidad_max_und_ha"),
    ("aprovechamiento", "Aprovechamiento", "aprovechamiento_max"),
)
_UMBRAL_LIMITE = 0.9   # ≥90% del máximo → "al límite"


def evaluar(urbanistico: dict | None, pot: dict | None) -> dict:
    """Contrasta el urbanístico calculado contra los límites POL del POT. `pot` vacío → 'sin_pot'."""
    urb = urbanistico or {}
    pot = pot or {}
    items = []
    for key, nombre, pot_key in COMPARABLES:
        real = urb.get(key)
        limite = pot.get(pot_key)
        if real is None or not limite:
            continue
        uso = real / limite if limite else None
        items.append({
            "concepto": nombre, "real": real, "limite": limite,
            "cumple": bool(real <= limite),
            "uso_pct": uso,
        })

    n_excede = sum(1 for i in items if not i["cumple"])
    n_limite = sum(1 for i in items if i["cumple"] and i["uso_pct"] is not None and i["uso_pct"] >= _UMBRAL_LIMITE)
    if not items:
        nivel = "sin_pot"
    elif n_excede:
        nivel = "excede"
    elif n_limite:
        nivel = "al_limite"
    else:
        nivel = "cumple"

    # Límites POT que el motor NO puede comparar (altura, cesiones…) → referencia informativa.
    comparadas = {c[2] for c in COMPARABLES}
    referencia = {k: v for k, v in pot.items() if k not in comparadas and not str(k).startswith("_")}

    return {
        "disponible": bool(items),
        "items": items,
        "veredicto": {"nivel": nivel, "n": len(items), "n_excede": n_excede},
        "referencia": referencia,
    }
