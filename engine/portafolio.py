# -*- coding: utf-8 -*-
"""
Motor de Hitos y Portafolio (Fase 1 — paridad APEX, hojas Proyectos + k.hitos + k.Ventas).
Modela un portafolio multi-etapa secuencial: cada etapa abre ventas cuando su etapa
sucesora alcanza el Punto de Equilibrio (+ desfase). Calcula por etapa los hitos
de ventas: IV (Inicio Ventas), PE (Punto de Equilibrio), FV (Fin de Ventas).
IC/FC (construcción) se incorporan al portar k.Directo (fase posterior).

Validado contra APEX 20250701.xlsm (portafolio Torre Eco E1..E5).
"""
from datetime import date
from dateutil.relativedelta import relativedelta


def eomonth(d, n=0):
    """Último día del mes, n meses después de d (equivalente a EOMONTH de Excel)."""
    p = d.replace(day=1) + relativedelta(months=n + 1)
    return p - relativedelta(days=1)


def generar_ritmo(total, por_evento, frecuencia, horizonte):
    """Unidades vendidas por mes según ritmo (cantidad por evento cada 'frecuencia' meses).
    Garantiza que la suma == total (el residuo va al último evento dentro del horizonte)."""
    frecuencia = max(1, int(frecuencia)); por_evento = max(1, int(por_evento))
    serie = [0] * horizonte
    acum = 0
    for m in range(horizonte):
        if acum >= total:
            break
        if m % frecuencia == 0:
            lote = min(por_evento, total - acum)
            serie[m] = lote; acum += lote
    return serie


def hitos_ventas(unidades, vmes, frec, pe_pct, iv: date, horizonte=120):
    """Calcula IV, PE y FV a partir del ritmo de ventas desde la fecha de inicio (iv).
    Devuelve (iv, pe, fv, pe_idx, fv_idx)."""
    serie = generar_ritmo(unidades, vmes, frec, horizonte)
    objetivo = pe_pct * unidades
    acum = 0; pe_idx = None; fv_idx = 0
    for m, v in enumerate(serie):
        acum += v
        if v > 0:
            fv_idx = m
        if pe_idx is None and acum >= objetivo:
            pe_idx = m
    if pe_idx is None:
        pe_idx = fv_idx
    return {
        "IV": eomonth(iv, 0) if iv.day != 1 else iv,  # respeta inicio; PE/FV a fin de mes
        "iv_real": iv,
        "PE": eomonth(iv, pe_idx),
        "FV": eomonth(iv, fv_idx),
        "pe_idx": pe_idx, "fv_idx": fv_idx,
    }


def calcular_portafolio(etapas):
    """etapas: lista de dicts con
        cod, nombre, unidades, vmes, frec, pe_pct,
        fecha_inicio (date|None) — solo etapa raíz,
        sucesora (cod de la etapa predecesora|None), desfase (meses).
    Resuelve el secuenciamiento: IV de cada etapa = EOMONTH(PE de su sucesora, desfase).
    Devuelve dict {cod: {nombre, IV, PE, FV, ...}} respetando dependencias.
    """
    by_cod = {e["cod"]: e for e in etapas}
    res = {}

    def resolver(cod, visitando=None):
        if cod in res:
            return res[cod]
        visitando = visitando or set()
        if cod in visitando:
            raise ValueError(f"Ciclo de sucesoras en etapa {cod}")
        visitando.add(cod)
        e = by_cod[cod]
        suc = e.get("sucesora")
        if suc:                                  # IV = PE de la sucesora + desfase
            r_suc = resolver(suc, visitando)
            iv = eomonth(r_suc["PE"], int(e.get("desfase", 0)))
        else:                                    # etapa raíz: fecha de inicio dada
            iv = e["fecha_inicio"]
        h = hitos_ventas(e["unidades"], e["vmes"], e["frec"], e.get("pe_pct", 0.60), iv)
        res[cod] = {"cod": cod, "nombre": e["nombre"], "unidades": e["unidades"],
                    "IV": iv, "PE": h["PE"], "FV": h["FV"],
                    "pe_idx": h["pe_idx"], "fv_idx": h["fv_idx"]}
        return res[cod]

    for e in etapas:
        resolver(e["cod"])
    return res
