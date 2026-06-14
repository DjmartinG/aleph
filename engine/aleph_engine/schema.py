# -*- coding: utf-8 -*-
"""Contrato de datos del proyecto (validación en el BORDE con Pydantic v2).

Hoy el "shape" del proyecto es un dict implícito, reconstruido con `.get()` por todo el código:
un campo mal escrito o de tipo equivocado se silencia con un default y puede corromper una cifra
auditada sin avisar. Este módulo declara el contrato y permite VALIDARLO al entrar (al cargar de
Supabase o desde un futuro ERP/CRM): `schema.parse(dict)` lanza un error legible si los datos no
cumplen, antes de que lleguen al motor.

IMPORTANTE — no transforma los datos: el motor sigue consumiendo el MISMO dict. La validación es
una compuerta, no una conversión (cero riesgo para las cifras). El cableado en la capa de
servicios/almacenamiento llega en fases posteriores.

Diseño: `extra="allow"` porque el shape es heterogéneo y evolutivo (Dominica no trae tipologías ni
fiducia; los reales traen `_nota`, `directos_cap`, etc.). Solo se exige lo estructural que el motor
necesita sí o sí; el resto es opcional (sus defaults viven en config.py).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .config import ESTADOS as _ESTADOS  # fuente única del conjunto válido de estados

# Permisivo: acepta claves extra (el shape varía entre proyectos y crece con el tiempo).
_PERMISIVO = ConfigDict(extra="allow")


class Meta(BaseModel):
    model_config = _PERMISIVO
    nombre: str
    tipo: Optional[str] = None            # "VIS" | "VIP" | "No VIS" (regla de parqueaderos/depósitos)
    unidades: Optional[int] = None
    estado: Optional[str] = None          # ciclo de vida (config.ESTADOS): prefactibilidad|aprobado|construccion|entregado
    # ubicacion, zona, moneda, propietario, socios… → extra

    @field_validator("estado")
    @classmethod
    def _estado_valido(cls, v: Optional[str]) -> Optional[str]:
        """Rechaza estados mal escritos (p.ej. 'construcion') antes de que lleguen a la UI.
        None es válido: el respaldo (config.ESTADO_DEFAULT) lo resuelve la capa de presentación."""
        if v is not None and v not in _ESTADOS:
            raise ValueError(f"estado '{v}' inválido; debe ser uno de {_ESTADOS}")
        return v


class Wacc(BaseModel):
    """Parámetros del build-up CAPM. Opcionales para no rechazar proyectos sin WACC propio;
    `calcular_wacc` exige los suyos cuando se invoca."""
    model_config = _PERMISIVO
    rf: Optional[float] = None
    rm: Optional[float] = None
    beta_us: Optional[float] = None
    de_us: Optional[float] = None
    tax_us: Optional[float] = None
    de_col: Optional[float] = None
    tax_col: Optional[float] = None
    rp: Optional[float] = None
    inf_col: Optional[float] = None
    inf_us: Optional[float] = None
    tasa_d: Optional[float] = None
    spread: Optional[float] = None
    eq_w: Optional[float] = None
    kd_us: Optional[float] = None


class Financiero(BaseModel):
    model_config = _PERMISIVO
    wacc: Optional[Wacc] = None
    # renta, split_cg, pct_ci, sep_und_miles, tasa_credito_ea, cobertura_cc, tio,
    # tir_apalancada_ref, credito_cap_miles… → extra (defaults en config.py)


class CostosPct(BaseModel):
    """Estructura de costos como % de ventas. El motor lee estos cuatro directamente."""
    model_config = _PERMISIVO
    directos: float
    indirectos: float
    honorarios: float
    util_lote: float
    # recon_codensa, hon_construccion, hon_gerencia, hon_ventas → extra (defaults en pyg)


class Etapa(BaseModel):
    model_config = _PERMISIVO
    cod: Optional[int] = None
    und: Optional[int] = None
    vmes: Optional[int] = None
    frec: Optional[int] = None
    pe_pct: Optional[float] = None
    sucesora: Optional[int] = None        # cod de la etapa predecesora (o null en la raíz)
    fecha_inicio: Optional[str] = None     # ISO "YYYY-MM-DD"; el motor la parsea
    # nom, metodo, precio, area_und, ventas_miles, emes, efrec, desfase, obra_offset,
    # dur_obra, escrituracion, ic_offset, ventas_vivienda_miles… → extra


class Proyecto(BaseModel):
    """Contrato mínimo que el motor necesita para calcular. Todo lo demás es opcional/extra."""
    model_config = _PERMISIVO
    etapas: list[Etapa] = Field(min_length=1)
    costos_pct: CostosPct
    financiero: Financiero
    lote_bruto_miles: float
    meta: Optional[Meta] = None
    schema_version: int = 1
    vehiculo: Optional[str] = None  # M3: estructura legal (vehiculos.claves()); None/ausente = 'fiducia'
    # areas, cronograma, tipologias, directos_cap, indirectos_cap, gastos_fijos, fiducia,
    # ventas_miles, _nota… → extra

    @field_validator("vehiculo")
    @classmethod
    def _vehiculo_valido(cls, v: Optional[str]) -> Optional[str]:
        from . import vehiculos
        if v is not None and not vehiculos.existe(v):
            raise ValueError(f"vehiculo desconocido: {v!r}; válidos: {vehiculos.claves()}")
        return v


def parse(d: dict) -> Proyecto:
    """Valida un dict de proyecto contra el contrato. Devuelve el modelo (para inspección);
    lanza `pydantic.ValidationError` (mensaje legible) si los datos no cumplen.

    El motor NO usa el modelo: tras validar, se le pasa el MISMO dict `d` a `calcular(d)`.
    """
    return Proyecto.model_validate(d)
