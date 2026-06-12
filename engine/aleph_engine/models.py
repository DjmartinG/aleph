# -*- coding: utf-8 -*-
"""Contrato de datos del proyecto ALEPH (validación en el BORDE con Pydantic v2).

Declara el "shape" del proyecto (hoy un dict implícito en `app_streamlit`) para poder VALIDARLO al
entrar (al cargar de Supabase o de un futuro ERP/CRM): `parse(dict)` lanza un error legible si los
datos no cumplen, ANTES de que lleguen al motor.

ORIGEN: portado desde `app_streamlit/cg_engine/schema.py` (mismo contrato), enriquecido con los
bloques descriptivos `Areas` y `Cronograma` ya presentes en los JSON reales. `aleph_engine` es PURO
y autónomo: este módulo NO importa de `cg_engine`.

Diseño (igual que el original): `extra="allow"` porque el shape es heterogéneo y evolutivo (Dominica
no trae tipologías ni fiducia; los reales traen `_nota`, `directos_cap`, etc.). Solo se exige lo
estructural que el motor necesita sí o sí; el resto es opcional (sus defaults vivirán en config.py al
extraer la lógica en PROMPT 3). La validación es una COMPUERTA, no una conversión: no transforma datos.
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


class Areas(BaseModel):
    """Cabida del lote. HOY es DESCRIPTIVA: alimenta KPIs urbanísticos, no el cálculo financiero
    (ver aprendizaje 2026-06-11). Todo opcional para no rechazar proyectos sin cabida cargada."""
    model_config = _PERMISIVO
    m2_vendibles: Optional[float] = None
    m2_construidos: Optional[float] = None
    lote_bruta: Optional[float] = None
    lote_util: Optional[float] = None


class Wacc(BaseModel):
    """Parámetros del build-up CAPM (Damodaran). Opcionales para no rechazar proyectos sin WACC
    propio; el cálculo del WACC exige los suyos cuando se invoque (lógica en PROMPT 3)."""
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
    # tir_apalancada_ref, credito_cap_miles… → extra (defaults en config al extraer la lógica)


class CostosPct(BaseModel):
    """Estructura de costos como % de ventas. El motor lee estos cuatro directamente."""
    model_config = _PERMISIVO
    directos: float
    indirectos: float
    honorarios: float
    util_lote: float
    # recon_codensa, hon_construccion, hon_gerencia, hon_ventas → extra (defaults en pyg)


class Cronograma(BaseModel):
    """Curva de obra (PERT/Gauss). Opcional: sus defaults los aporta el motor al calcular."""
    model_config = _PERMISIVO
    dur_obra: Optional[int] = None
    moda_pert: Optional[int] = None
    curva: Optional[str] = None           # "Gauss" | "PERT"
    rel_materiales: Optional[float] = None
    ea_materiales: Optional[float] = None
    ea_mano_obra: Optional[float] = None


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
    areas: Optional[Areas] = None
    cronograma: Optional[Cronograma] = None
    schema_version: int = 1
    # tipologias, directos_cap, indirectos_cap, gastos_fijos, fiducia, ventas_miles, _nota… → extra


def parse(d: dict) -> Proyecto:
    """Valida un dict de proyecto contra el contrato. Devuelve el modelo (para inspección);
    lanza `pydantic.ValidationError` (mensaje legible) si los datos no cumplen.

    El motor NO usará el modelo: tras validar, se le pasa el MISMO dict `d` a `calcular(d)` (cuando
    la lógica se extraiga en PROMPT 3). La validación es una compuerta, no una conversión.
    """
    return Proyecto.model_validate(d)
