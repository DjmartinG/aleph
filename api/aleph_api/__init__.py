"""`aleph_api` — API FastAPI de ALEPH (lectura del motor de factibilidad).

Envuelve `aleph_engine`: lee los proyectos, corre `calcular()` y expone los indicadores (con etiqueta
de base), P&G, flujo, crédito, checks de cuadre y sensibilidad. NO reimplementa ninguna fórmula.

Estado: PROMPT 4 · Fase 4a — API de LECTURA sobre los datos actuales (sin migración de esquema, sin
tocar el Streamlit). Auth (Entra ID) y migración de datos llegan en fases posteriores.
"""
__version__ = "0.1.0"
