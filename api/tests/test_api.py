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


def test_404_proyecto_inexistente():
    assert client.get("/v1/projects/no_existe").status_code == 404
    assert client.get("/v1/scenarios/no_existe:base/results").status_code == 404


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
