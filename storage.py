# -*- coding: utf-8 -*-
"""
Capa de almacenamiento de proyectos (Fase 2 — persistencia compartida).

Si hay credenciales Supabase en st.secrets (SUPABASE_URL + SUPABASE_KEY) → lee/escribe en la BD
compartida ("uno ingresa, todos ven"). Si NO las hay (p. ej. local sin secrets) → usa los archivos
JSON locales (proyectos_privados/ con prioridad sobre proyectos/). Nunca se rompe: ante cualquier
error de red, cae al respaldo local.

Tabla Supabase `public.proyectos`: slug (PK) · nombre · es_real · data (jsonb) · updated_at · updated_by.
Acceso solo con clave secreta (service/secret key) — RLS bloquea la clave pública.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
PROY_DIR = HERE / "proyectos"            # ilustrativos (repo público)
PRIV_DIR = HERE / "proyectos_privados"   # reales (gitignored, local)

_CLIENT = None
_TRIED = False


def _secret(name):
    try:
        import streamlit as st
        return str(st.secrets.get(name, "")) if hasattr(st, "secrets") else ""
    except Exception:
        return ""


def _client():
    """Cliente Supabase (singleton perezoso). None si no hay credenciales o falla la conexión."""
    global _CLIENT, _TRIED
    if _TRIED:
        return _CLIENT
    _TRIED = True
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if url and key:
        try:
            from supabase import create_client
            _CLIENT = create_client(url, key)
        except Exception:
            _CLIENT = None
    return _CLIENT


def usando_supabase():
    return _client() is not None


# --------------------------- API (misma firma que usaba app.py) ---------------------------
def _listar_local():
    priv = sorted(p.stem for p in PRIV_DIR.glob("*.json")) if PRIV_DIR.exists() else []
    cubiertas = {s[:-5] for s in priv if s.endswith("_REAL")}   # "1_navarra_REAL" oculta "1_navarra"
    pub = sorted(p.stem for p in PROY_DIR.glob("*.json") if p.stem not in cubiertas) if PROY_DIR.exists() else []
    return priv + pub


def listar():
    cl = _client()
    if cl:
        try:
            r = cl.table("proyectos").select("slug").order("slug").execute()
            return [row["slug"] for row in r.data]
        except Exception:
            pass
    return _listar_local()


def cargar(slug):
    cl = _client()
    if cl:
        try:
            r = cl.table("proyectos").select("data").eq("slug", slug).limit(1).execute()
            if r.data:
                return r.data[0]["data"]
        except Exception:
            pass
    p = PRIV_DIR / f"{slug}.json"
    if not p.exists():
        p = PROY_DIR / f"{slug}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def es_real(slug):
    cl = _client()
    if cl:
        try:
            r = cl.table("proyectos").select("es_real").eq("slug", slug).limit(1).execute()
            if r.data:
                return bool(r.data[0]["es_real"])
        except Exception:
            pass
    return (PRIV_DIR / f"{slug}.json").exists()


def guardar(slug, data, nombre=None, es_real_flag=False, by=None):
    """Upsert del proyecto en Supabase. Devuelve True si guardó en la nube, False si no hay BD."""
    cl = _client()
    if not cl:
        return False
    nombre = nombre or (data.get("meta", {}) or {}).get("nombre", slug)
    cl.table("proyectos").upsert({
        "slug": slug, "nombre": nombre, "es_real": bool(es_real_flag),
        "data": data, "updated_by": by or "",
    }).execute()
    return True
