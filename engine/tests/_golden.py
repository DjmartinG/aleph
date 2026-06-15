# -*- coding: utf-8 -*-
"""Localización de los snapshots dorados de la migración (fuente única).

Los snapshots viven en `engine/tests/golden/` (se movieron aquí al RETIRAR Streamlit, jun-2026;
antes vivían en app_streamlit/tests/golden/). El harness del engine los LEE de su carpeta hermana.
Los `*_REAL_snapshot.json` (datos confidenciales, gitignored) se incluyen solo en local.
"""
from __future__ import annotations

import glob
import os


def golden_dir() -> str:
    """Carpeta de los snapshots dorados: `engine/tests/golden/` (hermana de este archivo)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden")


def find_snapshots() -> list[str]:
    """Todos los snapshots dorados (ilustrativos commiteados + REALES locales), ordenados."""
    d = golden_dir()
    if not os.path.isdir(d):
        return []
    return sorted(glob.glob(os.path.join(d, "*_snapshot.json")))
