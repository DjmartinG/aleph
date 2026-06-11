# -*- coding: utf-8 -*-
"""
Kernel de Ingresos (Fase 2: k.Ventas + k.Separ + k.CuotaInicial del modelo financiero CG).
Recaudo mensual de una etapa a partir del ritmo de ventas Y el ritmo de entregas:
  - Separación: sep_und por unidad, DIFERIDA en 'diferido_sep' meses desde la venta.
  - Cuota inicial: (pct_ci*precio - sep_und) por unidad, lineal de la venta a SU entrega.
  - Subrogación (crédito hipotecario): saldo (1-pct_ci)*precio por unidad, a SU entrega.
Las entregas se escalonan según el ritmo de entregas (cantidad/frecuencia) a partir del mes
de escrituración; la i-ésima unidad vendida es la i-ésima entregada (FIFO).
Series en línea de tiempo local (mes 0 = inicio de ventas de la etapa, IV).
"""
from . import portafolio


def recaudo_etapa(unidades, vmes, frec, precio_und, sep_und, pct_ci,
                  diferido_sep, mes_escrituracion, emes=None, efrec=1, horizonte=180,
                  adicional_miles=0):
    """Devuelve dict con series mensuales (relativas a IV) de ventas, entregas, separación,
    cuota inicial, subrogación y total. 'mes_escrituracion' = mes (desde IV) en que ARRANCAN
    las entregas. 'emes'/'efrec' = ritmo de entregas (unidades por evento cada 'efrec' meses);
    si emes es None o >= unidades, se entrega todo en el mes de escrituración (modelo previo).
    'adicional_miles' = ingreso de parqueaderos/depósitos (No VIS): se recauda en el perfil de
    CUOTA INICIAL (venta→entrega), SIN subrogación (no se hipotecan aparte)."""
    ventas = portafolio.generar_ritmo(unidades, vmes, frec, horizonte)
    sep = [0.0] * horizonte; ci = [0.0] * horizonte; sub = [0.0] * horizonte
    diferido_sep = max(1, int(diferido_sep))
    ci_por_und = max(0.0, pct_ci * precio_und - sep_und)   # cuota inicial neta de separación
    sub_por_und = (1 - pct_ci) * precio_und
    esc = max(1, int(mes_escrituracion))
    # --- ritmo de entregas, desplazado al mes de escrituración ---
    if not emes or emes <= 0:
        emes = unidades
    efrec = max(1, int(efrec))
    ent_ritmo = portafolio.generar_ritmo(unidades, int(emes), efrec, horizonte)
    entregas = [0.0] * horizonte
    for m in range(horizonte):
        if ent_ritmo[m] and m + esc < horizonte:
            entregas[m + esc] += ent_ritmo[m]
    # --- emparejar venta → entrega en FIFO (la i-ésima vendida es la i-ésima entregada) ---
    sale_m, deliv_m = [], []
    for m, u in enumerate(ventas):
        sale_m.extend([m] * int(round(u)))
    for m, u in enumerate(entregas):
        deliv_m.extend([m] * int(round(u)))
    if len(deliv_m) < len(sale_m):                 # remanente no entregado → último mes con entregas
        last = deliv_m[-1] if deliv_m else min(esc, horizonte - 1)
        deliv_m += [last] * (len(sale_m) - len(deliv_m))
    for i in range(len(sale_m)):
        s = sale_m[i]; d = max(deliv_m[i], s)      # no se entrega antes de vender
        for k in range(diferido_sep):              # separación diferida desde la venta
            if s + k < horizonte:
                sep[s + k] += sep_und / diferido_sep
        fin = max(s + 1, d)                         # cuota inicial lineal venta → entrega
        nper = fin - s
        for t in range(s, min(fin, horizonte)):
            ci[t] += ci_por_und / nper
        if d < horizonte:                          # subrogación a la entrega de esa unidad
            sub[d] += sub_por_und
    # --- adicionales (parqueaderos/depósitos): se recaudan con el perfil de la cuota inicial ---
    if adicional_miles:
        ci_total = sum(ci)
        if ci_total > 0:
            for m in range(horizonte):
                ci[m] += adicional_miles * (ci[m] / ci_total)
        else:                                          # sin perfil de CI: lineal 12m desde la 1ª venta
            first = next((m for m, u in enumerate(ventas) if u), 0)
            for m in range(first, min(first + 12, horizonte)):
                ci[m] += adicional_miles / 12
    total = [sep[i] + ci[i] + sub[i] for i in range(horizonte)]
    return {"ventas": ventas, "entregas": entregas, "separacion": sep, "cuota_inicial": ci,
            "subrogacion": sub, "total": total,
            "contrato_total": unidades * precio_und + adicional_miles}


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
                          e["escrituracion_offset"], e.get("emes"), e.get("efrec", 1), horizonte,
                          adicional_miles=e.get("adicional_miles", 0))
        por_etapa[cod] = {"offset": off, **r}
        for m in range(horizonte):
            g = off + m
            if 0 <= g < horizonte:
                sep[g]+=r["separacion"][m]; ci[g]+=r["cuota_inicial"][m]; sub[g]+=r["subrogacion"][m]
    total=[sep[i]+ci[i]+sub[i] for i in range(horizonte)]
    return {"separacion":sep,"cuota_inicial":ci,"subrogacion":sub,"total":total,"por_etapa":por_etapa}
