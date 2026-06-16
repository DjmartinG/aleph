# -*- coding: utf-8 -*-
"""Valores macro EN VIVO de las fuentes externas, para CONTRASTAR con la calibración del modelo en la
pestaña "Fuentes" (Fase 2). Hoy: Damodaran (CRP → `rp`, ERP de mercado maduro → `pm`) de Colombia.

SOLO REFERENCIA — NO alimenta el WACC ni mueve cifras (eso sería Fase 3, con re-baseline y aprobación).
Cacheado por DÍA (la tabla de Damodaran se actualiza ~anual; evita pegarle a la fuente en cada request).
Tolerante a fallos: si la fuente no responde, `disponible=False` y la web degrada a "solo modelo".
"""
from __future__ import annotations

import datetime

from .conectores import damodaran

_cache: dict[str, dict] = {}


def _hoy() -> str:
    return datetime.date.today().isoformat()


def damodaran_colombia(*, fetch=damodaran.fetch_damodaran) -> dict:
    """CRP/ERP de Colombia en vivo → {rp, pm} (cacheado por día). `fetch` inyectable para pruebas.

    `pm` (prima de mercado del WACC) = ERP de mercado MADURO = ERP total del país − CRP del país.
    `rp` (riesgo país del WACC) = CRP del país. Ambos como fracción (0.0285 = 2.85%), igual que el motor.
    """
    hoy = _hoy()
    if hoy in _cache:
        return _cache[hoy]

    payload = {"disponible": False, "fuente": "Damodaran (NYU Stern)", "url": damodaran.URL}
    try:
        por_clave = {v.clave.split(":")[1]: v for v in fetch("Colombia")}
        crp = por_clave.get("crp")
        erp = por_clave.get("erp_total")
        if crp is not None and erp is not None:
            mature = round(erp.valor - crp.valor, 6)  # ERP de mercado maduro = ERP total − CRP
            fila = (crp.detalle or {}).get("fila") or []
            payload = {
                "disponible": True,
                "fuente": "Damodaran (NYU Stern)",
                "url": damodaran.URL,
                "nota": crp.fuente_normativa,  # "Country Risk Premiums (anual)"
                "rating": fila[1] if len(fila) > 1 else None,
                "datos": {
                    "rp": {"valor": crp.valor},
                    "pm": {"valor": mature},
                },
            }
    except Exception:  # noqa: BLE001 — cualquier fallo de red/parseo → degrada a no-disponible
        pass

    _cache[hoy] = payload
    return payload
