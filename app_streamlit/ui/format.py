# -*- coding: utf-8 -*-
"""Formato único de presentación (moneda y porcentaje).

FUENTE ÚNICA: antes el formateo estaba disperso en `app.py` (varias variantes), lo que resta
credibilidad cuando una misma cifra se muestra distinto en dos pantallas. Centralizarlo aquí
garantiza consistencia y permite PROBARLO. No contiene lógica financiera (solo presentación).

Convención CG: montos en MILES COP; separador de miles con punto.
"""
from __future__ import annotations


def fmt_cop(x) -> str:
    """Formatea un monto en MILES COP a pesos legibles.

    - ≥ mil millones → 'mil M' (miles de millones), 1 decimal.
    - si no → 'M' (millones), sin decimales.
    - 0/None/falsy → '$0'.

    >>> fmt_cop(50000)      # 50.000 miles = 50 M
    '$50 M'
    >>> fmt_cop(1_500_000)  # 1.500.000 miles = 1,5 mil M
    '$1.5 mil M'
    """
    if not x:
        return "$0"
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.1f} mil M".replace(",", ".")
    return f"${x/1000:,.0f} M".replace(",", ".")


def fmt_pct(x, dec: int = 2) -> str:
    """Formatea una fracción como porcentaje (0.2183 → '21.83%'). None → 'n/d'."""
    if x is None:
        return "n/d"
    return f"{x*100:.{dec}f}%"


# Alias de compatibilidad: el nombre histórico en app.py era `fmt_mm`.
fmt_mm = fmt_cop
