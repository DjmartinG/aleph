# -*- coding: utf-8 -*-
"""M3 · Vehículos jurídico-financieros — catálogo + atributos fiscales (spec_pyg_dinamico.md).

Un VEHÍCULO es la estructura legal con la que CG desarrolla un proyecto. Cambia (a) el tratamiento
de RENTA y (b) —Fase 2— el WATERFALL/reparto. Aquí va SOLO el catálogo + sus atributos fiscales;
el cálculo lo hace `tributario.py`. Cero cifras: este módulo no toca el motor financiero.

ADVERTENCIA: cada regla viene de investigación y va marcada `[VALIDAR]` con su norma. Es APOYO A LA
DECISIÓN, no asesoría tributaria — confirmar con el asesor fiscal de CG antes de estructurar.

Atributos:
  transparente            — transparencia fiscal: el vehículo NO es contribuyente y cada
                            partícipe/socio declara su parte (fiducia ET 102, consorcio/UT ET 18,
                            cuentas en participación post-reforma 2022). NO implica ahorro por sí solo.
  habilita_exencion_vis   — si la estructura permite la renta exenta VIS (ET 235-2 num.4). HOY solo la
                            FIDUCIA con licencia VIS y patrimonio autónomo la habilita [VALIDAR].
  tasa_renta              — tasa efectiva de renta a aplicar; None = usar la del proyecto (fin['renta']).
  waterfall               — 'fiducia_override' (usa el FCL auditado, reproduce el dorado) |
                            'recalcular' (recalcula desde el modelo mensual — Fase 2, requiere golden propio).
"""
from __future__ import annotations

from dataclasses import dataclass, field

FIDUCIA = "fiducia"   # vehículo por defecto = el actual (no-op, dorado intacto)


@dataclass(frozen=True)
class Vehiculo:
    clave: str
    nombre: str
    transparente: bool
    habilita_exencion_vis: bool
    tasa_renta: float | None          # None = usa fin['renta'] del proyecto
    waterfall: str                    # 'fiducia_override' | 'recalcular'
    nota: str                         # descripción + [VALIDAR] + norma
    fuente_normativa: str = ""
    palancas: tuple[str, ...] = field(default_factory=tuple)  # optimizaciones legales [VALIDAR]


_CATALOGO: dict[str, Vehiculo] = {
    FIDUCIA: Vehiculo(
        clave=FIDUCIA, nombre="Fiducia inmobiliaria (patrimonio autónomo)",
        transparente=True, habilita_exencion_vis=True, tasa_renta=None,
        waterfall="fiducia_override",
        nota="Patrimonio autónomo transparente (ET 102). Es REQUISITO de la exención VIS "
             "(ET 235-2 num.4) cuando el PA ejecuta el 100% del proyecto con licencia VIS. "
             "[VALIDAR vigencia Ley 2277/2022 y plazos de licencia].",
        fuente_normativa="ET 102; ET 235-2 num.4",
    ),
    "encargo_fiduciario": Vehiculo(
        clave="encargo_fiduciario", nombre="Encargo fiduciario de preventas",
        transparente=True, habilita_exencion_vis=False, tasa_renta=None,
        waterfall="recalcular",
        nota="Recaudo de preventas en encargo (no es patrimonio autónomo desarrollador). Por sí solo "
             "NO habilita la exención VIS (falta el PA que ejecute la obra) [VALIDAR]. Renta plena.",
        fuente_normativa="ET 102 (parcial)",
    ),
    "consorcio": Vehiculo(
        clave="consorcio", nombre="Consorcio",
        transparente=True, habilita_exencion_vis=False, tasa_renta=None,
        waterfall="recalcular",
        nota="No contribuyente de renta (ET 18): cada consorciado declara su proporción y tributa al "
             "35% por su parte. No ahorra impuesto por sí mismo; sirve para unir capacidad/cupos. [VALIDAR].",
        fuente_normativa="ET 18",
    ),
    "union_temporal": Vehiculo(
        clave="union_temporal", nombre="Unión temporal (UT)",
        transparente=True, habilita_exencion_vis=False, tasa_renta=None,
        waterfall="recalcular",
        nota="Igual que el consorcio para efectos de renta (ET 18): transparente, cada socio declara su "
             "parte. Diferencia es la responsabilidad por sanciones, no el impuesto. [VALIDAR].",
        fuente_normativa="ET 18",
    ),
    "cuentas_en_participacion": Vehiculo(
        clave="cuentas_en_participacion", nombre="Cuentas en participación",
        transparente=True, habilita_exencion_vis=False, tasa_renta=None,
        waterfall="recalcular",
        nota="Tras la reforma 2022 hay transparencia plena: el partícipe oculto declara su utilidad → "
             "NO ahorra impuestos. Valor real = confidencialidad del partícipe, no fiscal. [VALIDAR].",
        fuente_normativa="Ley 2277/2022 (transparencia CeP)",
    ),
    "sas_spv": Vehiculo(
        clave="sas_spv", nombre="SAS / SPV (sociedad vehículo)",
        transparente=False, habilita_exencion_vis=False, tasa_renta=None,
        waterfall="recalcular",
        nota="Sociedad contribuyente: renta 35% PLENA (sin sobretasa; la +5% es solo del sector "
             "financiero). No habilita exención VIS salvo que la SAS sea fideicomitente de una fiducia "
             "con licencia VIS [VALIDAR]. Palanca: vender la SPV como activo (ganancia ocasional 15% si "
             ">2 años de posesión) en vez de distribuir utilidad [VALIDAR Art. 869 abuso].",
        fuente_normativa="ET 240; ET 300 (ganancia ocasional)",
        palancas=("Venta de SPV >2 años → ganancia ocasional 15% [VALIDAR Art. 869]",),
    ),
    "fcp": Vehiculo(
        clave="fcp", nombre="Fondo de Capital Privado (FCP)",
        transparente=True, habilita_exencion_vis=False, tasa_renta=None,
        waterfall="recalcular",
        nota="Diferimiento del impuesto del partícipe hasta la distribución, si el FCP cumple los "
             "requisitos de ET 23-1 (no concentración, gestor profesional). Difiere, no exime. [VALIDAR "
             "requisitos y vigencia post-reforma].",
        fuente_normativa="ET 23-1",
    ),
}


def obtener(clave: str | None) -> Vehiculo:
    """Devuelve el vehículo; None/desconocido → fiducia (default no-op). Para validación estricta usar `existe`."""
    if not clave:
        return _CATALOGO[FIDUCIA]
    v = _CATALOGO.get(str(clave).strip().lower())
    return v if v is not None else _CATALOGO[FIDUCIA]


def existe(clave: str | None) -> bool:
    return bool(clave) and str(clave).strip().lower() in _CATALOGO


def catalogo() -> list[Vehiculo]:
    """Lista de vehículos (fiducia primero, luego el resto en orden de inserción)."""
    return list(_CATALOGO.values())


def claves() -> list[str]:
    return list(_CATALOGO.keys())
