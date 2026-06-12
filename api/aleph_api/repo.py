# -*- coding: utf-8 -*-
"""Capa de datos de la API: lee los proyectos. Misma convención que `app_streamlit/storage.py`.

Dos fuentes (con fallback "nunca se rompe"):
  - Si hay `SUPABASE_URL` + `SUPABASE_KEY` en el entorno → tabla `public.proyectos`
    (columnas `slug`, `nombre`, `es_real`, `data` jsonb = el dict `par`).
  - Si no → JSON locales del monorepo: `app_streamlit/proyectos_privados/{slug}_REAL.json` (reales,
    PRIORIDAD) sobre `app_streamlit/proyectos/{slug}.json` (ilustrativos públicos).

Devuelve el `par` (dict) tal cual; el motor lo consume. NO calcula nada.
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache

log = logging.getLogger("aleph_api.repo")


def _repo_root() -> str | None:
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(d, "engine")) and os.path.isdir(os.path.join(d, "app_streamlit")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _dirs():
    root = _repo_root()
    base = os.path.join(root, "app_streamlit") if root else "."
    return os.path.join(base, "proyectos"), os.path.join(base, "proyectos_privados")


def _usa_supabase() -> bool:
    return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_KEY"))


@lru_cache(maxsize=1)
def _cliente():
    from supabase import create_client  # import perezoso: solo si se usa Supabase
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


# ---------- API pública (espejo de storage.py) ----------

def listar() -> list[str]:
    """Slugs de los proyectos disponibles, ordenados."""
    if _usa_supabase():
        try:
            r = _cliente().table("proyectos").select("slug").execute()
            return sorted(row["slug"] for row in (r.data or []))
        except Exception as e:
            log.warning("Supabase no respondió (%s); usando respaldo local", e.__class__.__name__)
    pub, priv = _dirs()
    slugs = set()
    for d, suf in ((pub, ".json"), (priv, "_REAL.json")):
        if os.path.isdir(d):
            for fn in os.listdir(d):
                if fn.endswith(suf):
                    slugs.add(fn[: -len(suf)])
    return sorted(slugs)


def cargar(slug: str) -> dict | None:
    """Devuelve el `par` (dict) del proyecto, o None si no existe."""
    if _usa_supabase():
        try:
            r = _cliente().table("proyectos").select("data").eq("slug", slug).limit(1).execute()
            if r.data:
                return r.data[0]["data"]
        except Exception as e:
            log.warning("Supabase no respondió (%s); usando respaldo local", e.__class__.__name__)
    pub, priv = _dirs()
    for path in (os.path.join(priv, f"{slug}_REAL.json"), os.path.join(pub, f"{slug}.json")):
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
    return None


def es_real(slug: str) -> bool:
    """True si el proyecto tiene datos REALES (confidenciales) en vez de ilustrativos."""
    if _usa_supabase():
        try:
            r = _cliente().table("proyectos").select("es_real").eq("slug", slug).limit(1).execute()
            if r.data:
                return bool(r.data[0].get("es_real"))
        except Exception as e:
            log.warning("Supabase no respondió (%s); usando respaldo local", e.__class__.__name__)
    _pub, priv = _dirs()
    return os.path.isfile(os.path.join(priv, f"{slug}_REAL.json"))


def fuente() -> str:
    return "supabase" if _usa_supabase() else "local"
