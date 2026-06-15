# -*- coding: utf-8 -*-
"""M4 (spec_pyg_dinamico.md) — goal-seek (motor bidireccional).

Helpers puros (bracket/biseccion) CI-safe + end-to-end sobre un snapshot dorado (si existe).
"""
import glob
import json
import os

import pytest

from aleph_engine import goal_seek as G


def test_bracket_y_biseccion_puros():
    f = lambda x: x * x   # noqa: E731
    br = G._bracket(f, 4.0, 0.0, 5.0)         # raiz de x^2=4 en [0,5]
    assert br is not None and br[0] <= 2.0 <= br[1]
    x, v = G._bisectar(f, 4.0, br[0], br[1])
    assert abs(x - 2.0) < 1e-3 and abs(v - 4.0) < 1e-3


def test_bracket_sin_solucion_devuelve_none():
    f = lambda x: x * x   # noqa: E731  (siempre >= 0)
    assert G._bracket(f, -1.0, 0.0, 5.0) is None


def _algun_input_par():
    for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "golden", "*_snapshot.json"))):
        return json.load(open(f, encoding="utf-8"))["input_par"]
    return None


@pytest.mark.skipif(_algun_input_par() is None, reason="sin snapshots para el end-to-end")
def test_resolver_margen_alcanza_la_meta():
    par = _algun_input_par()
    base = G.resolver(par, "margen", 0.0, "precio")["valor_base"]
    meta = base + 0.02   # meta alcanzable: 2 pp por encima del margen base
    r = G.resolver(par, "margen", meta, "precio")
    assert r["alcanzable"] is True
    assert abs(r["valor"] - meta) < 1e-3      # el motor logra la meta
    # subir el margen 2pp requiere subir el precio (delta > 0)
    assert r["delta"] > 0


@pytest.mark.skipif(_algun_input_par() is None, reason="sin snapshots para el end-to-end")
def test_resolver_meta_imposible():
    par = _algun_input_par()
    r = G.resolver(par, "margen", 5.0, "precio")   # 500% de margen: inalcanzable en el rango
    assert r["alcanzable"] is False
