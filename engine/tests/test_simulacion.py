# -*- coding: utf-8 -*-
"""M5 (spec_pyg_dinamico.md) — motor Monte Carlo Crystal Ball.

Piezas puras (samplers/stats/tornado) CI-safe + un end-to-end sobre un snapshot dorado (si existe).
"""
import glob
import json
import os

import numpy as np
import pytest

from aleph_engine import simulacion as S


def test_samplers_en_rango_y_deterministas():
    rng = np.random.default_rng(1)
    for _ in range(500):
        assert -0.1 <= S._muestra(rng, "uniforme", {"min": -0.1, "max": 0.1}) <= 0.1
        assert -0.1 <= S._muestra(rng, "triangular", {"min": -0.1, "moda": 0, "max": 0.1}) <= 0.1
        assert -0.05 <= S._muestra(rng, "pert", {"min": -0.05, "moda": 0, "max": 0.1}) <= 0.1
    # determinismo por seed
    a = [S._muestra(np.random.default_rng(7), "triangular", {"min": -1, "moda": 0, "max": 1})]
    b = [S._muestra(np.random.default_rng(7), "triangular", {"min": -1, "moda": 0, "max": 1})]
    assert a == b


def test_stats_percentiles():
    st = S._stats(list(range(101)))  # 0..100
    assert st["n"] == 101 and st["mediana"] == 50
    assert st["p5"] == 5 and st["p95"] == 95 and st["min"] == 0 and st["max"] == 100


def test_tornado_suma_100_y_detecta_dominante():
    # y depende fuerte de 'precio', poco de 'costo', nada de 'ritmo'
    rng = np.random.default_rng(0)
    pr = rng.normal(0, 1, 400); co = rng.normal(0, 1, 400); ri = rng.normal(0, 1, 400)
    y = 3 * pr + 0.3 * co + 0 * ri + rng.normal(0, 0.1, 400)
    t = S._tornado({"precio": pr, "costo": co, "ritmo": ri}, y)
    suma = sum(v["contribucion_pct"] for v in t.values())
    assert abs(suma - 100.0) < 1e-6
    assert max(t, key=lambda k: t[k]["contribucion_pct"]) == "precio"
    assert t["precio"]["rho"] > 0    # correlacion positiva


def _algun_input_par():
    for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "golden", "*_snapshot.json"))):
        return json.load(open(f, encoding="utf-8"))["input_par"]
    return None


@pytest.mark.skipif(_algun_input_par() is None, reason="sin snapshots para el end-to-end")
def test_simular_end_to_end_determinista():
    par = _algun_input_par()
    r1 = S.simular(par, n=60, seed=11, incluir_valores=False)
    r2 = S.simular(par, n=60, seed=11, incluir_valores=False)
    assert r1["forecasts"]["margen"]["stats"] == r2["forecasts"]["margen"]["stats"]  # determinista
    # forecasts presentes con stats
    for k in S.FORECASTS:
        assert k in r1["forecasts"]
    cert = r1["forecasts"]["margen"]["certeza"]
    assert cert is None or 0.0 <= cert["prob"] <= 1.0
