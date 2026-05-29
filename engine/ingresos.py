# -*- coding: utf-8 -*-
"""
Kernel de Ingresos (Fase 2 — paridad APEX: k.Ventas + k.Separ + k.CuotaInicial).
Recaudo mensual de una etapa a partir del ritmo de ventas:
  - Separación: sep_und por unidad, DIFERIDA en 'diferido_sep' meses desde la venta.
  - Cuota inicial: (pct_ci*precio - sep_und) por unidad, lineal de la venta a la escrituración.
  - Subrogación (crédito hipotecario): saldo (1-pct_ci)*precio por unidad, a la escrituración.
Series en línea de tiempo local (mes 0 = inicio de ventas de la etapa, IV).
"""
from . import portafolio


def recaudo_etapa(unidades, vmes, frec, precio_und, sep_und, pct_ci,
                  diferido_sep, mes_escrituracion, horizonte=180):
    """Devuelve dict con series mensuales (relativas a IV) de separación, cuota inicial,
    subrogación, total y ventas (unidades). 'mes_escrituracion' = mes (desde IV) de escrituración."""
    ventas = portafolio.generar_ritmo(unidades, vmes, frec, horizonte)
    sep = [0.0] * horizonte; ci = [0.0] * horizonte; sub = [0.0] * horizonte
    diferido_sep = max(1, int(diferido_sep))
    ci_por_und = max(0.0, pct_ci * precio_und - sep_und)   # cuota inicial neta de separación
    sub_por_und = (1 - pct_ci) * precio_und
    esc = max(1, int(mes_escrituracion))
    for m in range(horizonte):
        u = ventas[m]
        if u <= 0:
            continue
        # separación diferida en 'diferido_sep' meses desde la venta
        for k in range(diferido_sep):
            if m + k < horizonte:
                sep[m + k] += u * sep_und / diferido_sep
        # cuota inicial lineal desde la venta hasta la escrituración (si vende después, 1 mes)
        fin = max(m + 1, esc)
        n = fin - m
        for t in range(m, min(fin, horizonte)):
            ci[t] += u * ci_por_und / n
        # subrogación a la escrituración
        if esc < horizonte:
            sub[esc] += u * sub_por_und
    total = [sep[i] + ci[i] + sub[i] for i in range(horizonte)]
    return {"ventas": ventas, "separacion": sep, "cuota_inicial": ci,
            "subrogacion": sub, "total": total,
            "contrato_total": unidades * precio_und}


def recaudo_portafolio(etapas, hitos, horizonte=180):
    """Consolida el recaudo del portafolio en una línea de tiempo GLOBAL (mes 0 = IV de la
    etapa raíz). etapas: lista con cod, unidades, vmes, frec, precio_und, sep_und, pct_ci,
    diferido_sep, escrituracion_offset. hitos: salida de portafolio.calcular_portafolio
    (para ubicar el IV de cada etapa en la línea global)."""
    base = min(hitos[c]["IV"] for c in hitos)
    def offset(d):
        return (d.year - base.year) * 12 + (d.month - base.month)
    sep = [0.0]*horizonte; ci=[0.0]*horizonte; sub=[0.0]*horizonte
    por_etapa = {}
    for e in etapas:
        cod = e["cod"]
        if cod not in hitos:
            continue
        off = offset(hitos[cod]["IV"])
        r = recaudo_etapa(e["unidades"], e["vmes"], e["frec"], e["precio_und"],
                          e["sep_und"], e["pct_ci"], e["diferido_sep"],
                          e["escrituracion_offset"], horizonte)
        por_etapa[cod] = {"offset": off, **r}
        for m in range(horizonte):
            g = off + m
            if 0 <= g < horizonte:
                sep[g]+=r["separacion"][m]; ci[g]+=r["cuota_inicial"][m]; sub[g]+=r["subrogacion"][m]
    total=[sep[i]+ci[i]+sub[i] for i in range(horizonte)]
    return {"separacion":sep,"cuota_inicial":ci,"subrogacion":sub,"total":total,"por_etapa":por_etapa}
