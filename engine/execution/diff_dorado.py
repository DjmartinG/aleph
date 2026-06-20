# -*- coding: utf-8 -*-
"""Gobernanza del dorado: DIFF "viejo vs nuevo" con allowlist de acta (spec_pyg_dinamico.md §2.3).

Cuando un re-baseline mueve cifras A PROPÓSITO, el acta debe listar CADA cifra que cambia. Esta
herramienta compara el dorado VIEJO contra el NUEVO y **FALLA si cambió cualquier cifra que NO esté en
el allowlist del acta** — atrapa el "cambio colateral oculto" (un campo que se movió sin querer y que
el harness ordinario, al regenerar snapshots, ya no detectaría). Es la red que la spec exige y que
hasta hoy se hacía ad-hoc (ver docs/acta_flujo_equity_20260614.md «Pendiente relacionado»).

ADITIVA: no toca `calcular()` ni el motor; solo compara resultados YA producidos.

Dos modos:
  1) RECOMPUTE (por defecto) — viejo = `result` congelado en cada snapshot dorado; nuevo =
     `calcular(input_par)` con el motor ACTUAL. Úsalo tras cambiar el motor, ANTES de regenerar
     snapshots, para ver exactamente qué se movió:
        python execution/diff_dorado.py --permite apalancamiento.flujo_equity apalancamiento.tir_equity
  2) DOS CARPETAS — viejo = snapshots archivados; nuevo = snapshots regenerados:
        python execution/diff_dorado.py --viejo engine/tests/golden/_archivo/20260614 \
                                        --nuevo engine/tests/golden --permite pyg.udi pyg.renta

Sale con código 1 si hay cambios COLATERALES (o snapshots añadidos/faltantes) → rompe el build del
re-baseline. Las rutas del allowlist se comparan ignorando los índices de lista (`[i]`), así
`apalancamiento.flujo_equity` cubre toda la serie `apalancamiento.flujo_equity[*]`.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TOL_REL = 0.001   # 0.1% (igual que el harness dorado)
TOL_ABS = 1e-6
_MISSING = object()


@dataclass(frozen=True)
class Cambio:
    snapshot: str
    ruta: str
    viejo: object
    nuevo: object


@dataclass
class Reporte:
    esperados: list = field(default_factory=list)         # cambiaron Y están en el allowlist del acta
    colaterales: list = field(default_factory=list)       # cambiaron y NO están en el acta → FALLA
    permitido_sin_uso: list = field(default_factory=list) # entradas del acta que no movieron nada
    solo_viejo: list = field(default_factory=list)        # snapshots presentes solo en el viejo
    solo_nuevo: list = field(default_factory=list)        # snapshots presentes solo en el nuevo

    @property
    def ok(self) -> bool:
        """Verde solo si no hay cambios colaterales ni snapshots añadidos/faltantes."""
        return not (self.colaterales or self.solo_viejo or self.solo_nuevo)


def _norm(obj):
    """Normaliza a JSON puro (fechas/objetos → str), igual que el generador del snapshot."""
    return json.loads(json.dumps(obj, default=str, ensure_ascii=False))


def diff_resultados(viejo, nuevo, ruta="", tol_rel=TOL_REL, tol_abs=TOL_ABS, out=None):
    """Rutas HOJA donde `nuevo` difiere de `viejo` más que la tolerancia → [(ruta, viejo, nuevo), ...].

    Mismo criterio que el harness dorado: 0.1% relativo (abs 1e-6 para casi-cero), recursivo sobre
    dicts/listas, los bool se comparan exactos. Una clave/índice presente en un solo lado cuenta como
    cambio.
    """
    if out is None:
        out = []
    if isinstance(viejo, bool) or isinstance(nuevo, bool):
        if viejo != nuevo:
            out.append((ruta, viejo, nuevo))
    elif isinstance(viejo, (int, float)) and isinstance(nuevo, (int, float)):
        if abs(viejo - nuevo) > max(tol_abs, tol_rel * abs(viejo)):
            out.append((ruta, viejo, nuevo))
    elif isinstance(viejo, dict) and isinstance(nuevo, dict):
        for k in sorted(set(viejo) | set(nuevo)):
            diff_resultados(viejo.get(k, _MISSING), nuevo.get(k, _MISSING), f"{ruta}.{k}", tol_rel, tol_abs, out)
    elif isinstance(viejo, list) and isinstance(nuevo, list):
        if len(viejo) != len(nuevo):
            out.append((ruta, f"len={len(viejo)}", f"len={len(nuevo)}"))
        else:
            for i, (v, n) in enumerate(zip(viejo, nuevo)):
                diff_resultados(v, n, f"{ruta}[{i}]", tol_rel, tol_abs, out)
    else:
        if viejo != nuevo:
            out.append((ruta, viejo, nuevo))
    return out


def _normaliza_ruta(ruta: str) -> str:
    """Quita los índices de lista (`[12]`) y el punto inicial → 'apalancamiento.flujo_equity'."""
    return re.sub(r"\[\d+\]", "", ruta).lstrip(".")


def permitido(ruta: str, allowlist) -> bool:
    """True si la ruta (sin índices) coincide con una entrada del acta o cuelga de ella (prefijo)."""
    p = _normaliza_ruta(ruta)
    return any(p == e or p.startswith(e + ".") for e in allowlist)


def diff_snapshots(viejo_map: dict, nuevo_map: dict, allowlist=(), tol_rel=TOL_REL, tol_abs=TOL_ABS) -> Reporte:
    """Compara dos conjuntos de resultados {nombre_snapshot: result_dict} contra el allowlist del acta.

    Devuelve un Reporte: cambios `esperados` (en el acta), `colaterales` (NO en el acta → el build debe
    fallar), `permitido_sin_uso` (entradas del acta que no movieron nada → el acta sobre-declara), y los
    snapshots presentes en un solo lado.
    """
    rep = Reporte()
    allowlist = list(allowlist)
    usados = set()
    rep.solo_viejo = sorted(set(viejo_map) - set(nuevo_map))
    rep.solo_nuevo = sorted(set(nuevo_map) - set(viejo_map))
    for nombre in sorted(set(viejo_map) & set(nuevo_map)):
        for ruta, v, n in diff_resultados(viejo_map[nombre], nuevo_map[nombre], tol_rel=tol_rel, tol_abs=tol_abs):
            cambio = Cambio(nombre, ruta, v, n)
            if permitido(ruta, allowlist):
                rep.esperados.append(cambio)
                p = _normaliza_ruta(ruta)
                for e in allowlist:
                    if p == e or p.startswith(e + "."):
                        usados.add(e)
            else:
                rep.colaterales.append(cambio)
    rep.permitido_sin_uso = [e for e in allowlist if e not in usados]
    return rep


# ─────────────────────────────── carga / recompute ───────────────────────────────

def cargar_dir(d) -> dict:
    """{nombre_archivo: result} desde una carpeta de snapshots (*_snapshot.json)."""
    out = {}
    for p in sorted(Path(d).glob("*_snapshot.json")):
        snap = json.load(open(p, encoding="utf-8"))
        out[p.name] = snap.get("result", {})
    return out


def _golden_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "tests" / "golden"


def recompute_map(golden_dir=None):
    """viejo = `result` congelado de cada snapshot; nuevo = `calcular(input_par)` con el motor ACTUAL."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # engine/ → aleph_engine importable
    from aleph_engine import calcular
    golden_dir = Path(golden_dir) if golden_dir else _golden_dir()
    viejo, nuevo = {}, {}
    for p in sorted(golden_dir.glob("*_snapshot.json")):
        snap = json.load(open(p, encoding="utf-8"))
        viejo[p.name] = snap.get("result", {})
        nuevo[p.name] = _norm(calcular(copy.deepcopy(snap["input_par"])))
    return viejo, nuevo


# ─────────────────────────────── CLI ───────────────────────────────

def _fmt(c: Cambio) -> str:
    return f"    {c.snapshot}{c.ruta}: {c.viejo!r} -> {c.nuevo!r}"


def main(argv=None) -> int:
    try:                                  # consola Windows (cp1252) → utf-8 para no romper al imprimir
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Diff de gobernanza del dorado (viejo vs nuevo) con allowlist de acta.")
    ap.add_argument("--viejo", help="carpeta de snapshots VIEJOS (archivados). Si se omite, modo recompute.")
    ap.add_argument("--nuevo", help="carpeta de snapshots NUEVOS (regenerados).")
    ap.add_argument("--golden", help="carpeta de snapshots para el modo recompute (default engine/tests/golden).")
    ap.add_argument("--permite", nargs="*", default=[], metavar="RUTA",
                    help="rutas (del acta) cuyo cambio está APROBADO, p.ej. apalancamiento.tir_equity pyg.udi")
    ap.add_argument("--tol-rel", type=float, default=TOL_REL)
    args = ap.parse_args(argv)

    if args.viejo or args.nuevo:
        if not (args.viejo and args.nuevo):
            ap.error("usa --viejo Y --nuevo juntos, o ninguno (modo recompute)")
        viejo_map, nuevo_map = cargar_dir(args.viejo), cargar_dir(args.nuevo)
        modo = f"carpetas\n  viejo: {args.viejo}\n  nuevo: {args.nuevo}"
    else:
        viejo_map, nuevo_map = recompute_map(args.golden)
        modo = "recompute (snapshot congelado vs motor actual)"

    rep = diff_snapshots(viejo_map, nuevo_map, allowlist=args.permite, tol_rel=args.tol_rel)

    print(f"== Diff de gobernanza del dorado — {modo}")
    print(f"   snapshots comparados: {len(set(viejo_map) & set(nuevo_map))}; allowlist (acta): {args.permite or '(ninguno)'}")
    print(f"   cambios esperados (en el acta): {len(rep.esperados)}; colaterales: {len(rep.colaterales)}")
    if rep.permitido_sin_uso:
        print("   [aviso] allowlist sin uso (el acta declara cifras que NO se movieron): " + ", ".join(rep.permitido_sin_uso))
    if rep.solo_viejo:
        print("   [aviso] snapshots solo en VIEJO: " + ", ".join(rep.solo_viejo))
    if rep.solo_nuevo:
        print("   [aviso] snapshots solo en NUEVO: " + ", ".join(rep.solo_nuevo))
    if rep.colaterales:
        print(f"\n[X] {len(rep.colaterales)} CAMBIO(S) COLATERAL(ES) -- fuera del acta (muestra hasta 30):")
        for c in rep.colaterales[:30]:
            print(_fmt(c))
        print("\nFALLA: regenerar el dorado ENMASCARARIA estos cambios. Justificalos en el acta "
              "(--permite) o revierte lo que los causo.")
        return 1
    print("\n[OK] Todos los cambios estan listados en el acta (cero colaterales).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
