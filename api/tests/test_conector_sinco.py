# -*- coding: utf-8 -*-
"""Fase 1 · Paso 1 — conector SINCO de actuals: transformación pura + conexión mockeada. SIN red.

Prueba el roll-up PV/EV/AC/BAC por proyecto·nivel·periodo con un FIXTURE que simula filas de
`ControlProyecto`, sin tocar SINCO en vivo (la conexión real se mockea / inyecta). No toca el motor,
ni el dorado, ni Supabase. NO requiere `pymssql` instalado (el import del driver es perezoso).
"""
from datetime import date

import pytest

from aleph_api.conectores import sinco

# Mapeo de PRUEBA: nombres de columna del fixture (NO son los reales de SINCO; eso llega en el Paso 2).
MAPEO_FIXTURE = {
    "proyecto": "proyecto_cod",
    "nivel": "capitulo",
    "periodo": "mes",
    "pv": "valor_planeado",
    "ev": "valor_ganado",
    "ac": "costo_real",
    "bac": "presupuesto_total",
    "corte": "fecha_corte",
}

# Filas crudas de muestra: dos sub-ítems del mismo (proyecto, capítulo, mes) que deben SUMARSE,
# otro capítulo, otro mes, otro proyecto, y filas basura (sin proyecto / sin periodo) que se ignoran.
FIXTURE = [
    {"proyecto_cod": "navarra", "capitulo": "Cimentacion", "mes": "2026-01-01",
     "valor_planeado": "100", "valor_ganado": "90", "costo_real": "95",
     "presupuesto_total": "500", "fecha_corte": "2026-01-31"},
    {"proyecto_cod": "navarra", "capitulo": "Cimentacion", "mes": "2026-01-15",   # mismo mes -> suma
     "valor_planeado": "50", "valor_ganado": "40", "costo_real": "45",
     "presupuesto_total": "250", "fecha_corte": "2026-02-05"},                     # corte más reciente -> gana
    {"proyecto_cod": "navarra", "capitulo": "Estructura", "mes": "2026-01-01",     # otro capítulo
     "valor_planeado": "200", "valor_ganado": "180", "costo_real": "210",
     "presupuesto_total": "800", "fecha_corte": "2026-01-31"},
    {"proyecto_cod": "navarra", "capitulo": "Cimentacion", "mes": "2026-02-01",    # otro mes
     "valor_planeado": "30", "valor_ganado": "25", "costo_real": "28",
     "presupuesto_total": "500", "fecha_corte": "2026-02-28"},
    {"proyecto_cod": "dominica", "capitulo": "Cimentacion", "mes": "2026-01-01",   # otro proyecto
     "valor_planeado": "70", "valor_ganado": "60", "costo_real": "65",
     "presupuesto_total": "300", "fecha_corte": "2026-01-31"},
    {"proyecto_cod": "", "capitulo": "Cimentacion", "mes": "2026-01-01",           # sin proyecto -> se ignora
     "valor_planeado": "9", "valor_ganado": "9", "costo_real": "9"},
    {"proyecto_cod": "navarra", "capitulo": "Acabados", "mes": None,               # sin periodo -> se ignora
     "valor_planeado": "9", "valor_ganado": "9", "costo_real": "9"},
]


def _por_clave(actuals):
    return {(a.proyecto, a.nivel, a.periodo): a for a in actuals}


def test_rollup_suma_pv_ev_ac_por_clave():
    by = _por_clave(sinco.to_actuals(FIXTURE, MAPEO_FIXTURE))
    cim_ene = by[("navarra", "Cimentacion", date(2026, 1, 1))]
    assert cim_ene.pv == 150.0      # 100 + 50
    assert cim_ene.ev == 130.0      # 90 + 40
    assert cim_ene.ac == 140.0      # 95 + 45
    assert cim_ene.bac == 750.0     # 500 + 250 (BAC también se agrega en el roll-up)
    assert cim_ene.corte == date(2026, 2, 5)   # el corte más reciente del grupo
    assert cim_ene.source == "sinco"


def test_separa_niveles_periodos_y_proyectos():
    by = _por_clave(sinco.to_actuals(FIXTURE, MAPEO_FIXTURE))
    # 4 claves válidas (las 2 filas basura se descartan).
    assert len(by) == 4
    assert ("navarra", "Estructura", date(2026, 1, 1)) in by
    assert ("navarra", "Cimentacion", date(2026, 2, 1)) in by
    assert ("dominica", "Cimentacion", date(2026, 1, 1)) in by
    assert by[("navarra", "Cimentacion", date(2026, 2, 1))].pv == 30.0


def test_ignora_filas_sin_clave_minima():
    actuals = sinco.to_actuals(FIXTURE, MAPEO_FIXTURE)
    assert all(a.proyecto and a.periodo for a in actuals)
    assert not any(a.nivel == "Acabados" for a in actuals)  # la de mes=None no entra


def test_nivel_vacio_cae_a_TOTAL():
    filas = [{"proyecto_cod": "x", "capitulo": "", "mes": "2026-03-01",
              "valor_planeado": "1", "valor_ganado": "1", "costo_real": "1"}]
    mapeo = {**MAPEO_FIXTURE, "bac": None, "corte": None}
    out = sinco.to_actuals(filas, mapeo)
    assert len(out) == 1 and out[0].nivel == "TOTAL"
    assert out[0].bac is None and out[0].corte is None


def test_numerico_defensivo_coma_y_none():
    # SQL Server entrega numéricos como float/Decimal; el path de string es defensivo (coma decimal simple).
    filas = [{"proyecto_cod": "x", "capitulo": "C", "mes": "2026-04-01",
              "valor_planeado": "1234,5", "valor_ganado": None, "costo_real": ""}]
    out = sinco.to_actuals(filas, {**MAPEO_FIXTURE, "bac": None, "corte": None})
    assert out[0].pv == 1234.5 and out[0].ev == 0.0 and out[0].ac == 0.0


def test_mapeo_placeholder_falla_en_voz_alta():
    # El mapeo por defecto está en `# TODO` (None) -> debe abortar, no producir basura.
    with pytest.raises(RuntimeError, match="MAPEO_CONTROL_PROYECTO sin definir"):
        sinco.to_actuals(FIXTURE)


def test_as_record_tiene_columnas_de_la_tabla():
    a = sinco.to_actuals(FIXTURE, MAPEO_FIXTURE)[0]
    rec = a.as_record()
    assert set(rec) == {"proyecto", "nivel", "periodo", "pv", "ev", "ac", "bac", "corte", "source"}
    assert rec["periodo"] == "2026-01-01" and rec["source"] == "sinco"


# --- conexión: mockeada / inyectada, sin red ni driver -------------------------------------------
class _FakeCursor:
    def __init__(self, filas):
        self._filas = filas
        self.sql = None

    def execute(self, sql):
        self.sql = sql

    def fetchall(self):
        return self._filas


class _FakeConn:
    def __init__(self, filas):
        self.cursor_obj = _FakeCursor(filas)
        self.cerrada = False

    def cursor(self, as_dict=False):
        return self.cursor_obj

    def close(self):
        self.cerrada = True


def test_leer_control_proyecto_con_conexion_inyectada():
    conn = _FakeConn(FIXTURE)
    filas = sinco.leer_control_proyecto(conn, limit=5)
    assert filas == FIXTURE
    assert conn.cursor_obj.sql == f"SELECT TOP 5 * FROM {sinco.VIEW_CONTROL_PROYECTO}"
    assert conn.cerrada is False   # conn inyectada -> NO la cierra el conector (la maneja quien la pasó)


def test_pipeline_completo_leer_y_transformar_sin_red():
    conn = _FakeConn(FIXTURE)
    actuals = sinco.to_actuals(sinco.leer_control_proyecto(conn), MAPEO_FIXTURE)
    assert _por_clave(actuals)[("navarra", "Cimentacion", date(2026, 1, 1))].ev == 130.0


def test_config_incompleta_falla_sin_tocar_red(monkeypatch):
    for env in (sinco.ENV_SERVER, sinco.ENV_DB, sinco.ENV_USER, sinco.ENV_PASSWORD):
        monkeypatch.delenv(env, raising=False)
    with pytest.raises(RuntimeError, match="Config SINCO incompleta"):
        sinco._config()
