# -*- coding: utf-8 -*-
"""Tests del módulo `finanzas` — TIR/VPN únicas y consistentes (Paso 2 Fase 1).

Justifican y blindan la consolidación de la TIR (antes duplicada en modelo.py y apalancamiento.py):
los métodos coinciden, la TIR hace VPN≈0, y los valores de libro son correctos.
"""
import pytest

from cg_engine import finanzas


def test_vpn():
    # A tasa 0, el VPN es la suma simple.
    assert finanzas.vpn([-100, 50, 60], 0.0) == pytest.approx(10.0)
    # -100 + 110/1.10 = 0
    assert finanzas.vpn([-100, 110], 0.10) == pytest.approx(0.0, abs=1e-9)


def test_irr_hace_vpn_cero():
    """La TIR es, por definición, la tasa que anula el VPN."""
    for flujo in ([-1000, 300, 400, 500], [-500, 50, 600], [-8000, 2000, 3000, 4000, 1000]):
        r = finanzas.irr_periodo(flujo)
        assert r is not None
        assert finanzas.vpn(flujo, r) == pytest.approx(0.0, abs=1e-6)


def test_brentq_y_biseccion_coinciden():
    """Los dos métodos (brentq-escaneo y bisección) dan la MISMA raíz sobre series con un único
    cambio de signo. Es la justificación de tener una sola fuente de verdad para la TIR."""
    for flujo in ([-1000, 300, 400, 500], [-500, 50, 600], [-8000, 2000, 3000, 4000, 1000]):
        a = finanzas.irr_periodo(flujo)
        b = finanzas.irr_biseccion(flujo)
        assert a == pytest.approx(b, abs=1e-6), f"brentq {a} vs bisección {b} en {flujo}"


def test_irr_anual_anualiza_la_mensual():
    flujo = [-1000, 100, 100, 100, 900]
    m = finanzas.irr_periodo(flujo)
    assert finanzas.irr_anual(flujo) == pytest.approx((1 + m) ** 12 - 1, rel=1e-12)


def test_sin_raiz_devuelve_none():
    assert finanzas.irr_periodo([100, 110]) is None      # todo positivo: sin cambio de signo
    assert finanzas.irr_biseccion([100, 110]) is None


def test_wacc_estructura_y_estabilidad():
    """calcular_wacc devuelve un float (sin detalle) y un dict con los eslabones (con detalle),
    coherentes entre sí, sobre los parámetros WACC del proyecto ilustrativo del repo."""
    import json
    import os
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    par = json.load(open(os.path.join(raiz, "proyectos", "2_dominica.json"), encoding="utf-8"))
    w = par["financiero"]["wacc"]
    wacc = finanzas.calcular_wacc(w)
    det = finanzas.calcular_wacc(w, detalle=True)
    assert isinstance(wacc, float)
    assert det["wacc"] == pytest.approx(wacc)
    assert 0.0 < wacc < 1.0      # un WACC sensato (entre 0% y 100%)
