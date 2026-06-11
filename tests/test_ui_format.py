# -*- coding: utf-8 -*-
"""Tests del formato único (Paso 1a Fase 2). Clava el formateo de moneda/porcentaje para que la
centralización no cambie lo que se muestra y para evitar regresiones futuras."""
from ui.format import fmt_cop, fmt_mm, fmt_pct


def test_fmt_cop_millones():
    assert fmt_cop(50000) == "$50 M"          # 50.000 miles = 50 M


def test_fmt_cop_mil_millones():
    assert fmt_cop(1_500_000) == "$1.5 mil M"  # 1.500.000 miles = 1,5 mil M


def test_fmt_cop_separador_de_miles_con_punto():
    assert fmt_cop(250_000) == "$250 M"
    assert fmt_cop(12_000_000) == "$12.0 mil M"


def test_fmt_cop_cero_y_none():
    assert fmt_cop(0) == "$0"
    assert fmt_cop(None) == "$0"


def test_fmt_mm_es_alias_de_fmt_cop():
    assert fmt_mm is fmt_cop


def test_fmt_pct_default_dos_decimales():
    assert fmt_pct(0.2183) == "21.83%"


def test_fmt_pct_decimales_configurables():
    assert fmt_pct(0.5, dec=0) == "50%"


def test_fmt_pct_none():
    assert fmt_pct(None) == "n/d"
