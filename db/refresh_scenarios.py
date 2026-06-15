# -*- coding: utf-8 -*-
"""Refresca el modelo objetivo (`scenarios`) de los proyectos REALES en Supabase al `par` ACTUAL del repo.

POR QUÉ: prod lee el `par` desde `scenarios.snapshot`, congelado por el ETL del 12-jun (Fase 4b, PRE-M1).
El re-baseline del WACC (y los demás cambios de M1-M8 que viven en el DATO, no en el código) no está en
prod. Como un snapshot APROBADO es INMUTABLE (migración 0002), refrescar = crear una VERSIÓN NUEVA
aprobada (NO editar la vieja). `repo.cargar` lee la versión más alta → prod pasa a leer la nueva.

Qué hace por cada proyecto real (navarra/dominica/torres = los 3 que están en prod):
  1. Lee el `par` ACTUAL del JSON REAL local (`data/proyectos_privados/{slug}_REAL.json`).
  2. Valida con `schema.parse` (la MISMA compuerta del motor que el ETL y la API).
  3. GATE DORADO: recalcula `calcular(par)` y lo COMPARA contra el golden REAL local (tol 0.1%) +
     ancla dura (WACC 18.71% en los 3; Navarra TIR proyecto 37.60%). Si algo no cuadra → ABORTA TODO
     (no escribe nada): nunca empuja un `par` corrupto a prod.
  4. IDEMPOTENTE: si el snapshot vigente ya tiene este `par` (mismo hash) → SKIP.
  5. Inserta `scenarios` v(max+1) status='approved' snapshot=par (respeta inmutabilidad: INSERT, no UPDATE).
  6. Upsert `results_cache` (recálculo) + actualiza el espejo `proyectos.data` (best-effort) + audita.

SEGURO: DRY-RUN por defecto (NO escribe). Pasa `--apply` para escribir. Re-ejecutar es idempotente.
`--check-only` corre solo el gate dorado local (sin Supabase) — útil para verificar sin credenciales.

Requisitos: `SUPABASE_URL` + `SUPABASE_KEY` (service_role) en entorno o en
`.streamlit/secrets.toml`; el motor instalado (`pip install -e ./engine`).

Uso:  python db/refresh_scenarios.py               # dry-run (muestra qué haría, no escribe)
      python db/refresh_scenarios.py --apply       # aplica (crea v2 approved)
      python db/refresh_scenarios.py --check-only   # solo gate dorado local (sin Supabase)
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
    from aleph_engine import calcular, config, schema
    from aleph_engine import __version__ as ENGINE_V
except ImportError:
    sys.exit("Falta aleph_engine. Instálalo:  pip install -e ./engine  (o corre con PYTHONPATH=engine)")

# Los 3 proyectos REALES que están en producción (project_count=3). Argos (M8) NO está en prod: es un
# alta separada, fuera del alcance de este refresco de WACC.
SLUGS = ["1_navarra", "2_dominica", "3_torres_campinas"]

PRIV = ROOT / "data" / "proyectos_privados"
GOLDEN = ROOT / "engine" / "tests" / "golden"

# Anclas DURAS del re-baseline (belt-and-suspenders sobre la comparación contra el golden).
WACC_OBJETIVO = 0.187126          # 18.71% en los 3 (mismo bloque WACC)
NAVARRA_TIR_PROYECTO = 0.375975   # 37.60% — el ancla headline del dorado

# Campos del dorado que se comparan calcular(par) vs golden (apalancamiento).
_CAMPOS = ["tir_proyecto", "vpn_proyecto", "tir_equity", "credito_max", "wacc"]


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


def _hash(par: dict) -> str:
    snap = _con_schema(par)
    return hashlib.sha256(json.dumps(snap, sort_keys=True, default=str).encode()).hexdigest()


def _con_schema(par: dict) -> dict:
    snap = dict(par)
    snap.setdefault("schema_version", 1)
    return snap


def _fase(par: dict) -> str:
    e = (par.get("meta") or {}).get("estado") or config.ESTADO_DEFAULT
    return e if e in config.ESTADOS else config.ESTADO_DEFAULT


def _aprox(a, b, tol_rel=1e-3) -> bool:
    """Igual con tolerancia relativa 0.1% (o absoluta 1e-6 para valores ~0). None==None."""
    if a is None or b is None:
        return a is None and b is None
    if abs(b) < 1e-9:
        return abs(a - b) < 1e-6
    return abs(a - b) <= tol_rel * abs(b)


def gate_dorado(exigir_golden: bool = False) -> dict[str, dict]:
    """Lee cada REAL JSON, valida, recalcula y verifica contra el golden + anclas duras.
    Devuelve {slug: {par, R, nombre, es_real}}. ABORTA (sys.exit) si algo no cuadra.
    `exigir_golden=True` (modo --apply): ABORTA si falta el golden (no degrada el gate en silencio)."""
    out: dict[str, dict] = {}
    print("== GATE DORADO (verificación local antes de tocar Supabase) ==")
    for slug in SLUGS:
        src = PRIV / f"{slug}_REAL.json"
        if not src.is_file():
            sys.exit(f"FALTA el JSON REAL local: {src}. (Son los datos confidenciales; este script se "
                     f"corre desde tu máquina, donde existen.)")
        # `par` = el objeto EXACTO que se escribirá (con schema_version): así lo verificado == lo escrito,
        # bit a bit (calcular() ignora schema_version, no afecta ninguna cifra).
        par = _con_schema(json.load(open(src, encoding="utf-8")))
        try:
            schema.parse(par)
        except Exception as e:
            sys.exit(f"ABORT {slug}: el par no pasa schema.parse ({e.__class__.__name__}: {e})")
        R = calcular(json.loads(json.dumps(par)))
        ap = R.get("apalancamiento") or {}

        # (a) comparar contra el golden REAL local (la fuente de verdad ya verificada por los tests)
        gpath = GOLDEN / f"{slug}_REAL_snapshot.json"
        if gpath.is_file():
            gap = (json.load(open(gpath, encoding="utf-8")).get("result") or {}).get("apalancamiento") or {}
            for c in _CAMPOS:
                if not _aprox(ap.get(c), gap.get(c)):
                    sys.exit(f"ABORT {slug}: '{c}' calculado ({ap.get(c)}) != golden ({gap.get(c)}). "
                             f"El par en disco no reproduce el dorado verificado. NO se escribe nada.")
        elif exigir_golden:
            sys.exit(f"ABORT {slug}: falta el golden {gpath.name} y estás en --apply. El golden es la "
                     f"fuente de verdad auditada; no es opcional al escribir datos REALES. Regenera los "
                     f"snapshots (python engine/execution/snapshot_dorado.py) o, si SABES lo que "
                     f"haces, usa --skip-golden-check.")
        else:
            print(f"  ! {slug}: sin golden local ({gpath.name}); se omite la comparación contra golden.")

        # (b) anclas duras del re-baseline
        if not _aprox(ap.get("wacc"), WACC_OBJETIVO, tol_rel=3e-3):
            sys.exit(f"ABORT {slug}: WACC {ap.get('wacc')} != objetivo {WACC_OBJETIVO} (18.71%). "
                     f"¿Los JSON locales tienen kd_us=5.9 y rp=3.43? NO se escribe nada.")
        if slug == "1_navarra" and not _aprox(ap.get("tir_proyecto"), NAVARRA_TIR_PROYECTO):
            sys.exit(f"ABORT navarra: TIR proyecto {ap.get('tir_proyecto')} != dorado {NAVARRA_TIR_PROYECTO}.")

        nombre = (par.get("meta") or {}).get("nombre") or slug
        es_real = True   # son los *_REAL.json
        out[slug] = {"par": par, "R": R, "nombre": nombre, "es_real": es_real}
        print(f"  OK {slug:22s} TIRproy={ap.get('tir_proyecto'):.6f}  "
              f"WACC={ap.get('wacc'):.6f}  VPN={ap.get('vpn_proyecto'):.1f}  "
              f"créditoMax={ap.get('credito_max'):.0f}")
    print("== GATE DORADO OK: las 3 cifras cuadran. ==\n")
    return out


def main() -> None:
    pa = argparse.ArgumentParser(description="Refresca scenarios al par actual (crea v2 approved).")
    pa.add_argument("--apply", action="store_true", help="Escribe en Supabase (sin esto: dry-run).")
    pa.add_argument("--check-only", action="store_true", help="Solo el gate dorado local (sin Supabase).")
    pa.add_argument("--skip-golden-check", action="store_true",
                    help="(avanzado) no abortar en --apply si falta el golden local.")
    args = pa.parse_args()

    datos = gate_dorado(exigir_golden=(args.apply and not args.skip_golden_check))
    if args.check_only:
        print("--check-only: gate dorado verde. No se toca Supabase.")
        return

    url, key = _config_supabase()
    try:
        from supabase import create_client
    except ImportError:
        sys.exit("Falta supabase. Instálalo:  pip install supabase")
    sb = create_client(url, key)

    modo = "APPLY (escribiendo)" if args.apply else "DRY-RUN (no escribe)"
    print(f"== Refresco de scenarios — modo {modo} ==")

    creados = saltados = 0
    for slug, d in datos.items():
        par, R, nombre, es_real = d["par"], d["R"], d["nombre"], d["es_real"]
        proj = sb.table("projects").select("id").eq("slug", slug).limit(1).execute().data
        if not proj:
            print(f"  ! {slug}: NO existe en `projects` (¿corriste el ETL/migración 0001?). Saltado.")
            continue
        pid = proj[0]["id"]

        rows = (sb.table("scenarios").select("version,status,snapshot")
                .eq("project_id", pid).order("version", desc=True).execute().data) or []
        nuevo_hash = _hash(par)
        if rows and _hash(rows[0]["snapshot"]) == nuevo_hash:
            print(f"  = {slug}: el escenario vigente (v{rows[0]['version']}, {rows[0]['status']}) ya "
                  f"tiene este par (mismo hash). SKIP (idempotente).")
            saltados += 1
            continue
        nv = (max(r["version"] for r in rows) + 1) if rows else 1
        vigente = f"v{rows[0]['version']} {rows[0]['status']}" if rows else "(ninguno)"

        if not args.apply:
            ap = R.get("apalancamiento") or {}
            print(f"  + {slug}: CREARÍA scenarios v{nv} approved (vigente hoy: {vigente}). "
                  f"WACC {ap.get('wacc'):.4f}, TIRproy {ap.get('tir_proyecto'):.4f}.")
            creados += 1
            continue

        # --- ESCRITURA (--apply) ---
        snap = _con_schema(par)
        sid = sb.table("scenarios").insert({
            "project_id": pid, "version": nv, "status": "approved",
            "snapshot": snap, "label": "refresh_wacc_rebaseline_20260614", "created_by": "refresh_scenarios",
        }).execute().data[0]["id"]
        R_norm = json.loads(json.dumps(R, default=str))
        sb.table("results_cache").upsert({
            "scenario_id": sid, "engine_version": ENGINE_V, "inputs_hash": nuevo_hash, "results": R_norm,
        }, on_conflict="scenario_id").execute()
        sb.table("audit_log").insert({
            "entity_type": "scenario", "entity_id": sid, "action": "refresh_rebaseline",
            "actor": "refresh_scenarios", "diff": {"motivo": "WACC re-baseline beta_d BBB + rp BB-",
                                                   "version_nueva": nv, "version_anterior": vigente},
        }).execute()
        # espejo `proyectos.data` (best-effort: la lectura de prod ya es `scenarios`; esto es higiene)
        try:
            sb.table("proyectos").upsert(
                {"slug": slug, "nombre": nombre, "es_real": es_real, "data": par},
                on_conflict="slug").execute()
        except Exception as e:
            print(f"    (aviso) no se pudo actualizar el espejo proyectos.data de {slug}: {e.__class__.__name__}")
        print(f"  + {slug}: creado scenarios v{nv} approved (sid={sid}). Antes: {vigente}.")
        creados += 1

    print(f"\n{'Creados' if args.apply else 'Crearía'}: {creados}  ·  ya al día (skip): {saltados}")
    if not args.apply:
        print("DRY-RUN: nada se escribió. Vuelve a correr con --apply para aplicar.")
    else:
        print("\n*** LISTO el refresco del DATO (scenarios v2 approved). ***")
        print("!! IMPORTANTE — el API RECALCULA EN VIVO con el motor desplegado (NO usa caché). Si el")
        print("   REDEPLOY del API (motor M1-M8, SHA 2c533db) NO está hecho, prod queda en estado")
        print("   FRANKENSTEIN: el WACC 18.71% sale bien (va explícito en el dato) PERO tir_equity y la")
        print("   exención VIS se recalculan con código VIEJO. ORDEN CORRECTO: redeploy PRIMERO, refresco")
        print("   después (así nunca hay cifras de decisión viejas). Si ya redeployaste, estás OK.")
        print("   Verifica el WACC 18.71% en /web → Costo de capital (logueado; /v1 no es público).")


if __name__ == "__main__":
    main()
