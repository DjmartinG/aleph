# -*- coding: utf-8 -*-
"""Autorización por PERSONA (lista de administradores).

El control de acceso actual (`gate()` en app.py) solo distingue editor/viewer con una clave
COMPARTIDA: identifica el ROL, no a la persona. Para acciones restringidas a individuos concretos
—p. ej. la pestaña "Ingreso de datos", reservada a los 2 administradores— la única identidad
fiable es el email del login de Microsoft (Entra Easy Auth), que App Service inyecta en el header
de cada request autenticado.

Estas funciones son PURAS (sin Streamlit) y por eso testeables: deciden si un email pertenece a la
lista de administradores configurada en el secreto `ADMINS` (correos separados por coma).
"""
from __future__ import annotations


def parse_admins(csv: str | None) -> list[str]:
    """Convierte 'a@x.com, B@x.com' → ['a@x.com', 'b@x.com'] (minúsculas, sin vacíos)."""
    if not csv:
        return []
    return [p.strip().lower() for p in csv.split(",") if p.strip()]


def is_admin(email: str | None, admins_csv: str | None) -> bool:
    """True si `email` está en la lista `admins_csv` (comparación case-insensitive).

    Un usuario SIN email (no autenticado por SSO) NO es admin: la garantía de identidad por
    persona depende del login de Microsoft.
    """
    if not email:
        return False
    return email.strip().lower() in parse_admins(admins_csv)
