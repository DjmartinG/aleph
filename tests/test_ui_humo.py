# -*- coding: utf-8 -*-
"""Pruebas de humo de la UI: cada sección renderiza SIN excepciones (AppTest de Streamlit).

No verifica cifras (eso lo hace test_anclas.py) — verifica que la app no se rompa al navegar.
Atrapa el tipo de incidente real que ya ocurrió (app.py con SyntaxError llegó a producción).

Truco documentado (aprendizaje 2026-06-08): `gate()` hace `st.stop()` en la pantalla de login,
lo que dejaría TODAS las secciones vacías en AppTest. Se evita:
  1) inyectando `at.session_state['_rol']='viewer'` ANTES de `at.run()`, y
  2) monkeypatcheando `streamlit_option_menu.option_menu` para forzar área + sección.
Usa el proyecto ILUSTRATIVO `1_navarra` (en el repo) para que corra en CI sin datos reales.
"""
import os

import pytest
from streamlit.testing.v1 import AppTest
import streamlit_option_menu as _som

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# sección -> área (capa) a la que pertenece, para el menú de 2 niveles
SECCION_AREA = {
    "Inicio": "Tablero",
    "Cockpit": "Tablero",
    "P&G": "Factibilidad",
    "Flujo de caja": "Factibilidad",
    "Distribución costos": "Factibilidad",  # solo-lectura tras 1b-ii (editores movidos a Ingreso)
    "Costo de capital": "Factibilidad",   # usa calcular_wacc(detalle=True)
    "Apalancamiento": "Factibilidad",
    "Monte Carlo": "Factibilidad",
}


@pytest.mark.parametrize("seccion", list(SECCION_AREA))
def test_seccion_renderiza_sin_excepcion(seccion, monkeypatch):
    def fake_option_menu(menu_title, options, **kw):
        # menú de áreas (contiene 'Tablero') -> devuelve el área; menú de secciones -> la sección
        return SECCION_AREA[seccion] if "Tablero" in options else seccion

    monkeypatch.setattr(_som, "option_menu", fake_option_menu)

    at = AppTest.from_file(os.path.join(RAIZ, "app.py"), default_timeout=120)
    at.session_state["proj_sel"] = "1_navarra"   # proyecto ilustrativo, presente en el repo
    at.session_state["_rol"] = "viewer"
    at.run()

    assert not at.exception, f"La sección '{seccion}' lanzó excepción: {at.exception}"


def test_proyecto_aprobado_renderiza(monkeypatch):
    """Un proyecto en estado 'aprobado' (Torres de Campiñas) renderiza una sección de Factibilidad
    sin excepción (ejercita el badge de estado y la UI adaptativa, donde Seguimiento se oculta)."""
    def fake_option_menu(menu_title, options, **kw):
        return "Factibilidad" if "Tablero" in options else "P&G"

    monkeypatch.setattr(_som, "option_menu", fake_option_menu)

    at = AppTest.from_file(os.path.join(RAIZ, "app.py"), default_timeout=120)
    at.session_state["proj_sel"] = "3_torres_campinas"   # estado 'aprobado' (sin Seguimiento)
    at.session_state["_rol"] = "viewer"
    at.run()

    assert not at.exception, f"Proyecto aprobado lanzó excepción: {at.exception}"


def test_area_stale_degrada_sin_romper(monkeypatch):
    """Si el área persistida ('Seguimiento') ya no existe para el proyecto (aprobado → sin Seguimiento),
    la app cae al primer área en vez de romper con KeyError. Regresión del bug hallado en 1c-1."""
    def fake_option_menu(menu_title, options, **kw):
        if "Tablero" in options:        # menú de áreas: simula una selección STALE fuera de las opciones
            return "Seguimiento"
        return options[0] if options else "Inicio"

    monkeypatch.setattr(_som, "option_menu", fake_option_menu)

    at = AppTest.from_file(os.path.join(RAIZ, "app.py"), default_timeout=120)
    at.session_state["proj_sel"] = "3_torres_campinas"   # aprobado → 'Seguimiento' NO está en el menú
    at.session_state["_rol"] = "viewer"
    at.run()

    assert not at.exception, f"El área stale rompió la app: {at.exception}"


def test_ingreso_datos_admin_renderiza(monkeypatch):
    """La pestaña admin 'Ingreso de datos' (Paso 1b) renderiza sin excepción para un administrador.

    Admin por PERSONA: se simula un usuario SSO cuyo email está en ADMINS (variable de entorno, que
    `_secret` lee como respaldo). Sin esto, PUEDE_INGRESAR sería False y la sección no aparecería.
    """
    monkeypatch.setenv("ADMINS", "mgomez@cgconstructora.com")

    def fake_option_menu(menu_title, options, **kw):
        return "Administración" if "Tablero" in options else "Ingreso de datos"

    monkeypatch.setattr(_som, "option_menu", fake_option_menu)

    at = AppTest.from_file(os.path.join(RAIZ, "app.py"), default_timeout=120)
    at.session_state["proj_sel"] = "1_navarra"
    at.session_state["_rol"] = "viewer"
    at.session_state["_ms_user"] = "mgomez@cgconstructora.com"   # identidad SSO de un admin
    at.run()

    assert not at.exception, f"'Ingreso de datos' lanzó excepción: {at.exception}"
