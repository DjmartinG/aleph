# -*- coding: utf-8 -*-
"""Cierre financiero (Fuentes y Usos) — reconciliación + estructura.

`cierre.cierre_financiero(R)` reagrupa cifras YA producidas por `calcular()`; es ADITIVO (no lo llama
`calcular()` → dorado intacto). Estos tests verifican que la vista CUADRA (fuentes = usos operativos +
utilidad, la identidad del P&G) y que la estructura es coherente.
"""
import os
import json
import copy

import pytest

from aleph_engine import calcular, cierre

RAIZ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
ILUSTRATIVOS = ["proyectos/1_navarra.json", "proyectos/2_dominica.json", "proyectos/3_torres_campinas.json"]


def _R(rel):
    par = json.load(open(os.path.join(RAIZ, rel), encoding="utf-8"))
    return calcular(copy.deepcopy(par))


@pytest.mark.parametrize("rel", ILUSTRATIVOS)
def test_cierre_reconcilia(rel):
    if not os.path.exists(os.path.join(RAIZ, rel)):
        pytest.skip(f"sin dato: {rel}")
    c = cierre.cierre_financiero(_R(rel))
    assert c is not None
    # La identidad del P&G: fuentes (ingresos) == usos (inversión operativa) + utilidad operativa.
    assert c["cuadre"]["ok"], c["cuadre"]["detalle"]
    assert c["fuentes_total"] == pytest.approx(c["usos_total"] + c["utilidad_operativa"], rel=1e-6)
    # Los intereses son costo de financiación (NO se restan a la utilidad operativa) → van en el bloque.
    assert "intereses" in c["financiacion"]


@pytest.mark.parametrize("rel", ILUSTRATIVOS)
def test_cierre_estructura(rel):
    if not os.path.exists(os.path.join(RAIZ, rel)):
        pytest.skip(f"sin dato: {rel}")
    c = cierre.cierre_financiero(_R(rel))
    conceptos = [u["concepto"] for u in c["usos"]]
    assert "Lote" in conceptos and "Costos directos" in conceptos and "Honorarios" in conceptos
    assert any(f["concepto"] == "Ventas" for f in c["fuentes"])
    # La suma de las líneas de USOS == usos_total (operativos + intereses si aplica).
    assert sum(u["valor"] for u in c["usos"]) == pytest.approx(c["usos_total"], rel=1e-9)
    fin = c["financiacion"]
    assert "equity_pico" in fin and "credito_max" in fin and "exposicion_maxima" in fin


def test_cierre_sin_pyg_devuelve_none():
    assert cierre.cierre_financiero({}) is None
    assert cierre.cierre_financiero({"apalancamiento": {"intereses_total": 5.0}}) is None


def test_cierre_sin_apalancamiento_no_crashea():
    R = {"pyg": {"ventas": 1000.0, "recon_codensa": 0.0, "total_ingresos": 1000.0,
                 "costo_lote": 80.0, "directos": 550.0, "indirectos_otros": 120.0,
                 "gastos_fijos": 60.0, "honorarios": 90.0, "util_oper": 100.0}}
    c = cierre.cierre_financiero(R)
    assert c is not None
    assert c["financiacion"]["intereses"] == 0.0
    assert c["financiacion"]["credito_max"] is None
    # 80+550+(120+60)+90 = 900; +util 100 = 1000 = ingresos → cuadra.
    assert c["cuadre"]["ok"]
    assert c["usos_total"] == pytest.approx(900.0)
