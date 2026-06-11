# -*- coding: utf-8 -*-
"""Constantes y valores por defecto del motor — un solo lugar (antes dispersos como "números mágicos").

Cambiar un default aquí lo cambia en TODO el motor de forma consistente. Estos defaults SOLO
aplican cuando el proyecto no especifica el valor (la mayoría de proyectos reales sí lo traen
en `financiero`); por eso centralizarlos no altera ninguna cifra auditada.
"""
from datetime import date

# --- Horizontes de las series mensuales (en meses) ---
HORIZONTE_FLUJO = 96          # flujo_caja (vista del proyecto, single)
HORIZONTE_RECAUDO = 180       # recaudo y flujo apalancado (portafolio multi-etapa, más largo)
HORIZONTE_HITOS = 120         # cálculo de hitos de venta por etapa (IV/PE/FV)

# --- Defaults financieros (se usan solo si el proyecto no los trae en `financiero`) ---
PCT_CI = 0.30                 # fracción de cuota inicial sobre el precio
SEP_UND_MILES = 5000.0        # separación por unidad (miles COP)
DIFERIDO_SEP = 4              # meses en que se difiere la separación desde la venta
TASA_CREDITO_EA = 0.155       # tasa efectiva anual del crédito constructor
COBERTURA_CC = 0.80           # cobertura del crédito constructor sobre el valor financiable
TIO = 0.15                    # tasa interna de oportunidad (descuento CG)
RENTA = 0.35                  # tasa de renta (impuesto) sobre el reintegro sin lote
SPLIT_CG = 0.70               # reparto CG de la utilidad operativa (resto al socio)

# --- Valor Ganado (EVM) ---
# Fecha de corte por defecto. NO es "hoy": es el CORTE DE LOS DATOS de comité cargados (hoy = el
# corte de Navarra). El corte correcto debe venir del dato; esto es solo el respaldo. Cambiarlo a
# date.today() rompería el EVM (compararía datos viejos contra un plan de hoy → SPI falso).
FECHA_CORTE_EVM = date(2026, 5, 1)

# --- Ciclo de vida del proyecto (estados del pipeline / embudo) ---
# El estado es el EJE RECTOR de la UI (ver NORTE_TABLEROS.md §0): gobierna el pipeline, el filtro
# del portafolio y QUÉ secciones se muestran por proyecto. NO afecta el cálculo financiero.
ESTADO_PREFACT = "prefactibilidad"   # candidato en evaluación; lote = supuesto; foco decisión ir/no-ir
ESTADO_APROBADO = "aprobado"         # evaluado + lote adquirido; obra aún no inicia
ESTADO_CONSTRUCCION = "construccion" # en ejecución / obra; con seguimiento plan vs real
ESTADO_ENTREGADO = "entregado"       # proyecto cerrado / entregado
# Orden del embudo (de candidato a cerrado). Es también el conjunto válido del contrato (schema).
ESTADOS = (ESTADO_PREFACT, ESTADO_APROBADO, ESTADO_CONSTRUCCION, ESTADO_ENTREGADO)
ESTADO_LABEL = {
    ESTADO_PREFACT: "Pre-factibilidad",
    ESTADO_APROBADO: "Aprobado",
    ESTADO_CONSTRUCCION: "Construcción",
    ESTADO_ENTREGADO: "Entregado",
}
ESTADO_DEFAULT = ESTADO_CONSTRUCCION                  # respaldo si un proyecto no declara estado
ESTADOS_CON_SEGUIMIENTO = (ESTADO_CONSTRUCCION, ESTADO_ENTREGADO)  # tienen datos reales (ex-post)

# --- Umbrales de aprobación (gate Pre-factibilidad → Aprobado) ---
# Un candidato se APRUEBA solo si cumple los TRES criterios (checklist multicriterio).
# OJO: valores PROVISIONALES — confirmar con el comité al construir la "Decisión de inversión" (Paso 4).
UMBRAL_TIR_EQUITY = 0.18      # TIR del inversionista (apalancada) mínima exigida
UMBRAL_VPN_MIN = 0.0          # VPN del proyecto > 0 descontado a la TIO
UMBRAL_MARGEN_MIN = 0.08      # margen operacional mínimo (utilidad operativa / ventas)
