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
def test_tesoreria_consolidada_cuadra_y_es_coherente():
    items = _items()
    t = portfolio.tesoreria(items)
    if not t.get("disponible"):
        pytest.skip("ningún proyecto del set tiene cronograma datado")
    H = t["horizonte"]
    assert len(t["caja"]) == H and len(t["credito"]) == H
    # Reconciliación: la suma de la caja por proyecto == la caja consolidada (en cada mes).
    for g in range(0, H, max(1, H // 10)):
        assert sum(p["caja"][g] for p in t["por_proyecto"]) == pytest.approx(t["caja"][g], abs=1.0)
    # Exposición = valle de caja (≤ 0, financiación); crédito ≥ 0.
    assert t["exposicion_maxima"]["valor"] == pytest.approx(min(t["caja"]))
    assert t["exposicion_maxima"]["valor"] <= 0
    assert t["credito_maximo"]["valor"] == pytest.approx(max(t["credito"]))
    assert t["credito_maximo"]["valor"] >= 0
    # El crédito CONSOLIDADO ≤ suma de los picos individuales (los picos no coinciden en el tiempo).
    suma_picos = sum((R.get("apalancamiento") or {}).get("credito_max", 0) or 0 for _, _, R in items)
    assert t["credito_maximo"]["valor"] <= suma_picos + 1.0


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_estres_tesoreria_profundiza_el_valle():
    items = _items()
    base = portfolio.tesoreria(items)
    if not base.get("disponible"):
        pytest.skip("ningún proyecto con cronograma datado")
    escen = [{"nombre": "Severa", "precio": -0.15, "costo": 0.05, "ritmo": -0.30}]
    e = portfolio.estres_tesoreria(items, escen)
    assert e["disponible"]
    H = e["horizonte"]
    assert len(e["base"]["caja"]) == H and len(e["base"]["credito"]) == H
    assert len(e["escenarios"]) == 1
    es = e["escenarios"][0]
    assert es["nombre"] == "Severa"
    assert len(es["caja"]) == H and len(es["credito"]) == H      # base y escenario ALINEADOS
    # Estrés (ventas abajo, costos arriba, más lento) PROFUNDIZA el valle de caja (necesidad total).
    assert es["exposicion_maxima"]["valor"] <= e["base"]["exposicion_maxima"]["valor"] + 1.0
    assert es["delta_exposicion"] <= 1.0
    # OJO: el crédito consolidado puede SUBIR o BAJAR — un ritmo más lento atrasa el PE y DESINCRONIZA
    # los picos de crédito constructor entre proyectos (efecto de timing), así que NO se asume dirección.
    assert es["credito_maximo"]["valor"] >= 0.0
    # El valle estresado cae DENTRO de la ventana (no clipeado en el borde derecho).
    assert es["exposicion_maxima"]["mes"] < H - 1
    # Un escenario SIN shock reproduce la base (la fiducia no afecta la serie de tesorería).
    e0 = portfolio.estres_tesoreria(items, [{"nombre": "nulo", "precio": 0.0, "costo": 0.0, "ritmo": 0.0}])
    assert e0["escenarios"][0]["exposicion_maxima"]["valor"] == pytest.approx(
        e0["base"]["exposicion_maxima"]["valor"])
    assert e0["escenarios"][0]["delta_exposicion"] == pytest.approx(0.0, abs=1.0)


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_capital_asignacion_rankea_y_es_coherente():
    items = _items()
    c = portfolio.capital(items)
    assert c["n"] == len(items) and len(c["filas"]) == len(items)
    for f in c["filas"]:
        assert {"slug", "nombre", "equity_pico", "credito_max", "valor_creado", "crea_valor",
                "eficiencia"} <= set(f)
        assert f["equity_pico"] >= 0 and f["credito_max"] >= 0
        # Greenfield (sin veredicto) → sin valor ni eficiencia; consistente con la app.
        if f["crea_valor"] is None:
            assert f["valor_creado"] is None and f["eficiencia"] is None
        # Eficiencia = valor creado / equity pico (cuando ambos existen).
        if f["eficiencia"] is not None:
            assert f["eficiencia"] == pytest.approx(f["valor_creado"] / f["equity_pico"])
    # Rankeado por eficiencia descendente; greenfield (None) al final.
    effs = [f["eficiencia"] for f in c["filas"]]
    con = [e for e in effs if e is not None]
    assert con == sorted(con, reverse=True)
    assert all(e is not None for e in effs[: len(con)])      # los None van al final
    # Totales = suma de picos individuales.
    assert c["equity_total"] == pytest.approx(sum(f["equity_pico"] for f in c["filas"]))
    assert c["valor_creado_total"] == pytest.approx(
        sum(f["valor_creado"] for f in c["filas"] if f["valor_creado"] is not None))


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
