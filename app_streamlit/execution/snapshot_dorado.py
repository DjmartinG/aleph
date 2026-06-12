# -*- coding: utf-8 -*-
"""Genera el SNAPSHOT DORADO de la migración ALEPH (PROMPT 2.1).

Congela el resultado COMPLETO de `calcular()` (entrada + salida) para los 3 proyectos reales
ANTES de mover una sola línea del motor. La migración (extraer a aleph_engine, API, etc.) NO debe
cambiar ninguna de estas cifras: el harness `tests/test_golden_snapshot.py` re-ejecuta el motor
sobre la entrada congelada y exige que la salida coincida con tolerancia 0.1%.

Cada snapshot es AUTOCONTENIDO: guarda `input_par` (el dict del proyecto) y `result` (el dict R de
calcular). Así el harness no depende de los JSON de proyecto (que pueden editarse): re-corre el
motor sobre la entrada exacta que produjo las cifras doradas.

Uso:  python execution/snapshot_dorado.py        (desde app_factibilidad/)

Reales (proyectos_privados/*_REAL.json) → snapshot *_REAL_snapshot.json (gitignored, datos reales).
Ilustrativos (proyectos/*.json) → snapshot *_snapshot.json (commiteado, corre en CI).
"""
import copy
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]   # app_factibilidad/
sys.path.insert(0, str(RAIZ))
from aleph_engine import calcular, __version__ as ENGINE_V   # noqa: E402

GOLDEN = RAIZ / "tests" / "golden"
PUB = RAIZ / "proyectos"
PRIV = RAIZ / "proyectos_privados"
SLUGS = ["1_navarra", "2_dominica", "3_torres_campinas"]


def _snapshot(par):
    """Entrada + salida completa del motor, normalizadas a JSON (fechas → str)."""
    R = calcular(copy.deepcopy(par))
    norm = json.loads(json.dumps(R, default=str, ensure_ascii=False))   # fechas/objetos → str
    return {"engine_version": ENGINE_V, "input_par": par, "result": norm}


def main():
    GOLDEN.mkdir(parents=True, exist_ok=True)
    n = 0
    for slug in SLUGS:
        for src, suffix in ((PUB / f"{slug}.json", ""), (PRIV / f"{slug}_REAL.json", "_REAL")):
            if not src.exists():
                continue
            par = json.load(open(src, encoding="utf-8"))
            snap = _snapshot(par)
            out = GOLDEN / f"{slug}{suffix}_snapshot.json"
            with open(out, "w", encoding="utf-8") as fh:
                json.dump(snap, fh, ensure_ascii=False, indent=2, default=str)
            ap = snap["result"].get("apalancamiento") or {}
            print(f"OK  {out.name:38s}  TIR proyecto={ap.get('tir_proyecto')}  "
                  f"VPN={ap.get('vpn_proyecto')}  crédito_max={ap.get('credito_max')}")
            n += 1
    print(f"Listo: {n} snapshots en {GOLDEN}")


if __name__ == "__main__":
    main()
