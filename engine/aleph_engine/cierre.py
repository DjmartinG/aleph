# -*- coding: utf-8 -*-
"""Cierre financiero — Fuentes y Usos (curso Camacol §M6 "cierre financiero de los proyectos").

ESTRUCTURA (no calcula nada nuevo): reagrupa las cifras que `calcular()` YA produjo (`pyg` +
`apalancamiento`) en la vista clásica de FUENTES vs USOS + la estructura de financiación del desfase
temporal (equity pico, crédito máximo) + la utilidad antes/después de la financiación.

ADITIVO: este módulo NO lo llama `calcular()` → el snapshot dorado queda intacto (no se regenera).
La UI/API consumen de aquí; cero cálculo financiero en el front.

Identidad de cuadre (es el P&G reexpresado, sirve de check):
    total_ingresos == costo_lote + directos + (indirectos_otros + gastos_fijos) + honorarios + util_oper
Es decir: FUENTES (ingresos) = USOS (inversión operativa) + utilidad operativa.

OJO — los INTERESES del crédito NO se restan plano a la utilidad operativa: el costo de la deuda
afecta el retorno del EQUITY por TIMING (lo capta la TIR socio / el waterfall), no como una resta
estática (que daría una "utilidad neta" engañosa: en proyectos de margen fino los intereses brutos de
la vida pueden superar la utilidad operativa pese a una TIR muy positiva). Por eso los intereses se
presentan como COSTO DE LA FINANCIACIÓN en el bloque de financiación, no dentro de los usos.
"""
from __future__ import annotations

_TOL_REL = 0.001   # 0.1% (igual que checks.py / el harness dorado)
_TOL_ABS = 1.0     # miles COP


def _cerca(a: float, b: float) -> bool:
    return abs(a - b) <= max(_TOL_ABS, _TOL_REL * max(abs(a), abs(b)))


def cierre_financiero(R: dict) -> dict | None:
    """Fuentes y Usos + estructura de financiación, desde el resultado de `calcular()`.

    Devuelve None si no hay P&G (proyecto sin cifras). Los intereses/financiación salen del flujo
    apalancado si existe (si no, 0 / sin financiación de deuda).
    """
    pg = R.get("pyg") or {}
    if not pg:
        return None
    ap = R.get("apalancamiento") or {}

    ventas = float(pg.get("ventas") or 0.0)
    recon = float(pg.get("recon_codensa") or 0.0)
    total_ingresos = float(pg.get("total_ingresos") if pg.get("total_ingresos") is not None else ventas + recon)
    costo_lote = float(pg.get("costo_lote") or 0.0)
    directos = float(pg.get("directos") or 0.0)
    indirectos = float(pg.get("indirectos_otros") or 0.0) + float(pg.get("gastos_fijos") or 0.0)
    honorarios = float(pg.get("honorarios") or 0.0)
    util_oper = float(pg.get("util_oper") or 0.0)
    intereses = float(ap.get("intereses_total") or 0.0)

    # USOS: la inversión OPERATIVA (sin intereses — ver nota del módulo).
    usos = [
        {"concepto": "Lote", "valor": costo_lote},
        {"concepto": "Costos directos", "valor": directos},
        {"concepto": "Costos indirectos y gastos fijos", "valor": indirectos},
        {"concepto": "Honorarios", "valor": honorarios},
    ]
    usos_total = costo_lote + directos + indirectos + honorarios   # inversión operativa

    # FUENTES: los ingresos del proyecto (ventas + reconocimientos).
    fuentes = [{"concepto": "Ventas", "valor": ventas}]
    if recon:
        fuentes.append({"concepto": "Reconocimientos", "valor": recon})

    # Estructura de financiación del DESFASE temporal (cómo se cubre antes de que las ventas paguen):
    # equity pico = necesidad máxima de caja propia (tras el crédito); crédito máximo del constructor;
    # intereses = costo de esa deuda (NO se resta a la utilidad operativa — afecta el retorno del equity).
    exposicion = ap.get("max_necesidad_caja")
    financiacion = {
        "equity_pico": abs(float(exposicion)) if exposicion is not None else None,
        "credito_max": ap.get("credito_max"),
        "exposicion_maxima": exposicion,
        "intereses": intereses,
    }

    # Cuadre: FUENTES (ingresos) == USOS (inversión operativa) + utilidad operativa (identidad del P&G).
    cuadra = _cerca(total_ingresos, usos_total + util_oper)

    return {
        "usos": usos,
        "usos_total": usos_total,
        "fuentes": fuentes,
        "fuentes_total": total_ingresos,
        "utilidad_operativa": util_oper,
        "financiacion": financiacion,
        "cuadre": {
            "clave": "cierre",
            "nombre": "Cierre: fuentes = usos + utilidad",
            "ok": bool(cuadra),
            "detalle": f"ingresos {total_ingresos:,.0f} vs usos+utilidad {usos_total + util_oper:,.0f}",
        },
    }
