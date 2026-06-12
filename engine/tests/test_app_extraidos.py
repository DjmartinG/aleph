# -*- coding: utf-8 -*-
"""Funciones extraídas de app.py al motor: `modelo.heatmap_sensibilidad` y `metrics.flujo_decision`.

Protegen los puntos 5-6 del desacople de app.py (§3.2 paso 13). Lógica copiada verbatim; estos tests
verifican su comportamiento sobre datos reales.
"""
import copy
import json

import pytest

from aleph_engine import calcular, modelo, metrics

from ._golden import find_snapshots

SNAPS = find_snapshots()


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_heatmap_estructura_y_monotonia():
    par = json.load(open(SNAPS[0], encoding="utf-8"))["input_par"]
    pasos = [-0.10, -0.05, 0.0, 0.05, 0.10]
    mat = modelo.heatmap_sensibilidad(par, pasos)
    assert len(mat) == 5 and all(len(fila) == 5 for fila in mat)
    # Subir el precio (columnas, izq→der) nunca baja el margen: cada fila es no decreciente.
    for fila in mat:
        assert all(fila[j] <= fila[j + 1] + 1e-9 for j in range(len(fila) - 1))
    # La celda central es la base (sin variación de precio ni costo).
    base = modelo._correr(dict(par, ventas_miles=par.get("ventas_miles",
                          sum(e.get("ventas_miles", 0) for e in par.get("etapas", [])))))["margen"] * 100
    assert mat[2][2] == pytest.approx(base)


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_flujo_decision_manda_el_waterfall():
    par = json.load(open(SNAPS[0], encoding="utf-8"))["input_par"]
    R = calcular(copy.deepcopy(par))
    fd = metrics.flujo_decision(R)
    ap = R.get("apalancamiento") or {}
    if ap:                                   # si el waterfall corrió, sus cifras mandan
        assert fd["credito_max"] == ap.get("credito_max")
        assert fd["vpn_proyecto"] == ap.get("vpn_proyecto")
        assert fd["tir_equity"] == ap.get("tir_equity")
        assert fd["tir_apalancada_ref"] == ap.get("tir_apalancada_ref")
    # Conserva las demás claves del flujo simple.
    assert set(R.get("flujo", {})) <= set(fd)
