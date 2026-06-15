# -*- coding: utf-8 -*-
"""Veredicto de Valor (EVA del proyecto). Verifica: (1) los helpers puros, (2) que el motor inyecta
crea_valor/spread_valor/valor_creado SIN mover el dorado, (3) greenfield → sin veredicto.
"""
import json
import os

import pytest

from aleph_engine import calcular
from aleph_engine import valor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data")


# ----------------------------- helpers puros -----------------------------

def test_veredicto_binario_genera_y_destruye():
    crea, spread = valor.veredicto_binario(0.30, 0.20)
    assert crea is True and spread == pytest.approx(0.10)
    crea, spread = valor.veredicto_binario(0.10, 0.20)
    assert crea is False and spread == pytest.approx(-0.10)


def test_veredicto_binario_greenfield_es_none():
    # TIR degenerada (greenfield) o ausente → sin veredicto (jamás un falso "destruye").
    assert valor.veredicto_binario(-0.9999, 0.18) == (None, None)
    assert valor.veredicto_binario(None, 0.18) == (None, None)
    assert valor.veredicto_binario(0.30, None) == (None, None)


def test_vpn_al_wacc_periodicidad():
    # Serie ANUAL: VPN al WACC anual. −100 + 110/1.10 = 0.
    assert valor.vpn_al_wacc([-100, 110], 0.10, anual=True) == pytest.approx(0.0, abs=1e-9)
    # Serie MENSUAL: descuenta a la tasa mensual equivalente (mismo valor presente que la anual).
    m = (1 + 0.10) ** (1 / 12) - 1
    esperado = sum(f / (1 + m) ** t for t, f in enumerate([-100, 50, 60, 30]))
    assert valor.vpn_al_wacc([-100, 50, 60, 30], 0.10, anual=False) == pytest.approx(esperado)
    # INVARIANTE: VPN@WACC > 0  ⟺  TIR(serie) > WACC. Serie con TIR alta, WACC bajo → positivo.
    assert valor.vpn_al_wacc([-1000, 400, 500, 600], 0.10, anual=True) > 0


# ----------------------------- motor: ilustrativos (corren en CI) -----------------------------

def test_dominica_ilustrativo_genera_valor():
    """Dominica ilustrativa: TIR proyecto ≈ 22,7% > WACC 18,71% → GENERA valor (crea_valor=True)."""
    par = json.load(open(os.path.join(DATA, "proyectos", "2_dominica.json"), encoding="utf-8"))
    ap = calcular(par)["apalancamiento"]
    assert ap["crea_valor"] is True
    assert ap["spread_valor"] == pytest.approx(ap["tir_proyecto"] - ap["wacc"])
    assert ap["spread_valor"] > 0
    assert ap["valor_creado"] > 0            # coherente: TIR > WACC → VPN@WACC positivo


def test_navarra_ilustrativo_greenfield_sin_veredicto():
    """El ilustrativo de Navarra tiene TIR proyecto degenerada (1 etapa) → sin veredicto."""
    par = json.load(open(os.path.join(DATA, "proyectos", "1_navarra.json"), encoding="utf-8"))
    ap = calcular(par)["apalancamiento"]
    assert ap["crea_valor"] is None and ap["spread_valor"] is None


# ----------------------------- motor: REALES (dorado; se saltan en CI) -----------------------------

_NAV = os.path.join(DATA, "proyectos_privados", "1_navarra_REAL.json")
_TOR = os.path.join(DATA, "proyectos_privados", "3_torres_campinas_REAL.json")


@pytest.mark.skipif(not os.path.exists(_NAV), reason="Navarra REAL no disponible (CI sin datos privados)")
def test_navarra_real_genera_valor_y_dorado_intacto():
    ap = calcular(json.load(open(_NAV, encoding="utf-8")))["apalancamiento"]
    # DORADO INTACTO (el veredicto es aditivo, no mueve estas cifras):
    assert ap["tir_proyecto"] == pytest.approx(0.375975, abs=1e-4)   # 37,60%
    assert ap["vpn_proyecto"] == pytest.approx(18280687.67, rel=1e-5)  # VPN@TIO 18,28 mil M
    # VEREDICTO: TIR 37,60% > WACC 18,71% → GENERA; spread ≈ +18,9 pp; valor creado positivo.
    assert ap["crea_valor"] is True
    assert ap["spread_valor"] == pytest.approx(0.375975 - ap["wacc"], abs=1e-4)
    assert ap["spread_valor"] == pytest.approx(0.1888, abs=2e-3)
    assert ap["valor_creado"] > 0
    # El valor_creado @WACC es MENOR que el VPN@TIO (WACC 18,71% > TIO 15%) pero positivo.
    assert ap["valor_creado"] < ap["vpn_proyecto"]


@pytest.mark.skipif(not os.path.exists(_TOR), reason="Torres REAL no disponible (CI sin datos privados)")
def test_torres_real_greenfield_sin_veredicto():
    ap = calcular(json.load(open(_TOR, encoding="utf-8")))["apalancamiento"]
    assert ap["crea_valor"] is None and ap["spread_valor"] is None   # TIR degenerada → "— greenfield"
