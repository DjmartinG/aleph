# -*- coding: utf-8 -*-
"""Tests del endpoint de valores macro EN VIVO (Fase 2 de Fuentes). NO toca el motor: solo mapea el
dato vivo de Damodaran (CRP→rp, ERP madura→pm) y degrada limpio si la fuente externa falla. Se inyecta
un `fetch` falso → sin red en CI.
"""
from fastapi.testclient import TestClient

from aleph_api import fuentes_live
from aleph_api.conectores.base import ValorMacro
from aleph_api.main import app

client = TestClient(app)


def _fake_ok(pais="Colombia"):
    return [
        ValorMacro(
            clave="damodaran:crp:colombia", nombre="Riesgo país (CRP)", valor=0.0285, unidad="ratio",
            fuente="Damodaran (NYU Stern)", fuente_normativa="Country Risk Premiums (anual)",
            detalle={"fila": ["Colombia", "Baa3", "1.87%", "2.85%", "7.08%", "35.00%"]},
        ),
        ValorMacro(
            clave="damodaran:erp_total:colombia", nombre="ERP total", valor=0.0708, unidad="ratio",
            fuente="Damodaran (NYU Stern)",
        ),
    ]


def _fake_falla(pais="Colombia"):
    raise RuntimeError("fuente caída")


def _fake_trm(clave="trm"):
    return ValorMacro(
        clave="banrep:trm", nombre="TRM (COP/USD)", valor=3433.71, unidad="COP",
        fuente="Banco de la República (SDMX)", detalle={"periodo": "20260626"},
    )


def _fake_trm_falla(clave="trm"):
    raise RuntimeError("Banrep caído")


def test_mapea_rp_y_pm_madura():
    fuentes_live._cache.clear()
    r = fuentes_live.damodaran_colombia(fetch=_fake_ok)
    assert r["disponible"] is True
    assert r["datos"]["rp"]["valor"] == 0.0285
    assert abs(r["datos"]["pm"]["valor"] - 0.0423) < 1e-9  # ERP total 0.0708 − CRP 0.0285
    assert r["rating"] == "Baa3"
    fuentes_live._cache.clear()


def test_degrada_si_la_fuente_falla():
    fuentes_live._cache.clear()
    r = fuentes_live.damodaran_colombia(fetch=_fake_falla)
    assert r["disponible"] is False
    assert r["fuente"] and r["url"]  # sigue identificando la fuente
    fuentes_live._cache.clear()


def test_cachea_por_dia():
    fuentes_live._cache.clear()
    calls = {"n": 0}

    def _contar(pais="Colombia"):
        calls["n"] += 1
        return _fake_ok(pais)

    fuentes_live.damodaran_colombia(fetch=_contar)
    fuentes_live.damodaran_colombia(fetch=_contar)  # segundo: del caché del día
    assert calls["n"] == 1
    fuentes_live._cache.clear()


def test_trm_banrep():
    fuentes_live._cache.clear()
    r = fuentes_live.banrep_trm(fetch=_fake_trm)
    assert r["disponible"] is True
    assert r["valor"] == 3433.71
    assert r["unidad"] == "COP"
    assert r["periodo"] == "20260626"
    assert r["fuente"] and r["url"]
    fuentes_live._cache.clear()


def test_trm_degrada_si_banrep_falla():
    fuentes_live._cache.clear()
    r = fuentes_live.banrep_trm(fetch=_fake_trm_falla)
    assert r["disponible"] is False
    assert r["fuente"] and r["url"]  # sigue identificando la fuente
    fuentes_live._cache.clear()


def test_endpoint_fuentes_live():
    # Sembramos AMBOS cachés del día para no pegarle a la red en CI (auth deshabilitada en dev/CI).
    fuentes_live._cache.clear()
    fuentes_live._cache[fuentes_live._hoy()] = {
        "disponible": True, "fuente": "Damodaran (NYU Stern)", "url": fuentes_live.damodaran.URL,
        "datos": {"rp": {"valor": 0.0285}, "pm": {"valor": 0.0423}},
    }
    fuentes_live._cache[f"trm:{fuentes_live._hoy()}"] = {
        "disponible": True, "fuente": "Banco de la República (SDMX)", "url": fuentes_live.URL_TRM,
        "valor": 3433.71, "unidad": "COP", "periodo": "20260626",
    }
    j = client.get("/v1/fuentes/live").json()
    assert j["disponible"] is True
    assert j["datos"]["rp"]["valor"] == 0.0285
    assert j["trm"]["disponible"] is True and j["trm"]["valor"] == 3433.71
    fuentes_live._cache.clear()
