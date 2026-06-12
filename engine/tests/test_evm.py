# -*- coding: utf-8 -*-
"""Fórmula EVM compartida (`evm.indices`) y `evm.calcular_evm`.

Punto 7 del desacople: la fórmula EVM (CPI/SPI/EAC/VAC) vive en `evm.indices` y la usan tanto el EVM
del modelo como el control de presupuesto real de la app. Verifica las identidades EVM y que el EAC
bottom-up (proyección por partida) se respeta cuando se pasa.
"""
import copy
import json

import pytest

from aleph_engine import calcular, evm

from ._golden import find_snapshots

SNAPS = find_snapshots()


def test_indices_identidades():
    # EV = avance × BAC; CPI = EV/AC; EAC por índice = BAC/CPI; VAC = BAC − EAC.
    ix = evm.indices(1000.0, 400.0, avance=0.5)         # EV=500, CPI=1.25
    assert ix["EV"] == pytest.approx(500.0)
    assert ix["CPI"] == pytest.approx(1.25)
    assert ix["EAC"] == pytest.approx(1000.0 / 1.25)    # = 800
    assert ix["VAC"] == pytest.approx(1000.0 - 800.0)
    assert ix["CV"] == pytest.approx(500.0 - 400.0)

    # EAC bottom-up (pasado explícito) se RESPETA, no se recalcula por índice.
    ix2 = evm.indices(1000.0, 400.0, EV=500.0, EAC=920.0)
    assert ix2["EAC"] == 920.0
    assert ix2["VAC"] == pytest.approx(1000.0 - 920.0)


def test_indices_sin_denominador():
    ix = evm.indices(1000.0, 0.0, avance=0.5)           # AC=0 → CPI/EAC indefinidos
    assert ix["CPI"] is None and ix["EAC"] is None
    assert ix["SPI"] is None                            # PV no provisto


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_calcular_evm_identidades():
    par = copy.deepcopy(json.load(open(SNAPS[0], encoding="utf-8"))["input_par"])
    for i, e in enumerate(par.get("etapas", [])):       # sembrar avance/costo reales
        e["avance_real"] = 0.4 + 0.1 * i
        e["costo_real"] = 1_000_000 * (i + 1)
    R = calcular(copy.deepcopy(par))
    ev = evm.calcular_evm(par, R)
    assert ev is not None
    # Identidades EVM que el refactor a indices() debe preservar.
    if ev["AC"]:
        assert ev["CPI"] == pytest.approx(ev["EV"] / ev["AC"])
        assert ev["EAC"] == pytest.approx(ev["BAC"] / ev["CPI"])
        assert ev["VAC"] == pytest.approx(ev["BAC"] - ev["EAC"])
        assert ev["CV"] == pytest.approx(ev["EV"] - ev["AC"])
