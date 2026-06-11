# -*- coding: utf-8 -*-
"""Tests del contrato de datos (Paso 4 Fase 1).

Verifica que TODOS los proyectos reales e ilustrativos cumplen el contrato (no rompe nada al
introducir la validación) y que un proyecto inválido se rechaza con un error legible.
"""
import glob
import json
import os

import pytest
from pydantic import ValidationError

from cg_engine import schema

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Ilustrativos (en el repo) + reales (gitignored, presentes solo en local). En CI corren los del repo.
PROYECTOS = sorted(glob.glob(os.path.join(RAIZ, "proyectos", "*.json"))) + \
            sorted(glob.glob(os.path.join(RAIZ, "proyectos_privados", "*.json")))


@pytest.mark.parametrize("path", PROYECTOS, ids=lambda p: os.path.basename(p))
def test_proyecto_valida(path):
    """Cada proyecto existente debe pasar la validación del contrato sin lanzar."""
    d = json.load(open(path, encoding="utf-8"))
    p = schema.parse(d)
    assert len(p.etapas) >= 1
    assert p.costos_pct.directos is not None


def test_proyecto_invalido_se_rechaza():
    """Un dict que no cumple lo estructural (etapas vacío, sin costos/financiero) se rechaza."""
    with pytest.raises(ValidationError):
        schema.parse({"etapas": [], "lote_bruto_miles": 1000})


def test_tipo_equivocado_se_rechaza():
    """Un campo numérico con texto se rechaza (lo que hoy se silenciaría con un default)."""
    with pytest.raises(ValidationError):
        schema.parse({
            "etapas": [{"cod": 1}],
            "costos_pct": {"directos": "no-es-numero", "indirectos": 0.18,
                           "honorarios": 0.08, "util_lote": 0.045},
            "financiero": {},
            "lote_bruto_miles": 1000.0,
        })
