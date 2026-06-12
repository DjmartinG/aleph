# -*- coding: utf-8 -*-
"""Navegación: construcción del menú ADAPTADA al estado del ciclo de vida (Paso 1c).

El estado del proyecto (eje rector) decide qué áreas aparecen:
- **Seguimiento** (real, ex-post) solo en construcción/entregado — en pre-factibilidad/aprobado se OCULTA
  (aún no hay obra que monitorear).
- **Administración → Ingreso de datos** solo para quien puede ingresar (admins).

Función pura (sin Streamlit) → testeable. `app.py` la usa para armar el menú lateral.
"""
from __future__ import annotations

from cg_engine import config as _cfg

# Secciones por área (etiqueta, icono bootstrap). Estáticas; el estado decide cuáles se muestran.
SECCIONES_TABLERO = [("Inicio", "house-door"), ("Pipeline / Embudo", "funnel"), ("Resumen ejecutivo", "speedometer2"),
                     ("Proyectos activos", "buildings"), ("Portafolio (burbujas)", "graph-up")]
# Orden: la tasa de descuento (WACC) se define ANTES del flujo (se descuenta con ella).
SECCIONES_FACTIBILIDAD = [("Datos del proyecto", "pencil-square"), ("Urbanístico", "building"),
                          ("Cronograma", "calendar3"), ("Ingresos", "cash-coin"),
                          ("Distribución costos", "bar-chart-line"), ("P&G", "table"), ("Reparto", "pie-chart"),
                          ("Costo de capital", "percent"), ("Flujo de caja", "cash-stack"),
                          ("Apalancamiento", "bank"), ("Escenarios", "bullseye"),
                          ("Monte Carlo", "dice-5"), ("Sensibilidad", "sliders")]
SECCIONES_SEGUIMIENTO = [("Monitor de ejecución", "clipboard-data"), ("Valor Ganado", "graph-up-arrow")]
SECCIONES_ADMIN = [("Ingreso de datos", "pencil-square")]

AREA_ICON = {"Tablero": "grid-1x2-fill", "Factibilidad": "calculator",
             "Seguimiento": "activity", "Administración": "shield-lock"}


def grupos(estado, puede_ingresar):
    """Menú (dict ordenado área→secciones) ADAPTADO al `estado` del proyecto.

    - Tablero y Factibilidad: siempre.
    - Seguimiento: solo si `estado` tiene datos reales (config.ESTADOS_CON_SEGUIMIENTO).
    - Administración: solo si `puede_ingresar`.
    El orden de inserción define el orden visual del menú.
    """
    g = {"Tablero": list(SECCIONES_TABLERO), "Factibilidad": list(SECCIONES_FACTIBILIDAD)}
    if estado in _cfg.ESTADOS_CON_SEGUIMIENTO:
        g["Seguimiento"] = list(SECCIONES_SEGUIMIENTO)
    if puede_ingresar:
        g["Administración"] = list(SECCIONES_ADMIN)
    return g
