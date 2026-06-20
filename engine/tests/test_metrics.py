# -*- coding: utf-8 -*-
"""El registro de indicadores (`aleph_engine.metrics`) es consistente y respeta la gobernanza de cifras.

Verifica, contra el resultado real de `calcular()` sobre un snapshot dorado:
  1) cada indicador del registro RESUELVE su ruta en el resultado del motor (no hay rutas muertas);
  2) NINGÚN indicador queda sin ETIQUETA DE BASE (regla innegociable: nunca "TIR" a secas);
  3) `valor()` devuelve el mismo número que está en el dict del motor (es lookup, no cálculo).
"""
import copy
import json

import pytest

from aleph_engine import calcular
from aleph_engine import metrics

from ._golden import find_snapshots

SNAPS = find_snapshots()


def test_todo_indicador_tiene_etiqueta_de_base():
    for clave, m in metrics.REGISTRO.items():
        assert m.etiqueta_base and m.etiqueta_base.strip(), f"{clave} sin etiqueta de base"
        assert m.nombre and m.nombre.strip(), f"{clave} sin nombre"
        # La etiqueta para UI siempre lleva nombre + base.
        assert metrics.etiqueta(clave).startswith(m.nombre)


def test_doble_tir_presente_y_distinta():
    # La TIR doble (proyecto y socio) es obligatoria y son indicadores DISTINTOS.
    assert "tir_proyecto" in metrics.REGISTRO
    assert "tir_socio" in metrics.REGISTRO
    assert metrics.REGISTRO["tir_proyecto"].ruta != metrics.REGISTRO["tir_socio"].ruta


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_incidencia_lote_y_costo_oportunidad():
    """Métricas A2 (curso Camacol): incidencia del lote = lote_bruto/ventas; costo de oportunidad = TIO."""
    snap = json.load(open(SNAPS[0], encoding="utf-8"))
    R = calcular(copy.deepcopy(snap["input_par"]))
    pg = R["pyg"]
    assert "incidencia_lote" in metrics.REGISTRO and "costo_oportunidad" in metrics.REGISTRO
    assert metrics.valor(R, "incidencia_lote") == pytest.approx(pg["lote_bruto"] / pg["ventas"], rel=1e-9)
    assert metrics.valor(R, "costo_oportunidad") == R["apalancamiento"]["tio"]


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_cada_ruta_resuelve_en_el_resultado():
    snap = json.load(open(SNAPS[0], encoding="utf-8"))
    R = calcular(copy.deepcopy(snap["input_par"]))
    for clave, m in metrics.REGISTRO.items():
        sec, k = m.ruta
        assert isinstance(R.get(sec), dict), f"{clave}: sección '{sec}' ausente en el resultado"
        assert k in R[sec], f"{clave}: clave '{k}' ausente en R['{sec}']"
        # valor() es lookup puro: devuelve exactamente lo que el motor calculó.
        assert metrics.valor(R, clave) == R[sec][k]
