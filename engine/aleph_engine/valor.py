# -*- coding: utf-8 -*-
"""Veredicto de Valor (EVA del proyecto): ¿el proyecto GENERA o DESTRUYE valor sobre el costo del
capital (WACC)?

ADITIVO: no mueve ninguna cifra de decisión (TIR, VPN@TIO, flujo, crédito). Reutiliza la TIR proyecto
y el WACC ya calculados, y la MISMA serie de flujo del proyecto que el VPN@TIO de decisión, pero
descontada al WACC en vez de a la TIO.

NUANCE EXPERTA: para un proyecto FINITO, la fórmula de empresa-en-marcha `Inversión×(ROI−WACC)` NO
aplica (su ROI es plurianual, el WACC es anual → falso negativo). Para un proyecto inmobiliario:
  - crea_valor   = TIR proyecto > WACC      (ambas ANUALES → comparación válida)
  - spread_valor = TIR proyecto − WACC      (en puntos)
  - valor_creado = VPN del flujo del proyecto descontado al WACC (no a la TIO), con la periodicidad
                   CORRECTA: serie ANUAL → WACC anual; serie MENSUAL → tasa mensual equivalente
                   `(1+WACC)^(1/12)−1` (igual que el VPN@TIO usa la TIO mensual). Es el espejo exacto
                   del VPN@TIO pero al WACC; sale POSITIVO cuando la TIR proyecto supera al WACC.

Greenfield: una TIR proyecto degenerada (sin cruce real de IRR, p.ej. −99,99%) o ausente hace que el
veredicto BINARIO sea None → la UI muestra "— greenfield" (jamás un falso "destruye valor").
"""
from __future__ import annotations

# Umbral de TIR "degenerada" (IRR sin raíz real); coincide con la regla de presentación de la UI (format.ts).
TIR_DEGENERADA = -0.5


def es_degenerada(tir) -> bool:
    """True si la TIR no permite un veredicto (None o degenerada → greenfield)."""
    return tir is None or tir <= TIR_DEGENERADA


def vpn_al_wacc(flujo, wacc: float, anual: bool) -> float:
    """VPN del `flujo` descontado al WACC, con la periodicidad correcta.
    `anual=True`: serie ANUAL (descuenta al WACC anual). `anual=False`: serie MENSUAL (descuenta a la
    tasa mensual equivalente `(1+WACC)^(1/12)−1`)."""
    r = wacc if anual else (1 + wacc) ** (1 / 12) - 1
    return sum(f / (1 + r) ** t for t, f in enumerate(flujo))


def veredicto_binario(tir_proyecto, wacc):
    """Devuelve (crea_valor, spread_valor). (None, None) si la TIR es degenerada/ausente (greenfield)
    o no hay WACC. `crea_valor` = TIR proyecto > WACC; `spread_valor` = TIR − WACC (puntos)."""
    if wacc is None or es_degenerada(tir_proyecto):
        return None, None
    return bool(tir_proyecto > wacc), tir_proyecto - wacc
