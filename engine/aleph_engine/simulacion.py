# -*- coding: utf-8 -*-
"""Motor Monte Carlo profesional (estilo Crystal Ball) — M5 · spec_pyg_dinamico.md.

Sobre el trial reutilizable `modelo.mc_trial` (verificado identico a `montecarlo_tir`), añade:
  - DISTRIBUCIONES por variable de riesgo (uniforme/triangular/PERT/normal/lognormal),
  - FORECASTS multiples (TIR proyecto, TIR socio, VPN, margen, exposicion maxima, breakeven),
  - estadisticos completos (media/mediana/std/min/max + P5/P10/P25/P50/P75/P90/P95),
  - BANDAS DE CERTEZA (prob. de alcanzar la meta: TIR ≥ hurdle, VPN ≥ 0, margen ≥ 0),
  - TORNADO DE CONTRIBUCION A LA VARIANZA (rank-correlation de Spearman al cuadrado, normalizada).

Deterministico por `seed` (numpy Generator). NO muta `par`, NO toca el motor base (cifras intactas).
Las distribuciones por defecto estan centradas en el caso base (delta 0) con rangos prudentes;
son sobre-escribibles (se calibran con benchmarks_cg y el modulo de supuestos macro).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import config, modelo

VARIABLES = ("precio", "costo", "ritmo")           # dp (ventas), dc (costo directo), dv (ritmo/vmes)
FORECASTS = ("tir_proyecto", "tir_equity", "vpn_proyecto", "margen", "exposicion_maxima", "breakeven_mes")
_NOMBRE_FC = {
    "tir_proyecto": "TIR proyecto", "tir_equity": "TIR socio CG", "vpn_proyecto": "VPN @TIO",
    "margen": "Margen operativo", "exposicion_maxima": "Exposicion maxima de caja",
    "breakeven_mes": "Mes de breakeven",
}


@dataclass(frozen=True)
class Supuesto:
    """Una variable de riesgo y su distribucion. `params` depende de `dist`:
    uniforme {min,max} · triangular/pert {min,moda,max} · normal/lognormal {media,sigma}."""
    variable: str
    dist: str
    params: dict = field(default_factory=dict)
    nombre: str = ""


def supuestos_default():
    """Distribuciones por defecto (delta sobre el caso base). Precio simetrico ±10%; costo sesgado al
    alza (PERT, los sobrecostos son mas probables); ritmo ±30%."""
    return [
        Supuesto("precio", "triangular", {"min": -0.10, "moda": 0.0, "max": 0.10}, "Precio de venta"),
        Supuesto("costo", "pert", {"min": -0.05, "moda": 0.0, "max": 0.10}, "Costo directo"),
        Supuesto("ritmo", "triangular", {"min": -0.30, "moda": 0.0, "max": 0.30}, "Ritmo de ventas"),
    ]


def _muestra(rng, dist, p):
    if dist == "uniforme":
        return float(rng.uniform(p["min"], p["max"]))
    if dist == "triangular":
        return float(rng.triangular(p["min"], p["moda"], p["max"]))
    if dist == "pert":                              # beta-PERT (lambda=4)
        a, c, b = p["min"], p["moda"], p["max"]
        if b <= a:
            return float(a)
        lam = p.get("lambda", 4.0)
        alpha = 1 + lam * (c - a) / (b - a)
        beta = 1 + lam * (b - c) / (b - a)
        return float(a + rng.beta(alpha, beta) * (b - a))
    if dist == "normal":
        return float(rng.normal(p["media"], p["sigma"]))
    if dist == "lognormal":
        return float(rng.lognormal(p["media"], p["sigma"]))
    raise ValueError(f"distribucion desconocida: {dist}")


def _stats(arr):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size), "media": float(a.mean()), "mediana": float(np.median(a)),
        "std": float(a.std(ddof=1)) if a.size > 1 else 0.0, "min": float(a.min()), "max": float(a.max()),
        "p5": float(np.percentile(a, 5)), "p10": float(np.percentile(a, 10)),
        "p25": float(np.percentile(a, 25)), "p50": float(np.percentile(a, 50)),
        "p75": float(np.percentile(a, 75)), "p90": float(np.percentile(a, 90)),
        "p95": float(np.percentile(a, 95)),
    }


def _certeza(arr, umbral, signo=">="):
    a = np.asarray(arr, dtype=float)
    if a.size == 0:
        return None
    frac = (a >= umbral).mean() if signo == ">=" else (a <= umbral).mean()
    return {"umbral": umbral, "signo": signo, "prob": float(frac)}


def _rank(a):
    """Rangos (para Spearman) sin scipy: promedia los empates."""
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a), dtype=float)
    ranks[order] = np.arange(len(a), dtype=float)
    # promedio de empates
    a_sorted = a[order]
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and a_sorted[j + 1] == a_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return ranks


def _spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    if x.size < 3 or x.std() == 0 or y.std() == 0:
        return 0.0
    rx, ry = _rank(x), _rank(y)
    rho = np.corrcoef(rx, ry)[0, 1]
    return 0.0 if np.isnan(rho) else float(rho)


def _tornado(draws_por_var, fc_valores):
    """Contribucion a la varianza por variable (rank-correlation^2 normalizada). Incluye el signo de
    la correlacion (direccion del efecto). Es el grafico insignia de Crystal Ball."""
    rho = {v: _spearman(draws_por_var[v], fc_valores) for v in draws_por_var}
    tot = sum(r * r for r in rho.values()) or 1.0
    return {
        v: {"rho": rho[v], "contribucion_pct": 100.0 * rho[v] * rho[v] / tot}
        for v in sorted(rho, key=lambda k: -rho[k] * rho[k])
    }


def simular(par, *, supuestos=None, n=1000, seed=42, hurdle=None, escrituracion_sigue_obra=True,
            incluir_valores=True):
    """Corre el Monte Carlo Crystal Ball. Devuelve, por cada forecast: distribucion, estadisticos,
    banda de certeza, y el tornado de contribucion a la varianza. Deterministico por `seed`."""
    ctx = modelo.mc_contexto(par, escrituracion_sigue_obra=escrituracion_sigue_obra)
    sup = supuestos or supuestos_default()
    sup_por_var = {s.variable: s for s in sup}
    if hurdle is None:
        hurdle = (par.get("financiero", {}) or {}).get("tio", config.TIO)
    rng = np.random.default_rng(seed)

    fc = {k: [] for k in FORECASTS}
    draws = {k: {v: [] for v in VARIABLES} for k in FORECASTS}
    for _ in range(int(n)):
        d = {v: (_muestra(rng, s.dist, s.params) if v in sup_por_var else 0.0)
             for v, s in [(vv, sup_por_var.get(vv)) for vv in VARIABLES]}
        t = modelo.mc_trial(ctx, d["precio"], d["costo"], d["ritmo"])
        for k in FORECASTS:
            val = t.get(k)
            if val is None:
                continue
            fc[k].append(float(val))
            for v in VARIABLES:
                draws[k][v].append(d[v])

    _umbral = {"tir_proyecto": (hurdle, ">="), "tir_equity": (hurdle, ">="),
               "vpn_proyecto": (0.0, ">="), "margen": (0.0, ">=")}
    salida = {}
    for k in FORECASTS:
        ent = {"nombre": _NOMBRE_FC[k], "stats": _stats(fc[k]),
               "certeza": _certeza(fc[k], *_umbral[k]) if k in _umbral else None,
               "tornado": _tornado(draws[k], fc[k]) if fc[k] else {}}
        if incluir_valores:
            ent["valores"] = fc[k]
        salida[k] = ent

    return {
        "n": int(n), "seed": seed, "hurdle": hurdle,
        "supuestos": [{"variable": s.variable, "dist": s.dist, "params": s.params, "nombre": s.nombre}
                      for s in sup],
        "forecasts": salida,
    }
