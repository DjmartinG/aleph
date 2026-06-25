# -*- coding: utf-8 -*-
"""Push de un proyecto a Supabase: projects + scenario approved + results_cache + audit_log.

Lee un JSON de proyecto (el `par`), lo VALIDA con `aleph_engine.schema.parse`, RECALCULA con `calcular()`
(gate: aborta si los checks de cuadre no quedan verdes) y lo escribe en el modelo objetivo de Supabase:
  - `projects`: si el slug NO existe, lo CREA; si existe, lo usa para versionar.
  - `scenarios` v(max+1) status='approved', snapshot = el `par` (bit a bit, inmutable).
  - `results_cache`: el recálculo (engine_version + hash de inputs).
  - `audit_log`: rastro de la escritura.
  - espejo `proyectos.data` (best-effort: la lectura de prod ya es `scenarios`; esto es higiene).

Mismo patrón que `db/refresh_scenarios.py` (config, dry-run, idempotencia) + la lógica crear/aprobar de
`api/aleph_api/write.py`. NO toca el motor ni el dorado: solo persiste lo que `calcular()` produce.

SEGURO:
  - DRY-RUN por defecto (NO escribe). `--apply` escribe.
  - IDEMPOTENTE: si el escenario vigente ya tiene este `par` (mismo hash) → SKIP.
  - `--check-only`: corre solo el gate (schema + calcular + checks) SIN tocar Supabase.

Default: Argos-CVP (`data/proyectos_privados/4_argos_cvp_REAL.json`). Parametrizable con --json/--slug/--nombre.

Requisitos: `SUPABASE_URL` + `SUPABASE_KEY` (service_role) en el entorno o en `.streamlit/secrets.toml`;
el motor instalado (`pip install -e ./engine`) y el cliente (`pip install supabase`).

Uso (desde la raíz del repo):
  python db/push_proyecto.py --check-only     # solo valida + calcula (sin Supabase)
  python db/push_proyecto.py                   # DRY-RUN (muestra qué haría, no escribe)
  python db/push_proyecto.py --apply           # ESCRIBE en Supabase
  python db/push_proyecto.py --json data/proyectos_privados/X_REAL.json --slug x_real --nombre "X" --apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))   # por si el motor no está instalado pero sí en el repo

try:
    from aleph_engine import __version__ as ENGINE_V
    from aleph_engine import calcular, checks, config, schema
except ImportError:
    sys.exit("Falta aleph_engine. Instálalo:  pip install -e ./engine  (o corre con PYTHONPATH=engine)")

# Defaults para Argos-CVP (el proyecto de este push). Cambiables por CLI.
JSON_DEFAULT = ROOT / "data" / "proyectos_privados" / "4_argos_cvp_REAL.json"
SLUG_DEFAULT = "4_argos_cvp_REAL"      # sufijo _REAL como los demás reales en prod
NOMBRE_DEFAULT = "Argos (CVP/RenoBo)"
COMPANY_SLUG = "cg-constructora"


def _config_supabase() -> tuple[str, str]:
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY")
    if url and key:
        return url, key
    sec = ROOT / ".streamlit" / "secrets.toml"
    if sec.is_file():
        data = tomllib.loads(sec.read_text(encoding="utf-8"))
        if data.get("SUPABASE_URL") and data.get("SUPABASE_KEY"):
            return data["SUPABASE_URL"], data["SUPABASE_KEY"]
    sys.exit("Faltan SUPABASE_URL/SUPABASE_KEY (entorno o .streamlit/secrets.toml).")


def _con_schema(par: dict) -> dict:
    snap = dict(par)
    snap.setdefault("schema_version", 1)
    return snap


def _hash(par: dict) -> str:
    return hashlib.sha256(json.dumps(_con_schema(par), sort_keys=True, default=str).encode()).hexdigest()


def _fase(par: dict) -> str:
    e = (par.get("meta") or {}).get("estado") or config.ESTADO_DEFAULT
    return e if e in config.ESTADOS else config.ESTADO_DEFAULT


def gate(json_path: Path) -> dict:
    """Lee el JSON, valida, recalcula y exige checks verdes. ABORTA (sys.exit) si algo no cuadra."""
    print("== GATE (validación local antes de tocar Supabase) ==")
    if not json_path.is_file():
        sys.exit(f"No existe el JSON: {json_path}")
    par = _con_schema(json.load(open(json_path, encoding="utf-8")))   # lo que se escribe == lo verificado
    try:
        schema.parse(par)
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ABORT: el par no pasa schema.parse ({e.__class__.__name__}: {e})")
    try:
        R = calcular(json.loads(json.dumps(par)))                     # copia; no muta
    except Exception as e:  # noqa: BLE001
        sys.exit(f"ABORT: el motor no pudo calcular ({e.__class__.__name__}: {e})")
    cu = checks.correr(R)
    malos = [c.clave for c in cu if not c.ok]
    if malos:
        sys.exit(f"ABORT: checks de cuadre en rojo: {malos}. NO se escribe nada.")
    ap = R.get("apalancamiento") or {}
    print(f"  OK schema.parse + calcular + checks ({len(cu)} verdes).")
    print(f"  TIR proy {ap.get('tir_proyecto', float('nan')):.4f} | TIR proy after-tax "
          f"{ap.get('tir_proyecto_at', float('nan')):.4f} | VPN@TIO ${ap.get('vpn_proyecto', 0)/1e6:,.1f} mil M")
    print("== GATE OK ==\n")
    return {"par": par, "R": R, "ap": ap}


def main() -> None:
    pa = argparse.ArgumentParser(description="Push de un proyecto a Supabase (projects + scenario approved).")
    pa.add_argument("--json", default=str(JSON_DEFAULT), help="Ruta del JSON del proyecto (par).")
    pa.add_argument("--slug", default=SLUG_DEFAULT, help="Slug del proyecto en la BD.")
    pa.add_argument("--nombre", default=NOMBRE_DEFAULT, help="Nombre del proyecto.")
    pa.add_argument("--apply", action="store_true", help="Escribe en Supabase (sin esto: dry-run).")
    pa.add_argument("--check-only", action="store_true", help="Solo el gate local (sin Supabase).")
    pa.add_argument("--actor", default="push_proyecto", help="Actor para la auditoría.")
    args = pa.parse_args()

    try:                                  # consola Windows cp1252: evita UnicodeEncodeError
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                     # noqa: BLE001
        pass

    d = gate(Path(args.json))
    par, R, ap = d["par"], d["R"], d["ap"]
    if args.check_only:
        print("--check-only: gate verde. No se toca Supabase.")
        return

    url, key = _config_supabase()
    try:
        from supabase import create_client
    except ImportError:
        sys.exit("Falta supabase. Instálalo:  pip install supabase")
    sb = create_client(url, key)

    modo = "APPLY (escribiendo)" if args.apply else "DRY-RUN (no escribe)"
    print(f"== Push de '{args.nombre}' (slug={args.slug}) — modo {modo} ==")

    # 1) empresa
    comp = sb.table("companies").select("id").eq("slug", COMPANY_SLUG).limit(1).execute().data
    if not comp:
        sys.exit(f"La empresa '{COMPANY_SLUG}' no existe (¿corriste la migración 0001?).")
    company_id = comp[0]["id"]

    # 2) proyecto (crear si no existe)
    proj = sb.table("projects").select("id").eq("slug", args.slug).limit(1).execute().data
    nuevo_hash = _hash(par)
    if proj:
        pid = proj[0]["id"]
        rows = (sb.table("scenarios").select("version,status,snapshot")
                .eq("project_id", pid).order("version", desc=True).execute().data) or []
        if rows and _hash(rows[0]["snapshot"]) == nuevo_hash:
            print(f"  = Proyecto existe y el escenario vigente (v{rows[0]['version']}, {rows[0]['status']}) "
                  f"ya tiene este par (mismo hash). SKIP (idempotente).")
            return
        nv = (max(r["version"] for r in rows) + 1) if rows else 1
        print(f"  Proyecto EXISTE (pid={pid}); crearía scenarios v{nv} approved.")
    else:
        pid = None
        nv = 1
        print(f"  Proyecto NO existe; crearía projects '{args.slug}' + scenarios v1 approved.")

    if not args.apply:
        print(f"\n  DRY-RUN: TIR proy {ap.get('tir_proyecto', 0):.4f}, fase '{_fase(par)}'. Nada escrito.")
        print("  Vuelve a correr con --apply para aplicar.")
        return

    # --- ESCRITURA (--apply) ---
    if pid is None:
        pid = sb.table("projects").insert({
            "company_id": company_id, "slug": args.slug, "nombre": args.nombre,
            "es_real": True, "fase": _fase(par), "updated_by": args.actor,
        }).execute().data[0]["id"]
        print(f"  + projects creado (pid={pid}).")

    snap = _con_schema(par)
    sid = sb.table("scenarios").insert({
        "project_id": pid, "version": nv, "status": "approved",
        "snapshot": snap, "label": f"push v{nv} ({args.actor})", "created_by": args.actor,
    }).execute().data[0]["id"]
    R_norm = json.loads(json.dumps(R, default=str))
    sb.table("results_cache").upsert({
        "scenario_id": sid, "engine_version": ENGINE_V, "inputs_hash": nuevo_hash, "results": R_norm,
    }, on_conflict="scenario_id").execute()
    sb.table("audit_log").insert({
        "entity_type": "scenario", "entity_id": sid, "action": "push_proyecto",
        "actor": args.actor, "diff": {"slug": args.slug, "version": nv, "nombre": args.nombre},
    }).execute()
    # espejo proyectos.data (best-effort)
    try:
        sb.table("proyectos").upsert(
            {"slug": args.slug, "nombre": args.nombre, "es_real": True, "data": par},
            on_conflict="slug").execute()
    except Exception as e:  # noqa: BLE001
        print(f"    (aviso) no se pudo actualizar el espejo proyectos.data: {e.__class__.__name__}")

    print(f"  + scenarios v{nv} approved (sid={sid}) + results_cache + audit. LISTO.")
    print("\n*** El proyecto quedó en Supabase. El API lo sirve en /web (recalcula en vivo). ***")
    print("    Verifica en /web → Portafolio que aparezca, o en /health/data el project_count.")


if __name__ == "__main__":
    main()
