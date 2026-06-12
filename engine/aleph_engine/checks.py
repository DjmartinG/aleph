# -*- coding: utf-8 -*-
"""Checks de CUADRE del motor — reconciliaciones sobre el resultado de `calcular()`.

Constitución §Gobernanza de cifras: el motor expone checks de cuadre que la UI/API muestran en cada
módulo (estado verde/rojo). NO son fórmulas nuevas: son **reconciliaciones** que verifican que las
cifras ya calculadas sean internamente consistentes. Si un check falla, hay un error de modelo o de
datos que la UI debe señalar.

Invariantes verificados (numéricamente ciertos en los 3 proyectos reales):
  1. P&G: `total_ingresos == ventas + reconocimientos`.
  2. Recaudo: `sum(ingresos del flujo apalancado) == total_ingresos` (lo recaudado cuadra con el P&G).
  3. Flujo: `acumulado_operativo[-1] == utilidad operativa` (el flujo operativo cierra en la utilidad).
  4. Reparto: `CG + socio == resultados` (la utilidad repartida cuadra con el total repartible).
  5. Crédito: `0 <= cupo_credito <= valor_financiable` y `credito_max >= 0` (el cupo no excede la base).
  6. (EVM, opcional) SPI plausible en [0.4, 2.0].
"""
from __future__ import annotations

from dataclasses import dataclass

_TOL_REL = 0.001   # 0.1% (igual que el snapshot dorado)
_TOL_ABS = 1.0     # miles COP: 1 es ruido


@dataclass(frozen=True)
class Check:
    clave: str
    nombre: str
    ok: bool
    detalle: str


def _cerca(a: float, b: float) -> bool:
    return abs(a - b) <= max(_TOL_ABS, _TOL_REL * max(abs(a), abs(b)))


def _mk(clave: str, nombre: str, ok: bool, detalle: str) -> Check:
    return Check(clave, nombre, bool(ok), detalle)


def correr(R: dict) -> list[Check]:
    """Corre los checks de cuadre sobre el resultado de `calcular()`. Devuelve solo los que aplican
    (omite un check si faltan sus insumos, p.ej. un proyecto sin flujo apalancado)."""
    out: list[Check] = []
    pyg = R.get("pyg") or {}
    ap = R.get("apalancamiento") or {}

    # 1) P&G: ingresos cuadran
    ti, v, rc = pyg.get("total_ingresos"), pyg.get("ventas"), pyg.get("recon_codensa", 0.0)
    if ti is not None and v is not None:
        out.append(_mk("pyg_ingresos", "P&G: ingresos cuadran", _cerca(ti, v + rc),
                       f"total_ingresos {ti:,.0f} vs ventas+recon {v + rc:,.0f}"))

    # 2) Recaudo = ingresos del P&G
    ing = ap.get("ingresos")
    if isinstance(ing, list) and ing and ti is not None:
        s = sum(ing)
        out.append(_mk("recaudo_ventas", "Recaudo = ingresos del P&G", _cerca(s, ti),
                       f"recaudo {s:,.0f} vs total_ingresos {ti:,.0f}"))

    # 3) Flujo operativo acumulado = utilidad operativa
    acum, uo = ap.get("acumulado"), pyg.get("util_oper")
    if isinstance(acum, list) and acum and uo is not None:
        out.append(_mk("flujo_utilidad", "Flujo final = utilidad operativa", _cerca(acum[-1], uo),
                       f"acumulado[-1] {acum[-1]:,.0f} vs util_oper {uo:,.0f}"))

    # 4) Reparto CG + socio = resultados
    cg, so, res = pyg.get("cg"), pyg.get("socio"), pyg.get("resultados")
    if None not in (cg, so, res):
        out.append(_mk("reparto", "Reparto CG + socio = resultados", _cerca(cg + so, res),
                       f"cg+socio {cg + so:,.0f} vs resultados {res:,.0f}"))

    # 5) Crédito: cupo no excede el valor financiable; saldo máx no es negativo
    cap, vf, cm = ap.get("cap_credito"), ap.get("valor_financiable"), ap.get("credito_max")
    if None not in (cap, vf, cm):
        ok = (0 <= cap <= vf + _TOL_ABS) and (cm >= -_TOL_ABS)
        out.append(_mk("credito", "Crédito cuadra (cupo ≤ financiable)", ok,
                       f"cupo {cap:,.0f} ≤ financiable {vf:,.0f}; crédito_max {cm:,.0f}"))

    return out


# --- Check de EVM (requiere un resultado de evm.calcular_evm, que no está en calcular()) ---
SPI_MIN, SPI_MAX = 0.4, 2.0


def check_spi(evm: dict) -> Check:
    """SPI dentro de un rango plausible [0.4, 2.0]. Fuera de ahí, sospechar de los datos de avance."""
    spi = (evm or {}).get("SPI")
    ok = spi is not None and SPI_MIN <= spi <= SPI_MAX
    return _mk("spi_plausible", f"SPI plausible [{SPI_MIN}, {SPI_MAX}]", ok, f"SPI={spi}")


def todos_ok(checks: list[Check]) -> bool:
    """True si todos los checks pasaron (para el badge global de la UI)."""
    return all(c.ok for c in checks)
