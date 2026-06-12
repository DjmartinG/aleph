# -*- coding: utf-8 -*-
"""Tests de autorización por persona (Paso 1a Fase 2). Garantiza que SOLO los correos de la lista
ADMINS sean admin, sin importar mayúsculas/espacios, y que un usuario sin email nunca lo sea."""
from ui.auth import is_admin, parse_admins

ADMINS = "mgomez@cgconstructora.com, jgonzalez@cgconstructora.com"


def test_admin_reconoce_correos_de_la_lista():
    assert is_admin("mgomez@cgconstructora.com", ADMINS)
    assert is_admin("jgonzalez@cgconstructora.com", ADMINS)


def test_admin_es_case_insensitive_y_tolera_espacios():
    assert is_admin("  JGonzalez@CGConstructora.com  ", ADMINS)


def test_correo_fuera_de_la_lista_no_es_admin():
    assert not is_admin("otro@cgconstructora.com", ADMINS)


def test_sin_email_nunca_es_admin():
    # Camino de contraseña (sin SSO): no hay identidad de persona → no admin.
    assert not is_admin(None, ADMINS)
    assert not is_admin("", ADMINS)


def test_sin_lista_admins_nadie_es_admin():
    assert not is_admin("mgomez@cgconstructora.com", "")
    assert not is_admin("mgomez@cgconstructora.com", None)


def test_parse_admins_normaliza():
    assert parse_admins("A@x.com, b@x.com ") == ["a@x.com", "b@x.com"]
    assert parse_admins("") == []
    assert parse_admins(None) == []
