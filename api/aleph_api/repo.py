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


# ---------- Fase 1: cut-over de lectura al modelo objetivo (projects/scenarios) ----------
# El ETL (db/etl_import_v1.py) pobló `scenarios` con el snapshot = el `par` COMPLETO bit a bit, así que
# leer de ahí devuelve EXACTAMENTE el mismo dato que `proyectos.data` (el dorado sigue verde por
# construcción). `proyectos` queda como ESPEJO de respaldo. Palanca de rollback: ALEPH_READ_SCENARIOS=false
# vuelve a leer de `proyectos.data` sin redeploy de código.

def _read_scenarios() -> bool:
    return os.environ.get("ALEPH_READ_SCENARIOS", "true").strip().lower() not in ("0", "false", "no")


def _snapshot_de_scenario(sb, slug: str) -> dict | None:
    """`par` desde el modelo objetivo: project(slug) → escenario BASELINE (o el `approved` de mayor
    versión) → snapshot. None si el proyecto/escenario no existe en el modelo nuevo (→ respaldo)."""
    proj = sb.table("projects").select("id").eq("slug", slug).limit(1).execute().data
    if not proj:
        return None
    rows = (sb.table("scenarios").select("snapshot,status,version")
            .eq("project_id", proj[0]["id"]).in_("status", ["baseline", "approved"])
            .order("version", desc=True).execute().data) or []
    if not rows:
        return None
    elegido = next((r for r in rows if r["status"] == "baseline"), rows[0])  # baseline manda
    return elegido["snapshot"]


# ---------- API pública (espejo de storage.py) ----------

def listar() -> list[str]:
    """Slugs de los proyectos disponibles, ordenados."""
    if _usa_supabase():
        sb = _cliente()
        try:
            if _read_scenarios():
                r = sb.table("projects").select("slug").execute()
                slugs = sorted(row["slug"] for row in (r.data or []))
                if slugs:
                    return slugs                              # modelo objetivo
            r = sb.table("proyectos").select("slug").execute()  # respaldo (espejo)
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
        sb = _cliente()
        try:
            if _read_scenarios():
                snap = _snapshot_de_scenario(sb, slug)
                if snap is not None:
                    return snap                              # modelo objetivo (baseline/approved)
            r = sb.table("proyectos").select("data").eq("slug", slug).limit(1).execute()  # respaldo
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
        sb = _cliente()
        try:
            if _read_scenarios():
                r = sb.table("projects").select("es_real").eq("slug", slug).limit(1).execute()
                if r.data:
                    return bool(r.data[0].get("es_real"))
            r = sb.table("proyectos").select("es_real").eq("slug", slug).limit(1).execute()  # respaldo
            if r.data:
                return bool(r.data[0].get("es_real"))
        except Exception as e:
            log.warning("Supabase no respondió (%s); usando respaldo local", e.__class__.__name__)
    _pub, priv = _dirs()
    return os.path.isfile(os.path.join(priv, f"{slug}_REAL.json"))


def fuente() -> str:
    return "supabase" if _usa_supabase() else "local"


def read_model() -> str:
    """De dónde lee el API el `par`: 'scenarios' (modelo objetivo, Fase 1), 'proyectos' (espejo de
    respaldo) o 'local' (JSON). Diagnóstico para verificar el cut-over en prod SIN exponer cifras."""
    if not _usa_supabase():
        return "local"
    if not _read_scenarios():
        return "proyectos"
    try:
        r = _cliente().table("projects").select("slug").limit(1).execute()
        return "scenarios" if r.data else "proyectos"
    except Exception:
        return "proyectos"


def data_required() -> bool:
    """True si la API DEBE tener datos (producción): 0 proyectos → la ruta de datos responde 503 en vez
    de 200-vacío. La imagen del API NO trae JSON de respaldo, así que en prod Supabase es OBLIGATORIO;
    sin esto, una mala config de Supabase serviría un portafolio vacío en silencio (HTTP 200, n=0)."""
    return os.environ.get("ALEPH_DATA_REQUIRED", "").strip().lower() in ("1", "true", "yes", "si", "sí")
