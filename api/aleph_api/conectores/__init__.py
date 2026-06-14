"""Conectores de datos macro de ALEPH (M6 · spec_pyg_dinamico.md).

Cada conector LEE una fuente externa (Banrep, datos.gov.co/SFC, Damodaran, DANE) y devuelve
`ValorMacro` normalizados. **Capa de SOLO LECTURA / preview:** no escriben en Supabase, no tocan el
motor y no mueven ninguna cifra. El cableado a `supuestos_macro` (con compuerta de revisión) y la
tarea programada llegan en incrementos posteriores de M6.
"""
from .base import ValorMacro, get_json

__all__ = ["ValorMacro", "get_json"]
