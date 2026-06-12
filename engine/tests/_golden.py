# -*- coding: utf-8 -*-
"""Localización de los snapshots dorados de la migración (fuente única).

Los snapshots viven en `app_streamlit/tests/golden/` (los generó PROMPT 2.1) y NO se duplican aquí:
el harness del engine los LEE desde ahí. Así hay un solo conjunto de cifras doradas para toda la
migración, y los `*_REAL_snapshot.json` (datos confidenciales, gitignored) se incluyen en local sin
riesgo de copiarse al repo del engine.
"""
from __future__ import annotations

import glob
import os


def repo_root() -> str | None:
    """Sube desde este archivo hasta la raíz del monorepo (la que contiene `engine` y
    `app_streamlit`). Devuelve None si no la encuentra (p.ej. el engine instalado suelto)."""
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(d, "engine")) and os.path.isdir(os.path.join(d, "app_streamlit")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def golden_dir() -> str | None:
    root = repo_root()
    return os.path.join(root, "app_streamlit", "tests", "golden") if root else None


def find_snapshots() -> list[str]:
    """Todos los snapshots dorados (ilustrativos commiteados + REALES locales), ordenados."""
    d = golden_dir()
    if not d or not os.path.isdir(d):
        return []
    return sorted(glob.glob(os.path.join(d, "*_snapshot.json")))
