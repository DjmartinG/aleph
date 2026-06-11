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
