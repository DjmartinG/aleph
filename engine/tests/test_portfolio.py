# -*- coding: utf-8 -*-
"""Las agregaciones de portafolio (`aleph_engine.portfolio`) son consistentes con la suma por-proyecto.

Estas funciones se extrajeron de `app.py` (consolidado/burbujas/pipeline) y NO están cubiertas por el
snapshot dorado (que es por-proyecto). Este test las protege: construye `items` desde los snapshots,
corre las 3 funciones y verifica que los totales cuadren con la suma de los proyectos individuales.
"""
import copy
import json

import pytest

from aleph_engine import calcular, portfolio, config

from ._golden import find_snapshots

SNAPS = find_snapshots()


def _items():
    items = []
    for p in SNAPS:
        snap = json.load(open(p, encoding="utf-8"))
        par = snap["input_par"]
        items.append((p, par, calcular(copy.deepcopy(par))))
    return items


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_consolidar_cuadra_con_la_suma():
    items = _items()
    cons = portfolio.consolidar(items)
    assert cons["n"] == len(items)
    assert len(cons["filas"]) == len(items)
    # Los totales son la suma de los proyectos individuales.
    assert cons["ventas"] == pytest.approx(sum(R["pyg"]["ventas"] for _, _, R in items))
    assert cons["util_oper"] == pytest.approx(sum(R["pyg"]["util_oper"] for _, _, R in items))
    assert cons["udi"] == pytest.approx(sum(R["pyg"]["udi"] for _, _, R in items))
    # Margen consolidado = util/ventas.
    assert cons["margen"] == pytest.approx(cons["util_oper"] / cons["ventas"])


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_burbujas_y_pipeline_estructura():
    items = _items()
    pts = portfolio.puntos_burbujas(items)
    assert len(pts) == len(items)
    assert all({"nombre", "tir", "margen", "ventas", "tipo", "und"} <= set(p) for p in pts)

    pipe = portfolio.pipeline(items)
    assert len(pipe) == len(items)
    for d in pipe:
        assert d["estado"] in config.ESTADOS          # estado siempre válido (cae al default si no)
        assert "slug" in d and "vpn" in d and "ventas" in d
