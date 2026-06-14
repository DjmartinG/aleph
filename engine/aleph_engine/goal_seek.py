# -*- coding: utf-8 -*-
"""Goal-seek (motor bidireccional, M5/M4 · spec_pyg_dinamico.md) — "empezar por el P&G y devolvernos".

Dada una META sobre un indicador (margen, TIR proyecto/socio, VPN, exposicion, breakeven) resuelve
QUE valor necesita un DRIVER (precio, costo, ritmo de ventas — como delta sobre el caso base) para
alcanzarla. Determinista: usa `modelo.mc_trial` (un trial sin aleatoriedad) como funcion objetivo, y
la resuelve por BRACKET (busca cambio de signo en el rango) + BISECCION. Aditivo: no toca el motor
base ni mueve cifras; es analisis "hacia atras".
"""
from __future__ import annotations

from . import modelo

DRIVERS = ("precio", "costo", "ritmo")
OBJETIVOS = ("tir_proyecto", "tir_equity", "vpn_proyecto", "margen", "exposicion_maxima", "breakeven_mes")


def _bracket(f, meta, lo, hi, pasos=24):
    """Busca un sub-intervalo [a,b] de [lo,hi] donde f(x)-meta cambia de signo (escaneo)."""
    prev_x = lo
    pv = f(lo)
    prev_g = (pv - meta) if pv is not None else None
    for i in range(1, pasos + 1):
        x = lo + (hi - lo) * i / pasos
        v = f(x)
        g = (v - meta) if v is not None else None
        if prev_g is not None and g is not None and prev_g * g <= 0:
            return prev_x, x
        prev_x, prev_g = x, g
    return None


def _bisectar(f, meta, lo, hi, tol=1e-5, max_iter=60):
    """Bisección sobre f(x)=meta en [lo,hi] (asume cambio de signo). Devuelve (x, valor)."""
    glo = f(lo) - meta
    a, b = lo, hi
    for _ in range(max_iter):
        mid = (a + b) / 2
        v = f(mid)
        if v is None:
            break
        g = v - meta
        if abs(g) <= tol * max(1.0, abs(meta)) or (b - a) < 1e-7:
            return mid, v
        if glo * g <= 0:
            b = mid
        else:
            a, glo = mid, g
    mid = (a + b) / 2
    return mid, f(mid)


def resolver(par, objetivo, meta, driver, *, rango=(-0.5, 0.5), tol=1e-5):
    """Resuelve el `driver` (delta) para que `objetivo` == `meta`. Devuelve dict con `alcanzable`,
    el `delta` necesario y el `valor` logrado (o alcanzable=False si no hay solucion en el rango)."""
    if objetivo not in OBJETIVOS:
        raise ValueError(f"objetivo desconocido: {objetivo}")
    if driver not in DRIVERS:
        raise ValueError(f"driver desconocido: {driver}")
    ctx = modelo.mc_contexto(par)

    def f(x):
        d = {"precio": 0.0, "costo": 0.0, "ritmo": 0.0}
        d[driver] = x
        return modelo.mc_trial(ctx, d["precio"], d["costo"], d["ritmo"]).get(objetivo)

    base = f(0.0)
    br = _bracket(f, meta, rango[0], rango[1])
    if br is None:
        return {"alcanzable": False, "objetivo": objetivo, "meta": meta, "driver": driver,
                "valor_base": base, "rango": list(rango)}
    delta, valor = _bisectar(f, meta, br[0], br[1], tol=tol)
    return {"alcanzable": True, "objetivo": objetivo, "meta": meta, "driver": driver,
            "delta": delta, "valor": valor, "valor_base": base}


def alcanzar(par, objetivo, meta, *, drivers=DRIVERS, rango=(-0.5, 0.5)):
    """Resuelve la meta por CADA driver: muestra cuanto habria que mover precio, costo o ritmo para
    llegar (el 'devolvernos' completo). Cada entrada trae alcanzable/delta/valor."""
    return {d: resolver(par, objetivo, meta, d, rango=rango) for d in drivers}
