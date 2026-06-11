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
