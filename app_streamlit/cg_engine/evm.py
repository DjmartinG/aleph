# -*- coding: utf-8 -*-
"""
Earned Value Management (EVM) — Valor Ganado. Estándar PMI/PMBOK.

A partir de:
  - la curva de costo directo PLANEADA por mes (campana de Gauss del motor) → PV (Valor Planeado),
  - el **% de avance real** y el **costo real** por etapa ingresados por el usuario,
calcula las 3 curvas S acumuladas (PV, EV, AC), los índices de desempeño (CPI, SPI), las varianzas
(CV, SV) y la proyección a la terminación (EAC, ETC, VAC).

Convenciones (todo en miles COP, mensual, acumulado):
  BAC = presupuesto total a la terminación (costo directo planeado total)
  PV  = Valor Planeado   = costo planeado acumulado hasta la fecha de corte
  EV  = Valor Ganado     = % avance real × BAC (lo realmente ejecutado, valorado al presupuesto)
  AC  = Costo Real        = lo efectivamente gastado a la fecha
  CPI = EV/AC  (eficiencia en costo:   >1 gasta menos de lo ganado = bien)
  SPI = EV/PV  (eficiencia en plazo:   >1 avanza más de lo planeado = bien)
  CV  = EV−AC  · SV = EV−PV
  EAC = BAC/CPI (estimación del costo final al ritmo actual) · ETC = EAC−AC · VAC = BAC−EAC
"""
from datetime import date
from . import config


def _curva_planeada(distribucion):
    """Serie mensual del costo directo planeado (ya escalado) y su acumulada."""
    esc = list(distribucion.get("escalada", []))
    acum = []
    s = 0.0
    for v in esc:
        s += v
        acum.append(s)
    return esc, acum


def calcular_evm(par, R, hoy=None):
    """Calcula EVM del proyecto. `par` = dict del proyecto; `R` = salida de modelo.calcular(par).
    Devuelve None si no hay datos de avance real ingresados (no se puede computar EV/AC).

    El usuario ingresa por etapa (en par['etapas'][i]):
        'avance_real'  : 0..1   (% de avance de obra de esa etapa, a la fecha de corte)
        'costo_real'   : miles COP gastados en esa etapa a la fecha de corte
    """
    etapas = par.get("etapas", [])
    tiene = any(("avance_real" in e or "costo_real" in e) for e in etapas)
    if not tiene:
        return None

    pg = R.get("pyg", {})
    dist = R.get("distribucion", {})
    hitos = R.get("hitos", {})
    V = pg.get("ventas", 0) or 1

    BAC = pg.get("directos", 0.0)                      # presupuesto = costo directo total planeado
    esc, acum = _curva_planeada(dist)

    # fecha base de la obra (mes 0 de la curva planeada) = inicio de construcción más temprano
    ic = [h.get("IC") for h in hitos.values() if h.get("IC")]
    base_obra = min(ic) if ic else None

    # ---- EV y AC (a la fecha de corte), agregados de las etapas ----
    ev = 0.0; ac = 0.0; av_ponderado_num = 0.0
    detalle = []
    for e in etapas:
        share = (e.get("ventas_miles", 0) / V) if V else 0
        bac_e = BAC * share                            # presupuesto directo de la etapa
        av = e.get("avance_real")
        cr = e.get("costo_real")
        ev_e = (av or 0.0) * bac_e
        ac_e = (cr if cr is not None else 0.0)
        ev += ev_e; ac += ac_e
        if av is not None:
            av_ponderado_num += av * bac_e
        detalle.append({"etapa": e.get("nom", f"E{e.get('cod')}"), "bac": bac_e,
                        "avance_real": av, "costo_real": cr, "ev": ev_e, "ac": ac_e})

    avance_global = (av_ponderado_num / BAC) if BAC else 0.0   # % avance ponderado por presupuesto

    # ---- PV a la fecha de corte = costo planeado acumulado al mes de corte ----
    # mes de corte = meses transcurridos de obra desde base_obra hasta hoy
    hoy = hoy or config.FECHA_CORTE_EVM
    pv = 0.0; mes_corte = None
    if base_obra:
        mes_corte = (hoy.year - base_obra.year) * 12 + (hoy.month - base_obra.month)
        if mes_corte < 0:
            pv = 0.0
        elif mes_corte >= len(acum):
            pv = acum[-1] if acum else BAC
        else:
            pv = acum[mes_corte]
    else:
        pv = avance_global * BAC                         # sin calendario: PV≈avance esperado

    # ---- índices y proyecciones ----
    cpi = (ev / ac) if ac else None
    spi = (ev / pv) if pv else None
    cv = ev - ac
    sv = ev - pv
    eac = (BAC / cpi) if cpi else None                   # costo final estimado al ritmo actual
    etc = (eac - ac) if eac is not None else None
    vac = (BAC - eac) if eac is not None else None

    return {
        "BAC": BAC, "PV": pv, "EV": ev, "AC": ac,
        "avance_global": avance_global, "mes_corte": mes_corte, "base_obra": base_obra,
        "CPI": cpi, "SPI": spi, "CV": cv, "SV": sv,
        "EAC": eac, "ETC": etc, "VAC": vac,
        "curva_pv": acum,                                 # PV acumulado mensual (toda la obra)
        "curva_pv_mensual": esc,
        "detalle": detalle, "hoy": hoy,
    }


def estado_en_palabras(evm):
    """Resumen legible del estado EVM (CPI/SPI → adelantado/atrasado, sobre/bajo presupuesto)."""
    if not evm:
        return ""
    av = evm["avance_global"] * 100
    partes = [f"La obra va al **{av:.0f}%** de avance"]
    cpi, spi = evm.get("CPI"), evm.get("SPI")
    if cpi is not None:
        if cpi >= 1.0:
            partes.append(f"**bajo presupuesto** (CPI {cpi:.2f}: por cada $1 ganado se gastó ${1/cpi:.2f})")
        else:
            partes.append(f"**sobre presupuesto** (CPI {cpi:.2f}: por cada $1 ganado se gastó ${1/cpi:.2f})")
    if spi is not None:
        if spi >= 1.0:
            partes.append(f"**adelantada** en cronograma (SPI {spi:.2f})")
        else:
            partes.append(f"**atrasada** en cronograma (SPI {spi:.2f})")
    txt = "; ".join(partes) + "."
    if evm.get("EAC") is not None:
        txt += (f" Costo final estimado (EAC) **{evm['EAC']/1000:,.0f} mil M**"
                .replace(",", ".") + f" vs presupuesto {evm['BAC']/1000:,.0f} mil M".replace(",", "."))
        if evm.get("VAC") is not None:
            signo = "ahorro" if evm["VAC"] >= 0 else "sobrecosto"
            txt += f" → {signo} estimado {abs(evm['VAC'])/1000:,.0f} mil M.".replace(",", ".")
    return txt
