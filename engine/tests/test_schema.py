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

from aleph_engine import schema, config

# Base mínima válida para construir casos de prueba del contrato.
_BASE = {
    "etapas": [{"cod": 1}],
    "costos_pct": {"directos": 0.55, "indirectos": 0.18, "honorarios": 0.08, "util_lote": 0.045},
    "financiero": {},
    "lote_bruto_miles": 1000.0,
}

# Datos en data/ (raíz), reubicados al retirar Streamlit.
RAIZ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
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
        schema.parse({**_BASE, "costos_pct": {"directos": "no-es-numero", "indirectos": 0.18,
                                              "honorarios": 0.08, "util_lote": 0.045}})


# --- Ciclo de vida: campo `estado` (Paso 0 Fase 2) ---

@pytest.mark.parametrize("estado", config.ESTADOS)
def test_estado_valido_se_acepta(estado):
    """Cada estado del ciclo de vida es aceptado y se preserva en el modelo."""
    p = schema.parse({**_BASE, "meta": {"nombre": "X", "estado": estado}})
    assert p.meta.estado == estado


def test_estado_invalido_se_rechaza():
    """Un estado mal escrito (p.ej. 'construcion') se rechaza antes de llegar a la UI."""
    with pytest.raises(ValidationError):
        schema.parse({**_BASE, "meta": {"nombre": "X", "estado": "construcion"}})


def test_estado_ausente_es_valido():
    """estado es opcional (None); el respaldo lo resuelve la capa de presentación."""
    p = schema.parse({**_BASE, "meta": {"nombre": "X"}})
    assert p.meta.estado is None


def test_proyectos_tienen_estado_valido():
    """Todos los proyectos existentes declaran un estado del conjunto válido."""
    for path in PROYECTOS:
        d = json.load(open(path, encoding="utf-8"))
        est = d.get("meta", {}).get("estado")
        assert est in config.ESTADOS, f"{os.path.basename(path)}: estado '{est}' inválido"
