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
        vm_viv = e.get("ventas_vivienda_miles", e.get("ventas_miles", 0))   # precio por unidad = vivienda
        adic = e.get("ventas_adicional_miles", 0)                            # parqueaderos/depósitos (No VIS)
        et.append({
            "cod": e.get("cod", i + 1), "unidades": und,
            "vmes": e.get("vmes", 6), "frec": e.get("frec", 1),
            "precio_und": (vm_viv / und if und else 0),
            "sep_und": fin.get("sep_und_miles", 5000),
            "pct_ci": fin.get("pct_ci", 0.30),
            "diferido_sep": par.get("diferido_sep", fin.get("diferido_sep", 4)),
            "escrituracion_offset": e.get("escrituracion", e.get("dur_obra", 24) + 6),
            "emes": e.get("emes"), "efrec": e.get("efrec", 1),
            "adicional_miles": adic,
        })
    try:
        return ingresos.recaudo_portafolio(et, hitos)
    except Exception:
        return {}


# ----------------------------- utilidades financieras -----------------------------
def calcular_wacc(p, detalle=False):
    """WACC en COP por el build-up CAPM de mercado emergente (metodología Damodaran/CESLA, auditada CG).

    Cadena: beta de la deuda → desapalancar beta US (CON beta de deuda) → reapalancar a la estructura
    de Colombia → Ke USD → + riesgo país (EMBI) → paridad de inflación a COP → Kd COP (compuesto) →
    WACC = E·Ke$COP + D·Kd·(1−t). Reproduce la hoja k.beta (WACC Navarra = 21,54%).

    `detalle=True` devuelve todos los eslabones intermedios (para la sección Costo de Capital).
    """
    rf = p["rf"]/100; rm = p["rm"]/100; pm = rm - rf                  # prima de mercado = Rm − Rf
    # --- beta de la deuda del comparable US: βd = (kd_us − rf) / (Rm − Rf) ---
    kd_us = p.get("kd_us", 9.335)/100
    beta_d = (kd_us - rf)/pm if pm else 0.0
    # --- desapalancar beta US CON beta de deuda (no Hamada simple) ---
    de_us = p["de_us"]/100; t_us = p["tax_us"]/100
    E_us = 1.0/(1.0+de_us); D_us = 1.0 - E_us                         # de_us = D/E
    den_u = E_us + D_us*(1-t_us)
    beta_u = (E_us/den_u)*p["beta_us"] + (D_us*(1-t_us)/den_u)*beta_d
    # --- reapalancar a la estructura de Colombia CON beta de deuda ---
    de_col = p["de_col"]/100; t_col = p["tax_col"]/100
    beta_l = beta_u + (beta_u - beta_d)*(1-t_col)*de_col
    # --- costo de recursos propios en USD + riesgo país (EMBI) ---
    ke_usd = rf + beta_l*pm
    ke_usd_rp = ke_usd + p["rp"]/100
    # --- pasar a COP por paridad de inflación de largo plazo (RPLP/DPLP) ---
    rplp = (1+p["inf_col"]/100)/(1+p["inf_us"]/100) - 1
    ke_cop = (1+ke_usd_rp)*(1+rplp) - 1
    # --- costo de la deuda en Colombia (COMPUESTO, no aditivo) ---
    kd_cop = (1+p["tasa_d"]/100)*(1+p["spread"]/100) - 1
    # --- WACC ---
    we = p["eq_w"]/100; wd = 1.0 - we
    wacc = we*ke_cop + wd*kd_cop*(1-t_col)
    if detalle:
        return {"pm":pm, "beta_d":beta_d, "beta_u":beta_u, "beta_l":beta_l,
                "ke_usd":ke_usd, "rp":p["rp"]/100, "ke_usd_rp":ke_usd_rp, "rplp":rplp,
                "ke_cop":ke_cop, "kd_cop":kd_cop, "we":we, "wd":wd, "t_col":t_col, "wacc":wacc,
                "E_us":E_us, "D_us":D_us}
    return wacc

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
def directos_total(par, V):
    """Costo directo total (miles COP). Si el proyecto trae presupuesto por capítulos
    (`par['directos_cap']`, lista {capitulo, valor_miles}), el directo es su SUMA (bottom-up,
    presupuesto absoluto). Si no, es el % de ventas (`costos_pct['directos']`)·V (top-down).
    `par['_costo_scale']` (escenarios/sensibilidad/Monte Carlo) escala el directo en ambos casos."""
    scale = par.get("_costo_scale", 1.0)
    cap = par.get("directos_cap")
    if cap:
        return sum(x.get("valor_miles", 0) or 0 for x in cap) * scale
    return par["costos_pct"]["directos"] * V * scale

def indirectos_total(par, V):
    """Costo indirecto total (miles COP). Si el proyecto trae presupuesto por capítulos
    (`par['indirectos_cap']`: diseños, licencias, interventoría, pólizas, comisión fiduciaria, predial,
    ICA, etc.), es su SUMA (bottom-up); si no, el % de ventas (`costos_pct['indirectos']`)·V (top-down).
    No escala con `_costo_scale` (el costo directo es el que se sensibiliza)."""
    cap = par.get("indirectos_cap")
    if cap:
        return sum(x.get("valor_miles", 0) or 0 for x in cap)
    return par["costos_pct"]["indirectos"] * V

def gastos_fijos_total(par):
    """Suma de gastos fijos del proyecto (miles COP) = Σ valor_mes × nº de meses activos.
    `gastos_fijos`: lista {concepto, valor_mes_miles, desde, hasta} (meses sobre la línea del proyecto)."""
    tot = 0.0
    for g in par.get("gastos_fijos", []):
        vm = g.get("valor_mes_miles", 0) or 0
        d = int(g.get("desde", 0) or 0)
        h = g.get("hasta")
        meses = (int(h) - d) if h is not None else 1
        tot += vm * max(0, meses)
    return tot

def pyg(par):
    """Estado de resultados (miles COP). par = params['costos_pct'], par['lote_bruto_miles'],
    par['financiero'], y ventas (par['ventas_miles'])."""
    V = par["ventas_miles"]
    c = par["costos_pct"]; fin = par["financiero"]
    recon = c.get("recon_codensa", 0.002) * V
    total_ingresos = V + recon
    directos   = directos_total(par, V)
    indirectos = indirectos_total(par, V)                        # % de ventas o suma de capítulos (bottom-up)
    gastos_fijos = gastos_fijos_total(par)                       # personal/generales/mercadeo ($/mes × meses)
    indirectos_otros = max(indirectos - gastos_fijos, 0.0)       # los fijos se tallan del lump (carve-out)
    honorarios = c["honorarios"]* V
    util_lote  = c["util_lote"] * V
    costo_lote = par["lote_bruto_miles"] + util_lote
    # si los gastos fijos exceden el indirecto, el exceso baja la UO (additivo); si no, UO sin cambio
    util_oper  = total_ingresos - costo_lote - directos - indirectos_otros - gastos_fijos - honorarios
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
        "gastos_fijos": gastos_fijos, "indirectos_otros": indirectos_otros,
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
        ini_o=e.get("ini_obra",0); dur=max(1, int(e.get("dur_obra") or 24)); ent=e.get("entrega",dur+ini_o)
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
        # solo el indirecto RESTANTE (tras tallar los gastos fijos) se prorratea en obra
        ind_obra=pg.get("indirectos_otros", pg["indirectos"])
        for m in range(ini_o,min(ent,N)): costos[m]+=ind_obra*share/per
        for m in range(ini_o,min(ini_o+dur,N)): costos[m]+=pg["honorarios"]*share/dur
    # gastos fijos: monto mensual sobre su ventana (timing real, no prorrateado en obra)
    for g in par.get("gastos_fijos", []):
        vm=g.get("valor_mes_miles",0) or 0; d=int(g.get("desde",0) or 0)
        h=g.get("hasta"); h=int(h) if h is not None else d+1
        for m in range(max(0,d), min(h,N)): costos[m]+=vm
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
    # d_precio escala las ventas; d_costo escala el costo directo (vía _costo_scale, que
    # respeta tanto el presupuesto por capítulos como el % de ventas — ver directos_total()).
    p2=dict(par); p2["ventas_miles"]=par["ventas_miles"]*(1+d_precio)
    p2["_costo_scale"]=par.get("_costo_scale",1.0)*(1+d_costo)
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


def montecarlo_tir(par, n=300, rango_precio=(-0.15, 0.15), rango_costo=(-0.10, 0.10),
                   rango_ventas=(-0.30, 0.30), seed=42, escrituracion_sigue_obra=True):
    """Monte Carlo de la TIR y el VPN del PROYECTO (criterio de decisión del comité).

    Varía de forma uniforme tres fuentes de riesgo y, para cada escenario, recalcula la
    cadena hitos → recaudo → flujo apalancado:
      - precio de venta (`rango_precio`): escala las ventas de cada etapa,
      - costo directo (`rango_costo`): escala el directo (vía `_costo_scale`, respeta capítulos o %),
      - ritmo de ventas (`rango_ventas`): escala las unidades/mes (`vmes`) de cada etapa → mueve
        los hitos (PE→IC→FC) y el calendario de recaudo → cambia cuándo entra la caja → cambia
        la TIR/VPN y los intereses. (El margen operativo NO depende del ritmo; por eso aquí la
        salida es TIR/VPN, no margen.)

    Captura por escenario: `tir_proyecto` (sobre los reintegros, @TIO), `tir_equity` (socio
    apalancado) y `vpn_proyecto` (@TIO). IMPORTANTE: ignora el override de FCL de fiducia
    (`par['fiducia']`) y usa la TIR del MODELO — la cifra auditada es fija y no respondería a las
    variables. Determinística por `seed` (reproducible). NO muta `par`.

    Devuelve: distribuciones (`tir_proyecto`/`tir_equity`/`vpn_proyecto`), sus estadísticos
    (`stats_tir`/`stats_equity`/`stats_vpn` con p10/p50/p90/media/std/n), el `hurdle` (=TIO),
    la prob. de TIR > TIO y de VPN > 0, y los rangos usados.
    """
    base = dict(par)
    base.pop("fiducia", None)                          # usar la TIR del MODELO, no la auditada (es fija)
    base_etapas = par.get("etapas", []) or []
    base_tip = par.get("tipologias")
    hurdle = (par.get("financiero", {}) or {}).get("tio", 0.15)
    # --- línea base de hitos: para que la escrituración SIGA a la obra hay que mantener fija la
    #     brecha (equilibrio→escrituración). Capturamos el PE de cada etapa con el ritmo base y la
    #     escrituración base; en cada escenario desplazamos la escrituración por el mismo Δ de PE. ---
    base_pe = {}; base_esc = {}
    if escrituracion_sigue_obra:
        try:
            hb = _hitos(par)
            for e in base_etapas:
                cod = e.get("cod")
                if cod in hb:
                    base_pe[cod] = hb[cod].get("pe_idx", 0)
                    base_esc[cod] = e.get("escrituracion", e.get("dur_obra", 24) + 6)
        except Exception:
            base_pe = {}
    rng = random.Random(seed)
    tir_p = []; tir_e = []; vpn_p = []
    for _ in range(int(n)):
        dp = rng.uniform(*rango_precio); dc = rng.uniform(*rango_costo); dv = rng.uniform(*rango_ventas)
        p = dict(base)
        p["etapas"] = [dict(e) for e in base_etapas]   # copia superficial: solo mutamos escalares
        if base_tip is not None:
            p["tipologias"] = [dict(t) for t in base_tip]
        p["_costo_scale"] = base.get("_costo_scale", 1.0) * (1 + dc)
        for e in p["etapas"]:                          # ritmo de ventas: ±dv sobre vmes (mín 1 und/mes)
            vm = e.get("vmes", 6) or 6
            e["vmes"] = max(1, int(round(vm * (1 + dv))))
        normalizar_tipologias(p)                       # ventas/und por etapa (no-op sin tipologías)
        f = 1 + dp
        for e in p["etapas"]:                          # precio: ±dp sobre las ventas de cada etapa
            e["ventas_miles"] = (e.get("ventas_miles", 0) or 0) * f
            if e.get("ventas_vivienda_miles") is not None: e["ventas_vivienda_miles"] *= f
            if e.get("ventas_adicional_miles") is not None: e["ventas_adicional_miles"] *= f
        p["ventas_miles"] = sum(e.get("ventas_miles", 0) for e in p["etapas"])
        pg = pyg(p); hitos = _hitos(p)
        if base_pe:                                    # escrituración sigue a la obra (entregas tras construir)
            for e in p["etapas"]:
                cod = e.get("cod")
                if cod in hitos and cod in base_pe:
                    delta = hitos[cod].get("pe_idx", 0) - base_pe[cod]
                    e["escrituracion"] = max(1, base_esc[cod] + delta)
        recaudo = _recaudo(p, hitos)
        ap = apalancamiento.flujo_apalancado(p, pg, hitos, recaudo)
        tp = ap.get("tir_proyecto"); te = ap.get("tir_equity"); vp = ap.get("vpn_proyecto")
        if tp is not None: tir_p.append(tp)
        if te is not None: tir_e.append(te)
        if vp is not None: vpn_p.append(vp)

    def _stats(serie):
        s = sorted(serie)
        if not s:
            return {"p10": None, "p50": None, "p90": None, "media": None, "std": None, "n": 0}
        media = sum(serie) / len(serie)
        var = sum((x - media) ** 2 for x in serie) / len(serie)
        return {"p10": _percentil(s, 0.10), "p50": _percentil(s, 0.50), "p90": _percentil(s, 0.90),
                "media": media, "std": var ** 0.5, "n": len(serie)}

    prob_hurdle = (sum(1 for x in tir_p if x > hurdle) / len(tir_p)) if tir_p else 0.0
    prob_vpn_pos = (sum(1 for x in vpn_p if x > 0) / len(vpn_p)) if vpn_p else 0.0
    return {
        "tir_proyecto": tir_p, "tir_equity": tir_e, "vpn_proyecto": vpn_p,
        "stats_tir": _stats(tir_p), "stats_equity": _stats(tir_e), "stats_vpn": _stats(vpn_p),
        "hurdle": hurdle, "prob_tir_hurdle": prob_hurdle, "prob_vpn_pos": prob_vpn_pos,
        "n": int(n), "n_validas": len(tir_p),
        "rango_precio": rango_precio, "rango_costo": rango_costo, "rango_ventas": rango_ventas,
    }


# ----------------------------- tipologías (ingresos por producto) -----------------------------
HOUSING = ("apartamento", "comercio")        # generan unidad escriturable (separación/CI/subrogación)
ADICIONAL = ("parqueadero", "deposito")      # ingreso adicional (No VIS); no son unidad de vivienda

def _ventas_tipologia(t):
    """Ventas (miles COP) de una tipología: und × precio (× área si el método es $/m²)."""
    und = t.get("und", 0) or 0
    precio = t.get("precio", 0) or 0
    if t.get("metodo", "$/und") == "$/m²":
        return und * precio * (t.get("area_und", 0) or 0) / 1000
    return und * precio / 1000

def normalizar_tipologias(par):
    """Si el proyecto trae `par['tipologias']` (lista con {etapa, clase, und, metodo, precio, area_und}),
    deriva por etapa las ventas (vivienda + adicionales) y las unidades de VIVIENDA. Mutación in situ:
    fija `e['ventas_miles']` (total) y `e['und']` (solo vivienda) en cada etapa. No-op sin tipologías.
    Regla CG: en VIS los parqueaderos/depósitos son comunales (no entran); en No VIS van por separado."""
    tip = par.get("tipologias")
    if not tip:
        return
    # Regla CG (en el MOTOR, fuente única): en VIS/VIP los parqueaderos y depósitos son comunales →
    # ingreso CERO; en No VIS van por separado. No se confía solo en el filtro de la UI.
    es_vis = str(par.get("meta", {}).get("tipo", "")).strip().upper() in ("VIS", "VIP")
    por_etapa = {}
    for t in tip:
        por_etapa.setdefault(t.get("etapa"), []).append(t)
    for e in par.get("etapas", []):
        ts = por_etapa.get(e.get("cod"))
        if not ts:
            continue
        v_viv = 0.0; v_adic = 0.0; u_viv = 0
        for t in ts:
            if t.get("clase", "apartamento") in HOUSING:
                v_viv += _ventas_tipologia(t); u_viv += t.get("und", 0) or 0
            elif not es_vis:                           # parqueadero/depósito: solo suman en No VIS
                v_adic += _ventas_tipologia(t)
        e["ventas_miles"] = v_viv + v_adic             # total (P&G)
        e["ventas_vivienda_miles"] = v_viv             # vivienda → recaudo completo (sep+CI+subrogación)
        e["ventas_adicional_miles"] = v_adic           # adicionales → recaudo en cuota inicial (sin subrogación)
        if u_viv:
            e["und"] = u_viv


# ----------------------------- orquestador -----------------------------
def calcular(par):
    """Recibe params de proyecto, devuelve todos los resultados."""
    normalizar_tipologias(par)                  # ingresos por tipología → ventas/und por etapa (no-op sin ellas)
    # ventas = suma de etapas (recalcular si hay tipologías; si no, respetar override existente)
    if "ventas_miles" not in par or par.get("tipologias"):
        par["ventas_miles"] = sum(e.get("ventas_miles", 0) for e in par["etapas"])
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
