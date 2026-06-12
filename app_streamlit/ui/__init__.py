# -*- coding: utf-8 -*-
"""Paquete de UI modular (Fase 2).

Hogar de la capa de presentación a medida que `app.py` se adelgaza hacia un orquestador:
- `ui.format` — formato único de moneda/porcentaje (fuente única, sin lógica financiera).
- `ui.auth`   — autorización por persona (lista de administradores vía email/SSO).

Más adelante: `ui/pages/` (una página por sección), `ui/components/`, `ui/services/`.
Este paquete es parte de la APLICACIÓN (no del motor distribuible `cg_engine`).
"""
