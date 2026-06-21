# -*- coding: utf-8 -*-
"""Estudio de mercado — contrasta los supuestos del proyecto (precio, ritmo) contra comparables de la zona.

Curso Camacol M3 (estudio de mercado: demanda/oferta/precios/competencia/absorción). El proyecto fija
un precio/m² y un ritmo de ventas (`vmes`); aquí se confrontan con los comparables de mercado que el
analista captura en `par['mercado']` y se emiten SEÑALES de sanidad (precio sobre/bajo el comparable;
ritmo más rápido que la absorción de la zona).

ADITIVO: agregación descriptiva, no toca `calcular()` (dorado intacto). Los comparables viven en el
`par` del escenario (como el due diligence y los límites POT); el motor financiero los ignora.
"""
from __future__ import annotations

_TOL = 0.10   # ±10% → "en mercado"; fuera de eso, señal


def _ritmo_proyecto(par: dict):
    """Ritmo de ventas asumido por el proyecto (und/mes), promedio ponderado por unidades de cada etapa."""
    etapas = par.get("etapas") or []
    pares = [(e.get("vmes"), e.get("und")) for e in etapas if e.get("vmes")]
    if not pares:
        return None
    tot = sum(u for _, u in pares if u)
    if tot:
        return sum(v * (u or 0) for v, u in pares) / tot
    return sum(v for v, _ in pares) / len(pares)


def evaluar(par: dict | None, R: dict | None) -> dict:
    """Contrasta precio/m² y ritmo del proyecto contra los comparables de `par['mercado']`."""
    m = (par or {}).get("mercado") or {}
    urb = (R or {}).get("urbanistico") or {}
    items = []

    # Precio de venta /m²: fuera de ±10% del comparable es señal (encima = riesgo de venta lenta;
    # debajo = posible valor dejado en la mesa).
    p_proy = urb.get("precio_m2_vend")
    p_mkt = m.get("precio_m2_mercado")
    if p_proy and p_mkt:
        desv = p_proy / p_mkt - 1
        items.append({
            "dimension": "Precio de venta /m²", "sentido": "precio",
            "proyecto": p_proy, "mercado": p_mkt, "desviacion": desv,
            "estado": "alerta" if abs(desv) > _TOL else "ok",
        })

    # Ritmo de ventas (und/mes) vs absorción de la zona: asumir MÁS rápido que el mercado es optimista.
    r_proy = _ritmo_proyecto(par or {})
    r_mkt = m.get("absorcion_mercado_und_mes")
    if r_proy and r_mkt:
        desv = r_proy / r_mkt - 1
        items.append({
            "dimension": "Ritmo de ventas (und/mes)", "sentido": "ritmo",
            "proyecto": r_proy, "mercado": r_mkt, "desviacion": desv,
            "estado": "alerta" if desv > _TOL else "ok",
        })

    n_alerta = sum(1 for i in items if i["estado"] == "alerta")
    if not items:
        nivel = "sin_datos"
    elif n_alerta:
        nivel = "revisar"
    else:
        nivel = "en_mercado"

    # Contexto cualitativo de mercado (oferta, demanda, fuente…) que no se contrasta numéricamente.
    comparados = {"precio_m2_mercado", "absorcion_mercado_und_mes"}
    referencia = {k: v for k, v in m.items() if k not in comparados and not str(k).startswith("_")}

    return {
        "disponible": bool(items),
        "items": items,
        "veredicto": {"nivel": nivel, "n": len(items), "n_alerta": n_alerta},
        "referencia": referencia,
    }
