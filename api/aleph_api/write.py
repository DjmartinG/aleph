# -*- coding: utf-8 -*-
"""Capa de ESCRITURA (Fase 2): crear/editar borradores y aprobar/fijar baseline en projects/scenarios.

Toda mutación cumple las invariantes de la directiva (`directives/plan_escritura.md`):
  (a) VALIDA el `par` con `aleph_engine.schema.parse` ANTES de persistir (la MISMA compuerta que el
      Streamlit y el ETL) → cero datos malformados entran al snapshot;
  (b) valida la TRANSICIÓN legal — solo se edita un `draft`; `approved`/`baseline` son INMUTABLES;
  (c) AUDITA (actor = email/oid del JWT de Entra) en `audit_log`;
  (d) al APROBAR recalcula con el motor (`calcular`) y guarda `results_cache` (engine_version +
      hash de inputs) — réplica del patrón ya probado en `db/etl_import_v1.py`.

NO toca el motor `aleph_engine` (las fórmulas y el SNAPSHOT DORADO quedan intactos): la escritura
valida + persiste + recalcula con el motor existente. El snapshot se guarda BIT A BIT.

Atomicidad: las operaciones usan llamadas secuenciales al cliente Supabase (con validación previa y
manejo de error). La transaccionalidad fuerte vía RPC plpgsql + la concurrencia optimista (If-Match)
son el endurecimiento de la Fase 3 (ver la directiva).
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata

from aleph_engine import __version__ as ENGINE_V
from aleph_engine import calcular, checks, config, schema
from fastapi import HTTPException

from . import repo


# ---------- helpers ----------

def _sb():
    """Cliente Supabase, o 503 si la escritura no está configurada (la escritura EXIGE Supabase)."""
    if not repo._usa_supabase():
        raise HTTPException(status_code=503, detail="La escritura requiere Supabase configurado en el servidor")
    return repo._cliente()


def _slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s or "proyecto"


def _hash(par: dict) -> str:
    return hashlib.sha256(json.dumps(par, sort_keys=True, default=str).encode()).hexdigest()


def _fase(par: dict) -> str:
    e = (par.get("meta") or {}).get("estado") or config.ESTADO_DEFAULT
    return e if e in config.ESTADOS else config.ESTADO_DEFAULT


def _validar(par: dict) -> None:
    """Compuerta del contrato del motor. 422 con mensaje legible si no cumple."""
    try:
        schema.parse(par)
    except Exception as e:  # pydantic.ValidationError u otros
        raise HTTPException(status_code=422, detail=f"Proyecto inválido: {e}") from e


def _audit(sb, entity_type: str, entity_id, action: str, actor: str | None, diff=None) -> None:
    sb.table("audit_log").insert({
        "entity_type": entity_type, "entity_id": entity_id,
        "action": action, "actor": actor, "diff": diff,
    }).execute()


def _company_id(sb) -> str:
    r = sb.table("companies").select("id").eq("slug", "cg-constructora").limit(1).execute().data
    if not r:
        raise HTTPException(status_code=500, detail="Empresa 'cg-constructora' no existe (¿migración 0001?)")
    return r[0]["id"]


def _scenario(sb, scenario_id: str) -> dict:
    r = (sb.table("scenarios").select("id,project_id,version,status,snapshot")
         .eq("id", scenario_id).limit(1).execute().data)
    if not r:
        raise HTTPException(status_code=404, detail="Escenario no encontrado")
    return r[0]


def _con_schema(par: dict) -> dict:
    snap = dict(par)
    snap.setdefault("schema_version", 1)
    return snap


# ---------- operaciones de escritura ----------

def crear_proyecto(par: dict, *, slug: str | None, nombre: str | None, es_real: bool, actor: str | None) -> dict:
    """Crea un proyecto NUEVO con su escenario v1 en estado `draft`. Valida el `par` y audita."""
    _validar(par)
    sb = _sb()
    nombre = nombre or (par.get("meta") or {}).get("nombre") or "Proyecto"
    slug = _slugify(slug or nombre)
    if sb.table("projects").select("id").eq("slug", slug).limit(1).execute().data:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto cuyo nombre genera el identificador '{slug}'. "
                   f"Usa un nombre distinguible.")
    proj = sb.table("projects").insert({
        "company_id": _company_id(sb), "slug": slug, "nombre": nombre,
        "es_real": bool(es_real), "fase": _fase(par), "updated_by": actor,
    }).execute().data[0]
    # Atomicidad débil: insertar el escenario + auditar; si algo falla DESPUÉS de crear el proyecto,
    # COMPENSAMOS borrándolo para no dejar un proyecto sin escenario que ocupe el slug e impida
    # reintentar (la transacción fuerte vía RPC es el endurecimiento de Fase 3, ver la directiva).
    try:
        sc = sb.table("scenarios").insert({
            "project_id": proj["id"], "version": 1, "status": "draft",
            "snapshot": _con_schema(par), "label": "draft v1", "created_by": actor,
        }).execute().data[0]
        _audit(sb, "scenario", sc["id"], "create_draft", actor)
    except Exception:
        try:
            sb.table("projects").delete().eq("id", proj["id"]).execute()
        except Exception:
            pass
        raise
    return {"project_id": proj["id"], "scenario_id": sc["id"], "slug": slug, "version": 1, "status": "draft"}


def nuevo_draft(project_id: str, par: dict, *, actor: str | None) -> dict:
    """Crea un escenario `draft` NUEVO (siguiente versión) sobre un proyecto existente."""
    _validar(par)
    sb = _sb()
    vers = [r["version"] for r in
            (sb.table("scenarios").select("version").eq("project_id", project_id).execute().data or [])]
    if not vers:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    nv = max(vers) + 1
    sc = sb.table("scenarios").insert({
        "project_id": project_id, "version": nv, "status": "draft",
        "snapshot": _con_schema(par), "label": f"draft v{nv}", "created_by": actor,
    }).execute().data[0]
    _audit(sb, "scenario", sc["id"], "create_draft", actor)
    return {"scenario_id": sc["id"], "version": nv, "status": "draft"}


def editar_draft(scenario_id: str, par: dict, *, actor: str | None, if_match: str | None = None) -> dict:
    """Reemplaza el snapshot de un escenario SOLO si está en `draft` (approved/baseline → 409).

    Concurrencia OPTIMISTA (Fase 3): si se pasa `if_match` (el `updated_at` que el cliente leyó), el
    UPDATE solo aplica si la fila NO cambió desde entonces; si cambió (otro usuario editó) no afecta
    filas → 409. La inmutabilidad del snapshot fuera de draft la garantiza además el trigger (0002)."""
    _validar(par)
    sb = _sb()
    sc = _scenario(sb, scenario_id)
    if sc["status"] != "draft":
        raise HTTPException(status_code=409,
                            detail=f"Solo se edita un borrador; este está '{sc['status']}' (inmutable)")
    q = (sb.table("scenarios").update({"snapshot": _con_schema(par)})
         .eq("id", scenario_id).eq("status", "draft"))
    if if_match is not None:
        q = q.eq("updated_at", if_match)                  # compare-and-swap por ETag
    res = q.execute()
    if if_match is not None and not (res.data or []):
        raise HTTPException(status_code=409,
                            detail="El borrador cambió desde que lo abriste (otro usuario lo editó); recarga e intenta de nuevo")
    _audit(sb, "scenario", scenario_id, "edit", actor)
    return {"scenario_id": scenario_id, "version": sc["version"], "status": "draft"}


def aprobar(scenario_id: str, *, actor: str | None) -> dict:
    """`draft → approved`: valida, recalcula con el motor, guarda results_cache + audita. El snapshot
    pasa a INMUTABLE (la garantía dura por trigger llega en Fase 3). Devuelve la TIR y los cuadres."""
    sb = _sb()
    sc = _scenario(sb, scenario_id)
    if sc["status"] != "draft":
        raise HTTPException(status_code=409, detail=f"Solo se aprueba un borrador; este está '{sc['status']}'")
    par = sc["snapshot"]
    _validar(par)
    # El motor puede CRASHEAR con un par que pasó schema.parse pero está incompleto para calcular
    # (p.ej. `financiero.wacc` ausente → KeyError, porque en el contrato WACC es Optional). El
    # formulario siempre manda WACC, pero un par enviado por API directo no. Traducimos cualquier
    # fallo de cálculo a un 422 LEGIBLE (no un 500 opaco) para que el mensaje sea accionable.
    try:
        R = calcular(json.loads(json.dumps(par)))             # recálculo con el motor (copia; no muta)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"El proyecto no se pudo calcular: {e}") from e
    R_norm = json.loads(json.dumps(R, default=str))
    cuadres = checks.correr(R)
    sb.table("scenarios").update({"status": "approved"}).eq("id", scenario_id).eq("status", "draft").execute()
    sb.table("results_cache").upsert({
        "scenario_id": scenario_id, "engine_version": ENGINE_V,
        "inputs_hash": _hash(par), "results": R_norm,
    }, on_conflict="scenario_id").execute()
    _audit(sb, "scenario", scenario_id, "approve", actor)
    ap = R.get("apalancamiento") or {}
    return {
        "scenario_id": scenario_id, "status": "approved", "version": sc["version"],
        "tir_proyecto": ap.get("tir_proyecto"),
        "checks_ok": all(c.ok for c in cuadres),
        "checks": [{"clave": c.clave, "nombre": c.nombre, "ok": c.ok} for c in cuadres],
    }


def fijar_baseline(scenario_id: str, *, actor: str | None) -> dict:
    """`approved → baseline`: degrada el baseline previo del proyecto y fija este (un baseline/proyecto)."""
    sb = _sb()
    sc = _scenario(sb, scenario_id)
    if sc["status"] not in ("approved", "baseline"):
        raise HTTPException(status_code=409, detail="Solo un escenario aprobado puede ser baseline")
    # degradar el baseline previo (respeta el unique index un-baseline-por-proyecto)
    (sb.table("scenarios").update({"status": "approved"})
     .eq("project_id", sc["project_id"]).eq("status", "baseline").execute())
    sb.table("scenarios").update({"status": "baseline"}).eq("id", scenario_id).execute()
    _audit(sb, "scenario", scenario_id, "set_baseline", actor)
    return {"scenario_id": scenario_id, "status": "baseline", "version": sc["version"]}
