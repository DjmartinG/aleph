# -*- coding: utf-8 -*-
"""
Modelo financiero de factibilidad — fuente única de verdad.
Toma un dict de parámetros de proyecto y devuelve P&G, reparto, distribución de costos,
flujo de caja, escenarios, sensibilidades e indicadores. Metodología validada contra
prefactibilidades reales. Enfoque híbrido: TIR apalancada de referencia es un parámetro.
"""
import random
from datetime import datetime
from . import curvas
from . import portafolio
from . import ingresos
from . import apalancamiento
try:
    from scipy import optimize
    _SCIPY = True
except Exception:
    _SCIPY = False


def _hitos(par):
    """Calcula los hitos del portafolio (IV/PE/FV por etapa)."""
    et = par.get("etapas", [])
    plist = []
    for i, e in enumerate(et):
        fi = e.get("fecha_inicio")
        if isinstance(fi, str):
            try: fi = datetime.strptime(fi[:10], "%Y-%m-%d").date()
            except Exception: fi = None
        plist.append({
            "cod": e.get("cod", i + 1), "nombre": e.get("nom", f"Etapa {i+1}"),
            "unidades": e.get("und", 0), "vmes": e.get("vmes", 6), "frec": e.get("frec", 1),
            "pe_pct": e.get("pe_pct", 0.60), "fecha_inicio": fi,
            "sucesora": e.get("sucesora"), "desfase": e.get("desfase", 0),
            "obra_offset": e.get("obra_offset", 1), "dur_obra": e.get("dur_obra", 24),
            "ic_offset": e.get("ic_offset"),
        })
    if not any(p["sucesora"] is None and p["fecha_inicio"] for p in plist):
        return {}
    try:
        return portafolio.calcular_portafolio(plist)
    except Exception:
        return {}


def _recaudo(par, hitos):
    """Recaudo consolidado del portafolio (separación/cuota inicial/subrogación) — Fase 2."""
    if not hitos:
        return {}
    fin = par.get("financiero", {})
    et = []
    for i, e in enumerate(par.get("etapas", [])):
        und = e.get("und", 0)
        vm = e.get("ventas_miles", 0)
        et.append({
            "cod": e.get("cod", i + 1), "unidades": und,
            "vmes": e.get("vmes", 6), "frec": e.get("frec", 1),
            "precio_und": (vm / und if und else 0),
            "sep_und": fin.get("sep_und_miles", 5000),
            "pct_ci": fin.get("pct_ci", 0.30),
            "diferido_sep": par.get("diferido_sep", fin.get("diferido_sep", 4)),
            "escrituracion_offset": e.get("escrituracion", e.get("dur_obra", 24) + 6),
            "emes": e.get("emes"), "efrec": e.get("efrec", 1),
        })
    try:
        return ingresos.recaudo_portafolio(et, hitos)
    except Exception:
        return {}


# ----------------------------- utilidades financieras -----------------------------
def calcular_wacc(p):
    b_d = p["beta_us"]/(1+(1-p["tax_us"]/100)*(p["de_us"]/100))
    b_c = b_d*(1+(1-p["tax_col"]/100)*(p["de_col"]/100))
    ke  = p["rf"]/100 + b_c*((p["rm"]-p["rf"])/100) + p["rp"]/100
    rplp = (1+p["inf_col"]/100)/(1+p["inf_us"]/100)-1
    ke_cop = (1+ke)*(1+rplp)-1
    kd = p["tasa_d"]/100 + p["spread"]/100
    dw = (100-p["eq_w"])/100
    return (p["eq_w"]/100)*ke_cop + dw*kd*(1-p["tax_col"]/100)

def tir(flujos):
    if not _SCIPY:
        return None
    def vpn(r): return sum(f/(1+r)**t for t,f in enumerate(flujos))
    r=-0.6; prev=vpn(r)
    while r<5.0:
        r2=r+0.005; cur=vpn(r2)
        if prev*cur<0:
            try: return optimize.brentq(vpn,r,r2,xtol=1e-10)
            except Exception: pass
        prev=cur; r=r2
    return None


# ----------------------------- P&G -----------------------------
def pyg(par):
    """Estado de resultados (miles COP). par = params['costos_pct'], par['lote_bruto_miles'],
    par['financiero'], y ventas (par['ventas_miles'])."""
    V = par["ventas_miles"]
    c = par["costos_pct"]; fin = par["financiero"]
    recon = c.get("recon_codensa", 0.002) * V
    total_ingresos = V + recon
    directos   = c["directos"]  * V
    indirectos = c["indirectos"]* V
    honorarios = c["honorarios"]* V
    util_lote  = c["util_lote"] * V
    costo_lote = par["lote_bruto_miles"] + util_lote
    util_oper  = total_ingresos - costo_lote - directos - indirectos - honorarios
    reint_sin_lote = honorarios + util_oper
    renta = fin.get("renta", 0.35) * reint_sin_lote
    udi   = reint_sin_lote - renta
    # reparto CG / socio
    split = fin.get("split_cg", 0.70)
    hc = c.get("hon_construccion", 0.035) * V
    hg = c.get("hon_gerencia",     0.030) * V
    hv = c.get("hon_ventas",       0.015) * V
    cg = hg + hv + util_oper*split + util_lote
    socio = hc + util_oper*(1-split)
    return {
        "ventas": V, "recon_codensa": recon, "total_ingresos": total_ingresos,
        "directos": directos, "indirectos": indirectos, "honorarios": honorarios,
        "util_lote": util_lote, "costo_lote": costo_lote, "lote_bruto": par["lote_bruto_miles"],
        "util_oper": util_oper, "margen_oper": util_oper/V if V else 0,
        "renta": renta, "udi": udi,
        "cg": cg, "socio": socio, "resultados": cg+socio,
        "hon_construccion": hc, "hon_gerencia": hg, "hon_ventas": hv,
    }


# ----------------------------- distribución de costos (PERT) -----------------------------
def distribucion_costos(par, directos_miles):
    cr = par.get("cronograma", {})
    dur = int(cr.get("dur_obra", 40)); moda = int(cr.get("moda_pert", 24))
    tipo = cr.get("curva", "Gauss")          # curva Gauss (Normal) de avance de obra
    base = curvas.distribuir(directos_miles, dur, tipo, moda=moda)
    esc  = curvas.escalar_mat_mo(base, rel_mat=cr.get("rel_materiales",0.8),
                                 ea_mat=cr.get("ea_materiales",0.06), ea_mo=cr.get("ea_mano_obra",0.12))
    acum=[]; s=0
    for x in esc: s+=x; acum.append(s)
    return {"base":base, "escalada":esc, "acumulada":acum,
            "pico_mes": esc.index(max(esc))+1 if esc else 0,
            "incremento": sum(esc)-sum(base)}


# ----------------------------- flujo de caja (proyecto) -----------------------------
def flujo_caja(par, pg):
    fin = par["financiero"]; N = 96
    etapas = par["etapas"]; V = pg["ventas"]
    ingresos=[0.0]*N; costos=[0.0]*N
    PCT_CI=fin.get("pct_ci",0.30); PCT_SUB=1-PCT_CI; SEP=fin.get("sep_und_miles",5000.0)
    for e in etapas:
        und=e["und"]; vent=e["ventas_miles"]; share=vent/V if V else 0
        ini_o=e.get("ini_obra",0); dur=e.get("dur_obra",24); ent=e.get("entrega",dur+ini_o)
        ini_v=e.get("ini_venta",0)
        precio=vent/und if und else 0
        fase=max(1,ent-ini_v)
        ci=vent*PCT_CI - SEP*und
        for m in range(N):
            if ini_v<=m<ent: ingresos[m]+=ci/fase
            if m==ini_v:     ingresos[m]+=SEP*und
            if m==ent-1:     ingresos[m]+=vent*PCT_SUB
        cd=pg["directos"]*share
        serie=curvas.distribuir(cd,dur,"PERT",moda=int(dur*0.6))
        for k,val in enumerate(serie):
            if ini_o+k<N: costos[ini_o+k]+=val
        per=max(1,ent-ini_o)
        for m in range(ini_o,min(ent,N)): costos[m]+=pg["indirectos"]*share/per
        for m in range(ini_o,min(ini_o+dur,N)): costos[m]+=pg["honorarios"]*share/dur
    # lote en t0 (necesidad de caja)
    costos[0]+=pg["costo_lote"]
    flujo=[ingresos[m]-costos[m] for m in range(N)]
    acum=[]; s=0
    for x in flujo: s+=x; acum.append(s)
    # crédito constructor (tope = ancla)
    cap=fin.get("credito_cap_miles", 0.8*pg["directos"])
    tasa_m=(1+fin.get("tasa_credito_ea",0.155))**(1/12)-1
    saldo=0.0; saldo_serie=[0.0]*N; intereses=0.0
    for m in range(N):
        interes=saldo*tasa_m; intereses+=interes
        neto=flujo[m]-interes
        if neto<0:
            saldo+=min(-neto, max(0,cap-saldo))
        else:
            saldo-=min(neto,saldo)
        saldo_serie[m]=saldo
    wacc=calcular_wacc(fin["wacc"]); wacc_m=(1+wacc)**(1/12)-1
    tir_m=tir(flujo);
    return {
        "ingresos":ingresos,"costos":costos,"flujo":flujo,"acumulado":acum,
        "saldo_credito":saldo_serie,"credito_max":max(saldo_serie),
        "intereses_total":intereses,"max_caja":min(acum),
        "tir_proyecto":((1+tir_m)**12-1) if tir_m else None,
        "vpn_proyecto":sum(f/(1+wacc_m)**t for t,f in enumerate(flujo)),
        "wacc":wacc,
        "tir_apalancada_ref":fin.get("tir_apalancada_ref"),
    }


# ----------------------------- escenarios y sensibilidades -----------------------------
def _correr(par, d_precio=0.0, d_costo=0.0):
    p2=dict(par); p2["ventas_miles"]=par["ventas_miles"]*(1+d_precio)
    c=dict(par["costos_pct"]); c["directos"]=par["costos_pct"]["directos"]*(1+d_costo)
    p2["costos_pct"]=c
    r=pyg(p2)
    return {"ventas":r["ventas"],"util_oper":r["util_oper"],"margen":r["margen_oper"]}

def escenarios(par):
    return {"Base":_correr(par), "Optimista":_correr(par,+0.05,-0.02), "Pesimista":_correr(par,-0.10,+0.05)}

def sensibilidades(par):
    base=pyg(par)["util_oper"]
    return {
        "Precio -10%": _correr(par,-0.10,0)["util_oper"]-base,
        "Precio +10%": _correr(par,+0.10,0)["util_oper"]-base,
        "Costo directo +10%": _correr(par,0,+0.10)["util_oper"]-base,
        "Costo directo -10%": _correr(par,0,-0.10)["util_oper"]-base,
    }


def _percentil(serie_ordenada, q):
    """Percentil q (0..1) por interpolación lineal sobre una lista YA ordenada."""
    s = serie_ordenada
    if not s: return 0.0
    i = q * (len(s) - 1); lo = int(i); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)

def montecarlo(par, n=500, rango_precio=(-0.15, 0.15), rango_costo=(-0.10, 0.10), seed=42):
    """Simulación Monte Carlo del margen operativo y la utilidad operativa.

    Varía el precio de venta y el costo directo de forma uniforme en los rangos dados y recorre
    el P&G `n` veces (vía _correr). Determinística por `seed` (reproducible). NO muta `par`.

    Devuelve dict con: margenes[], util_oper[], p10/p50/p90 (del margen), media, std, prob_pos
    (fracción de escenarios con margen > 0), n, y los rangos usados.
    """
    p = dict(par)
    if "ventas_miles" not in p:
        p["ventas_miles"] = sum(e.get("ventas_miles", 0) for e in p.get("etapas", []))
    rng = random.Random(seed)
    margenes = []; utils = []
    for _ in range(int(n)):
        dp = rng.uniform(*rango_precio); dc = rng.uniform(*rango_costo)
        r = _correr(p, dp, dc)
        margenes.append(r["margen"]); utils.append(r["util_oper"])
    ms = sorted(margenes)
    media = sum(margenes) / len(margenes) if margenes else 0.0
    var = sum((x - media) ** 2 for x in margenes) / len(margenes) if margenes else 0.0
    prob_pos = sum(1 for x in margenes if x > 0) / len(margenes) if margenes else 0.0
    return {
        "margenes": margenes, "util_oper": utils,
        "p10": _percentil(ms, 0.10), "p50": _percentil(ms, 0.50), "p90": _percentil(ms, 0.90),
        "media": media, "std": var ** 0.5, "prob_pos": prob_pos, "n": int(n),
        "rango_precio": rango_precio, "rango_costo": rango_costo,
    }


# ----------------------------- orquestador -----------------------------
def calcular(par):
    """Recibe params de proyecto, devuelve todos los resultados."""
    # ventas = suma de etapas si no viene explícito
    if "ventas_miles" not in par:
        par["ventas_miles"] = sum(e["ventas_miles"] for e in par["etapas"])
    pg = pyg(par)
    hitos = _hitos(par)
    recaudo = _recaudo(par, hitos)
    return {
        "meta": par.get("meta", {}),
        "pyg": pg,
        "distribucion": distribucion_costos(par, pg["directos"]),
        "flujo": flujo_caja(par, pg),
        "escenarios": escenarios(par),
        "sensibilidades": sensibilidades(par),
        "urbanistico": _urbanistico(par, pg),
        "hitos": hitos,
        "recaudo": recaudo,
        "apalancamiento": apalancamiento.flujo_apalancado(par, pg, hitos, recaudo),
    }

def _urbanistico(par, pg):
    a=par.get("areas",{})
    av=a.get("m2_vendibles",0); ac=a.get("m2_construidos",0)
    au=a.get("lote_util",0); ab=a.get("lote_bruta",0)
    und=par.get("meta",{}).get("unidades",0)
    return {
        "lote_bruta":ab,"lote_util":au,"ratio_bruta_util":(ab/au if au else None),
        "area_construida":ac,"area_vendible":av,
        "indice_construccion":(ac/au if au else None),
        "aprovechamiento":(av/ac if ac else None),
        "densidad_und_ha":(und/(au/10000) if au else None),
        "precio_m2_vend":(pg["ventas"]*1000/av if av else None),
        "costo_dir_m2_const":(pg["directos"]*1000/ac if ac else None),
    }
