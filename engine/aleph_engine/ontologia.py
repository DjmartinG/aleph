# -*- coding: utf-8 -*-
"""Ontología canónica de ALEPH — fachada de SOLO LECTURA del vocabulario del motor.

Consolida en UN solo lugar el vocabulario que hoy vive disperso (fases, tipos, categorías de costo,
indicadores, vehículos) + nombra lo que hoy es implícito (códigos de hito, conceptos de recaudo) +
un registro de los INVARIANTES de cuadre. Es el cimiento del futuro "Auditor de presupuestos" y de la
normalización de datos del cotizador/SmartHome.

QUÉ ES: una fachada que **referencia/re-exporta** las definiciones que ya existen (cero valores
duplicados que puedan derivar) y **añade** como constantes el vocabulario aún implícito.

QUÉ NO ES: una reescritura. **Dependencia de UNA sola dirección:** este módulo importa DE los demás;
los demás NO se reconectan a este (eso acoplaría comportamiento y arriesgaría el dorado — es un paso
futuro). Es 100% ADITIVO: no toca `calcular()`, no mueve cifras, no extrae/reescribe lógica.

Mapeo elemento ↔ fuente real (auditado, no asumido):
  FASES             → config.ESTADOS
  TIPOS_PROYECTO    → constante canónica (hoy schema.Meta.tipo es Optional[str], sin fuente tipada)
  CATEGORIAS_COSTO  → campos de schema.CostosPct
  HITOS             → códigos IV/PE/FV/IC/FC ya usados en el cronograma (aquí solo NOMBRADOS)
  CONCEPTOS_RECAUDO → constantes nuevas (esquema colombiano, hoy implícito en modelo._recaudo)
  INDICADORES       → metrics.REGISTRO
  VEHICULOS         → vehiculos.claves()
  INVARIANTES       → checks.correr / checks.check_spi (funciones existentes)
"""
from __future__ import annotations

from dataclasses import dataclass

from . import checks, config, metrics, vehiculos
from .schema import CostosPct

# ───────────────────────── Fases del ciclo de vida ─────────────────────────
# Fuente única: config.ESTADOS (NO se redefine la lista; se referencia).
FASES = config.ESTADOS
FASE_DEFAULT = config.ESTADO_DEFAULT
FASE_LABEL = config.ESTADO_LABEL

# ───────────────────────── Tipos de proyecto ─────────────────────────
# Hoy schema.Meta.tipo es `Optional[str]` (un comentario, no un Literal) → NO hay fuente tipada.
# Se fija aquí la constante canónica. NO se re-cablea `schema` para validar contra esto en este paso.
TIPOS_PROYECTO = ("VIS", "VIP", "No VIS")

# ───────────────────────── Categorías de costo ─────────────────────────
# Fuente única: los campos declarados de schema.CostosPct (sin drift; si el modelo cambia, esto sigue).
CATEGORIAS_COSTO = tuple(CostosPct.model_fields)   # ('directos', 'indirectos', 'honorarios', 'util_lote')


# ───────────────────────── Hitos del cronograma ─────────────────────────
@dataclass(frozen=True)
class Hito:
    codigo: str
    nombre: str


# Códigos que el cálculo de cronograma YA produce (modelo._hitos → portafolio.calcular_portafolio):
# IV/PE/FV/IC/FC por etapa. Aquí solo quedan NOMBRADOS; el cálculo no se toca. `escrituracion` es el
# evento de escrituración (offset de recaudo), incluido por completitud del vocabulario de cronograma.
HITOS = (
    Hito("IV", "Inicio de ventas"),
    Hito("PE", "Punto de equilibrio"),
    Hito("FV", "Fin de ventas"),
    Hito("IC", "Inicio de construcción"),
    Hito("FC", "Fin de construcción"),
    Hito("escrituracion", "Escrituración"),
)
HITOS_POR_CODIGO = {h.codigo: h for h in HITOS}


# ───────────────────────── Conceptos de recaudo (esquema colombiano) ─────────────────────────
@dataclass(frozen=True)
class ConceptoRecaudo:
    clave: str
    nombre: str
    descripcion: str


# Constantes NUEVAS: nombran el vocabulario de recaudo hoy implícito en modelo._recaudo /
# ingresos.recaudo_portafolio. Documentales (no cambian ningún cálculo).
CONCEPTOS_RECAUDO = (
    ConceptoRecaudo("separacion", "Separación",
                    "Pago inicial por unidad al reservar; se difiere unos meses desde la venta."),
    ConceptoRecaudo("cuota_inicial", "Cuota inicial fraccionada",
                    "Fracción del precio (≈30%) que el comprador paga en cuotas durante la preventa/obra."),
    ConceptoRecaudo("subrogacion", "Contra-escritura / subrogación",
                    "Al escriturar, el crédito hipotecario del comprador (o su recurso) paga el saldo del precio."),
    ConceptoRecaudo("fiducia", "Fiducia (recaudo en patrimonio autónomo)",
                    "El recaudo de preventas se administra en fiducia hasta alcanzar el punto de equilibrio."),
    ConceptoRecaudo("credito_constructor", "Crédito constructor",
                    "Línea del banco con desembolsos contra avance de obra; se amortiza con las subrogaciones."),
)


# ───────────────────────── Indicadores ─────────────────────────
# Fuente única: metrics.REGISTRO (NO se duplica). `INDICADORES` es una referencia al mismo dict.
INDICADORES = metrics.REGISTRO


def indicador(clave: str) -> metrics.Metric:
    """Accesor canónico a un indicador (re-exporta `metrics.metric`)."""
    return metrics.metric(clave)


# ───────────────────────── Vehículos jurídico-financieros ─────────────────────────
# Fuente única: vehiculos.claves() (catálogo en vehiculos._CATALOGO).
VEHICULOS = tuple(vehiculos.claves())


# ───────────────────────── Registro de INVARIANTES de cuadre (topología) ─────────────────────────
@dataclass(frozen=True)
class Invariante:
    id: str
    nombre: str
    descripcion: str
    referencia: object   # callable existente que lo calcula (o str con la ubicación, si fuera inline)


# Cada invariante apunta a la FUNCIÓN existente que ya lo calcula (no se extrae ni se reescribe nada).
# Los 5 primeros los produce `checks.correr(R)` (función reutilizable, no inline); SPI lo produce
# `checks.check_spi(evm)`. Los `id` coinciden con las `clave` que emiten esos checks (consistencia
# verificada en el test, sin drift).
INVARIANTES = (
    Invariante("pyg_ingresos", "P&G cierra",
               "total_ingresos == ventas + reconocimientos", checks.correr),
    Invariante("recaudo_ventas", "Recaudo = ingresos del P&G",
               "sum(ingresos del flujo apalancado) == total_ingresos", checks.correr),
    Invariante("flujo_utilidad", "Flujo ≈ utilidad",
               "acumulado_operativo[-1] == utilidad operativa", checks.correr),
    Invariante("reparto", "Reparto cuadra",
               "CG + socio == resultados", checks.correr),
    Invariante("credito", "Crédito cuadra",
               "0 <= cupo_credito <= valor_financiable y credito_max >= 0", checks.correr),
    Invariante("spi_plausible", "SPI plausible",
               f"SPI dentro de [{checks.SPI_MIN}, {checks.SPI_MAX}]", checks.check_spi),
)


# ───────────────────────── TODO [por validar] — NO encodear hasta confirmar ─────────────────────────
# No se hornean suposiciones en la fuente canónica. Estos ítems del glosario quedan SIN valor hasta
# que el comité / asesor los confirme:
#
# TODO [por validar]: capítulos del WBS (presupuesto bottom-up). Hoy el costo es TOP-DOWN (% de ventas,
#   ver schema.CostosPct). El desglose por capítulo (preliminares, cimentación, estructura, …) llegará
#   con el "Auditor de presupuestos" / SINCO; no se inventa la lista aquí.
# TODO [por validar]: % exacto del crédito constructor. config.COBERTURA_CC=0.80 es un DEFAULT; el
#   valor real por proyecto debe confirmarse con el banco.
# TODO [por validar]: uso de VIP. Hoy el motor trata VIS y VIP igual para la exención de renta
#   (modelo: VIS/VIP → exento); confirmar si hay diferencia operativa/normativa que amerite separarlos.
# TODO [por validar]: yield on cost. Aún no existe como indicador en metrics.REGISTRO; definir la
#   fórmula y la etiqueta de base antes de encodearlo.
