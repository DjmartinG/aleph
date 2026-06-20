# -*- coding: utf-8 -*-
"""Evaluación a precios CONSTANTES (reales) — curso Camacol §M6 "precios corrientes y constantes".

El motor trabaja en COP CORRIENTES (nominales). La tasa REAL (de poder adquisitivo) se obtiene por la
ecuación de Fisher, deflactando por la inflación: (1+real) = (1+nominal)/(1+π)  →  real = (1+i)/(1+π)−1.

OJO — el VPN es INVARIANTE entre corrientes y constantes si se hace consistente (flujos reales a tasa
real == flujos nominales a tasa nominal): por eso NO se reporta un "VPN real" distinto (sería el mismo
o, mal hecho, engañoso). Lo que SÍ cambia y es informativo es la TASA real (TIR/TIO/WACC reales).

ADITIVO: no toca `calcular()` ni mueve las cifras nominales; solo añade sus versiones reales.
"""
from __future__ import annotations

TIR_DEGENERADA = -0.5   # mismo umbral que la regla greenfield de la UI (jamás deflactar un −99%)


def _real(nominal, infl):
    """Tasa real por Fisher; None si la nominal es degenerada/ausente o no hay inflación."""
    if nominal is None or infl is None:
        return None
    if nominal <= TIR_DEGENERADA:
        return None
    return (1 + nominal) / (1 + infl) - 1


def tasas_reales(tir_proyecto, tir_equity, tio, wacc, inflacion):
    """Versiones REALES (precios constantes) de las tasas, deflactadas por `inflacion` (fracción).

    `inflacion` None → todas None (no se inventa un deflactor). Greenfield/TIR degenerada → None.
    """
    return {
        "inflacion": inflacion,
        "tir_proyecto_real": _real(tir_proyecto, inflacion),
        "tir_equity_real": _real(tir_equity, inflacion),
        "tio_real": _real(tio, inflacion),
        "wacc_real": _real(wacc, inflacion) if wacc else None,
    }
