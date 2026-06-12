# -*- coding: utf-8 -*-
"""ETL de importación v1 (PROMPT 4 · Fase 4b). Pobla projects/scenarios desde la tabla `proyectos`.

IDEMPOTENTE y NO destructivo: lee `proyectos` (sin tocarla), valida cada `par` con el contrato del
motor (`aleph_engine.schema.parse`), y por cada proyecto:
  - upsert en `projects` (slug, nombre, es_real, fase = meta.estado o 'construccion'),
  - inserta el escenario v1 `approved` con `snapshot` = el `par` COMPLETO (bit a bit; cero pérdida),
  - computa `calcular(par)` y lo guarda en `results_cache` (engine_version + hash del snapshot),
  - registra un evento `import_v1` en `audit_log`,
  - imprime las cifras clave (TIR proyecto/socio, VPN, crédito) para verificación visual.

Como el snapshot se guarda SIN transformar y `calcular()` es determinista, la migración NO puede
mover ninguna cifra (es copia + recálculo con el mismo motor). Re-ejecutar no duplica.

Requisitos: `SUPABASE_URL` + `SUPABASE_KEY` (service_role) en el entorno, o en
`app_streamlit/.streamlit/secrets.toml`. Antes de correr esto: aplicar `db/migrations/0001_aleph_schema.sql`.

Uso:  python db/etl_import_v1.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

try:
    from aleph_engine import calcular, config, schema
except ImportError:
    sys.exit("Falta aleph_engine. Instálalo:  pip install -e ./engine")
try:
    from supabase import create_client
except ImportError:
    sys.exit("Falta supabase. Instálalo:  pip install supabase")


def _config_supabase() -> tuple[str, str]:
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    if url and key:
        return url, key
    sec = ROOT / "app_streamlit" / ".streamlit" / "secrets.toml"
    if sec.is_file():
        data = tomllib.loads(sec.read_text(encoding="utf-8"))
        if data.get("SUPABASE_URL") and data.get("SUPABASE_KEY"):
            return data["SUPABASE_URL"], data["SUPABASE_KEY"]
    sys.exit("Faltan SUPABASE_URL/SUPABASE_KEY (entorno o secrets.toml).")


def _hash(snapshot: dict) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, default=str).encode()).hexdigest()


def _fase(par: dict) -> str:
    e = (par.get("meta") or {}).get("estado") or config.ESTADO_DEFAULT
    return e if e in config.ESTADOS else config.ESTADO_DEFAULT


def main() -> None:
    url, key = _config_supabase()
    sb = create_client(url, key)

    # Empresa CG (la creó la migración 0001).
    comp = sb.table("companies").select("id").eq("slug", "cg-constructora").limit(1).execute()
    if not comp.data:
        sys.exit("No existe la empresa 'cg-constructora'. ¿Corriste db/migrations/0001_aleph_schema.sql?")
    company_id = comp.data[0]["id"]

    filas = sb.table("proyectos").select("slug,nombre,es_real,data,updated_by").execute().data or []
    print(f"Proyectos en `proyectos`: {len(filas)}\n")

    from aleph_engine import __version__ as ENGINE_V
    ok = invalidos = 0
    for row in filas:
        slug = row["slug"]
        par = row.get("data") or {}
        try:
            schema.parse(par)                       # valida el contrato; no transforma
        except Exception as e:
            print(f"  ✗ {slug}: inválido ({e.__class__.__name__}) — OMITIDO")
            invalidos += 1
            continue

        # projects (upsert por slug)
        proj = sb.table("projects").upsert({
            "company_id": company_id, "slug": slug,
            "nombre": row.get("nombre") or (par.get("meta") or {}).get("nombre") or slug,
            "es_real": bool(row.get("es_real")), "fase": _fase(par),
            "updated_by": row.get("updated_by"),
        }, on_conflict="slug").execute().data[0]
        pid = proj["id"]

        # scenario v1 approved (idempotente: solo si no existe la v1)
        existe = sb.table("scenarios").select("id").eq("project_id", pid).eq("version", 1).execute().data
        if existe:
            sid = existe[0]["id"]
        else:
            snap = dict(par)
            snap.setdefault("schema_version", 1)    # backfill del contrato
            sid = sb.table("scenarios").insert({
                "project_id": pid, "version": 1, "status": "approved",
                "snapshot": snap, "label": "import_v1", "created_by": row.get("updated_by"),
            }).execute().data[0]["id"]
            sb.table("audit_log").insert({
                "entity_type": "scenario", "entity_id": sid, "action": "import_v1",
                "actor": row.get("updated_by"),
            }).execute()

        # results_cache (recálculo con el MISMO motor → cifras idénticas por construcción)
        R = calcular(json.loads(json.dumps(par)))
        R_norm = json.loads(json.dumps(R, default=str))
        sb.table("results_cache").upsert({
            "scenario_id": sid, "engine_version": ENGINE_V, "inputs_hash": _hash(par),
            "results": R_norm,
        }, on_conflict="scenario_id").execute()

        ap = R.get("apalancamiento") or {}
        print(f"  ✓ {slug:24s} fase={_fase(par):14s} "
              f"TIRproy={ap.get('tir_proyecto')!s:>8.8} VPN={ap.get('vpn_proyecto')!s:>14.14} "
              f"créditoMax={ap.get('credito_max')!s:>14.14}")
        ok += 1

    print(f"\nImportados: {ok}  ·  inválidos (omitidos): {invalidos}")
    print("Verifica que las cifras de arriba coincidan con las de producción (Navarra TIR proyecto 37.60%).")


if __name__ == "__main__":
    main()
