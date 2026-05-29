# -*- coding: utf-8 -*-
"""
Apalancamiento (Fase 4 — paridad APEX: hoja Apalancamiento + k.FC).
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

    # ---- costos por etapa (F3): directos Gauss sobre IC..FC; indirectos/honorarios; lote ----
    costos_m = [0.0] * N
    for e in par.get("etapas", []):
        cod = e.get("cod")
        if cod not in hitos:
            continue
        share = e.get("ventas_miles", 0) / V
        ic = max(0, _offset(hitos[cod]["IC"], base))
        fc = max(ic, _offset(hitos[cod]["FC"], base))
        iv = max(0, _offset(hitos[cod]["IV"], base))
        dur = max(1, fc - ic + 1)
        serie = curvas.distribuir(pg["directos"] * share, dur, "Gauss")   # costo directo
        for k, val in enumerate(serie):
            if ic + k < N:
                costos_m[ic + k] += val
        per = max(1, fc - iv + 1)                                          # indirectos lineal
        for m in range(iv, min(fc + 1, N)):
            costos_m[m] += pg["indirectos"] * share / per
        for m in range(ic, min(fc + 1, N)):                                # honorarios sobre obra
            costos_m[m] += pg["honorarios"] * share / dur

    # ---- flujo del proyecto (no apalancado): operativo de obra − lote en t0 ----
    operativo = [ingresos_m[m] - costos_m[m] for m in range(N)]
    operativo[0] -= pg["costo_lote"]

    # ---- waterfall: crédito constructor + aportes ----
    valor_financiable = pg["directos"] + pg["indirectos"]
    cap = fin.get("monto_cc_pct", 0.80) * valor_financiable
    tasa_cc = (1 + fin.get("tasa_credito_ea", 0.155)) ** (1 / 12) - 1
    saldo = 0.0; intereses = 0.0
    saldo_serie = [0.0] * N; flujo_equity = [0.0] * N; aportes = [0.0] * N
    for m in range(N):
        interes = saldo * tasa_cc; intereses += interes
        neto = operativo[m] - interes
        if neto < 0:
            deficit = -neto
            usar = min(deficit, max(0.0, cap - saldo)); saldo += usar
            ap = deficit - usar; aportes[m] = ap; flujo_equity[m] = -ap
        else:
            repago = min(neto, saldo); saldo -= repago
            flujo_equity[m] = neto - repago
        saldo_serie[m] = saldo

    acum = []; s = 0.0
    for x in operativo:
        s += x; acum.append(s)
    from .modelo import calcular_wacc          # import diferido: evita ciclo de importación
    wacc = calcular_wacc(fin["wacc"]) if fin.get("wacc") else 0.0
    wacc_m = (1 + wacc) ** (1 / 12) - 1 if wacc else 0.0

    return {
        "ingresos": ingresos_m, "costos": costos_m, "operativo": operativo,
        "acumulado": acum, "saldo_credito": saldo_serie, "flujo_equity": flujo_equity,
        "credito_max": max(saldo_serie), "intereses_total": intereses,
        "aportes_total": sum(aportes), "max_necesidad_caja": min(acum),
        "valor_financiable": valor_financiable, "cap_credito": cap,
        "tir_proyecto": _tir(operativo), "tir_equity": _tir(flujo_equity),
        "vpn_proyecto": sum(f / (1 + wacc_m) ** t for t, f in enumerate(operativo)) if wacc else None,
        "wacc": wacc,
    }
