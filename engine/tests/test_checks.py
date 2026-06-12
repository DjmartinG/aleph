# -*- coding: utf-8 -*-
"""Los checks de cuadre (`aleph_engine.checks`) PASAN para todos los proyectos dorados.

Si el motor produjera un resultado internamente inconsistente (P&G que no suma, recaudo que no cuadra
con ventas, flujo que no cierra en la utilidad, reparto descuadrado, cupo de crédito imposible), estos
checks lo atraparían. Que pasen sobre las cifras AUDITADAS es la prueba de que las reconciliaciones
están bien definidas.
"""
import copy
import json
import os

import pytest

from aleph_engine import calcular, checks

from ._golden import find_snapshots

SNAPS = find_snapshots()


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
@pytest.mark.parametrize("snap_path", SNAPS, ids=lambda p: os.path.basename(p))
def test_cuadres_pasan(snap_path):
    snap = json.load(open(snap_path, encoding="utf-8"))
    R = calcular(copy.deepcopy(snap["input_par"]))
    cs = checks.correr(R)
    assert cs, "no se evaluó ningún check (resultado sin pyg/apalancamiento)"
    fallidos = [f"{c.clave}: {c.detalle}" for c in cs if not c.ok]
    assert not fallidos, "checks de cuadre FALLARON:\n" + "\n".join(fallidos)


def test_spi_rango():
    # Plausible dentro de rango, implausible fuera.
    assert checks.check_spi({"SPI": 1.0}).ok
    assert checks.check_spi({"SPI": 0.5}).ok
    assert not checks.check_spi({"SPI": 3.0}).ok
    assert not checks.check_spi({"SPI": 0.1}).ok
    assert not checks.check_spi({}).ok
