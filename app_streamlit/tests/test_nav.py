# -*- coding: utf-8 -*-
"""Tests del menú adaptativo al estado del ciclo de vida (Paso 1c-1). Verifica que Seguimiento
aparezca SOLO en construcción/entregado y Administración solo para quien puede ingresar."""
from aleph_engine import config as cfg
from ui import nav


def test_factibilidad_y_tablero_siempre():
    g = nav.grupos(cfg.ESTADO_PREFACT, puede_ingresar=False)
    assert "Tablero" in g and "Factibilidad" in g


def test_seguimiento_oculto_en_prefact_y_aprobado():
    for est in (cfg.ESTADO_PREFACT, cfg.ESTADO_APROBADO):
        assert "Seguimiento" not in nav.grupos(est, puede_ingresar=True)


def test_seguimiento_visible_en_construccion_y_entregado():
    for est in (cfg.ESTADO_CONSTRUCCION, cfg.ESTADO_ENTREGADO):
        assert "Seguimiento" in nav.grupos(est, puede_ingresar=False)


def test_administracion_solo_si_puede_ingresar():
    assert "Administración" not in nav.grupos(cfg.ESTADO_CONSTRUCCION, puede_ingresar=False)
    assert "Administración" in nav.grupos(cfg.ESTADO_CONSTRUCCION, puede_ingresar=True)


def test_orden_de_areas():
    # El orden de inserción gobierna el orden visual: Tablero, Factibilidad, [Seguimiento], [Administración].
    g = nav.grupos(cfg.ESTADO_CONSTRUCCION, puede_ingresar=True)
    assert list(g.keys()) == ["Tablero", "Factibilidad", "Seguimiento", "Administración"]


def test_areas_tienen_icono():
    for area in nav.grupos(cfg.ESTADO_CONSTRUCCION, puede_ingresar=True):
        assert area in nav.AREA_ICON
