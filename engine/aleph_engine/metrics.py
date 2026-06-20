# -*- coding: utf-8 -*-
"""Diccionario ÚNICO de indicadores del motor — registro/lookup, SIN cálculos nuevos.

Constitución §Gobernanza de cifras: cada indicador declara clave, nombre, **ETIQUETA DE BASE**
(innegociable: nunca "TIR" a secas → "TIR proyecto" / "TIR socio CG" / "TIR apalancada (ref)"),
definición, unidad y la RUTA donde vive el valor dentro del resultado de `calcular()`. La UI/API
consume SOLO de aquí para mostrar cifras con su etiqueta correcta y de forma consistente.

Este módulo NO calcula nada: `valor(R, clave)` solo BUSCA el número ya calculado por el motor.
Las etiquetas replican las que ya usa la UI Streamlit (app.py), para no introducir un segundo criterio.

Nota greenfield: un proyecto sin calendario produce TIR degenerada (p.ej. −99.99%). El valor crudo
vive aquí igual; la regla de presentación "— greenfield" (jamás mostrar −99%) es de la capa UI/API.
"""
from __future__ import annotations

from dataclasses import dataclass

# Unidades (etiquetas neutras; el formateo es-CO vive en la capa de presentación).
PCT = "%"
COP_MILES = "COP_miles"
MES = "mes"
RATIO = "ratio"
BOOL = "bool"     # veredicto binario (la UI lo muestra como GENERA/DESTRUYE, no como número)


@dataclass(frozen=True)
class Metric:
    clave: str
    nombre: str            # nombre corto para la UI
    etiqueta_base: str     # la BASE (proyecto / socio / ref / @TIO / sobre ventas…) — OBLIGATORIA
    definicion: str
    unidad: str
    ruta: tuple            # (sección, clave) dentro del dict que devuelve calcular()
    grupo: str             # agrupación para la UI
    # --- M0 (spec_pyg_dinamico.md): soporte para [VALIDAR] exigible por test (lo usan M1/M2) ---
    estado_validacion: str = "vigente"   # vigente | por_validar  (p.ej. supuesto fiscal a confirmar)
    fuente_normativa: str = ""           # norma/fuente del supuesto (ET, decreto, serie Banrep)


# Registro único. La clave es estable (la usan UI/API); `ruta` apunta al resultado de calcular().
REGISTRO: dict[str, Metric] = {
    # --- Rentabilidad — DOBLE TIR obligatoria: proyecto (desapalancada) y socio (apalancada) ---
    "tir_proyecto": Metric(
        "tir_proyecto", "TIR proyecto", "proyecto (desapalancada)",
        "TIR del flujo de caja libre del proyecto, sin deuda.",
        PCT, ("apalancamiento", "tir_proyecto"), "rentabilidad"),
    "tir_socio": Metric(
        "tir_socio", "TIR socio CG", "socio / equity (apalancada)",
        "TIR del flujo de equity del inversionista (waterfall de fiducia).",
        PCT, ("apalancamiento", "tir_equity"), "rentabilidad"),
    "tir_apalancada_ref": Metric(
        "tir_apalancada_ref", "TIR apalancada", "ref · modelo aprobado",
        "TIR apalancada de referencia tomada del modelo aprobado.",
        PCT, ("apalancamiento", "tir_apalancada_ref"), "rentabilidad"),
    # --- A3: precios constantes (reales) — TIR deflactada por inflación (Fisher). Camacol §M6 ---
    "tir_proyecto_real": Metric(
        "tir_proyecto_real", "TIR proyecto real", "precios constantes (deflactada)",
        "TIR del proyecto en términos REALES (poder adquisitivo), deflactada por la inflación "
        "(Fisher). Greenfield / sin inflación → sin dato.",
        PCT, ("apalancamiento", "tir_proyecto_real"), "rentabilidad"),
    "tir_socio_real": Metric(
        "tir_socio_real", "TIR socio real", "precios constantes (deflactada)",
        "TIR del socio (equity) en términos REALES, deflactada por la inflación (Fisher).",
        PCT, ("apalancamiento", "tir_equity_real"), "rentabilidad"),
    "vpn_proyecto": Metric(
        "vpn_proyecto", "VPN", "@TIO",
        "Valor presente neto del flujo del proyecto descontado a la TIO.",
        COP_MILES, ("apalancamiento", "vpn_proyecto"), "rentabilidad"),
    "wacc": Metric(
        "wacc", "WACC", "build-up CAPM (Damodaran)",
        "Costo promedio ponderado de capital.",
        PCT, ("apalancamiento", "wacc"), "rentabilidad"),
    "tio": Metric(
        "tio", "TIO", "tasa de descuento CG",
        "Tasa interna de oportunidad usada para descontar.",
        PCT, ("apalancamiento", "tio"), "rentabilidad"),
    "costo_oportunidad": Metric(
        "costo_oportunidad", "Costo de oportunidad", "tasa de descuento (TIO)",
        "Rendimiento mínimo exigido al capital (costo de oportunidad de CG); es la tasa que descuenta "
        "el VPN de decisión. Coincide con la TIO.",
        PCT, ("apalancamiento", "tio"), "rentabilidad"),
    "payback_mes": Metric(
        "payback_mes", "Payback", "mes desde inicio",
        "Mes en que el flujo acumulado del proyecto se vuelve positivo.",
        MES, ("apalancamiento", "payback_mes"), "rentabilidad"),

    # --- Veredicto de Valor (EVA del proyecto): ¿genera o destruye valor sobre el WACC? ---
    "crea_valor": Metric(
        "crea_valor", "Veredicto de valor", "TIR proyecto vs WACC",
        "¿El proyecto genera valor sobre el costo del capital? (TIR proyecto > WACC). "
        "Greenfield/TIR degenerada → sin veredicto.",
        BOOL, ("apalancamiento", "crea_valor"), "valor"),
    "valor_creado": Metric(
        "valor_creado", "Valor creado", "VPN @WACC",
        "VPN del flujo del proyecto descontado al WACC (valor sobre el costo del capital). "
        "Espejo del VPN@TIO pero al WACC; positivo cuando la TIR proyecto supera al WACC.",
        COP_MILES, ("apalancamiento", "valor_creado"), "valor"),
    "spread_valor": Metric(
        "spread_valor", "Spread de desarrollo", "TIR proyecto − WACC",
        "Diferencia entre la TIR del proyecto y el WACC, en puntos.",
        PCT, ("apalancamiento", "spread_valor"), "valor"),

    # --- Caja y financiamiento (crédito constructor / fiducia) ---
    "exposicion_maxima": Metric(
        "exposicion_maxima", "Exposición máxima de caja", "mínimo del acumulado",
        "Necesidad máxima de caja: la posición acumulada más negativa del proyecto.",
        COP_MILES, ("apalancamiento", "max_necesidad_caja"), "caja"),
    "credito_max": Metric(
        "credito_max", "Crédito máx", "pico del saldo de crédito",
        "Saldo máximo alcanzado por el crédito constructor.",
        COP_MILES, ("apalancamiento", "credito_max"), "caja"),
    "valor_financiable": Metric(
        "valor_financiable", "Valor financiable", "base del crédito",
        "Valor sobre el que se calcula la cobertura del crédito constructor.",
        COP_MILES, ("apalancamiento", "valor_financiable"), "caja"),
    "cap_credito": Metric(
        "cap_credito", "Cupo de crédito", "cobertura × financiable",
        "Cupo máximo del crédito constructor.",
        COP_MILES, ("apalancamiento", "cap_credito"), "caja"),
    "intereses_total": Metric(
        "intereses_total", "Intereses del crédito", "total acumulado",
        "Intereses totales pagados por el crédito constructor.",
        COP_MILES, ("apalancamiento", "intereses_total"), "caja"),

    # --- Estado de resultados (P&G) ---
    "ventas": Metric(
        "ventas", "Ventas", "total del proyecto",
        "Ingreso total por ventas de unidades.",
        COP_MILES, ("pyg", "ventas"), "pyg"),
    "costo_directo": Metric(
        "costo_directo", "Costo directo", "total de obra",
        "Costo directo de construcción.",
        COP_MILES, ("pyg", "directos"), "pyg"),
    "util_oper": Metric(
        "util_oper", "Utilidad operativa", "antes de renta",
        "Utilidad operativa del proyecto (ventas − costos − honorarios − lote).",
        COP_MILES, ("pyg", "util_oper"), "pyg"),
    "margen_oper": Metric(
        "margen_oper", "Margen operacional", "sobre ventas",
        "Utilidad operativa dividida por las ventas.",
        PCT, ("pyg", "margen_oper"), "pyg"),
    "incidencia_lote": Metric(
        "incidencia_lote", "Incidencia del lote", "lote / ventas",
        "Costo de adquisición del lote como fracción de las ventas (peso del suelo en el proyecto).",
        PCT, ("pyg", "incidencia_lote"), "pyg"),
    "utilidad_cg": Metric(
        "utilidad_cg", "Utilidad CG", "reparto CG",
        "Parte de la utilidad operativa que corresponde a CG.",
        COP_MILES, ("pyg", "cg"), "pyg"),
    "utilidad_socio": Metric(
        "utilidad_socio", "Utilidad socio", "reparto socio",
        "Parte de la utilidad operativa que corresponde al socio.",
        COP_MILES, ("pyg", "socio"), "pyg"),
    "udi": Metric(
        "udi", "UDI", "utilidad después de renta",
        "Utilidad después del impuesto de renta.",
        COP_MILES, ("pyg", "udi"), "pyg"),
}


def metric(clave: str) -> Metric:
    """Devuelve el descriptor del indicador (lanza KeyError si la clave no existe en el registro)."""
    return REGISTRO[clave]


def flujo_decision(R: dict) -> dict:
    """KPIs de decisión del proyecto: parten del `flujo` (vista simple) pero, si el waterfall
    apalancado corrió, **sus cifras mandan** (crédito/VPN/intereses/TIR equity/ref). Es una SELECCIÓN
    de fuente (no un cálculo nuevo). Regla extraída de app.py para no duplicarla en la UI."""
    fl = dict(R.get("flujo") or {})
    ap = R.get("apalancamiento") or {}
    if ap:
        fl.update({
            "credito_max": ap.get("credito_max", fl.get("credito_max")),
            "vpn_proyecto": ap.get("vpn_proyecto", fl.get("vpn_proyecto")),
            "intereses_total": ap.get("intereses_total", fl.get("intereses_total")),
            "tir_equity": ap.get("tir_equity"),
            "tir_apalancada_ref": ap.get("tir_apalancada_ref", fl.get("tir_apalancada_ref")),
            "credito_prom": ap.get("credito_prom"),
        })
    return fl


def valor(R: dict, clave: str):
    """Busca el valor YA CALCULADO de un indicador en el resultado de `calcular()`. NO calcula nada.
    Devuelve None si la sección o la clave no están (p.ej. proyecto sin apalancamiento)."""
    m = REGISTRO[clave]
    sec, k = m.ruta
    seccion = R.get(sec)
    return seccion.get(k) if isinstance(seccion, dict) else None


def etiqueta(clave: str) -> str:
    """Etiqueta completa para la UI: nombre + BASE (nunca el nombre a secas).
    Ej.: 'TIR proyecto · proyecto (desapalancada)', 'VPN · @TIO'."""
    m = REGISTRO[clave]
    return f"{m.nombre} · {m.etiqueta_base}"


def listar(grupo: str | None = None) -> list[Metric]:
    """Indicadores del registro, opcionalmente filtrados por grupo (rentabilidad/caja/pyg)."""
    ms = list(REGISTRO.values())
    return [m for m in ms if m.grupo == grupo] if grupo else ms
