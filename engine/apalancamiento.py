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

try:
    from scipy import optimize
    _SCIPY = True
except Exception:
    _SCIPY = False


def _offset(d, base):
    return (d.year - base.year) * 12 + (d.month - base.month)


def _tir(flujos, anual=True):
    if not _SCIPY:
        return None
    def vpn(r): return sum(f / (1 + r) ** t for t, f in enumerate(flujos))
    r = -0.6; prev = vpn(r)
    while r < 5.0:
        r2 = r + 0.005; cur = vpn(r2)
        if prev * cur < 0:
            try:
                m = optimize.brentq(vpn, r, r2, xtol=1e-10)
                return ((1 + m) ** 12 - 1) if anual else m
            except Exception:
                pass
        prev = cur; r = r2
    return None

def _tir_periodo(flujos):
    """TIR por periodo (la serie ya viene en su periodicidad, p.ej. anual). Bisección robusta."""
    def vpn(r): return sum(f / (1 + r) ** t for t, f in enumerate(flujos))
    lo, hi = -0.95, 5.0
    if vpn(lo) * vpn(hi) > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        if vpn(lo) * vpn(mid) <= 0: hi = mid
        else: lo = mid
    return (lo + hi) / 2

def _vpn(flujos, r):
    return sum(f / (1 + r) ** t for t, f in enumerate(flujos))


def flujo_apalancado(par, pg, hitos, recaudo, horizonte=180):
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
        share = e.get("ventas_miles", 0) / V
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
    # gastos fijos de estructura: mensuales sobre su ventana (los financia el equity, no el crédito)
    for g in par.get("gastos_fijos", []):
        vm = g.get("valor_mes_miles", 0) or 0; d = int(g.get("desde", 0) or 0)
        h = g.get("hasta"); h = int(h) if h is not None else d + 1
        for m in range(max(0, d), min(h, N)):
            costos_m[m] += vm

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
    cobertura = fin.get("cobertura_cc", fin.get("monto_cc_pct", 0.80))
    valor_financiable = pg["directos"] + ind_obra             # gastos de estructura no son financiables
    cupo = cobertura * valor_financiable                       # construction-loan ceiling
    subr = recaudo.get("subrogacion", [])
    sub_m = [subr[i] if i < len(subr) else 0.0 for i in range(N)]
    tasa_cc = (1 + fin.get("tasa_credito_ea", 0.155)) ** (1 / 12) - 1
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
        # flujo al equity = operativo + crédito neto recibido − intereses
        flujo_equity[m] = operativo[m] + desembolso - amort - interes
    cap = cupo

    acum = []; s = 0.0
    for x in operativo:
        s += x; acum.append(s)

    # ---- flujo de RETORNO AL DESARROLLADOR (criterio CG para TIR/VPN) ----
    # CG evalúa el proyecto sobre los REINTEGROS = honorarios + utilidad operativa + utilidad lote
    # (PREFACTIBILIDAD "PROYECTO (Reembolsables+Honorarios+Util.Lote+Utilidad)"), descontados a la
    # TIO (15% EA), NO sobre la utilidad operativa sola ni a WACC. Los honorarios y la utilidad del
    # lote se restan en el flujo de obra como costo, pero RETORNAN al desarrollador → se reintegran a
    # la curva de retorno (proporcional al recaudo, que es cuando el proyecto libera caja al socio).
    # honorarios y util_lote se restan como costo en 'operativo' pero RETORNAN al desarrollador →
    # se reincorporan a la curva de retorno (proporcional al recaudo). El crédito NO entra aquí: la
    # TIR/VPN del PROYECTO es sin apalancamiento (el socio apalancado va en flujo_equity). Así
    # sum(retorno) = total_ingresos − directos − indirectos − lote_bruto = reintegros del proyecto.
    reintegro_extra = pg["honorarios"] + pg["util_lote"]
    tot_rec = sum(ingresos_m) or 1.0
    retorno = [operativo[m] + reintegro_extra * (ingresos_m[m] / tot_rec) for m in range(N)]

    # tasa de descuento = TIO (tasa de oportunidad). Por defecto 15% EA (criterio CG); si el proyecto
    # define financiero.tio se usa esa. (El WACC Damodaran queda disponible pero no es el descuento CG.)
    from .modelo import calcular_wacc          # import diferido: evita ciclo de importación
    wacc = calcular_wacc(fin["wacc"]) if fin.get("wacc") else 0.0
    tio = fin.get("tio", 0.15)
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
    fd = par.get("fiducia") or {}
    fcl_p = fd.get("fcl_proyecto")
    if fcl_p:
        tio_f = fd.get("tio", tio)
        out["fiducia_real"] = True
        out["fcl_proyecto_anual"] = fcl_p
        out["anio0_fiducia"] = fd.get("anio0")
        out["tir_proyecto"] = _tir_periodo(fcl_p)
        out["vpn_proyecto"] = _vpn(fcl_p, tio_f)
        fcl_s = fd.get("fcl_socio_cg")
        if fcl_s:
            out["fcl_socio_anual"] = fcl_s
            out["tir_equity"] = _tir_periodo(fcl_s)
            out["vpn_socio"] = _vpn(fcl_s, tio_f)
    return out
