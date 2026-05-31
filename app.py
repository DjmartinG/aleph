# -*- coding: utf-8 -*-
"""
Aplicativo de Prefactibilidad / Factibilidad — CG Constructora.
Capa de presentación (Streamlit). NO contiene lógica financiera: usa engine/ (fuente única).
Navegación por menú lateral (estilo APEX) con tablero de Inicio. Data 100% en plataforma. v2.0.0
"""
import json, io, copy
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from streamlit_option_menu import option_menu
from engine import calcular, __version__ as ENGINE_V
import charts as _charts   # gráficos financieros pro (marca CG)

# ---------------- marca CG ----------------
TEAL="#004854"; AMBER="#F09C00"; INK="#13262B"; MUTED="#6B7280"
GREEN="#1E874B"; RED="#C0392B"; BORDER="#E6E9EF"
HERE=Path(__file__).parent; PROY_DIR=HERE/"proyectos"; PRIV_DIR=HERE/"proyectos_privados"; LOGO=HERE/"assets"/"logo_cg.png"
_icon = str(LOGO) if LOGO.exists() else "🏗️"
st.set_page_config(page_title="Factibilidad CG", page_icon=_icon, layout="wide",
                   initial_sidebar_state="expanded")

pio.templates["cg"]=go.layout.Template(layout=dict(
    font=dict(family="Inter, sans-serif", color=INK, size=13),
    paper_bgcolor="white", plot_bgcolor="white",
    colorway=[TEAL, AMBER, GREEN, MUTED, RED, "#0E7C86"],
    margin=dict(l=54, r=24, t=54, b=44),
    xaxis=dict(gridcolor="#EEF1F5", zerolinecolor=BORDER),
    yaxis=dict(gridcolor="#EEF1F5", zerolinecolor=BORDER),
    legend=dict(orientation="h", y=-0.2), title=dict(font=dict(size=15, color=TEAL))))
pio.templates.default="cg"
_charts.registrar_template()   # plantilla CG también para el módulo de gráficos pro

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family:'Inter',-apple-system,sans-serif; }
/* Ocultar SOLO menú hamburguesa y widget de estado — NO la toolbar entera (ahí vive el botón del menú lateral) */
#MainMenu, footer, [data-testid="stStatusWidget"] { visibility:hidden; height:0; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#F7F9FA; border-right:1px solid #E6E9EF; }
/* El control para abrir/colapsar el menú lateral SIEMPRE visible (varios nombres según versión de Streamlit) */
[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"], [data-testid="stExpandSidebarButton"] {
    visibility:visible !important; display:flex !important; opacity:1 !important; z-index:999999 !important; }
.block-container { padding-top:1.3rem; max-width:1320px; }
h1 { color:#004854; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; }
h2,h3 { color:#13262B; font-weight:700; }
.brandbar { height:4px; background:linear-gradient(90deg,#004854 0%,#F09C00 100%); border-radius:4px; margin:.4rem 0 1rem; }
.kpi { background:#fff; border:1px solid #E6E9EF; border-radius:14px; padding:12px 14px;
       box-shadow:0 1px 2px rgba(16,24,40,.05); min-height:104px; }
.kpi .l { font-size:.64rem; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color:#6B7280; min-height:1.9em; }
.kpi .v { font-size:1.22rem; font-weight:700; color:#004854; margin-top:6px; line-height:1.15; white-space:nowrap; }
.kpi .s { font-size:.74rem; font-weight:600; margin-top:3px; }
.navcard { background:#fff; border:1px solid #E6E9EF; border-radius:14px; padding:16px 18px;
           box-shadow:0 1px 2px rgba(16,24,40,.05); height:100%; }
.navcard h4 { color:#004854; margin:0 0 8px; font-size:1rem; font-weight:700; }
.navcard ul { margin:0; padding-left:1.05em; color:#374151; font-size:.86rem; line-height:1.75; }
</style>
""", unsafe_allow_html=True)

def fmt_mm(x):
    # x viene en MILES COP. ≥ mil millones → "mil M" (miles de millones); si no → "M" (millones).
    if not x: return "$0"
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.1f} mil M".replace(",", ".")
    return f"${x/1000:,.0f} M".replace(",", ".")
def fmt_pct(x): return f"{x*100:.2f}%" if x is not None else "n/d"
def kpi(col, label, value, sub="", sub_color=MUTED):
    s = f'<div class="s" style="color:{sub_color}">{sub}</div>' if sub else ''
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>{s}</div>', unsafe_allow_html=True)
# Almacenamiento: Supabase si hay credenciales, si no archivos locales (capa storage.py)
from storage import listar, cargar, es_real, guardar, usando_supabase, diagnostico, probar_conexion

# ---------------- control de acceso (Fase 1) ----------------
def _secret(nombre):
    try:
        return str(st.secrets.get(nombre, "")) if hasattr(st, "secrets") else ""
    except Exception:
        return ""

def gate():
    """Sin CLAVE_EQUIPO -> app abierta (rol editor, local). Con CLAVE_EQUIPO exige clave para ver;
    CLAVE_EDITOR habilita edicion. Devuelve 'editor' | 'viewer'."""
    clave_eq = _secret("CLAVE_EQUIPO"); clave_ed = _secret("CLAVE_EDITOR")
    if not clave_eq:
        st.session_state["_rol"] = "editor"; return "editor"
    if st.session_state.get("_rol") in ("viewer", "editor"):
        return st.session_state["_rol"]
    c = st.columns([1, 2, 1])[1]
    with c:
        if LOGO.exists(): st.image(str(LOGO), width=160)
        st.markdown("### Acceso — Factibilidad CG")
        st.caption("Herramienta interna de CG Constructora. Clave de **equipo** para ver el tablero; "
                   "clave de **editor** para ingresar datos.")
        pwd = st.text_input("Clave", type="password", key="_pwd_in")
        if st.button("Entrar", type="primary", width="stretch"):
            if clave_ed and pwd == clave_ed:
                st.session_state["_rol"] = "editor"; st.rerun()
            elif pwd == clave_eq:
                st.session_state["_rol"] = "viewer"; st.rerun()
            else:
                st.error("Clave incorrecta.")
    st.stop()

ROL = gate()
ES_EDITOR = (ROL == "editor")

def _irr_anual(flujos):
    """TIR anualizada de un flujo mensual (bisección robusta). None si no hay cambio de signo."""
    def vpn(r): return sum(f/(1+r)**t for t,f in enumerate(flujos))
    lo,hi=-0.95,5.0; flo,fhi=vpn(lo),vpn(hi)
    if flo*fhi>0:                                   # buscar cambio de signo
        r=lo; prev=flo; found=False
        while r<hi:
            r2=r+0.01; cur=vpn(r2)
            if prev*cur<0: lo,hi,flo=r,r2,prev; found=True; break
            prev=cur; r=r2
        if not found: return None
    for _ in range(200):
        mid=(lo+hi)/2; fm=vpn(mid)
        if flo*fm<=0: hi=mid
        else: lo=mid; flo=fm
    m=(lo+hi)/2
    try: return (1+m)**12-1
    except Exception: return None

@st.cache_data(show_spinner=False)
def consolidado(_keys):
    """Consolidado del portafolio. _keys = tuple(listar()) → invalida el caché si cambia el set."""
    # eje GLOBAL absoluto (epoch ene-2022) para alinear proyectos que arrancan en años distintos
    EPOCH=2022; N=240; oper=[0.0]*N; equity=[0.0]*N; saldo=[0.0]*N
    ventas=util=udi=vpn=und=0.0; n=0; filas=[]; tir_num=tir_den=0.0
    for name in _keys:
        try:
            par=cargar(name); R=calcular(copy.deepcopy(par))
        except Exception:
            continue
        pg=R["pyg"]; ap=R.get("apalancamiento") or {}; mt=R["meta"]; h=R.get("hitos") or {}   # waterfall calibrado
        ventas+=pg["ventas"]; util+=pg["util_oper"]; udi+=pg["udi"]
        if ap.get("vpn_proyecto"): vpn+=ap["vpn_proyecto"]
        tref=ap.get("tir_apalancada_ref")
        if tref: tir_num+=pg["ventas"]*tref; tir_den+=pg["ventas"]   # TIR ref ponderada por ventas
        und+=sum(e.get("und",0) or 0 for e in par.get("etapas",[]))
        base=min((h[c]["IV"] for c in h), default=None)             # offset al eje global
        off=((base.year-EPOCH)*12+(base.month-1)) if base else 0
        o=ap.get("operativo") or []; e=ap.get("flujo_equity") or []; s=ap.get("saldo_credito") or []
        for m in range(max(len(o),len(e),len(s))):
            g=off+m
            if 0<=g<N:
                if m<len(o): oper[g]+=o[m]
                if m<len(e): equity[g]+=e[m]
                if m<len(s): saldo[g]+=s[m]
        filas.append({"Proyecto":mt.get("nombre",name),"Unidades":sum(x.get("und",0) or 0 for x in par.get("etapas",[])),
                      "Ventas":fmt_mm(pg["ventas"]),"Utilidad oper.":fmt_mm(pg["util_oper"]),
                      "Margen":f"{pg['margen_oper']*100:.1f}%","Crédito máx":fmt_mm(ap.get('credito_max',0) or 0)})
        n+=1
    return {"n":n,"unidades":int(und),"ventas":ventas,"util_oper":util,"udi":udi,"vpn":vpn,
            "margen":util/ventas if ventas else 0,
            "tir_ref":(tir_num/tir_den if tir_den else None),
            "tir_eq":_irr_anual(equity),
            "credito_max":max(saldo) if saldo else 0.0,"filas":filas}

def nuevo_proyecto():
    return {"meta":{"nombre":"Nuevo proyecto","ubicacion":"","zona":"","tipo":"No VIS","unidades":0,"moneda":"miles COP"},
        "areas":{"m2_vendibles":0.0,"m2_construidos":0.0,"lote_bruta":0.0,"lote_util":0.0},
        "etapas":[{"cod":1,"nom":"Etapa 1","und":50,"metodo":"$/m²","precio":5000000,"area_und":75.0,
                   "ventas_miles":0,"vmes":6,"frec":1,"emes":20,"efrec":1,"pe_pct":0.60,"fecha_inicio":"2026-01-01",
                   "sucesora":None,"desfase":0,"obra_offset":1,"dur_obra":24,"escrituracion":30}],
        "costos_pct":{"directos":0.55,"indirectos":0.18,"honorarios":0.08,"util_lote":0.045,"recon_codensa":0.002,
                      "hon_construccion":0.035,"hon_gerencia":0.03,"hon_ventas":0.015},
        "lote_bruto_miles":5000000,
        "cronograma":{"dur_obra":40,"moda_pert":24,"curva":"Gauss","rel_materiales":0.8,"ea_materiales":0.06,"ea_mano_obra":0.12},
        "financiero":{"renta":0.35,"split_cg":0.70,"pct_ci":0.30,"sep_und_miles":5000,"diferido_sep":4,
                      "tasa_credito_ea":0.155,"cobertura_cc":0.80,"monto_cc_pct":0.80,"tir_apalancada_ref":0.20,
                      "wacc":{"beta_us":1.29,"tax_us":13.3,"de_us":21.56,"tax_col":33.0,"de_col":233.3,"rf":0.12,
                              "rm":12.44,"rp":3.14,"inf_col":5.1,"inf_us":2.9,"tasa_d":15.0,"spread":10.43,"eq_w":30.0}}}

# ---------------- sidebar: proyecto + menú ----------------
with st.sidebar:
    if LOGO.exists(): st.image(str(LOGO), width=150)
    st.markdown("##### Proyecto")
    proys = listar()
    nombres = {p: cargar(p).get("meta",{}).get("nombre", p) for p in proys}
    opciones = (["➕ Nuevo proyecto"] + proys) if ES_EDITOR else (proys or ["➕ Nuevo proyecto"])
    if st.session_state.get("_pending_proj") in opciones:
        st.session_state["proj_sel"] = st.session_state.pop("_pending_proj")
    if "proj_sel" not in st.session_state or st.session_state["proj_sel"] not in opciones:
        st.session_state["proj_sel"] = next((o for o in opciones if o != "➕ Nuevo proyecto"), opciones[0])
    sel = st.selectbox("Seleccionar / crear", opciones, key="proj_sel", label_visibility="collapsed",
        format_func=lambda o: o if o == "➕ Nuevo proyecto" else nombres.get(o, o))
    if "par" not in st.session_state or st.session_state.get("sel") != sel:
        st.session_state.par = nuevo_proyecto() if sel == "➕ Nuevo proyecto" else cargar(sel)
        st.session_state.sel = sel
    par = st.session_state.par
    MENU=["Inicio","Proyectos activos","Datos del proyecto","Urbanístico","Cronograma","Ingresos",
          "Distribución costos","P&G","Reparto","Flujo de caja","Apalancamiento","Escenarios","Sensibilidad"]
    ICONS=["house-door","buildings","pencil-square","building","calendar3","cash-coin",
           "bar-chart-line","table","pie-chart","cash-stack","bank","bullseye","sliders"]
    seccion = option_menu(None, MENU, icons=ICONS, default_index=0, menu_icon="list",
        styles={"container":{"padding":"2px","background-color":"#F7F9FA"},
                "icon":{"color":TEAL,"font-size":"14px"},
                "nav-link":{"font-size":"13.5px","color":INK,"--hover-color":"#EAF0F2","margin":"1px 0"},
                "nav-link-selected":{"background-color":TEAL,"color":"white","font-weight":"600"}})

    if _secret("CLAVE_EQUIPO"):
        st.divider()
        if ES_EDITOR:
            st.caption("🟢 Modo **editor** — puedes ingresar datos.")
        else:
            st.caption("🔒 Modo **consulta** (solo lectura).")
            _ed = st.text_input("Clave de editor", type="password", key="_elevar_pwd",
                                label_visibility="collapsed", placeholder="Clave de editor…")
            if st.button("Activar edición", width="stretch"):
                if _ed and _ed == _secret("CLAVE_EDITOR"):
                    st.session_state["_rol"] = "editor"; st.rerun()
                else:
                    st.error("Clave de editor incorrecta.")
        if st.button("Cerrar sesión", width="stretch"):
            st.session_state.pop("_rol", None); st.rerun()

# ---------------- cálculo ----------------
R = calcular(copy.deepcopy(par)); pg=R["pyg"]; fl=R["flujo"]; meta=R["meta"]
ap=R.get("apalancamiento") or {}
# El crédito/VPN/TIR de decisión salen del waterfall CALIBRADO (apalancamiento), no del flujo_caja
# legacy. Si el waterfall corrió, sus cifras mandan en los KPIs.
if ap:
    fl={**fl, "credito_max":ap.get("credito_max",fl.get("credito_max")),
        "vpn_proyecto":ap.get("vpn_proyecto",fl.get("vpn_proyecto")),
        "intereses_total":ap.get("intereses_total",fl.get("intereses_total")),
        "tir_equity":ap.get("tir_equity"), "tir_apalancada_ref":ap.get("tir_apalancada_ref",fl.get("tir_apalancada_ref")),
        "credito_prom":ap.get("credito_prom")}

# ---------------- encabezado + KPIs ----------------
CONS=None
if seccion == "Proyectos activos":
    # --- KPIs CONSOLIDADOS del portafolio (suma de los proyectos listados) ---
    CONS = consolidado(tuple(listar()))
    hc1,hc2 = st.columns([1,9])
    if LOGO.exists(): hc1.image(str(LOGO), width=78)
    hc2.markdown("<h1>Portafolio CG — Consolidado</h1>", unsafe_allow_html=True)
    hc2.caption(f"CG Constructora · {CONS['n']} proyectos · {CONS['unidades']:,} unidades · suma del portafolio".replace(",", "."))
    st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
    k=st.columns(6)
    kpi(k[0],"Ventas totales", fmt_mm(CONS["ventas"]), "reconciliado", GREEN)
    kpi(k[1],"Utilidad operativa", fmt_mm(CONS["util_oper"]), fmt_pct(CONS["margen"]), GREEN)
    kpi(k[2],"UDI", fmt_mm(CONS["udi"]), "reconciliado", GREEN)
    kpi(k[3],"TIR apalancada (ref)", fmt_pct(CONS["tir_ref"]) if CONS["tir_ref"] is not None else "n/d", "ref · ponderada", MUTED)
    kpi(k[4],"VPN @WACC (suma)", fmt_mm(CONS["vpn"]), "preliminar", AMBER)
    kpi(k[5],"Crédito máx (pico)", fmt_mm(CONS["credito_max"]), "preliminar", AMBER)
    st.write("")
elif seccion != "Inicio":
    hc1,hc2 = st.columns([1,9])
    if LOGO.exists(): hc1.image(str(LOGO), width=78)
    hc2.markdown("<h1>Factibilidad de Proyectos</h1>", unsafe_allow_html=True)
    _badge = " · 🔒 datos reales" if es_real(sel) else " · cifras ilustrativas"
    hc2.caption(f"CG Constructora · {meta.get('nombre','')} · {meta.get('ubicacion','')} · {meta.get('unidades','')} unidades{_badge}")
    st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
    k=st.columns(6)
    kpi(k[0],"Ventas totales", fmt_mm(pg["ventas"]))
    kpi(k[1],"Utilidad operativa", fmt_mm(pg["util_oper"]), fmt_pct(pg["margen_oper"]), GREEN)
    kpi(k[2],"UDI", fmt_mm(pg["udi"]))
    if ap.get("fiducia_real"):                  # TIR/VPN auditados (FCL real de fiducia)
        kpi(k[3],"TIR proyecto", fmt_pct(ap.get("tir_proyecto")), "auditado · fiducia", GREEN)
        kpi(k[4],"VPN @TIO", fmt_mm(ap.get("vpn_proyecto")), "auditado", GREEN)
        kpi(k[5],"TIR socio CG", fmt_pct(ap.get("tir_equity")), "auditado", GREEN)
    else:
        kpi(k[3],"TIR apalancada (ref)", fmt_pct(fl.get("tir_apalancada_ref")), "modelo aprobado", MUTED)
        kpi(k[4],"VPN @WACC", fmt_mm(fl.get("vpn_proyecto")), "preliminar", AMBER)
        kpi(k[5],"Crédito máx", fmt_mm(fl.get("credito_max")), "preliminar", AMBER)
    st.write("")

# ============ INICIO (portada / bienvenida) ============
if seccion=="Inicio":
    pc1,pc2 = st.columns([1,5])
    if LOGO.exists(): pc1.image(str(LOGO), width=150)
    with pc2:
        st.markdown("<h1 style='font-size:2.3rem;margin:.2rem 0 0'>Evaluación Financiera de Proyectos</h1>", unsafe_allow_html=True)
        st.markdown("<div style='color:#6B7280;font-size:1.02rem;font-weight:600'>APEX ARCHITECT® · Modelo de factibilidad inmobiliaria · CG Constructora</div>", unsafe_allow_html=True)
    st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
    st.markdown(
        "Plataforma para evaluar la **prefactibilidad y factibilidad financiera** de los proyectos "
        "inmobiliarios de CG: portafolio multi‑etapa, hitos de venta y construcción, recaudo, costos "
        "por curva de obra, flujo de caja, apalancamiento (crédito constructor) e indicadores de "
        "rentabilidad (**TIR · VPN · WACC**). Todos los datos se ingresan en la plataforma."
    )
    st.markdown("#### Cómo empezar")
    s=st.columns(3)
    s[0].markdown('<div class="navcard"><h4>1 · Elige el proyecto</h4><ul>'
                  '<li>Abre <b>🏢 Proyectos activos</b></li>'
                  '<li>Navarra · Dominica · Torres de Campiñas</li>'
                  '<li>o crea uno nuevo desde el menú lateral</li></ul></div>', unsafe_allow_html=True)
    s[1].markdown('<div class="navcard"><h4>2 · Ingresa los datos</h4><ul>'
                  '<li>En <b>📝 Datos del proyecto</b></li>'
                  '<li>Generales · áreas · etapas · costos · recaudo</li>'
                  '<li>Todo se digita aquí (sin importar archivos)</li></ul></div>', unsafe_allow_html=True)
    s[2].markdown('<div class="navcard"><h4>3 · Revisa resultados</h4><ul>'
                  '<li>P&G · Flujo · Apalancamiento</li>'
                  '<li>Cronograma · Escenarios · Sensibilidad</li>'
                  '<li>Exporta el respaldo a Excel/JSON</li></ul></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("#### Módulos del modelo")
    g=st.columns(4)
    mods=[("🏢 Portafolio",["Proyectos activos","Datos del proyecto"]),
          ("📐 Definición",["Urbanístico (áreas e índices)","Cronograma de hitos","Ingresos (recaudo)"]),
          ("📊 Resultados",["Distribución de costos","P&G (Estado de Resultados)","Reparto CG / socio"]),
          ("💵 Flujo & Análisis",["Flujo de caja","Apalancamiento (crédito)","Escenarios","Sensibilidad"])]
    for i,(t,items) in enumerate(mods):
        li="".join(f"<li>{x}</li>" for x in items)
        g[i].markdown(f'<div class="navcard"><h4>{t}</h4><ul>{li}</ul></div>', unsafe_allow_html=True)
    st.write("")
    st.caption("APEX ARCHITECT® · modelo financiero CG Constructora · estándar FAST de modelación")

# ============ PROYECTOS ACTIVOS ============
if seccion=="Proyectos activos":
    st.markdown("### 🏢 Proyectos activos — CG Constructora")
    st.caption("Portafolio de proyectos en evaluación. **Abre** uno para trabajarlo, o crea uno nuevo desde el selector lateral.")
    _proys=listar()
    if not _proys:
        st.info("No hay proyectos. Crea uno con «➕ Nuevo proyecto» en el menú lateral.")
    else:
        gc=st.columns(3)
        for i,nombre in enumerate(_proys):
            p=cargar(nombre); mp=p.get("meta",{})
            und=sum(e.get("und",0) or 0 for e in p.get("etapas",[]))
            activo = (nombre==sel)
            with gc[i%3]:
                borde = TEAL if activo else "#E6E9EF"
                st.markdown(f'<div class="navcard" style="border:2px solid {borde}">'
                    f'<h4>{mp.get("nombre",nombre)} {"· abierto" if activo else ""}</h4>'
                    f'<div style="color:#6B7280;font-size:.84rem">{mp.get("ubicacion","")} · {mp.get("zona","")} · {mp.get("tipo","")}</div>'
                    f'<div style="margin-top:10px;font-weight:600;color:#13262B">{und} unidades · {len(p.get("etapas",[]))} etapas</div></div>',
                    unsafe_allow_html=True)
                if st.button("Abrir proyecto", key=f"open_{nombre}", width="stretch", disabled=activo):
                    st.session_state["_pending_proj"]=nombre; st.rerun()
        st.write("")
        st.markdown("##### Resumen financiero del portafolio")
        filas=list(CONS["filas"]) if CONS else []
        filas.append({"Proyecto":"— TOTAL —","Unidades":CONS["unidades"] if CONS else 0,
                      "Ventas":fmt_mm(CONS["ventas"] if CONS else 0),
                      "Utilidad oper.":fmt_mm(CONS["util_oper"] if CONS else 0),
                      "Margen":f"{(CONS['margen'] if CONS else 0)*100:.1f}%",
                      "Crédito máx":fmt_mm(CONS["credito_max"] if CONS else 0)})
        st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True)
        st.caption("Cifras en **millones COP**. **Ventas, utilidad y UDI** se suman (reconciliadas con las "
                   "prefactibilidades). **Crédito máx** calibrado (Navarra 0.87× del real) y **reintegros 1.00×**. "
                   "**VPN/TIR** quedan **preliminares** (falta el detalle de aportes/devoluciones de fiducia) → la "
                   "TIR mostrada es la **referencia del modelo aprobado**. *Dominica y Torres aún greenfield-2026.* "
                   + ("Datos reales (privados)." if _proys and es_real(_proys[0]) else "Cifras ilustrativas."))

# ============ DATOS DEL PROYECTO ============
if seccion=="Datos del proyecto" and not ES_EDITOR:
    st.markdown("### 📝 Datos del proyecto")
    st.info("🔒 **Modo solo lectura.** El ingreso de datos está restringido al editor del modelo. "
            "Activa la **clave de editor** en el panel lateral para modificar datos.")
    st.caption("El resto del tablero (resultados, flujo, apalancamiento, cronograma) está disponible para consulta.")
elif seccion=="Datos del proyecto":
    st.markdown("### 📝 Datos del proyecto")
    with st.expander("🔌 Diagnóstico de conexión a la nube (Supabase)"):
        d = probar_conexion()
        ok = d.get("refs_coinciden")
        st.write({
            "URL apunta al proyecto (ref)": d.get("url_ref"),
            "Clave: formato": d.get("formato"),
            "Clave: rol": d.get("role") or "—",
            "Clave: pertenece al proyecto (ref)": d.get("ref") or "— (formato nuevo, no verificable aquí)",
            "¿URL y clave del MISMO proyecto?": ("✅ sí" if ok else ("❌ NO — esa es la causa" if ok is False else "no verificable")),
            "Prueba de lectura": d.get("lectura"),
        })
        if d.get("refs_coinciden") is False:
            st.error("La clave es de OTRO proyecto distinto al de la URL. Copia la clave service_role "
                     "del MISMO proyecto que la URL (ref **"+str(d.get('url_ref'))+"**).")
    st.caption("Ingresa aquí toda la información del proyecto. **No se importan archivos** — todo se digita en la plataforma. "
               "Las demás secciones se calculan automáticamente.")
    with st.expander("1 · Datos generales", expanded=True):
        cg1=st.columns(3); meta_e=par.setdefault("meta",{})
        meta_e["nombre"]=cg1[0].text_input("Nombre del proyecto", meta_e.get("nombre",""))
        meta_e["ubicacion"]=cg1[1].text_input("Ubicación (ciudad)", meta_e.get("ubicacion",""))
        meta_e["zona"]=cg1[2].text_input("Zona / Barrio", meta_e.get("zona",""))
        cg2=st.columns(3); tipos=["No VIS","VIS","VIP","Mixto"]
        meta_e["tipo"]=cg2[0].selectbox("Tipo de vivienda", tipos, index=tipos.index(meta_e["tipo"]) if meta_e.get("tipo") in tipos else 0)
        _raiz=next((e for e in par["etapas"] if not e.get("sucesora")), (par["etapas"][0] if par["etapas"] else None))
        if _raiz is not None:
            try: _fi=date.fromisoformat(str(_raiz.get("fecha_inicio") or "2026-01-01")[:10])
            except Exception: _fi=date(2026,1,1)
            _raiz["fecha_inicio"]=str(cg2[1].date_input("Fecha de inicio de ventas (etapa raíz)", value=_fi, key=f"fi_{sel}"))
        _tot_und=int(sum(e.get("und",0) or 0 for e in par.get("etapas",[])))
        cg2[2].metric("Unidades totales", _tot_und, help="Suma automática de las unidades por etapa. Ajústalas en «3 · Etapas».")
    with st.expander("2 · Áreas y lote (m²)", expanded=True):
        a=par.setdefault("areas",{}); ac=st.columns(4)
        a["m2_vendibles"]=ac[0].number_input("Área vendible total", value=float(a.get("m2_vendibles",0)), step=100.0, format="%.0f")
        a["m2_construidos"]=ac[1].number_input("Área construida total", value=float(a.get("m2_construidos",0)), step=100.0, format="%.0f")
        a["lote_bruta"]=ac[2].number_input("Área lote (bruta)", value=float(a.get("lote_bruta",0)), step=100.0, format="%.0f")
        a["lote_util"]=ac[3].number_input("Área lote (útil)", value=float(a.get("lote_util",0)), step=100.0, format="%.0f")
    with st.expander("3 · Etapas, producto y ventas", expanded=True):
        st.caption("✏️ Ajusta las **unidades** de cada etapa en la columna *Unidades*. Cada etapa abre ventas cuando su "
                   "**sucesora** llega al equilibrio; la raíz no tiene sucesora. **Precio**: $/m² (× área/und) o $/und. "
                   "**Ritmo de ventas** (Vtas/mes·Frec) y **ritmo de entregas** (Entr/mes·Frec ent) mueven los hitos y el recaudo.")
        cols=["cod","nom","und","metodo","precio","area_und","vmes","frec","emes","efrec","pe_pct","sucesora","desfase","dur_obra","escrituracion"]
        df_et=pd.DataFrame(par["etapas"]).reindex(columns=cols)
        if "metodo" in df_et: df_et["metodo"]=df_et["metodo"].fillna("$/m²")
        edited=st.data_editor(df_et, num_rows="dynamic", width="stretch", key=f"editor_{sel}",
            column_config={
                "cod": st.column_config.NumberColumn("Cód", format="%d", width="small"),
                "nom": st.column_config.TextColumn("Etapa"),
                "und": st.column_config.NumberColumn("Unidades", format="%d"),
                "metodo": st.column_config.SelectboxColumn("Método precio", options=["$/m²","$/und"], width="small"),
                "precio": st.column_config.NumberColumn("Precio (COP)", format="%d"),
                "area_und": st.column_config.NumberColumn("Área/und (m²)", format="%.1f"),
                "vmes": st.column_config.NumberColumn("Vtas/mes", format="%d", help="Ritmo de ventas: unidades vendidas por evento"),
                "frec": st.column_config.NumberColumn("Frec (m)", format="%d", help="Ritmo de ventas: cada cuántos meses"),
                "emes": st.column_config.NumberColumn("Entr/mes", format="%d", help="Ritmo de entregas: unidades entregadas por evento (desde la escrituración)"),
                "efrec": st.column_config.NumberColumn("Frec ent (m)", format="%d", help="Ritmo de entregas: cada cuántos meses"),
                "pe_pct": st.column_config.NumberColumn("% Equilibrio", format="%.2f", min_value=0.0, max_value=1.0),
                "sucesora": st.column_config.NumberColumn("Sucesora", format="%d"),
                "desfase": st.column_config.NumberColumn("Desfase (m)", format="%d"),
                "dur_obra": st.column_config.NumberColumn("Dur. obra (m)", format="%d"),
                "escrituracion": st.column_config.NumberColumn("Escrit. (m)", format="%d")})
        def _i(v):
            try: return int(v) if v is not None and not pd.isna(v) else None
            except Exception: return None
        def _f(v):
            try: return float(v) if v is not None and not pd.isna(v) else None
            except Exception: return None
        recs=[]
        for r in edited.to_dict("records"):
            if (r.get("nom") in (None,"")) and not r.get("und"): continue
            und=_i(r.get("und")) or 0; metodo=r.get("metodo") or "$/m²"
            precio=_f(r.get("precio")) or 0; area=_f(r.get("area_und")) or 0
            ventas_miles=und*precio*area/1000 if metodo=="$/m²" else und*precio/1000
            recs.append({"cod":_i(r.get("cod")),"nom":r.get("nom") or "Etapa","und":und,"metodo":metodo,
                "precio":precio,"area_und":area,"ventas_miles":ventas_miles,"vmes":_i(r.get("vmes")) or 6,
                "frec":_i(r.get("frec")) or 1,"emes":_i(r.get("emes")),"efrec":_i(r.get("efrec")) or 1,
                "pe_pct":_f(r.get("pe_pct")) or 0.60,"sucesora":_i(r.get("sucesora")),
                "desfase":_i(r.get("desfase")) or 0,"obra_offset":1,"dur_obra":_i(r.get("dur_obra")) or 24,
                "escrituracion":_i(r.get("escrituracion")) or 30})
        for idx,r in enumerate(recs):
            if not r["cod"]: r["cod"]=idx+1
        if _raiz is not None:
            for r in recs:
                if r.get("sucesora") is None: r["fecha_inicio"]=_raiz["fecha_inicio"]
        if recs:
            st.session_state.par["etapas"]=recs
            st.session_state.par.setdefault("meta",{})["unidades"]=sum(r["und"] for r in recs)
        tv=sum(r["ventas_miles"] for r in recs)
        st.success(f"**{len(recs)} etapas · {sum(r['und'] for r in recs)} unidades · ventas totales {tv/1000:,.0f} M**")
    with st.expander("4 · Costos"):
        c=par["costos_pct"]; cc1=st.columns(3)
        c["directos"]=cc1[0].slider("Costo directo (% ventas)", 0.30, 0.70, float(c["directos"]), 0.001)
        c["indirectos"]=cc1[1].slider("Costos indirectos (% ventas)", 0.05, 0.30, float(c["indirectos"]), 0.001)
        c["honorarios"]=cc1[2].slider("Honorarios (% ventas)", 0.05, 0.12, float(c["honorarios"]), 0.001)
        cc2=st.columns(3)
        par["lote_bruto_miles"]=cc2[0].number_input("Costo del lote (miles COP)", value=float(par["lote_bruto_miles"]), step=500_000.0, format="%.0f")
        cr=par.setdefault("cronograma",{})
        cr["dur_obra"]=cc2[1].number_input("Duración de obra (meses, global)", value=int(cr.get("dur_obra",40)), step=1)
        c["util_lote"]=cc2[2].slider("Utilidad del lote (% ventas)", 0.0, 0.10, float(c.get("util_lote",0.045)), 0.001)
    with st.expander("5 · Recaudo (condiciones de venta)"):
        f=par["financiero"]; rc1=st.columns(3)
        f["sep_und_miles"]=rc1[0].number_input("Separación por unidad (miles COP)", value=float(f.get("sep_und_miles",5000)), step=500.0, format="%.0f")
        f["diferido_sep"]=rc1[1].number_input("Diferido separación (meses)", value=int(f.get("diferido_sep",4)), step=1)
        f["pct_ci"]=rc1[2].slider("% Cuota inicial", 0.10, 0.50, float(f.get("pct_ci",0.30)), 0.01)
    with st.expander("6 · Financiero (avanzado — valores por defecto CG)"):
        f=par["financiero"]; fc1=st.columns(3)
        f["split_cg"]=fc1[0].slider("Reparto utilidad CG", 0.0, 1.0, float(f.get("split_cg",0.70)), 0.05)
        f["tasa_credito_ea"]=fc1[1].slider("Tasa crédito constructor (E.A.)", 0.08, 0.25, float(f.get("tasa_credito_ea",0.155)), 0.005)
        f["cobertura_cc"]=fc1[2].slider("Cobertura crédito (% obra)", 0.50, 0.90, float(f.get("cobertura_cc",0.80)), 0.05)
        fc2=st.columns(3)
        f["renta"]=fc2[0].slider("Provisión renta", 0.0, 0.40, float(f.get("renta",0.35)), 0.01)
        f["tir_apalancada_ref"]=fc2[1].number_input("TIR apalancada de referencia", value=float(f.get("tir_apalancada_ref",0.20)), step=0.01, format="%.4f")

# ============ P&G ============
if seccion=="P&G":
    df=pd.DataFrame([
        ("Ingresos por ventas",pg["ventas"]),("(+) Reconocimiento Codensa",pg["recon_codensa"]),
        ("(-) Costo lote",-pg["costo_lote"]),("(-) Costos directos",-pg["directos"]),
        ("(-) Costos indirectos",-pg["indirectos"]),("(-) Honorarios",-pg["honorarios"]),
        ("UTILIDAD OPERATIVA",pg["util_oper"]),("(-) Provisión renta",-pg["renta"]),("UDI",pg["udi"]),
    ],columns=["Concepto","Miles COP"]); df["% ventas"]=df["Miles COP"]/pg["ventas"] if pg["ventas"] else 0
    st.dataframe(df.style.format({"Miles COP":"{:,.0f}","% ventas":"{:.1%}"}), width="stretch", hide_index=True)
    costo_total=pg["costo_lote"]+pg["directos"]+pg["indirectos"]
    st.markdown("**Indicadores del Estado de Resultados**")
    e=st.columns(4)
    kpi(e[0],"Margen de contribución",fmt_mm(pg["util_oper"]),fmt_pct(pg["margen_oper"])+" /ventas",GREEN)
    kpi(e[1],"Margen sobre costo",fmt_pct(pg["util_oper"]/costo_total if costo_total else 0))
    kpi(e[2],"Incidencia directos",fmt_pct(pg["directos"]/costo_total if costo_total else 0))
    kpi(e[3],"Incidencia indirectos+lote",fmt_pct((pg["indirectos"]+pg["costo_lote"])/costo_total if costo_total else 0))

# ============ REPARTO ============
if seccion=="Reparto":
    fig=go.Figure(data=[go.Pie(labels=["CG","Socio"],values=[pg["cg"],pg["socio"]],hole=.55,marker_colors=[TEAL,AMBER])])
    fig.update_layout(title="Distribución de resultados",height=380); st.plotly_chart(fig, width="stretch")

# ============ DISTRIBUCIÓN COSTOS ============
if seccion=="Distribución costos":
    d=R["distribucion"]
    st.plotly_chart(_charts.curva_obra_s(d["escalada"], d["acumulada"]), width="stretch")
    st.caption(f"Curva S de avance de obra: barras = costo directo mensual (campana de Gauss); línea ámbar = "
               f"avance acumulado en %. Pico de obra: mes {d['pico_mes']}.")

# ============ FLUJO DE CAJA ============
if seccion=="Flujo de caja":
    _saldo=(R.get("apalancamiento") or {}).get("saldo_credito") or fl.get("saldo_credito")
    st.plotly_chart(_charts.flujo_caja_waterfall(fl["flujo"], fl["acumulado"], _saldo), width="stretch")
    st.caption("Barras = flujo neto mensual (🟢 caja positiva / 🔴 requiere financiación) · línea oscura = caja "
               "acumulada · línea ámbar punteada = saldo de crédito constructor · anotación = mes de exposición máxima.")
    cc=st.columns(4)
    kpi(cc[0],"TIR proyecto (no apal.)",fmt_pct(fl["tir_proyecto"])); kpi(cc[1],"Crédito constructor máx",fmt_mm(fl["credito_max"]))
    kpi(cc[2],"Necesidad máx de caja",fmt_mm(fl["max_caja"])); kpi(cc[3],"Intereses (prelim.)",fmt_mm(fl["intereses_total"]))

# ============ APALANCAMIENTO ============
if seccion=="Apalancamiento":
    a=R.get("apalancamiento",{})
    if not a or not a.get("operativo"):
        st.info("Completa los datos del proyecto para ver el apalancamiento.")
    else:
        op=a["operativo"]; sc=a["saldo_credito"]; ac=a["acumulado"]; an=a.get("anual",{})
        if an:
            yrs=sorted(an); cum=[]; s=0.0
            for y in yrs: s+=an[y]; cum.append(s)
            fig=go.Figure(); fig.add_bar(x=[str(y) for y in yrs],y=[an[y] for y in yrs],name="Flujo operativo",marker_color=TEAL)
            fig.add_scatter(x=[str(y) for y in yrs],y=cum,name="Acumulado",line=dict(color=INK,width=3))
            fig.update_layout(title="Flujo de caja consolidado del portafolio (anual)",height=400); st.plotly_chart(fig, width="stretch")
        if a.get("fiducia_real"):
            cc=st.columns(4)
            kpi(cc[0],"TIR proyecto",fmt_pct(a.get("tir_proyecto")),"auditado · fiducia",GREEN)
            kpi(cc[1],"VPN proyecto @TIO",fmt_mm(a.get("vpn_proyecto")),f"TIO {fmt_pct(a.get('tio'))}",GREEN)
            kpi(cc[2],"TIR socio CG",fmt_pct(a.get("tir_equity")),"auditado",GREEN)
            kpi(cc[3],"VPN socio CG",fmt_mm(a.get("vpn_socio")) if a.get("vpn_socio") is not None else "n/d","auditado",GREEN)
            fp=a.get("fcl_proyecto_anual"); fs=a.get("fcl_socio_anual"); y0=a.get("anio0_fiducia")
            if fp and y0:
                st.markdown("##### Flujo de caja libre (auditado · fiducia)")
                cols=[str(y0+i) for i in range(len(fp))]
                dff={"Concepto":["FCL Proyecto","FCL Socio CG"]}
                for i,c in enumerate(cols):
                    dff[c]=[round(fp[i]/1000), round((fs[i] if fs and i<len(fs) else 0)/1000)]
                st.dataframe(pd.DataFrame(dff), width="stretch", hide_index=True)
                st.caption("Cifras en millones COP. FCL = Retornos + Devoluciones de aportes − Aportes "
                           "(hoja *FC LOTE CG -V2K*). TIR/VPN reproducen exacto el modelo aprobado.")
        c1=st.columns(4)
        kpi(c1[0],"TIR proyecto",fmt_pct(a.get("tir_proyecto")))
        kpi(c1[1],"VPN",fmt_mm(a["vpn_proyecto"]) if a.get("vpn_proyecto") is not None else "n/d")
        kpi(c1[2],"WACC E.A.",fmt_pct(a.get("wacc")))
        pb=a.get("payback_mes"); kpi(c1[3],"Payback (caja+)",(f"{pb} meses" if pb else "—"))
        c2=st.columns(4)
        kpi(c2[0],"Crédito constructor máx",fmt_mm(a["credito_max"])); kpi(c2[1],"Necesidad máx de caja",fmt_mm(a["max_necesidad_caja"]))
        kpi(c2[2],"Valor financiable",fmt_mm(a["valor_financiable"])); kpi(c2[3],"Intereses",fmt_mm(a["intereses_total"]))
        n=max([i for i,v in enumerate(op) if abs(v)>1],default=0)+2; m=list(range(1,n+1))
        fig2=go.Figure(); fig2.add_scatter(x=m,y=ac[:n],name="Operativo acumulado",line=dict(color=INK,width=2))
        fig2.add_scatter(x=m,y=sc[:n],name="Saldo crédito constructor",line=dict(color=AMBER,dash="dot"))
        fig2.update_layout(title="Mensual: caja acumulada y saldo de crédito",height=340,xaxis_title="Mes"); st.plotly_chart(fig2, width="stretch")
        st.caption("Crédito constructor: cobertura (~80%) del costo de obra, amortizado con las subrogaciones; los aportes cubren el resto.")

# ============ CRONOGRAMA ============
if seccion=="Cronograma":
    h=R.get("hitos",{})
    if not h:
        st.info("Completa los datos de etapas (en 📝 Datos del proyecto) para ver el cronograma.")
    else:
        st.markdown("#### Hitos por etapa")
        rows=[{"Etapa":h[c]["nombre"],"Und":h[c]["unidades"],"Inicio Ventas":h[c]["IV"],"Pto Equilibrio":h[c]["PE"],
               "Fin Ventas":h[c]["FV"],"Inicio Constr.":h[c].get("IC"),"Fin Constr.":h[c].get("FC")} for c in sorted(h)]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        st.plotly_chart(_charts.gantt_etapas(h), width="stretch")
        st.caption("Barras: 🟦 período de **ventas** · 🟧 período de **construcción** por etapa. "
                   "Marcas: ◆ Punto de Equilibrio · ⚫ Fin de Ventas.")

        # -------- Ritmo de ventas y entregas (estilo R.ventas) --------
        st.markdown("#### Ritmo de ventas y entregas")
        st.caption("El ritmo de ventas y de entregas **mueve los números**: de aquí salen el equilibrio, el fin de "
                   "ventas y el recaudo. Se ajusta por etapa en 📝 Datos del proyecto.")
        rec=[]
        for i,e in enumerate(par.get("etapas",[])):
            und=e.get("und",0) or 0
            rec.append({"No.":i+1,"Proyecto / Etapa":e.get("nom","") or f"Etapa {i+1}","Und":und,
                        "Ventas · Cant":e.get("vmes"),"Ventas · Frec":e.get("frec"),
                        "Entregas · Cant":e.get("emes") or und,"Entregas · Frec":e.get("efrec",1)})
        st.dataframe(pd.DataFrame(rec), width="stretch", hide_index=True)

        # -------- Proyección de ventas y entregas (curva de absorción) --------
        pe=R.get("recaudo",{}).get("por_etapa",{})
        if pe:
            st.markdown("#### Proyección de ventas y entregas")
            HZ=180; base=min(h[c]["IV"] for c in h)
            def _addm(d,n):
                y=d.year+(d.month-1+n)//12; mo=(d.month-1+n)%12+1; return date(y,mo,1)
            ventas_g={}; entregas_t=[0.0]*HZ; maxm=0
            for cod,d in pe.items():
                off=d.get("offset",0); g=[0.0]*HZ
                for m,u in enumerate(d.get("ventas",[])):
                    if u and 0<=off+m<HZ: g[off+m]+=u; maxm=max(maxm,off+m)
                ventas_g[cod]=g
                for m,u in enumerate(d.get("entregas",[])):
                    if u and 0<=off+m<HZ: entregas_t[off+m]+=u; maxm=max(maxm,off+m)
            n=min(HZ,maxm+2); xd=[_addm(base,i) for i in range(n)]
            pal=[TEAL,AMBER,GREEN,"#7B61FF","#E2574C","#00A5A5"]
            tot_sold=[sum(ventas_g[c][i] for c in ventas_g) for i in range(n)]
            cum=[]; run=0
            for v in tot_sold: run+=v; cum.append(run)
            fig2=go.Figure()
            for j,cod in enumerate(sorted(ventas_g)):
                fig2.add_bar(x=xd,y=ventas_g[cod][:n],name=h.get(cod,{}).get("nombre",f"Etapa {cod}"),marker_color=pal[j%len(pal)])
            fig2.add_scatter(x=xd,y=entregas_t[:n],name="Entregas/mes",mode="lines",line=dict(color=RED,width=2.5))
            fig2.add_scatter(x=xd,y=cum,name="Acumulado vendido",mode="lines",yaxis="y2",line=dict(color=INK,width=2,dash="dot"))
            fig2.update_layout(barmode="stack",title="Unidades vendidas por mes (por etapa) · entregas · acumulado",
                height=440,xaxis_title="",yaxis=dict(title="Unidades / mes"),
                yaxis2=dict(title="Acum. vendido",overlaying="y",side="right",showgrid=False),
                legend=dict(orientation="h",y=-0.18)); st.plotly_chart(fig2, width="stretch")
            und_tot=sum(e.get("und",0) or 0 for e in par.get("etapas",[]))
            ve=[i for i,v in enumerate(tot_sold) if v>0]; en=[i for i,v in enumerate(entregas_t[:n]) if v>0]
            cc=st.columns(3)
            kpi(cc[0],"Unidades totales", f"{und_tot:,}".replace(",", "."))
            kpi(cc[1],"Meses con ventas", str((ve[-1]-ve[0]+1) if ve else 0))
            kpi(cc[2],"Meses con entregas", str((en[-1]-en[0]+1) if en else 0))
            st.caption("Barras = unidades vendidas por mes y etapa · línea roja = entregas/mes · punteada = acumulado vendido (curva de absorción).")

# ============ INGRESOS ============
if seccion=="Ingresos":
    rc=R.get("recaudo",{})
    if not rc or not rc.get("total"):
        st.info("Completa los datos de etapas para ver el recaudo de ingresos.")
    else:
        sepr=rc["separacion"]; cir=rc["cuota_inicial"]; subr=rc["subrogacion"]; tot=rc["total"]
        st.plotly_chart(_charts.recaudo_stacked(sepr, cir, subr), width="stretch")
        cc=st.columns(4)
        kpi(cc[0],"Separación",fmt_mm(sum(sepr))); kpi(cc[1],"Cuota inicial",fmt_mm(sum(cir)))
        kpi(cc[2],"Subrogación",fmt_mm(sum(subr))); kpi(cc[3],"Recaudo total",fmt_mm(sum(tot)))
        st.caption("Separación diferida + cuota inicial (venta → escrituración) + subrogación (a la entrega).")

# ============ ESCENARIOS ============
if seccion=="Escenarios":
    esc=R["escenarios"]
    fig=go.Figure(data=[go.Bar(x=list(esc.keys()),y=[v["util_oper"] for v in esc.values()],
        marker_color=[TEAL,GREEN,RED],text=[fmt_pct(v["margen"]) for v in esc.values()],textposition="outside")])
    fig.update_layout(title="Utilidad operativa por escenario",height=420); st.plotly_chart(fig, width="stretch")
    st.caption("Optimista: +5% precio, −2% costo · Pesimista: −10% precio, +5% costo")

# ============ SENSIBILIDAD ============
if seccion=="Sensibilidad":
    s=R["sensibilidades"]; it=sorted(s.items(),key=lambda kv:kv[1])
    fig=go.Figure(data=[go.Bar(y=[k for k,_ in it],x=[v for _,v in it],orientation="h",
        marker_color=[GREEN if v>=0 else RED for _,v in it])])
    fig.update_layout(title="Tornado — impacto en utilidad operativa (miles COP)",height=380); st.plotly_chart(fig, width="stretch")

# ============ URBANÍSTICO ============
if seccion=="Urbanístico":
    u=R["urbanistico"]
    df=pd.DataFrame([
        ("Área lote bruta (m²)",u["lote_bruta"]),("Área lote útil (m²)",u["lote_util"]),
        ("Ratio bruta/útil",u["ratio_bruta_util"]),("Área construida (m²)",u["area_construida"]),
        ("Área vendible (m²)",u["area_vendible"]),("Índice de construcción",u["indice_construccion"]),
        ("Aprovechamiento",u["aprovechamiento"]),("Densidad (und/ha)",u["densidad_und_ha"]),
        ("Precio venta /m² (COP)",u["precio_m2_vend"]),("Costo directo /m² const (COP)",u["costo_dir_m2_const"]),
    ],columns=["Indicador","Valor"])
    st.dataframe(df.style.format({"Valor":"{:,.2f}"}, na_rep="—"), width="stretch", hide_index=True)

# ---------------- acciones (solo dentro de un proyecto, no en Inicio) ----------------
if seccion != "Inicio":
    st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
    a1,a2=st.columns(2)
    with a1:
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as xl:
            pd.DataFrame([{"Concepto":"Ventas","Miles COP":pg["ventas"]},{"Concepto":"Utilidad operativa","Miles COP":pg["util_oper"]},
                {"Concepto":"UDI","Miles COP":pg["udi"]},{"Concepto":"CG","Miles COP":pg["cg"]},
                {"Concepto":"Socio","Miles COP":pg["socio"]},{"Concepto":"Credito max","Miles COP":fl["credito_max"]}]).to_excel(xl,sheet_name="Resumen",index=False)
            pd.DataFrame({"Mes":range(1,len(fl["flujo"])+1),"Flujo":fl["flujo"],"Acumulado":fl["acumulado"],"SaldoCredito":fl["saldo_credito"]}).to_excel(xl,sheet_name="Flujo",index=False)
        st.download_button("📥 Exportar resultados a Excel", buf.getvalue(),
            file_name=f"Factibilidad_{meta.get('nombre','proyecto')}_{date.today():%Y%m%d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with a2:
        if ES_EDITOR:
            par["_fecha"]=str(date.today())
            st.download_button("💾 Descargar proyecto (.json, respaldo)",
                json.dumps(par,ensure_ascii=False,indent=2).encode("utf-8"),
                file_name=f"{meta.get('nombre','proyecto')}.json", mime="application/json",
                help="Respaldo de tu proyecto para guardarlo localmente. No es fuente de entrada.")
    # Guardar en la nube (compartir con el equipo) — solo editor y solo si hay Supabase
    if ES_EDITOR and usando_supabase() and sel and sel != "➕ Nuevo proyecto":
        if st.button("☁️ Guardar en la nube (compartir con el equipo)", type="primary", width="stretch"):
            try:
                guardar(sel, par, nombre=meta.get("nombre", sel), es_real_flag=es_real(sel),
                        by=_secret("CLAVE_EDITOR") and "editor")
                st.cache_data.clear()        # refresca el consolidado
                st.success("Guardado. El equipo verá estos datos al recargar.")
            except Exception as e:
                st.error(f"No se pudo guardar en la nube: {e}")
    elif ES_EDITOR and not usando_supabase():
        st.caption("ℹ️ Sin base de datos compartida configurada: los cambios viven en tu sesión. "
                   "Configura Supabase (SUPABASE_URL/SUPABASE_KEY) para compartir con el equipo.")
_origen = "☁️ nube (compartido)" if usando_supabase() else "💾 local"
_diag = "" if usando_supabase() else f" · ⚠️ {diagnostico()}"
st.caption(f"Aplicativo v2.18.1 · motor v{ENGINE_V} · datos: {_origen}{_diag} · CG Constructora")
