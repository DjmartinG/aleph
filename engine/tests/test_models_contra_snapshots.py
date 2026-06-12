# -*- coding: utf-8 -*-
"""El contrato de datos (`aleph_engine.models`) acepta la entrada REAL de cada proyecto.

Prueba que el `input_par` congelado en cada snapshot dorado parsea SIN error contra los modelos
Pydantic del engine. Es la validación que SÍ podemos exigir hoy (esqueleto): demuestra que el
contrato refleja la forma real de los datos de los 3 proyectos, antes de extraer la lógica financiera.
"""
import json
import os

import pytest

from aleph_engine import Proyecto, parse

from ._golden import find_snapshots

SNAPS = find_snapshots()


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados (¿falta app_streamlit/tests/golden?)")
@pytest.mark.parametrize("snap_path", SNAPS, ids=lambda p: os.path.basename(p))
def test_input_par_cumple_el_contrato(snap_path):
    snap = json.load(open(snap_path, encoding="utf-8"))
    modelo = parse(snap["input_par"])      # lanza ValidationError si el dict no cumple el contrato
    assert isinstance(modelo, Proyecto)
    assert modelo.etapas, "el proyecto debe tener al menos una etapa"
