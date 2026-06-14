# -*- coding: utf-8 -*-
"""M3 · Motor fiscal por vehículo (spec_pyg_dinamico.md). Extrae la línea de RENTA antes incrustada
en `modelo.pyg` y la generaliza por VEHÍCULO + VIS/No-VIS.

GARANTÍA (no-op): con `vehiculo='fiducia'` reproduce EXACTAMENTE la lógica anterior de `pyg`
(M2) → el snapshot dorado NO se mueve. Solo cambia algo si se elige un vehículo distinto.

ADVERTENCIA: reglas marcadas `[VALIDAR]` (ver `vehiculos.py`). Apoyo a la decisión, NO asesoría
tributaria. Fase 1 = efecto en RENTA (P&G after-tax). El efecto en el WATERFALL es Fase 2.
"""
from __future__ import annotations

from . import vehiculos


def calcular_renta(*, vehiculo: str | None, es_vis: bool, honorarios: float,
                   reint_sin_lote: float, tasa_renta_proyecto: float,
                   vis_exime_honorarios: bool = False) -> dict:
    """Renta e UDI (utilidad después de impuestos) según el vehículo.

    Bases (en miles COP, vienen de `pyg`):
      honorarios       — servicios (gravados aun en VIS por defecto).
      reint_sin_lote   — reintegro sin lote = honorarios + utilidad operativa (base No-VIS).
      tasa_renta_proyecto — fin['renta'] del proyecto (35% por defecto).

    Devuelve dict con: renta, udi, base_gravable, tasa, etiqueta, exencion_vis_aplicada,
    transparente, vehiculo, nombre_vehiculo, nota, fuente_normativa.
    """
    veh = vehiculos.obtener(vehiculo)
    tasa = veh.tasa_renta if veh.tasa_renta is not None else tasa_renta_proyecto

    exencion = bool(es_vis and veh.habilita_exencion_vis)
    if exencion:
        # VIS en una estructura que habilita la exención (fiducia): utilidad exenta; honorarios
        # gravados salvo que el asesor confirme exención total.
        base = 0.0 if vis_exime_honorarios else honorarios
        etiqueta = ("VIS exenta (total)" if vis_exime_honorarios
                    else "VIS exenta (utilidad; honorarios gravados)")
    else:
        base = reint_sin_lote
        if es_vis:
            etiqueta = f"VIS SIN exención · {veh.nombre} ({tasa * 100:.0f}%)"
        else:
            etiqueta = f"No-VIS · {veh.nombre} ({tasa * 100:.0f}%)"

    renta = tasa * base
    udi = reint_sin_lote - renta
    return {
        "renta": renta,
        "udi": udi,
        "base_gravable": base,
        "tasa": tasa,
        "etiqueta": etiqueta,
        "exencion_vis_aplicada": exencion,
        "transparente": veh.transparente,
        "vehiculo": veh.clave,
        "nombre_vehiculo": veh.nombre,
        "nota": veh.nota,
        "fuente_normativa": veh.fuente_normativa,
    }


def _es_vis_de(par: dict) -> bool:
    return str((par.get("meta") or {}).get("tipo", "")).strip().upper() in ("VIS", "VIP")


def comparar(par: dict, claves: list[str] | None = None) -> dict:
    """Comparador de vehículos (M3 Fase 1+2). Corre el motor UNA vez y, sobre las MISMAS series
    mensuales pre-impuesto, aplica a cada vehículo (a) su renta (Fase 1) y (b) el overlay fiscal del
    waterfall (Fase 2: renta+GMF+dividendos) -> TIR socio AFTER-TAX en base CONSISTENTE (mensual) para
    todos, incluida la fiducia. Asi el delta refleja economia del vehiculo, no el metodo.

    La TIR auditada de la fiducia (serie anual real, p.ej. 37,60%) se reporta APARTE como cifra oficial
    de la estructura real; NO se usa para los deltas. Todas las tasas fiscales son [VALIDAR].
    Devuelve dict {base_comparacion, oficial_fiducia, nota, vehiculos}.
    """
    from . import config, finanzas, modelo

    R = modelo.calcular(par)
    ap = R.get("apalancamiento", {})
    pg = R.get("pyg", {})
    retorno = ap.get("retorno", [])
    flujo_equity = ap.get("flujo_equity", [])
    honorarios = pg.get("honorarios", 0.0)
    reint_sin_lote = honorarios + pg.get("util_oper", 0.0)
    es_vis = _es_vis_de(par)
    fin = par.get("financiero", {})
    tasa_proy = fin.get("renta", config.RENTA)
    exime = fin.get("vis_exime_honorarios", False)
    tio = fin.get("tio", config.TIO)
    tio_m = (1 + tio) ** (1 / 12) - 1

    def _fila(clave):
        t = calcular_renta(vehiculo=clave, es_vis=es_vis, honorarios=honorarios,
                           reint_sin_lote=reint_sin_lote, tasa_renta_proyecto=tasa_proy,
                           vis_exime_honorarios=exime)
        ov = overlay_after_tax(retorno, flujo_equity, vehiculo=clave, renta_total=t["renta"])
        return {
            **t,
            "es_vis": es_vis,
            "tir_proyecto_at": finanzas.irr_anual(ov["retorno_at"]),
            "tir_socio_at": finanzas.irr_anual(ov["flujo_equity_at"]),
            "vpn_proyecto_at": sum(f / (1 + tio_m) ** k for k, f in enumerate(ov["retorno_at"])),
            "carga_tributaria": ov["carga_total"],
            "carga_detalle": {"renta": ov["renta"], "gmf": ov["gmf"], "dividendos": ov["dividendos"]},
        }

    claves = claves or vehiculos.claves()
    ref = _fila(vehiculos.FIDUCIA)
    filas = []
    for clave in claves:
        f = _fila(clave)
        f["delta_udi_vs_fiducia"] = f["udi"] - ref["udi"]
        f["delta_tir_socio_vs_fiducia"] = f["tir_socio_at"] - ref["tir_socio_at"]
        f["delta_carga_vs_fiducia"] = f["carga_tributaria"] - ref["carga_tributaria"]
        f["es_referencia"] = clave == vehiculos.FIDUCIA
        filas.append(f)

    return {
        "base_comparacion": "mensual after-tax (consistente entre vehiculos)",
        "oficial_fiducia": {
            "tir_proyecto_auditada": ap.get("tir_proyecto"),
            "tir_socio_auditada": ap.get("tir_equity"),
            "fuente": "FCL fiducia auditado" if ap.get("fiducia_real") else "modelo mensual",
        },
        "nota": "[VALIDAR] GMF/dividendos son placeholders; la TIR de comparacion es mensual "
                "(mas conservadora que la anual auditada de la fiducia, que se muestra como oficial).",
        "vehiculos": filas,
    }


# ============================================================================
# M3 Fase 2 — overlay tributario del WATERFALL (efecto del vehículo en los flujos/TIR).
# Solo aplica a vehículos NO-fiducia: la fiducia conserva su FCL auditado (cifra dorada).
# TODAS las tasas son PLACEHOLDERS [VALIDAR con asesor fiscal] — el comparador es direccional.
# ============================================================================

GMF_TASA = 0.004          # 4x1000 sobre movimientos de caja [VALIDAR Art. 871 ET; exenciones de fiducia]
DIVIDENDOS_TASA = 0.10    # impuesto a dividendos al socio en vehículos OPACOS (SAS/SPV) [VALIDAR Ley 2277/2022, tarifa marginal]


def overlay_after_tax(retorno: list, flujo_equity: list, *, vehiculo: str | None,
                      renta_total: float) -> dict:
    """Aplica la carga tributaria del VEHÍCULO a las series mensuales pre-impuesto y devuelve las
    series after-tax + el desglose. Modelo DIRECCIONAL [VALIDAR]:
      1) RENTA  — outflow prorrateado a los retornos positivos (aprox. del impuesto sobre la utilidad).
      2) GMF    — 4x1000 sobre el movimiento bruto de caja, prorrateado a los flujos.
      3) DIVIDENDOS — solo vehículos OPACOS (no transparentes, p.ej. SAS/SPV): segunda imposición al
                      distribuir al socio, sobre las salidas positivas del equity.
    Supuestos de TIMING simplificados (impuesto contemporáneo al flujo) → cifra direccional, no fiscal.
    """
    veh = vehiculos.obtener(vehiculo)
    n = len(retorno)
    pos_ret = sum(x for x in retorno if x > 0) or 1.0
    bruto = sum(abs(x) for x in retorno) or 1.0

    # 1) renta prorrateada a los retornos positivos; 2) GMF prorrateado al movimiento bruto
    gmf_total = GMF_TASA * bruto
    ret_at = []
    for x in retorno:
        renta_x = renta_total * (x / pos_ret) if x > 0 else 0.0
        gmf_x = gmf_total * (abs(x) / bruto)
        ret_at.append(x - renta_x - gmf_x)

    # 3) dividendos: solo si el vehículo NO es transparente (doble imposición al distribuir)
    div_total = 0.0
    eq_at = list(flujo_equity)
    if not veh.transparente:
        eq_at = []
        for x in flujo_equity:
            div_x = DIVIDENDOS_TASA * x if x > 0 else 0.0
            div_total += div_x
            eq_at.append(x - div_x)

    return {
        "retorno_at": ret_at,
        "flujo_equity_at": eq_at,
        "vehiculo": veh.clave,
        "transparente": veh.transparente,
        "renta": renta_total,
        "gmf": gmf_total,
        "dividendos": div_total,
        "carga_total": renta_total + gmf_total + div_total,
        "nota_timing": "[VALIDAR] impuesto modelado contemporáneo al flujo (sin diferimiento a la "
                       "declaración del año siguiente); tasas GMF/dividendos son placeholders.",
    }
