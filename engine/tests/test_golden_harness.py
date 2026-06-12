# -*- coding: utf-8 -*-
"""Harness del SNAPSHOT DORADO en el engine — la red de seguridad SAGRADA de la migración.

Re-ejecuta `aleph_engine.calcular()` sobre la entrada CONGELADA de cada snapshot y compara TODA la
salida contra el `result` congelado, recursivamente, con tolerancia **0.1% relativa** (abs 1e-6 para
casi-cero). Si cualquier cifra del motor se mueve más de eso, ROMPE EL BUILD.

ESTADO (PROMPT 2.3): `aleph_engine.calcular` AÚN NO existe (se extrae en PROMPT 3). Mientras no
exista, este test se SALTA (skip) — el harness ya está cableado y leyendo los snapshots, listo para
exigir paridad de cifras en cuanto la lógica se porte. Es el equivalente, del lado del engine, de
`app_streamlit/tests/test_golden_snapshot.py`.
"""
import copy
import json
import os

import pytest

from ._golden import find_snapshots

try:
    from aleph_engine import calcular as _calcular   # existirá tras PROMPT 3
except ImportError:
    _calcular = None

SNAPS = find_snapshots()

_TOL_REL = 0.001    # 0.1%
_TOL_ABS = 1e-6


def _norm(obj):
    """Normaliza a JSON puro (fechas/objetos → str), igual que el generador del snapshot."""
    return json.loads(json.dumps(obj, default=str, ensure_ascii=False))


def _desviaciones(esperado, actual, ruta=""):
    """Rutas donde `actual` se desvía de `esperado` más de la tolerancia."""
    out = []
    if isinstance(esperado, bool) or isinstance(actual, bool):
        if esperado != actual:
            out.append(f"{ruta}: {esperado!r} != {actual!r}")
    elif isinstance(esperado, (int, float)) and isinstance(actual, (int, float)):
        if abs(esperado - actual) > max(_TOL_ABS, _TOL_REL * abs(esperado)):
            out.append(f"{ruta}: esperado {esperado} vs actual {actual}")
    elif isinstance(esperado, dict) and isinstance(actual, dict):
        for k in set(esperado) | set(actual):
            out += _desviaciones(esperado.get(k), actual.get(k), f"{ruta}.{k}")
    elif isinstance(esperado, list) and isinstance(actual, list):
        if len(esperado) != len(actual):
            out.append(f"{ruta}: longitud {len(esperado)} != {len(actual)}")
        else:
            for i, (e, a) in enumerate(zip(esperado, actual)):
                out += _desviaciones(e, a, f"{ruta}[{i}]")
    else:
        if esperado != actual:
            out.append(f"{ruta}: {esperado!r} != {actual!r}")
    return out


@pytest.mark.skipif(_calcular is None, reason="aleph_engine.calcular aún no extraído (llega en PROMPT 3)")
@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados (¿falta app_streamlit/tests/golden?)")
@pytest.mark.parametrize("snap_path", SNAPS, ids=lambda p: os.path.basename(p))
def test_snapshot_dorado_no_cambia(snap_path):
    snap = json.load(open(snap_path, encoding="utf-8"))
    fresco = _norm(_calcular(copy.deepcopy(snap["input_par"])))
    desv = _desviaciones(snap["result"], fresco)
    assert not desv, (f"{len(desv)} cifras del motor se movieron > 0.1% en {os.path.basename(snap_path)}:\n"
                      + "\n".join(desv[:25]))
