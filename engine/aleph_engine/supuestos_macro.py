# -*- coding: utf-8 -*-
"""Registro ÚNICO de supuestos macro/financieros con METADATOS (valor, fuente, fecha, método).

M0 (Spec `directives/spec_pyg_dinamico.md`). **Capa ADITIVA y no-destructiva:** los DEFAULTS
numéricos provienen de `config.py` (no se duplica ni se mueve ninguna cifra). Este módulo añade,
sobre cada default, su procedencia (fuente/fecha/método) y un `resolver()` con la regla de
**precedencia** que el motor ya aplica hoy de forma dispersa:

    el `par` del proyecto (bloque `financiero`) MANDA; el default macro solo rellena AUSENCIAS.

Es decir, `resolver(financiero, clave)` ≡ `financiero.get(clave, DEFAULT_config)` — misma semántica
que los `fin.get("renta", config.RENTA)` repartidos por `modelo.py`/`apalancamiento.py`. M0 NO
reconecta esos call-sites (para garantizar dorado intacto); deja la pieza lista para que M1/M6 la
usen como fuente única. Las cifras de Navarra/Dominica/TDC NO cambian.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import config


@dataclass(frozen=True)
class Supuesto:
    """Un supuesto macro/financiero con su procedencia. `valor` es el DEFAULT (= config);
    el proyecto puede sobreescribirlo en su bloque `financiero`."""
    clave: str
    nombre: str
    valor: float
    unidad: str                         # ratio | ratio_ea | COP_miles | meses
    fuente: str                         # de dónde sale el dato (Banrep, DANE, SFC, Damodaran, Comité CG…)
    metodo: str                         # "config" | "api" | "manual" | "benchmark"
    descripcion: str = ""
    fecha: date | None = None           # corte del dato (None = constante de política, sin fecha)
    estado_validacion: str = "vigente"  # vigente | por_validar  (alimenta los [VALIDAR] de M1/M2)
    fuente_normativa: str = ""          # norma/fuente puntual (ET, decreto, serie Banrep…)


# Registro. La CLAVE coincide con la del bloque `financiero` del proyecto (para que `resolver`
# espeje exactamente los `fin.get(clave, default)` de hoy). El `valor` toma el default de config:
# una sola fuente numérica, cero cifras nuevas.
REGISTRO: dict[str, Supuesto] = {
    "tio": Supuesto(
        "tio", "TIO (tasa de oportunidad)", config.TIO, "ratio_ea", "Comité CG", "config",
        "Tasa interna de oportunidad / hurdle de descuento del VPN."),
    "renta": Supuesto(
        "renta", "Tasa de renta", config.RENTA, "ratio", "DIAN / Estatuto Tributario", "config",
        "Renta sobre el reintegro sin lote. OJO: hoy plana; la exención VIS se modela en M2.",
        estado_validacion="por_validar", fuente_normativa="ET Art. 240 (35%) · 235-2 num.4 (exención VIS)"),
    "split_cg": Supuesto(
        "split_cg", "Reparto CG", config.SPLIT_CG, "ratio", "Estructura societaria CG", "config",
        "Fracción de la utilidad operativa que corresponde a CG (resto al socio)."),
    "tasa_credito_ea": Supuesto(
        "tasa_credito_ea", "Tasa crédito constructor", config.TASA_CREDITO_EA, "ratio_ea",
        "SFC / banco (negociada)", "config",
        "Tasa EA del crédito constructor. M6: tabla por banco (IBR/DTF + spread).",
        estado_validacion="por_validar", fuente_normativa="SFC Formato 414 (referencia) · spread negociado CG"),
    "cobertura_cc": Supuesto(
        "cobertura_cc", "Cobertura crédito constructor", config.COBERTURA_CC, "ratio",
        "Política bancaria", "config",
        "Cobertura del crédito constructor sobre el valor financiable (~80% del costo de obra)."),
    "pct_ci": Supuesto(
        "pct_ci", "Cuota inicial", config.PCT_CI, "ratio", "Política comercial CG", "config",
        "Fracción de cuota inicial sobre el precio de la unidad."),
    "sep_und_miles": Supuesto(
        "sep_und_miles", "Separación por unidad", config.SEP_UND_MILES, "COP_miles",
        "Política comercial CG", "config", "Valor de separación por unidad (miles COP)."),
    "diferido_sep": Supuesto(
        "diferido_sep", "Diferido de separación", config.DIFERIDO_SEP, "meses",
        "Política comercial CG", "config", "Meses en que se difiere la separación desde la venta."),
}


def default(clave: str):
    """Default macro (= config) de un supuesto, o None si no está registrado."""
    s = REGISTRO.get(clave)
    return s.valor if s is not None else None


def resolver(financiero: dict | None, clave: str, fallback=None):
    """Valor efectivo del supuesto con PRECEDENCIA: el `par` del proyecto manda; el macro rellena
    ausencias. Espeja `financiero.get(clave, default(clave))` — misma semántica que los `fin.get`
    de hoy. `fallback` cubre el caso de una clave no registrada (mantiene compatibilidad).
    """
    if financiero is not None and clave in financiero:
        return financiero[clave]
    s = REGISTRO.get(clave)
    if s is not None:
        return s.valor
    return fallback


def listar() -> list[Supuesto]:
    """Todos los supuestos del registro (para UI/API y para sembrar la tabla `supuestos_macro`)."""
    return list(REGISTRO.values())
