# -*- coding: utf-8 -*-
"""Test del DIFF de gobernanza del dorado (`execution/diff_dorado.py`, spec §2.3).

Verifica la LÓGICA de la red que la spec exige: comparar dorado viejo vs nuevo y FALLAR si cambió una
cifra que NO está en el allowlist del acta (cambio colateral oculto). La herramienta es aditiva (no
toca `calcular()`); estos tests prueban su comportamiento con datos sintéticos + un escenario realista
sobre un snapshot dorado.
"""
import copy
import json

import pytest

from execution.diff_dorado import Reporte, diff_resultados, diff_snapshots, permitido

from ._golden import find_snapshots

SNAPS = find_snapshots()


# ───────────────────────── lógica pura (sintética, sin datos) ─────────────────────────

def test_sin_cambios_es_ok():
    base = {"pyg": {"util_oper": 100.0, "ventas": 1000.0}, "ap": {"serie": [1.0, 2.0, 3.0]}}
    rep = diff_snapshots({"s": base}, {"s": copy.deepcopy(base)}, allowlist=[])
    assert rep.ok and not rep.esperados and not rep.colaterales


def test_colateral_falla_y_allowlist_aprueba():
    viejo = {"s": {"pyg": {"util_oper": 100.0, "udi": 50.0}}}
    nuevo = {"s": {"pyg": {"util_oper": 110.0, "udi": 55.0}}}     # ambos cambian +10%
    # Sin acta: ambos son colaterales → FALLA.
    rep = diff_snapshots(viejo, nuevo, allowlist=[])
    assert not rep.ok and len(rep.colaterales) == 2
    # Acta cubre udi pero NO util_oper → util_oper sigue siendo colateral → FALLA.
    rep = diff_snapshots(viejo, nuevo, allowlist=["pyg.udi"])
    assert not rep.ok
    assert [c.ruta for c in rep.colaterales] == [".pyg.util_oper"]
    assert [c.ruta for c in rep.esperados] == [".pyg.udi"]
    # Acta cubre ambos → todo esperado → OK.
    rep = diff_snapshots(viejo, nuevo, allowlist=["pyg.udi", "pyg.util_oper"])
    assert rep.ok and len(rep.esperados) == 2 and not rep.colaterales


def test_allowlist_por_prefijo_cubre_la_serie_completa():
    viejo = {"s": {"ap": {"flujo_equity": [1.0, 2.0, 3.0], "tir": 0.4}}}
    nuevo = {"s": {"ap": {"flujo_equity": [9.0, 8.0, 7.0], "tir": 0.4}}}   # cambia toda la serie
    rep = diff_snapshots(viejo, nuevo, allowlist=["ap.flujo_equity"])      # un prefijo cubre [0],[1],[2]
    assert rep.ok and len(rep.esperados) == 3 and not rep.colaterales


def test_tolerancia_relativa_ignora_ruido():
    viejo = {"s": {"x": 1_000_000.0}}
    nuevo = {"s": {"x": 1_000_000.0 * 1.0005}}   # +0.05% < 0.1% → no es cambio
    assert diff_snapshots(viejo, nuevo).ok
    nuevo2 = {"s": {"x": 1_000_000.0 * 1.002}}   # +0.2% > 0.1% → sí
    assert not diff_snapshots(viejo, nuevo2).ok


def test_permitido_sin_uso_detecta_acta_sobre_declarada():
    base = {"pyg": {"util_oper": 100.0}}
    rep = diff_snapshots({"s": base}, {"s": copy.deepcopy(base)}, allowlist=["pyg.util_oper"])
    assert rep.ok                              # nada cambió
    assert rep.permitido_sin_uso == ["pyg.util_oper"]   # el acta declaró algo que no se movió


def test_clave_o_snapshot_faltante_es_cambio():
    # clave que desaparece
    rep = diff_snapshots({"s": {"a": {"x": 1.0, "y": 2.0}}}, {"s": {"a": {"x": 1.0}}})
    assert not rep.ok and any(c.ruta == ".a.y" for c in rep.colaterales)
    # snapshot que aparece/desaparece
    rep = diff_snapshots({"s1": {"x": 1.0}}, {"s1": {"x": 1.0}, "s2": {"x": 1.0}})
    assert rep.solo_nuevo == ["s2"] and not rep.ok


def test_bool_se_compara_exacto():
    rep = diff_snapshots({"s": {"crea_valor": True}}, {"s": {"crea_valor": False}})
    assert not rep.ok and any(c.ruta == ".crea_valor" for c in rep.colaterales)


def test_permitido_helper():
    assert permitido(".apalancamiento.flujo_equity[42]", ["apalancamiento.flujo_equity"])
    assert permitido(".apalancamiento.tir_equity", ["apalancamiento.tir_equity"])
    assert permitido(".pyg.udi", ["pyg"])                       # prefijo de sección
    assert not permitido(".pyg.util_oper", ["pyg.udi"])


def test_diff_resultados_devuelve_estructura():
    d = diff_resultados({"a": 1.0, "b": [1.0, 2.0]}, {"a": 1.0, "b": [1.0, 9.0]})
    assert d == [(".b[1]", 2.0, 9.0)]
    assert isinstance(Reporte().ok, bool)


# ───────────────────────── escenario realista sobre el dorado real ─────────────────────────

@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_self_diff_de_los_snapshots_reales_es_vacio():
    """Un snapshot contra sí mismo no tiene cambios (sanidad de la herramienta sobre datos reales)."""
    mapa = {}
    for p in SNAPS:
        mapa[p] = json.load(open(p, encoding="utf-8"))["result"]
    rep = diff_snapshots(mapa, copy.deepcopy(mapa))
    assert rep.ok and not rep.colaterales


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_rebaseline_simulado_un_campo_movido():
    """Simula un re-baseline: mover UNA cifra del result. Sin acta → colateral (falla); con el acta que
    la lista → esperado (pasa). Es el caso de uso central de §2.3."""
    snap = json.load(open(SNAPS[0], encoding="utf-8"))
    viejo = {"x": snap["result"]}
    nuevo_res = copy.deepcopy(snap["result"])
    nuevo_res["pyg"]["util_oper"] = nuevo_res["pyg"]["util_oper"] * 1.05   # +5% a propósito
    nuevo = {"x": nuevo_res}

    sin_acta = diff_snapshots(viejo, nuevo, allowlist=[])
    assert not sin_acta.ok and any(c.ruta == ".pyg.util_oper" for c in sin_acta.colaterales)

    con_acta = diff_snapshots(viejo, nuevo, allowlist=["pyg.util_oper"])
    assert con_acta.ok and not con_acta.colaterales and len(con_acta.esperados) == 1
