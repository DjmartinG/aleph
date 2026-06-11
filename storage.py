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


def slugify(s):
    """Convierte un nombre en un slug seguro para clave de almacenamiento (PK de la tabla).
    'Torres de Campiñas' -> 'torres_de_campinas'. Vacío / no alfanumérico -> 'proyecto'."""
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    return s or "proyecto"


_CLIENT = None
_TRIED = False
_DIAG = "no iniciado"     # motivo legible de por qué hay/no hay conexión a Supabase


def _secret(name):
    # 1) st.secrets (Streamlit Cloud / secrets.toml local). 2) variables de entorno (Azure App Service,
    # contenedores, cualquier host). Así la app es portable sin cambiar código.
    try:
        import streamlit as st
        v = st.secrets.get(name, "") if hasattr(st, "secrets") else ""
        if v:
            return str(v)
    except Exception:
        pass
    import os
    return str(os.environ.get(name, ""))


def _client():
    """Cliente Supabase (singleton perezoso). None si no hay credenciales o falla la conexión."""
    global _CLIENT, _TRIED, _DIAG
    if _TRIED:
        return _CLIENT
    _TRIED = True
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if not url or not key:
        faltan = ", ".join([n for n, v in [("SUPABASE_URL", url), ("SUPABASE_KEY", key)] if not v])
        _DIAG = f"faltan secrets: {faltan or 'ninguno'}"
        return None
    try:
        from supabase import create_client
        _CLIENT = create_client(url, key)
        _DIAG = "conectado"
    except Exception as e:
        _CLIENT = None
        _DIAG = f"error de conexión: {type(e).__name__}: {str(e)[:160]}"
    return _CLIENT


def diagnostico():
    _client()
    return _DIAG


def _ref_de_url(url):
    # https://<ref>.supabase.co  ->  <ref>
    try:
        return url.split("//", 1)[1].split(".", 1)[0]
    except Exception:
        return "?"


def _ref_de_key(key):
    """Si la key es un JWT legacy (eyJ...), extrae 'ref' y 'role' del payload (público, no secreto)."""
    import base64, json as _json
    if not key.startswith("eyJ"):
        fmt = "sb_secret" if key.startswith("sb_secret") else ("sb_publishable" if key.startswith("sb_publishable") else "desconocido")
        return {"formato": fmt, "ref": None, "role": None}
    try:
        payload = key.split(".")[1]
        payload += "=" * (-len(payload) % 4)            # padding base64
        d = _json.loads(base64.urlsafe_b64decode(payload))
        return {"formato": "JWT legacy", "ref": d.get("ref"), "role": d.get("role")}
    except Exception:
        return {"formato": "JWT (no decodificable)", "ref": None, "role": None}


def probar_conexion():
    """Diagnóstico seguro (sin exponer la clave). Devuelve dict con: refs, rol, y test de lectura."""
    url = _secret("SUPABASE_URL"); key = _secret("SUPABASE_KEY")
    info = {"url_ref": _ref_de_url(url) if url else None,
            "tiene_url": bool(url), "tiene_key": bool(key),
            "key_len": len(key)}
    info.update(_ref_de_key(key) if key else {"formato": None, "ref": None, "role": None})
    info["refs_coinciden"] = (info.get("ref") == info.get("url_ref")) if info.get("ref") else None
    cl = _client()
    if not cl:
        info["lectura"] = f"sin cliente: {_DIAG}"
        return info
    try:
        r = cl.table("proyectos").select("slug").execute()
        info["lectura"] = f"OK · {len(r.data)} filas en la nube: {[x['slug'] for x in r.data]}"
    except Exception as e:
        info["lectura"] = f"ERROR: {type(e).__name__}: {str(e)[:140]}"
    return info


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
