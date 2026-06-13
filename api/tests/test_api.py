# -*- coding: utf-8 -*-
"""Tests de la API (Fase 4a). Contrato dorado + fidelidad al motor + humo de endpoints.

La API NO debe alterar las cifras del motor: expone exactamente lo que `aleph_engine.calcular()`
produce. El test de contrato dorado (datos REALES de Navarra, solo en local) clava TIR proyecto ~37.60%.
"""
import pytest
from fastapi.testclient import TestClient

from aleph_engine import calcular

from aleph_api import repo
from aleph_api.main import app

client = TestClient(app)
SLUGS = repo.listar()
NAV = "1_navarra"


def test_version():
    j = client.get("/version").json()
    assert j["version"] and j["engine_version"]


@pytest.mark.skipif(not SLUGS, reason="no hay proyectos disponibles")
def test_portfolio():
    r = client.get("/v1/portfolio")
    assert r.status_code == 200
    j = r.json()
    assert "consolidado" in j and "embudo" in j
    assert len(j["items"]) == len(SLUGS)
    # el embudo cubre los estados del ciclo de vida
    assert {e["estado"] for e in j["embudo"]}
    # mapa de valor: cada item trae margen (TIR/margen/ventas/tipo ya presentes)
    assert all({"nombre", "tir", "margen", "ventas", "tipo"} <= it.keys() for it in j["items"])


@pytest.mark.skipif(NAV not in SLUGS, reason="Navarra no disponible")
def test_project_y_results_fieles_al_motor():
    pj = client.get(f"/v1/projects/{NAV}").json()
    assert pj["id"] == NAV and "kpis_cabecera" in pj and "estado_label" in pj

    res = client.get(f"/v1/scenarios/{NAV}:base/results").json()
    ind = res["indicadores"]
    # Gobernanza de cifras: etiqueta de base presente y TIR doble DISTINTA.
    assert ind["tir_proyecto_label"] and ind["tir_socio_label"]
    assert ind["tir_proyecto_label"] != ind["tir_socio_label"]
    # Fidelidad: la API expone EXACTAMENTE lo que calcula el motor.
    R = calcular(repo.cargar(NAV))
    assert ind["tir_proyecto"] == R["apalancamiento"]["tir_proyecto"]
    assert ind["tir_socio"] == R["apalancamiento"]["tir_equity"]
    assert ind["vpn_proyecto"] == R["apalancamiento"]["vpn_proyecto"]
    # Checks de cuadre presentes y todos OK.
    assert res["checks"] and all(c["ok"] for c in res["checks"])


@pytest.mark.skipif(not repo.es_real(NAV), reason="datos REALES de Navarra no presentes (p.ej. CI)")
def test_contrato_dorado_navarra():
    res = client.get(f"/v1/scenarios/{NAV}:base/results").json()
    # Cifra dorada de Navarra (datos reales): TIR proyecto 37.60%.
    assert 0.37 <= res["indicadores"]["tir_proyecto"] <= 0.385


@pytest.mark.skipif(NAV not in SLUGS, reason="Navarra no disponible")
def test_sensitivity_y_run():
    s = client.get(f"/v1/scenarios/{NAV}:base/sensitivity").json()
    assert len(s["matriz_2d"]["margen_pct"]) == 5
    assert "escenarios" in s and "tornado" in s
    r = client.post(f"/v1/scenarios/{NAV}:base/run", json={"tipo": "margen", "n": 50, "seed": 1})
    assert r.status_code == 200


@pytest.mark.skipif(NAV not in SLUGS, reason="Navarra no disponible")
def test_schedule_fiel_al_motor():
    """El cronograma expone EXACTAMENTE los hitos/recaudo del motor; la absorción reconcilia."""
    sc = client.get(f"/v1/scenarios/{NAV}:base/schedule").json()
    R = calcular(repo.cargar(NAV))
    # Una etapa por cada hito del motor; fechas presentes y la etapa raíz arranca en mes 0.
    assert sc["etapas"] and len(sc["etapas"]) == len(R["hitos"])
    e0 = sc["etapas"][0]
    assert all(e0[k] for k in ("iv", "pe", "fv", "ic", "fc"))
    assert e0["iv_mes"] == 0 and sc["base_date"]
    # Series alineadas al horizonte recortado.
    H = sc["horizonte"]
    assert H > 0 and len(sc["recaudo"]["total"]) == H == len(sc["absorcion"]["ventas"])
    # La absorción reconcilia: el acumulado de ventas llega a las unidades del proyecto.
    assert abs(sc["absorcion"]["acum_ventas"][-1] - sc["unidades_total"]) <= 1
    # Recaudo con caja real (separación + cuota inicial + subrogación).
    assert sum(sc["recaudo"]["total"]) > 0


@pytest.mark.skipif(NAV not in SLUGS, reason="Navarra no disponible")
def test_wacc_fiel_al_motor():
    """El build-up CAPM expone lo que el motor calcula; WACC Navarra ~21.54% (cifra dorada)."""
    w = client.get(f"/v1/scenarios/{NAV}:base/wacc").json()
    assert w["disponible"] is True
    # Cifra dorada del build-up (k.beta): WACC Navarra ~21.54%.
    assert 0.21 <= w["wacc"] <= 0.22
    # Cadena coherente: reapalancada > desapalancada > 0; Ke COP > Ke USD (riesgo país + inflación).
    assert w["beta_l"] > w["beta_u"] > 0
    assert w["ke_cop"] > w["ke_usd"]
    # Pesos suman 1 y las contribuciones suman el WACC.
    assert abs(w["we"] + w["wd"] - 1.0) < 1e-9
    assert abs(w["aporte_equity"] + w["aporte_deuda"] - w["wacc"]) < 1e-9
    # Fidelidad: el WACC expuesto == el del motor (apalancamiento).
    R = calcular(repo.cargar(NAV))
    assert abs(w["wacc"] - R["apalancamiento"]["wacc"]) < 1e-9


def test_404_proyecto_inexistente():
    assert client.get("/v1/projects/no_existe").status_code == 404
    assert client.get("/v1/scenarios/no_existe:base/results").status_code == 404


class _FakeQuery:
    """Encadena select/eq/in_/order/limit como el cliente de supabase, ignorando filtros."""
    def __init__(self, data):
        self._data = data

    def select(self, *a, **k):
        return self

    eq = in_ = order = limit = select

    def execute(self):
        import types as _t
        return _t.SimpleNamespace(data=self._data)


class _FakeSB:
    def __init__(self, tablas):
        self._t = tablas

    def table(self, nombre):
        return _FakeQuery(self._t.get(nombre, []))


def test_fase1_cut_over_lectura_a_scenarios(monkeypatch):
    """Fase 1: con Supabase, cargar() lee el snapshot del escenario (modelo objetivo); la palanca
    ALEPH_READ_SCENARIOS=false revierte a `proyectos.data` (espejo de respaldo)."""
    snap = {"meta": {"nombre": "X"}, "etapas": [{"und": 1}]}
    monkeypatch.setattr(repo, "_usa_supabase", lambda: True)

    # cut-over ON (default): lee de projects→scenarios.snapshot
    monkeypatch.delenv("ALEPH_READ_SCENARIOS", raising=False)
    monkeypatch.setattr(repo, "_cliente", lambda: _FakeSB(
        {"projects": [{"id": "p1", "slug": "x", "es_real": True}],
         "scenarios": [{"snapshot": snap, "status": "approved", "version": 1}]}))
    assert repo.cargar("x") == snap          # snapshot del escenario
    assert repo.es_real("x") is True         # projects.es_real
    assert repo.listar() == ["x"]            # projects.slug

    # palanca de rollback: lee de `proyectos.data`
    monkeypatch.setenv("ALEPH_READ_SCENARIOS", "false")
    monkeypatch.setattr(repo, "_cliente", lambda: _FakeSB({"proyectos": [{"data": {"viejo": True}}]}))
    assert repo.cargar("x") == {"viejo": True}


def test_health_data():
    """Salud de datos público (no sensible): fuente + nº de proyectos. Sirve para verificar el deploy."""
    j = client.get("/health/data").json()
    assert j["data_source"] in ("supabase", "local")
    assert j["project_count"] == len(SLUGS)


def test_portfolio_fail_loud_503_si_data_required_y_sin_datos(monkeypatch):
    """En prod la imagen NO trae respaldo local: 0 proyectos = la fuente cayó → 503, no 200 vacío."""
    monkeypatch.setattr(repo, "listar", lambda: [])
    monkeypatch.setenv("ALEPH_DATA_REQUIRED", "true")
    assert client.get("/v1/portfolio").status_code == 503


def test_portfolio_sin_data_required_sigue_devolviendo_vacio(monkeypatch):
    """Sin el flag (dev/CI), 0 proyectos sigue dando 200 con portafolio vacío (comportamiento previo)."""
    monkeypatch.setattr(repo, "listar", lambda: [])
    monkeypatch.delenv("ALEPH_DATA_REQUIRED", raising=False)
    r = client.get("/v1/portfolio")
    assert r.status_code == 200
    assert r.json()["consolidado"]["n"] == 0
