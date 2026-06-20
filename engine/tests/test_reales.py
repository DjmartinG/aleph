# -*- coding: utf-8 -*-
"""Precios constantes (tasas reales) — deflación de Fisher (curso Camacol §M6).

`reales.tasas_reales` es ADITIVO: deflacta las tasas nominales por la inflación; no toca cifras
nominales. Verifica la fórmula de Fisher, el manejo de greenfield/sin-inflación, y la consistencia
sobre un snapshot dorado real.
"""
import copy
import json

import pytest

from aleph_engine import calcular, reales

from ._golden import find_snapshots

SNAPS = find_snapshots()


def test_fisher_basico():
    r = reales.tasas_reales(0.3760, 0.4172, 0.15, 0.1871, 0.051)
    assert r["inflacion"] == 0.051
    assert r["tir_proyecto_real"] == pytest.approx((1.3760) / 1.051 - 1, rel=1e-9)   # ≈ 0.3092
    assert r["tir_equity_real"] == pytest.approx((1.4172) / 1.051 - 1, rel=1e-9)
    assert r["tio_real"] == pytest.approx(1.15 / 1.051 - 1, rel=1e-9)
    # real < nominal cuando hay inflación positiva.
    assert r["tir_proyecto_real"] < 0.3760


def test_sin_inflacion_o_greenfield_es_none():
    # sin inflación → todas None
    r = reales.tasas_reales(0.30, 0.40, 0.15, 0.18, None)
    assert all(r[k] is None for k in ("tir_proyecto_real", "tir_equity_real", "tio_real", "wacc_real"))
    # TIR degenerada (greenfield, ≤ −0.5) NO se deflacta
    r2 = reales.tasas_reales(-0.9999, 0.40, 0.15, 0.18, 0.05)
    assert r2["tir_proyecto_real"] is None
    assert r2["tir_equity_real"] is not None         # 0.40 sí se deflacta
    # wacc 0/None → wacc_real None
    assert reales.tasas_reales(0.30, 0.40, 0.15, 0.0, 0.05)["wacc_real"] is None


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_reales_en_el_resultado_del_motor():
    snap = json.load(open(SNAPS[0], encoding="utf-8"))
    R = calcular(copy.deepcopy(snap["input_par"]))
    ap = R["apalancamiento"]
    assert "tir_proyecto_real" in ap and "inflacion" in ap
    infl = ap.get("inflacion")
    if infl is not None and ap.get("tir_proyecto") is not None and ap["tir_proyecto"] > -0.5:
        assert ap["tir_proyecto_real"] == pytest.approx((1 + ap["tir_proyecto"]) / (1 + infl) - 1, rel=1e-9)
