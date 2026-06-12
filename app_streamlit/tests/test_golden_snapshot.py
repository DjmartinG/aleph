# -*- coding: utf-8 -*-
"""Harness del SNAPSHOT DORADO de la migración ALEPH (PROMPT 2.1) — la red de seguridad SAGRADA.

Por cada snapshot en `tests/golden/*_snapshot.json`: re-ejecuta `calcular()` sobre la entrada
CONGELADA (`input_par`) y compara TODA la salida contra el `result` congelado, recursivamente, con
tolerancia **0.1% relativa** (abs 1e-6 para casi-cero). Si cualquier cifra del motor se mueve más
de eso, ESTE TEST ROMPE EL BUILD. Es el contrato de "la migración no cambia ninguna cifra".

Los snapshots de proyectos REALES (`*_REAL_snapshot.json`) están gitignored (datos reales) y solo
corren en local; los ilustrativos (`*_snapshot.json`) se commitean y corren en CI.
"""
import copy
import glob
import json
import os

import pytest

from aleph_engine import calcular

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPS = sorted(glob.glob(os.path.join(RAIZ, "tests", "golden", "*_snapshot.json")))

_TOL_REL = 0.001    # 0.1%
_TOL_ABS = 1e-6


def _norm(obj):
    """Normaliza a JSON puro (fechas/objetos → str), igual que el generador."""
    return json.loads(json.dumps(obj, default=str, ensure_ascii=False))


def _desviaciones(esperado, actual, ruta=""):
    """Lista de rutas donde `actual` se desvía de `esperado` más de la tolerancia."""
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


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados; corre execution/snapshot_dorado.py")
@pytest.mark.parametrize("snap_path", SNAPS, ids=lambda p: os.path.basename(p))
def test_snapshot_dorado_no_cambia(snap_path):
    snap = json.load(open(snap_path, encoding="utf-8"))
    fresco = _norm(calcular(copy.deepcopy(snap["input_par"])))
    desv = _desviaciones(snap["result"], fresco)
    assert not desv, (f"{len(desv)} cifras del motor se movieron > 0.1% en {os.path.basename(snap_path)}:\n"
                      + "\n".join(desv[:25]))
