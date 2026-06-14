# -*- coding: utf-8 -*-
"""M6 (spec_pyg_dinamico.md) — conector Socrata de tasas por banco: parser DEFENSIVO, sin red.

Usa muestras (fixtures) con la forma real del dataset SFC/datos.gov.co. No toca la red ni Supabase
ni el motor: valida el filtrado/normalización y la robustez ante nombres de columna con tilde.
"""
from datetime import date

from aleph_api.conectores import socrata
from aleph_api.conectores.base import parse_fecha_iso, slug

FIXTURE = [
    {"nombre_entidad": "Bancolombia S.A.", "tipo_de_credito": "Vivienda",
     "producto_de_credito": "Adquisicion de vivienda no vis (colocacion en pesos)",
     "tasa_efectiva_promedio": "11.20", "fecha_corte": "2026-05-01T00:00:00.000"},
    {"nombre_entidad": "Banco Davivienda S.A.", "tipo_de_credito": "Vivienda",
     "producto_de_credito": "Adquisicion de vivienda VIS (colocacion en pesos)",
     "tasa_efectiva_promedio": "9.85", "fecha_corte": "2026-05-01"},
    {"nombre_entidad": "Bancolombia S.A.", "tipo_de_credito": "Comercial ordinario",
     "producto_de_credito": "capital de trabajo", "tasa_efectiva_promedio": "18.0"},
    {"nombre_entidad": "Banco X", "tipo_de_credito": "Vivienda",
     "producto_de_credito": "no vis", "tasa_efectiva_promedio": None},
    {"nombre_entidad": "Itau", "tipo_de_credito": "Vivienda",
     "producto_de_credito": "no vis", "tasa_efectiva_promedio": "10,5"},
]


def test_parse_solo_vivienda_con_tasa():
    claves = {v.clave for v in socrata.parse_tasas_vivienda(FIXTURE)}
    assert any("bancolombia" in c and c.endswith("no_vis") for c in claves)
    assert any("davivienda" in c and c.endswith(":vis") for c in claves)
    assert any("itau" in c for c in claves)
    assert not any("comercial" in c for c in claves)


def test_vis_vs_no_vis_y_valor():
    vals = {v.clave: v for v in socrata.parse_tasas_vivienda(FIXTURE)}
    dav = next(v for k, v in vals.items() if "davivienda" in k)
    assert dav.detalle["vis"] is True and dav.valor == 9.85 and dav.unidad == "pct_ea"
    ban = next(v for k, v in vals.items() if "bancolombia" in k)
    assert ban.detalle["vis"] is False and ban.valor == 11.20


def test_coma_decimal():
    vals = socrata.parse_tasas_vivienda([FIXTURE[4]])
    assert vals and vals[0].valor == 10.5


def test_filtro_por_banco():
    vals = socrata.parse_tasas_vivienda(FIXTURE, bancos=("Davivienda",))
    assert len(vals) == 1 and "davivienda" in vals[0].clave


def test_fetch_usa_get_inyectado_sin_red():
    captura = {}

    def fake_get(url, params=None):
        captura["url"], captura["params"] = url, params
        return FIXTURE

    vals = socrata.fetch_tasas_vivienda(get=fake_get)
    assert "tipo_de_credito" not in captura["params"]
    assert captura["params"]["$order"] == ":id DESC"
    assert len(vals) >= 3


def test_robusto_ante_columnas_con_tilde():
    filas = [
        {"nombre_entidad": "BBVA Colombia S.A.", "tipo_de_cr_dito": "Vivienda",
         "producto_de_cr_dito": "Adquisicion de vivienda VIS", "tasa_efectiva_promedio": "9.10",
         "fecha_corte": "2026-04-25"},
    ]
    vals = socrata.parse_tasas_vivienda(filas)
    assert len(vals) == 1
    assert "bbva" in vals[0].clave and vals[0].clave.endswith(":vis")
    assert vals[0].valor == 9.10


def test_helpers():
    assert slug("Banco Davivienda S.A.") == "banco_davivienda_s_a"
    assert parse_fecha_iso("2026-05-01T00:00:00.000") == date(2026, 5, 1)
    assert parse_fecha_iso(None) is None


def test_consolida_una_por_banco_la_mas_reciente():
    filas = [
        {"nombre_entidad": "Itau", "tipo_de_credito": "Vivienda", "producto_de_credito": "no vis",
         "tasa_efectiva_promedio": "13.59", "fecha_corte": "2026-05-08"},
        {"nombre_entidad": "Itau", "tipo_de_credito": "Vivienda", "producto_de_credito": "no vis",
         "tasa_efectiva_promedio": "13.20", "fecha_corte": "2026-05-22"},  # más reciente → gana
        {"nombre_entidad": "Itau", "tipo_de_credito": "Vivienda", "producto_de_credito": "no vis",
         "tasa_efectiva_promedio": "13.49", "fecha_corte": "2026-05-08"},
    ]
    vals = socrata.consolidar_por_clave(socrata.parse_tasas_vivienda(filas))
    assert len(vals) == 1 and vals[0].valor == 13.20
