# -*- coding: utf-8 -*-
"""Tests de la capa de almacenamiento (Paso 1b-ii-B). Por ahora cubre `slugify`, que genera la
clave (PK) de un proyecto NUEVO al crearlo en la nube. Debe ser estable y ascii-safe."""
from storage import slugify


def test_slugify_basico():
    assert slugify("Torres de Campiñas") == "torres_de_campinas"


def test_slugify_acentos_y_enie():
    assert slugify("Navárra Ñandú") == "navarra_nandu"


def test_slugify_colapsa_no_alfanumerico():
    assert slugify("  Proyecto #1 — Fase 2!! ") == "proyecto_1_fase_2"


def test_slugify_vacio_o_solo_simbolos():
    assert slugify("") == "proyecto"
    assert slugify("—  ") == "proyecto"


def test_slugify_idempotente_sobre_un_slug():
    assert slugify("1_navarra") == "1_navarra"
