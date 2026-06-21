# -*- coding: utf-8 -*-
"""
Apalancamiento (Fase 4: hoja Apalancamiento + k.FC del modelo financiero CG).
Ensambla el flujo operativo consolidado del portafolio (recaudo F2 − costos F3 por etapa,
costos directos distribuidos por curva Gauss sobre la ventana de obra IC..FC) y le aplica
el waterfall de financiación:
  - Crédito Constructor: revolvente, tope = monto_cc% × Valor Financiable (CD+CI+preop);
    cubre déficits de caja, se amortiza con los excedentes (subrogaciones), interés sobre saldo.
  - Aportes de capital (equity): cubren el lote (t0) y el déficit residual no cubierto por el CC.
Salidas: flujo operativo/equity mensual, saldo de crédito, intereses, crédito máx,
indicadores (TIR proyecto, TIR equity, VPN, máxima necesidad de caja).
"""
from . import curvas
from . import finanzas
from . import config
from . import vehiculos
from . import tributario
from . import valor
from . import reales
from .flujo import aplicar_gastos_fijos, acumular


def _offset(d, base):
    return (d.year - base.year) * 12 + (d.month - base.month)


# TIR/VPN: una sola implementación, en finanzas.py. Estos son alias finos que preservan la API
# interna de este módulo (firmas idénticas a las funciones que vivían aquí).
def _tir(flujos, anual=True):
    return finanzas.irr_anual(flujos) if anual else finanzas.irr_periodo(flujos)


_tir_periodo = finanzas.irr_biseccion   # bisección robusta (serie anual auditada de fiducia)
_vpn = finanzas.vpn


def flujo_apalancado(par, pg, hitos, recaudo, horizonte=config.HORIZONTE_RECAUDO):
    if not hitos or not recaudo or not recaudo.get("total"):
        return {}
    fin = par.get("financiero", {})
    base = min(hitos[c]["IV"] for c in hitos)
    N = horizonte
    V = pg["ventas"] or 1

    # ---- ingresos consolidados (F2) ----
    rt = recaudo["total"]
    ingresos_m = [rt[i] if i < len(rt) else 0.0 for i in range(N)]
    # otros ingresos (comercio + parqueaderos + recuperaciones + devolución IVA): están en el P&G
    # (total_ingresos − ventas) pero no en el recaudo de unidades. Se reparten proporcionales al
    # recaudo (entran a caja a medida que el proyecto vende/entrega).
    otros = pg.get("total_ingresos", pg["ventas"]) - pg["ventas"]
    tot_rec = sum(ingresos_m) or 1.0
    if otros:
        ingresos_m = [v + otros * (v / tot_rec) for v in ingresos_m]

    # ---- costos por etapa (F3) ----
    #   directos:   curva Gauss sobre la ventana de OBRA (IC..FC)
    #   indirectos: lineal sobre la ventana de OBRA (IC..FC) — financiables por el crédito (admin
    #               de obra); en el modelo CG el crédito constructor cubre obra, no la preventa.
    #   honorarios: lineal sobre la obra (IC..FC) — los paga el equity, no el crédito.
    # obra_fin_m = base financiable por el crédito constructor (directos + indirectos de obra).
    costos_m = [0.0] * N; directos_m = [0.0] * N; obra_fin_m = [0.0] * N
    ind_obra = pg.get("indirectos_otros", pg["indirectos"])   # indirecto tras tallar los gastos fijos
    for e in par.get("etapas", []):
        cod = e.get("cod")
        if cod not in hitos:
            continue
        share = e.get("ventas_miles", 0) / (V or 1)
        ic = max(0, _offset(hitos[cod]["IC"], base))
        fc = max(ic, _offset(hitos[cod]["FC"], base))
        dur = max(1, fc - ic + 1)
        serie = curvas.distribuir(pg["directos"] * share, dur, "Gauss")   # costo directo
        for k, val in enumerate(serie):
            if ic + k < N:
                costos_m[ic + k] += val; directos_m[ic + k] += val; obra_fin_m[ic + k] += val
        for m in range(ic, min(fc + 1, N)):                                # indirectos (resto) sobre obra
            v = ind_obra * share / dur
            costos_m[m] += v; obra_fin_m[m] += v
        for m in range(ic, min(fc + 1, N)):                                # honorarios sobre obra
            costos_m[m] += pg["honorarios"] * share / dur
    # gastos fijos de estructura: mensuales sobre su ventana (helper compartido con flujo_caja)
    aplicar_gastos_fijos(costos_m, par, N)

    # ---- flujo del proyecto (no apalancado): operativo de obra − lote en t0 ----
    operativo = [ingresos_m[m] - costos_m[m] for m in range(N)]
    operativo[0] -= pg["costo_lote"]

    # ---- waterfall: crédito constructor (cobertura del costo de obra, amortizado con subrogación) ----
    # El crédito constructor financia COBERTURA (~80%) del costo directo a medida que se ejecuta la
    # obra, y se amortiza con las subrogaciones (créditos hipotecarios a la escrituración). El resto
    # (lote, indirectos, 20% de obra) lo cubren los aportes (equity, sin interés de CC).
    # CG mechanic (sheet "CALCULO COSTOS FINANCIEROS"): the construction loan DISBURSES the monthly
    # construction cost (directos + indirectos, i.e. costos_m which excludes the lote) up to a CUPO =
    # cobertura% x (directos + indirectos). It is AMORTIZED by the subrogations (mortgage payoffs at
    # escrituración). Interest accrues on the outstanding balance. Peak balance = "Vr. Max Credito
    # Constructor"; average of the positive balance = "Promedio". Equity covers the lote and any
    # construction cost above the cupo.
    cobertura = fin.get("cobertura_cc", fin.get("monto_cc_pct", config.COBERTURA_CC))
    valor_financiable = pg["directos"] + ind_obra             # gastos de estructura no son financiables
    cupo = cobertura * valor_financiable                       # construction-loan ceiling
    subr = recaudo.get("subrogacion", [])
    sub_m = [subr[i] if i < len(subr) else 0.0 for i in range(N)]
    tasa_cc = (1 + fin.get("tasa_credito_ea", config.TASA_CREDITO_EA)) ** (1 / 12) - 1

    # Reintegros del desarrollador (honorarios + util_lote): se restan como COSTO en 'operativo' pero
    # RETORNAN al desarrollador/socio → se reincorporan proporcional al recaudo. Se calcula ANTES del
    # bucle porque el flujo de EQUITY (apalancado) TAMBIÉN los recibe: equity = retorno + crédito neto.
    reintegro_extra = pg["honorarios"] + pg["util_lote"]
    tot_rec = sum(ingresos_m) or 1.0
    retorno = [operativo[m] + reintegro_extra * (ingresos_m[m] / tot_rec) for m in range(N)]

    saldo = 0.0; intereses = 0.0; desemb_acum = 0.0
    saldo_serie = [0.0] * N; flujo_equity = [0.0] * N
    for m in range(N):
        interes = saldo * tasa_cc; intereses += interes
        # disburse COBERTURA% of the monthly construction cost (spread over the obra), capped at cupo
        desembolso = min(cobertura * obra_fin_m[m], max(0.0, cupo - desemb_acum))
        desemb_acum += desembolso
        saldo += desembolso
        amort = min(sub_m[m], saldo); saldo -= amort           # subrogaciones amortizan el CC
        saldo_serie[m] = saldo
        # flujo al equity = RETORNO al socio (operativo + reintegros) + crédito neto − intereses.
        # FIX (auditoría): antes partía de 'operativo' (sin reincorporar honorarios+util_lote) → la TIR
        # socio MENSUAL salía negativa (−3,3%); ahora parte de 'retorno' (con los reintegros), como debe.
        flujo_equity[m] = retorno[m] + desembolso - amort - interes
    cap = cupo

    acum = acumular(operativo)

    # ---- flujo de RETORNO AL DESARROLLADOR (criterio CG para la TIR/VPN del PROYECTO, desapalancado) ----
    # `retorno` ya se calculó arriba (lo comparte el flujo de equity apalancado). CG evalúa el PROYECTO
    # sobre los REINTEGROS = honorarios + utilidad operativa + utilidad lote, descontados a la TIO (15%
    # EA), NO sobre la utilidad operativa sola ni a WACC. El crédito NO entra en `retorno` (la TIR/VPN
    # del PROYECTO es SIN apalancamiento; el socio apalancado va en flujo_equity). Así
    # sum(retorno) = total_ingresos − directos − indirectos − lote_bruto = reintegros del proyecto.

    # tasa de descuento = TIO (tasa de oportunidad). Por defecto 15% EA (criterio CG); si el proyecto
    # define financiero.tio se usa esa. (El WACC Damodaran queda disponible pero no es el descuento CG.)
    wacc = finanzas.calcular_wacc(fin["wacc"]) if fin.get("wacc") else 0.0
    tio = fin.get("tio", config.TIO)
    tio_m = (1 + tio) ** (1 / 12) - 1
    wacc_m = tio_m                              # descuento usado para VPN del retorno

    # ---- ensamblaje: vista anual + payback ----
    anio0 = base.year
    anual = {}
    for m in range(N):
        yr = anio0 + (base.month - 1 + m) // 12
        anual[yr] = anual.get(yr, 0.0) + operativo[m]
    anual = {k: v for k, v in anual.items() if abs(v) > 1}
    payback = None                              # mes en que el acumulado vuelve a ser positivo
    toco_fondo = False
    for i, v in enumerate(acum):
        if v < -1:
            toco_fondo = True
        elif toco_fondo and v >= 0:
            payback = i; break

    pos = [x for x in saldo_serie if x > 0]
    # Serie + periodicidad usadas por el VPN@TIO de decisión (la sobreescriben las ramas fiducia/vehículo).
    # Se reusa para el `valor_creado` (VPN@WACC) — espejo exacto del VPN@TIO pero descontado al WACC.
    _flujo_vpn, _vpn_anual = retorno, False
    out = {
        "ingresos": ingresos_m, "costos": costos_m, "operativo": operativo,
        "acumulado": acum, "saldo_credito": saldo_serie, "flujo_equity": flujo_equity,
        "credito_max": max(saldo_serie), "credito_prom": (sum(pos) / len(pos)) if pos else 0.0,
        "intereses_total": intereses,
        "aportes_total": sum(-x for x in flujo_equity if x < 0), "max_necesidad_caja": min(acum),
        "valor_financiable": valor_financiable, "cap_credito": cap,
        "retorno": retorno,
        "tir_proyecto": _tir(retorno), "tir_equity": _tir(flujo_equity),
        "tir_apalancada_ref": fin.get("tir_apalancada_ref"),
        "vpn_proyecto": sum(f / (1 + tio_m) ** t for t, f in enumerate(retorno)),
        "tio": tio, "wacc": wacc, "anual": anual, "anio0": anio0, "payback_mes": payback,
        "fiducia_real": False,
    }

    # ---- FCL auditado de fiducia (autoritativo) ----
    # Si el proyecto trae el Flujo de Caja Libre anual real de la fiducia (hoja FC LOTE CG -V2K:
    # Aportes → Devoluciones → Retornos → FCL), la TIR/VPN del PROYECTO y del SOCIO se calculan
    # sobre esa serie anual a la TIO. Es la cifra auditada de CG (no la aproximación mensual).
    # Vehículo: SOLO la fiducia usa el FCL auditado; los demás recalculan + overlay fiscal (M3 Fase 2).
    _veh = vehiculos.obtener(par.get("vehiculo"))
    _es_fiducia = (_veh.waterfall == "fiducia_override")

    fd = par.get("fiducia") or {}
    fcl_p = fd.get("fcl_proyecto")
    if fcl_p and _es_fiducia:
        tio_f = fd.get("tio", tio)
        out["fiducia_real"] = True
        out["fcl_proyecto_anual"] = fcl_p
        out["anio0_fiducia"] = fd.get("anio0")
        out["tir_proyecto"] = _tir_periodo(fcl_p)
        out["vpn_proyecto"] = _vpn(fcl_p, tio_f)
        _flujo_vpn, _vpn_anual = fcl_p, True      # FCL auditado: serie ANUAL → VPN@WACC anual
        fcl_s = fd.get("fcl_socio_cg")
        if fcl_s:
            out["fcl_socio_anual"] = fcl_s
            out["tir_equity"] = _tir_periodo(fcl_s)
            out["vpn_socio"] = _vpn(fcl_s, tio_f)
    elif not _es_fiducia:
        # NO-fiducia: ignora el override (congela hitos), aplica la carga tributaria del vehículo al
        # flujo (renta + GMF + dividendos si es opaco) y recalcula TIR/VPN AFTER-TAX. [VALIDAR tasas].
        _ov = tributario.overlay_after_tax(retorno, flujo_equity, vehiculo=_veh.clave,
                                           renta_total=pg.get("renta", 0.0))
        out["vehiculo"] = _veh.clave
        out["vehiculo_nombre"] = _veh.nombre
        out["after_tax"] = True
        out["transparente"] = _veh.transparente
        out["carga_tributaria"] = _ov["carga_total"]
        out["carga_detalle"] = {"renta": _ov["renta"], "gmf": _ov["gmf"], "dividendos": _ov["dividendos"]}
        out["tir_proyecto"] = _tir(_ov["retorno_at"])
        out["vpn_proyecto"] = sum(f / (1 + tio_m) ** t for t, f in enumerate(_ov["retorno_at"]))
        _flujo_vpn, _vpn_anual = _ov["retorno_at"], False   # after-tax: serie MENSUAL → WACC mensual-equiv
        out["tir_equity"] = _tir(_ov["flujo_equity_at"])
        out["nota_vehiculo"] = _ov["nota_timing"]

    # ---- Capa after-tax de DECISIÓN (C1, Camacol M4/M6) — ADITIVA: no toca las cifras pre-impuesto ----
    # Sobre la serie mensual del modelo aplica renta + GMF (+ dividendos si el vehículo es opaco) y, en
    # VIS, suma la devolución del IVA. NO modela retención (anticipo de renta → doble conteo) ni ICA.
    # Preliminar [VALIDAR asesor]. La oficial pre-impuesto (auditada de fiducia) se conserva intacta.
    _es_vis = str((par.get("meta") or {}).get("tipo", "")).strip().upper() in ("VIS", "VIP")
    _atd = tributario.decision_after_tax(retorno, flujo_equity, vehiculo=_veh.clave,
                                         renta_total=pg.get("renta", 0.0),
                                         es_vis=_es_vis, ventas=pg.get("ventas", 0.0))
    out["tir_proyecto_at"] = _tir(_atd["retorno_at"])
    out["tir_equity_at"] = _tir(_atd["flujo_equity_at"])
    out["vpn_at"] = sum(f / (1 + tio_m) ** t for t, f in enumerate(_atd["retorno_at"]))
    # Base mensual PRE-impuesto (para que el delta tributario sea apples-to-apples; la oficial es anual).
    out["tir_proyecto_pre_mensual"] = _tir(retorno)
    out["impuesto_renta_at"] = _atd["renta"]
    out["gmf_at"] = _atd["gmf"]
    out["iva_vis_devolucion"] = _atd["iva_vis"]
    out["carga_tributaria_neta_at"] = _atd["carga_neta"]
    out["after_tax_metodo"] = _atd["metodo"]

    # ---- Veredicto de Valor (EVA del proyecto) — ADITIVO: no mueve TIR/VPN@TIO/flujo ----
    # crea_valor = TIR proyecto > WACC (ambas anuales); spread_valor = TIR − WACC; valor_creado =
    # VPN del MISMO flujo de decisión pero descontado al WACC (no a la TIO). Greenfield → None.
    out["valor_creado"] = valor.vpn_al_wacc(_flujo_vpn, wacc, anual=_vpn_anual) if wacc else None
    out["crea_valor"], out["spread_valor"] = valor.veredicto_binario(out["tir_proyecto"], wacc)

    # ---- Precios CONSTANTES (reales) — ADITIVO (curso Camacol §M6): tasas deflactadas por inflación ----
    # Inflación de largo plazo del build-up del WACC (inf_col, en %). Sin ella → reales None (no se inventa).
    _wp = fin.get("wacc") or {}
    _infl = (_wp["inf_col"] / 100.0) if _wp.get("inf_col") is not None else None
    out.update(reales.tasas_reales(out["tir_proyecto"], out["tir_equity"], tio, wacc, _infl))
    return out
