# -*- coding: utf-8 -*-
"""
Aplicativo de Prefactibilidad / Factibilidad — CG Constructora.
Capa de presentación (Streamlit). NO contiene lógica financiera: usa cg_engine/ (fuente única).
Navegación por menú lateral con tablero de Inicio. Data 100% en plataforma. v2.0.0
"""
import json, io, copy
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from streamlit_option_menu import option_menu
from cg_engine import calcular, __version__ as ENGINE_V
from cg_engine import evm as _evm   # Valor Ganado (EVM)
import charts as _charts   # gráficos financieros pro (marca CG)
import navarra_data as _nav   # datos operativos del comité (Monitor de Ejecución)

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

def _sem(v, amarillo, verde, invertir=False):
    """Color de semáforo (verde/ámbar/rojo) por umbral. `invertir`=True cuando menor es mejor (payback)."""
    if v is None: return MUTED
    if invertir:
        return GREEN if v <= verde else (AMBER if v <= amarillo else RED)
    return GREEN if v >= verde else (AMBER if v >= amarillo else RED)
_SEMLAB = {GREEN: "● saludable", AMBER: "● atención", RED: "● en riesgo", MUTED: "—"}

_SEV={"critica":("#FEF2F2","#FCA5A5","#991B1B","🔴","CRÍTICA"),
      "importante":("#FFFBEB","#FDE68A","#92400E","🟡","IMPORTANTE"),
      "info":("#F0FDF4","#BBF7D0","#14532D","✅","INFO")}
def render_alertas(alertas, solo_activas=True, modulo=None, max_items=None):
    """Panel de alertas reutilizable (marca CG). Filtra por estado/módulo."""
    fs=[a for a in alertas if (not solo_activas or a["estado"]=="Activa")
        and (modulo is None or a["modulo_origen"]==modulo)]
    if max_items: fs=fs[:max_items]
    if not fs: return
    for a in fs:
        bg,bd,tx,ic,lb=_SEV.get(a["severidad"], _SEV["info"])
        st.markdown(
            f'<div style="background:{bg};border:1px solid {bd};border-left:4px solid {bd};'
            f'border-radius:8px;padding:11px 15px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div style="flex:1;"><div style="font-size:12.5px;font-weight:700;color:{tx};">{ic} {a["titulo"]}</div>'
            f'<div style="font-size:11.5px;color:{tx};opacity:.85;line-height:1.5;margin-top:3px;">{a["descripcion"]}</div>'
            f'<div style="font-size:10px;color:{tx};opacity:.6;margin-top:6px;">📋 {a["modulo_origen"]} · 🗓 {a["fecha_reporte"]} · 👤 {a["responsable"]}</div></div>'
            f'<span style="background:{bd};color:{tx};font-size:9px;font-weight:800;padding:2px 8px;'
            f'border-radius:99px;margin-left:12px;white-space:nowrap;">{lb}</span></div></div>',
            unsafe_allow_html=True)
# Almacenamiento: Supabase si hay credenciales, si no archivos locales (capa storage.py)
from storage import listar, cargar, es_real, guardar, usando_supabase, diagnostico, probar_conexion

# ---------------- control de acceso (Fase 1) ----------------
def _secret(nombre):
    # st.secrets (Cloud/local) y, si no está, variable de entorno (Azure App Service / contenedores).
    try:
        v = st.secrets.get(nombre, "") if hasattr(st, "secrets") else ""
        if v:
            return str(v)
    except Exception:
        pass
    import os
    return str(os.environ.get(nombre, ""))

def _ms_user():
    """Email del usuario autenticado por Azure App Service Easy Auth (Entra ID), si la app corre
    detrás de él. App Service inyecta el header X-MS-CLIENT-PRINCIPAL-NAME en cada request autenticado."""
    try:
        h = st.context.headers
        return (h.get("X-MS-CLIENT-PRINCIPAL-NAME") or h.get("x-ms-client-principal-name")) or None
    except Exception:
        return None

def gate():
    """Control de acceso. Con CLAVE_EQUIPO exige clave para ver; CLAVE_EDITOR habilita edición.
    Si corre detrás de Azure Easy Auth (Entra), el login de Microsoft ya autentica → viewer sin clave
    (la de editor sigue elevando). **Seguridad:** si NO hay clave ni SSO configurados, NO se abre en
    modo editor (evita app pública editable sin contraseña) → cae a modo LECTURA con aviso.
    Devuelve 'editor' | 'viewer'."""
    clave_eq = _secret("CLAVE_EQUIPO"); clave_ed = _secret("CLAVE_EDITOR")
    ms = _ms_user()
    if ms:                                   # autenticado por Microsoft (Entra) — sin fricción de clave
        st.session_state["_ms_user"] = ms
        if st.session_state.get("_rol") not in ("viewer", "editor"):
            st.session_state["_rol"] = "viewer"
        return st.session_state["_rol"]
    if not clave_eq:
        # Sin clave y sin SSO: NO permitir edición pública. Solo lectura + bandera de aviso.
        # Para editar: configura CLAVE_EQUIPO/CLAVE_EDITOR en los secretos o usa el SSO de Microsoft.
        st.session_state["_rol"] = "viewer"; st.session_state["_sin_clave"] = True
        return "viewer"
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
if st.session_state.get("_sin_clave"):
    st.warning("🔒 **Modo solo lectura.** No hay clave de acceso configurada, así que la edición de datos "
               "está deshabilitada por seguridad. Para ingresar datos, define **CLAVE_EQUIPO** y **CLAVE_EDITOR** "
               "en los secretos del despliegue (o activa el acceso de Microsoft).")

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

@st.cache_data(show_spinner=False)
def puntos_portafolio(_keys):
    """Puntos del gráfico de burbujas: un dict por proyecto {nombre, tir, margen, ventas, tipo, und}.
    _keys = tuple(listar()) → invalida el caché igual que consolidado()."""
    pts=[]
    for name in _keys:
        try:
            par=cargar(name); R=calcular(copy.deepcopy(par))
        except Exception:
            continue
        pg=R["pyg"]; ap=R.get("apalancamiento") or {}; mt=R["meta"]
        tir=ap.get("tir_proyecto")
        if tir is None: tir=ap.get("tir_apalancada_ref")
        pts.append({"nombre":mt.get("nombre",name),"tir":tir,"margen":pg.get("margen_oper"),
                    "ventas":pg.get("ventas"),"tipo":mt.get("tipo","No VIS"),
                    "und":sum(e.get("und",0) or 0 for e in par.get("etapas",[]))})
    return pts

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
                      "wacc":{"beta_us":1.29,"kd_us":9.335,"tax_us":13.3,"de_us":21.56,"tax_col":33.0,"de_col":233.3,"rf":0.12,
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
    # --- navegación en 3 capas (Tablero / Factibilidad / Seguimiento) ---
    # Cada capa agrupa secciones EXISTENTES (sin renombrar). Las hojas "K." son el motor (engine), no menú.
    GRUPOS = {
        "Tablero": [("Inicio","house-door"),("Cockpit","speedometer2"),
                    ("Proyectos activos","buildings"),("Portafolio (burbujas)","graph-up")],
        "Factibilidad": [("Datos del proyecto","pencil-square"),("Urbanístico","building"),("Cronograma","calendar3"),
                         ("Ingresos","cash-coin"),("Distribución costos","bar-chart-line"),
                         ("P&G","table"),("Reparto","pie-chart"),("Flujo de caja","cash-stack"),
                         ("Costo de capital","percent"),("Apalancamiento","bank"),
                         ("Escenarios","bullseye"),("Monte Carlo","dice-5"),("Sensibilidad","sliders")],
        "Seguimiento": [("Monitor de ejecución","clipboard-data"),("Valor Ganado","graph-up-arrow")],
    }
    _AREA_ICON={"Tablero":"grid-1x2-fill","Factibilidad":"calculator","Seguimiento":"activity"}
    _smenu={"container":{"padding":"2px","background-color":"#F7F9FA"},
            "icon":{"color":TEAL,"font-size":"14px"},
            "nav-link":{"font-size":"13.5px","color":INK,"--hover-color":"#EAF0F2","margin":"1px 0"},
            "nav-link-selected":{"background-color":TEAL,"color":"white","font-weight":"600"}}
    area = option_menu(None, list(GRUPOS.keys()), icons=[_AREA_ICON[a] for a in GRUPOS], default_index=0,
        menu_icon="list", key="area_menu",
        styles={**_smenu, "nav-link":{**_smenu["nav-link"],"font-size":"13px","font-weight":"600"},
                "nav-link-selected":{"background-color":INK,"color":"white","font-weight":"700"}})
    _secs=GRUPOS[area]
    seccion = option_menu(None, [s[0] for s in _secs], icons=[s[1] for s in _secs], default_index=0,
        menu_icon="list", key=f"sub_{area}", styles=_smenu)

    if _secret("CLAVE_EQUIPO") or st.session_state.get("_ms_user"):
        st.divider()
        if st.session_state.get("_ms_user"):
            st.caption(f"👤 Conectado como **{st.session_state['_ms_user']}** (Microsoft)")
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
elif seccion not in ("Inicio","Cockpit","Portafolio (burbujas)"):
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
        st.markdown("<div style='color:#6B7280;font-size:1.02rem;font-weight:600'>Modelo de factibilidad inmobiliaria · CG Constructora</div>", unsafe_allow_html=True)
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
    st.caption("Modelo financiero CG Constructora · estándar FAST de modelación")

# ============ COCKPIT EJECUTIVO (resumen 1-vistazo, por proyecto) ============
if seccion=="Cockpit":
    hc1,hc2 = st.columns([1,9])
    if LOGO.exists(): hc1.image(str(LOGO), width=78)
    hc2.markdown(f"<h1>Cockpit ejecutivo — {meta.get('nombre','')}</h1>", unsafe_allow_html=True)
    _audit = ap.get("fiducia_real")
    hc2.caption("CG Constructora · resumen de comité, 1 vistazo · "
                + ("TIR/VPN **auditados** (FCL de fiducia)" if _audit else "cifras preliminares del modelo calibrado"))
    st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
    _tir=ap.get("tir_proyecto"); _marg=pg.get("margen_oper"); _vpn=ap.get("vpn_proyecto")
    _tireq=ap.get("tir_equity"); _cred=ap.get("credito_max"); _pb=ap.get("payback_mes"); _V=pg.get("ventas") or 0
    r1=st.columns(4)
    _c=_sem(_tir,0.20,0.30);            kpi(r1[0],"TIR del proyecto",fmt_pct(_tir),_SEMLAB[_c],_c)
    _c=_sem(_marg,0.03,0.05);           kpi(r1[1],"Margen operativo",fmt_pct(_marg),_SEMLAB[_c],_c)
    _c=_sem(pg.get("util_oper"),_V*0.01,_V*0.03); kpi(r1[2],"Utilidad operativa",fmt_mm(pg.get("util_oper")),_SEMLAB[_c],_c)
    _c=_sem(_vpn,-10_000_000,0);        kpi(r1[3],"VPN del proyecto",fmt_mm(_vpn),_SEMLAB[_c],_c)
    r2=st.columns(4)
    _c=_sem(_tireq,0.20,0.30);          kpi(r2[0],"TIR socio CG (equity)",fmt_pct(_tireq),_SEMLAB[_c],_c)
    kpi(r2[1],"UDI (a socios)",fmt_mm(pg.get("udi")),"utilidad distribuible",MUTED)
    kpi(r2[2],"Crédito constructor máx",fmt_mm(_cred),"exposición de deuda",MUTED)
    _c=_sem(_pb,60,36,invertir=True);   kpi(r2[3],"Payback (caja+)",(f"{_pb} meses" if _pb else "—"),(_SEMLAB[_c] if _pb else "—"),(_c if _pb else MUTED))
    st.write("")
    g=st.columns(2)
    with g[0]:
        st.plotly_chart(_charts.cockpit_gauge(_tir or 0,"TIR del proyecto",rango=(0,0.6),
            zonas=((0,0.20,RED),(0.20,0.30,AMBER),(0.30,0.6,GREEN))), width="stretch")
    with g[1]:
        st.plotly_chart(_charts.cockpit_gauge(_marg or 0,"Margen operativo",rango=(0,0.12),
            zonas=((0,0.03,RED),(0.03,0.05,AMBER),(0.05,0.12,GREEN))), width="stretch")
    if meta.get("nombre","") in _nav.PROYECTOS_CON_MONITOR:
        _act=[a for a in _nav.NAVARRA_ALERTAS if a["estado"]=="Activa"]
        if _act:
            st.markdown(f"##### ⚠️ Alertas activas de obra ({len(_act)})")
            render_alertas(_nav.NAVARRA_ALERTAS, solo_activas=True, max_items=3)
    st.caption("Semáforo por umbral de industria (inmobiliario CO): TIR 🟢≥30% / 🟡20–30% · margen 🟢≥5% / "
               "🟡3–5% · payback 🟢≤36m. Cifras del waterfall calibrado; donde hay FCL de fiducia, TIR/VPN son "
               "auditados. Detalle en **Apalancamiento**, **Flujo de caja** y **Monte Carlo**.")

# ============ PORTAFOLIO (BURBUJAS — mapa de valor) ============
if seccion=="Portafolio (burbujas)":
    hc1,hc2 = st.columns([1,9])
    if LOGO.exists(): hc1.image(str(LOGO), width=78)
    hc2.markdown("<h1>Portafolio CG — mapa de valor</h1>", unsafe_allow_html=True)
    hc2.caption("Compara los proyectos del portafolio en un vistazo: rentabilidad (TIR) vs margen, "
                "tamaño de burbuja = ventas, color = tipo (VIS / No VIS).")
    st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
    pts=[p for p in puntos_portafolio(tuple(listar())) if p.get("tir") is not None]
    if not pts:
        st.info("No hay proyectos con TIR calculada para comparar. Abre o crea proyectos en 🏢 **Proyectos activos**.")
    else:
        st.plotly_chart(_charts.bubbles_portafolio(pts), width="stretch")
        df=pd.DataFrame([{"Proyecto":p["nombre"],"Tipo":p["tipo"],"Unidades":p["und"],
                          "TIR":fmt_pct(p["tir"]),"Margen":fmt_pct(p["margen"]),
                          "Ventas":fmt_mm(p["ventas"])} for p in pts])
        st.dataframe(df, width="stretch", hide_index=True)
        st.caption("Cuadrantes: ★ **Estrella** (TIR≥30% y margen≥5%) · **Crecimiento** (TIR alta, margen ajustado) · "
                   "**Vigilancia** (margen alto, TIR baja) · **Revisar** (ambos bajos). Las burbujas se dimensionan "
                   "por ventas. Proyectos con TIR negativa (p.ej. greenfield) se recortan y anotan en el borde "
                   "izquierdo para no aplastar la escala.")

# ============ PROYECTOS ACTIVOS ============
if seccion=="Proyectos activos":
    st.markdown("### 🏢 Proyectos activos — CG Constructora")
    st.caption("Portafolio de proyectos en evaluación. **Abre** uno para trabajarlo, o crea uno nuevo desde el selector lateral.")
    # --- Navarra: estado operativo del comité (semáforo por etapa + alertas) ---
    _act=[a for a in _nav.NAVARRA_ALERTAS if a["estado"]=="Activa"]
    with st.expander(f"🏗️ Navarra — estado de obra (Corte Abr 2026) · ⚠️ {len(_act)} alertas activas", expanded=False):
        _sem={"green":("#F0FDF4","#4ADE80","🟢"),"red":("#FEF2F2","#FCA5A5","🔴"),
              "amber":("#FFFBEB","#FDE68A","🟡"),"gray":("#F8FAFC","#E2E8F0","⚪")}
        _ec=st.columns(len(_nav.NAVARRA_ESTRUCTURA))
        for _col,(_,e) in zip(_ec, _nav.NAVARRA_ESTRUCTURA.items()):
            _bg,_bd,_ic=_sem.get(e["semaforo"], _sem["gray"])
            _col.markdown(
                f'<div style="background:{_bg};border:1px solid {_bd};border-radius:10px;padding:12px;'
                f'text-align:center;min-height:170px;"><div style="font-size:18px;">{_ic}</div>'
                f'<div style="font-weight:700;font-size:12px;color:{TEAL};margin:4px 0;">{e["nombre"]}</div>'
                f'<div style="font-size:22px;font-weight:800;color:{TEAL};">{e["avance_pct"]:.0f}%</div>'
                f'<div style="font-size:10px;color:#64748B;">{e["estado"]} · {e["unidades"]} und</div>'
                f'<div style="font-size:10px;color:#64748B;margin-top:6px;line-height:1.4;">{e["detalle"]}</div></div>',
                unsafe_allow_html=True)
        st.write("")
        render_alertas(_nav.NAVARRA_ALERTAS, solo_activas=True, max_items=4)
        st.caption("Vista operativa por torre (951 und en 4 etapas) · seguimiento de comité. El modelo financiero "
                   "auditado agrupa en 3 etapas (951 und). Detalle completo en 🏗️ **Monitor de ejecución**.")
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
        cols=["cod","nom","und","metodo","precio","area_und","vmes","frec","emes","efrec","pe_pct","sucesora","desfase","dur_obra","escrituracion","avance_real","costo_real"]
        df_et=pd.DataFrame(par["etapas"]).reindex(columns=cols)
        if "metodo" in df_et: df_et["metodo"]=df_et["metodo"].fillna("$/m²")
        if "avance_real" in df_et:                       # se guarda 0..1, se muestra 0..100
            df_et["avance_real"]=df_et["avance_real"].apply(lambda v: v*100 if pd.notna(v) else v)
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
                "escrituracion": st.column_config.NumberColumn("Escrit. (m)", format="%d"),
                "avance_real": st.column_config.NumberColumn("Avance real %", format="%.0f", min_value=0, max_value=100,
                    help="Valor Ganado (EVM): % de avance de obra REAL de esta etapa a la fecha (0–100). Vacío = sin EVM."),
                "costo_real": st.column_config.NumberColumn("Costo real (miles)", format="%d",
                    help="Valor Ganado (EVM): costo directo realmente gastado en esta etapa a la fecha (miles COP).")})
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
            _av=_f(r.get("avance_real")); _cr=_f(r.get("costo_real"))
            rec={"cod":_i(r.get("cod")),"nom":r.get("nom") or "Etapa","und":und,"metodo":metodo,
                "precio":precio,"area_und":area,"ventas_miles":ventas_miles,"vmes":_i(r.get("vmes")) or 6,
                "frec":_i(r.get("frec")) or 1,"emes":_i(r.get("emes")),"efrec":_i(r.get("efrec")) or 1,
                "pe_pct":_f(r.get("pe_pct")) or 0.60,"sucesora":_i(r.get("sucesora")),
                "desfase":_i(r.get("desfase")) or 0,"obra_offset":1,"dur_obra":_i(r.get("dur_obra")) or 24,
                "escrituracion":_i(r.get("escrituracion")) or 30}
            if _av is not None: rec["avance_real"]=_av/100.0      # se guarda 0..1
            if _cr is not None: rec["costo_real"]=_cr
            recs.append(rec)
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
        if par.get("tipologias"):
            st.caption("ℹ️ Este proyecto tiene **tipologías**: las **unidades y el precio** se toman de «3b · Tipologías y "
                       "producto». Aquí se editan los **tiempos** (ritmo, equilibrio, obra, escrituración).")
    with st.expander("3b · Tipologías y producto (ingresos)", expanded=bool(par.get("tipologias"))):
        _tp=par.get("meta",{}).get("tipo","No VIS"); _es_vis=_tp in ("VIS","VIP")
        st.caption(f"Producto del proyecto **{_tp}**. " + (
            "En **VIS/VIP** los parqueaderos y depósitos son **comunales** → no se listan como ingreso." if _es_vis
            else "En **No VIS** los **parqueaderos y depósitos van por separado** → agrégalos como filas con su clase."))
        _clases=(["apartamento","comercio"] if _es_vis else ["apartamento","comercio","parqueadero","deposito"])
        _ecods=[e.get("cod") for e in par.get("etapas",[])]
        _tdf=pd.DataFrame(par.get("tipologias",[]), columns=["etapa","nombre","clase","und","metodo","precio","area_und"])
        for _c in ["etapa","und"]:   _tdf[_c]=pd.to_numeric(_tdf[_c], errors="coerce").astype("Int64")
        for _c in ["precio","area_und"]: _tdf[_c]=pd.to_numeric(_tdf[_c], errors="coerce").astype("float64")
        for _c in ["nombre","clase","metodo"]: _tdf[_c]=_tdf[_c].astype("object")
        _ted=st.data_editor(_tdf, num_rows="dynamic", width="stretch", key=f"tipo_{sel}",
            column_config={
                "etapa": st.column_config.SelectboxColumn("Etapa", options=_ecods, width="small"),
                "nombre": st.column_config.TextColumn("Nombre / tipo"),
                "clase": st.column_config.SelectboxColumn("Clase", options=_clases, width="small"),
                "und": st.column_config.NumberColumn("Unidades", format="%d"),
                "metodo": st.column_config.SelectboxColumn("Método", options=["$/und","$/m²"], width="small"),
                "precio": st.column_config.NumberColumn("Precio (COP)", format="%d",
                    help="Precio por unidad ($/und) o por m² ($/m²), en COP. Vivienda: lleva recaudo completo "
                         "(separación+cuota inicial+subrogación). Parqueadero/depósito: se paga en la cuota inicial."),
                "area_und": st.column_config.NumberColumn("Área/und (m²)", format="%.1f")})
        _newt=[]
        for r in _ted.to_dict("records"):
            cl=r.get("clase"); et=r.get("etapa")
            if cl in (None,"") or et is None or pd.isna(et): continue
            if _es_vis and str(cl) in ("parqueadero","deposito"): continue   # regla VIS: comunales, no entran
            _newt.append({"etapa":int(et),"nombre":str(r.get("nombre") or cl),"clase":str(cl),
                "und":int(r.get("und") or 0),"metodo":(r.get("metodo") or "$/und"),
                "precio":float(r.get("precio") or 0),"area_und":float(r.get("area_und") or 0)})
        par["tipologias"]=_newt
        def _vtip(t): return (t["und"]*t["precio"]/1000 if t["metodo"]=="$/und" else t["und"]*t["precio"]*t["area_und"]/1000)
        _viv=sum(t["und"] for t in _newt if t["clase"] in ("apartamento","comercio"))
        _vviv=sum(_vtip(t) for t in _newt if t["clase"] in ("apartamento","comercio"))
        _vad=sum(_vtip(t) for t in _newt if t["clase"] in ("parqueadero","deposito"))
        par.setdefault("meta",{})["unidades"]=_viv if _viv else par.get("meta",{}).get("unidades",0)
        _msg=f"**{len(_newt)} tipologías · {_viv} unidades de vivienda · ventas vivienda {_vviv/1000:,.0f} M**".replace(",", ".")
        if _vad: _msg+=f" **+ adicionales {_vad/1000:,.0f} M**".replace(",", ".")
        st.success(_msg)
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
    with st.expander("4b · Gastos fijos de estructura (personal, generales, mercadeo)"):
        st.caption("Gastos **fijos mensuales** del proyecto — **no** escalan con ventas. Se **tallan dentro de "
                   "los indirectos** (no cambian la utilidad si no superan el indirecto) y en el flujo se gastan "
                   f"**mes a mes** en su ventana. Indirecto total del proyecto: **{fmt_mm(pg['indirectos'])}**.")
        _gdf=pd.DataFrame(par.get("gastos_fijos",[]), columns=["concepto","valor_mes_miles","desde","hasta"])
        _gdf["concepto"]=_gdf["concepto"].astype("object")
        for _c in ["valor_mes_miles","desde","hasta"]: _gdf[_c]=pd.to_numeric(_gdf[_c],errors="coerce")
        _ged=st.data_editor(_gdf, num_rows="dynamic", width="stretch", key=f"gf_{sel}",
            column_config={
                "concepto": st.column_config.TextColumn("Concepto"),
                "valor_mes_miles": st.column_config.NumberColumn("Valor mensual (miles COP)", format="%d"),
                "desde": st.column_config.NumberColumn("Desde (mes)", format="%d", help="Mes de inicio (0 = arranque del proyecto)"),
                "hasta": st.column_config.NumberColumn("Hasta (mes)", format="%d", help="Mes final (exclusivo)")})
        _newg=[]
        for r in _ged.to_dict("records"):
            con=r.get("concepto"); vm=r.get("valor_mes_miles")
            if con and vm is not None and not pd.isna(vm):
                _h=r.get("hasta")
                _newg.append({"concepto":str(con),"valor_mes_miles":float(vm),
                    "desde":int(r.get("desde") or 0),
                    "hasta":(int(_h) if _h is not None and not pd.isna(_h) else None)})
        par["gastos_fijos"]=_newg
        if _newg:
            _gt=sum(g["valor_mes_miles"]*((g["hasta"]-g["desde"]) if g["hasta"] is not None else 1) for g in _newg)
            _exc=max(_gt-pg["indirectos"],0)
            st.success(f"**{len(_newg)} gastos · total {fmt_mm(_gt)}** — "
                       + ("dentro del indirecto · **UO sin cambio**" if _exc<=0 else f"**excede** el indirecto en {fmt_mm(_exc)} · **baja la UO**"))
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
    _rows=[("Ingresos por ventas",pg["ventas"]),("(+) Reconocimiento Codensa",pg["recon_codensa"]),
           ("(-) Costo lote",-pg["costo_lote"]),("(-) Costos directos",-pg["directos"])]
    if pg.get("gastos_fijos",0)>0:        # desglosar el indirecto en gastos fijos + otros
        _rows+=[("(-) Otros indirectos",-pg["indirectos_otros"]),
                ("(-) Gastos fijos (estructura)",-pg["gastos_fijos"])]
    else:
        _rows+=[("(-) Costos indirectos",-pg["indirectos"])]
    _rows+=[("(-) Honorarios",-pg["honorarios"]),("UTILIDAD OPERATIVA",pg["util_oper"]),
            ("(-) Provisión renta",-pg["renta"]),("UDI",pg["udi"])]
    df=pd.DataFrame(_rows,columns=["Concepto","Miles COP"]); df["% ventas"]=df["Miles COP"]/pg["ventas"] if pg["ventas"] else 0
    st.dataframe(df.style.format({"Miles COP":"{:,.0f}","% ventas":"{:.1%}"}), width="stretch", hide_index=True)
    costo_total=pg["costo_lote"]+pg["directos"]+pg["indirectos"]
    st.markdown("**Indicadores del Estado de Resultados**")
    e=st.columns(4)
    kpi(e[0],"Margen de contribución",fmt_mm(pg["util_oper"]),fmt_pct(pg["margen_oper"])+" /ventas",GREEN)
    kpi(e[1],"Margen sobre costo",fmt_pct(pg["util_oper"]/costo_total if costo_total else 0))
    kpi(e[2],"Incidencia directos",fmt_pct(pg["directos"]/costo_total if costo_total else 0))
    kpi(e[3],"Incidencia indirectos+lote",fmt_pct((pg["indirectos"]+pg["costo_lote"])/costo_total if costo_total else 0))
    # --- Gastos financieros (memo, bajo el operativo) e impuestos ---
    _int=ap.get("intereses_total")
    with st.expander("💳 Gastos financieros e impuestos (memo)"):
        gf1=st.columns(2)
        kpi(gf1[0],"Gastos financieros (intereses crédito)", fmt_mm(_int) if _int else "—", "no afectan la UO", AMBER)
        kpi(gf1[1],"Provisión de renta", fmt_mm(pg["renta"]), "impuesto sobre reintegros", MUTED)
        st.caption("La **utilidad operativa** es **antes de financiación**: los **gastos financieros** (intereses "
                   "del crédito constructor) impactan el retorno del **inversionista**, no la UO — se ven en la vista "
                   "*FC del Inversionista* de **Flujo de caja**. La **renta** ya está descontada en la **UDI**. "
                   "Otros impuestos operativos (**predial, ICA**) se cargan como capítulos del **indirecto** "
                   "(Distribución costos).")

# ============ REPARTO ============
if seccion=="Reparto":
    fig=go.Figure(data=[go.Pie(labels=["CG","Socio"],values=[pg["cg"],pg["socio"]],hole=.55,marker_colors=[TEAL,AMBER])])
    fig.update_layout(title="Distribución de resultados",height=380); st.plotly_chart(fig, width="stretch")

# ============ DISTRIBUCIÓN COSTOS ============
if seccion=="Distribución costos":
    # --- Presupuesto de costo directo por capítulos (bottom-up) ---
    _dcap = par.get("directos_cap")
    st.markdown("#### Presupuesto de costo directo — por capítulo")
    if _dcap:
        _tot = sum((x.get("valor_miles",0) or 0) for x in _dcap)
        _ac = par.get("areas",{}).get("m2_construidos",0) or 0
        kk=st.columns(3)
        kpi(kk[0],"Costo directo total", fmt_mm(_tot), f"{len(_dcap)} capítulos · bottom-up", TEAL)
        kpi(kk[1],"Costo directo /m² const", (f"${_tot*1000/_ac:,.0f}".replace(",", ".") if _ac else "—"), "por m² construido", MUTED)
        kpi(kk[2],"Incidencia s/ ventas", fmt_pct(_tot/pg["ventas"] if pg["ventas"] else 0), "del directo en ventas", MUTED)
        if ES_EDITOR:
            _dfc=pd.DataFrame([{"Capítulo":x.get("capitulo",""),"Valor (miles COP)":int(x.get("valor_miles",0) or 0)} for x in _dcap])
            _ed=st.data_editor(_dfc, num_rows="dynamic", width="stretch", key=f"dcap_{sel}",
                column_config={"Capítulo":st.column_config.TextColumn("Capítulo"),
                    "Valor (miles COP)":st.column_config.NumberColumn("Valor (miles COP)", format="%d",
                        help="Presupuesto del capítulo. La SUMA de capítulos es el costo directo del P&G (bottom-up).")})
            _new=[]
            for r in _ed.to_dict("records"):
                _cap=r.get("Capítulo"); _val=r.get("Valor (miles COP)")
                if _cap and _val is not None and not pd.isna(_val):
                    _new.append({"capitulo":str(_cap),"valor_miles":float(_val)})
            if _new:
                par["directos_cap"]=_new
                st.success(f"**{len(_new)} capítulos · costo directo total {fmt_mm(sum(x['valor_miles'] for x in _new))}** "
                           f"= base del P&G y de la curva S. (Incidencia {fmt_pct(sum(x['valor_miles'] for x in _new)/pg['ventas'] if pg['ventas'] else 0)} sobre ventas.)")
        else:
            _dfc=pd.DataFrame([{"Capítulo":x.get("capitulo",""),"Valor (miles COP)":int(x.get("valor_miles",0) or 0),
                               "% del directo":f"{(x.get('valor_miles',0) or 0)/_tot*100:.1f}%" if _tot else "—"} for x in _dcap])
            st.dataframe(_dfc, width="stretch", hide_index=True)
            st.caption(f"Costo directo total = **{fmt_mm(_tot)}** en {len(_dcap)} capítulos. Es la base del P&G y de la curva S de obra.")
    else:
        st.info("Este proyecto aún no tiene **presupuesto por capítulos**. El costo directo se calcula como "
                f"**{fmt_pct(par.get('costos_pct',{}).get('directos',0))} de las ventas** = {fmt_mm(pg['directos'])}. "
                "Para detallarlo por capítulo (bottom-up), cárgalo en este proyecto.")
    # --- Costos indirectos por capítulo (bottom-up, opcional) ---
    st.markdown("#### Costos indirectos — por capítulo")
    _icap=par.get("indirectos_cap")
    _ipct=par.get("costos_pct",{}).get("indirectos",0)
    if ES_EDITOR:
        st.caption("Desglosa el indirecto en capítulos (diseños, licencias, interventoría, pólizas, comisión "
                   "fiduciaria, **predial**, **ICA**…). Si lo usas, la **suma** es el indirecto del P&G (bottom-up); "
                   f"si lo dejas vacío, se usa el **{fmt_pct(_ipct)} de ventas** = {fmt_mm(pg['indirectos'])}.")
        _idf=pd.DataFrame(_icap or [], columns=["capitulo","valor_miles"])
        _idf["capitulo"]=_idf["capitulo"].astype("object")
        _idf["valor_miles"]=pd.to_numeric(_idf["valor_miles"],errors="coerce")
        _ied=st.data_editor(_idf, num_rows="dynamic", width="stretch", key=f"icap_{sel}",
            column_config={"capitulo":st.column_config.TextColumn("Capítulo indirecto"),
                "valor_miles":st.column_config.NumberColumn("Valor (miles COP)", format="%d")})
        _newi=[]
        for r in _ied.to_dict("records"):
            _cap=r.get("capitulo"); _val=r.get("valor_miles")
            if _cap and _val is not None and not pd.isna(_val):
                _newi.append({"capitulo":str(_cap),"valor_miles":float(_val)})
        par["indirectos_cap"]=_newi or None
        if _newi:
            _ns=sum(x["valor_miles"] for x in _newi)
            st.success(f"**{len(_newi)} capítulos · indirecto total {fmt_mm(_ns)}** = base del P&G "
                       f"(incidencia {fmt_pct(_ns/pg['ventas'] if pg['ventas'] else 0)} sobre ventas).")
    elif _icap:
        _itot=sum((x.get('valor_miles',0) or 0) for x in _icap)
        st.dataframe(pd.DataFrame([{"Capítulo":x.get("capitulo",""),"Valor (miles COP)":int(x.get("valor_miles",0) or 0),
            "% del indirecto":f"{(x.get('valor_miles',0) or 0)/_itot*100:.1f}%" if _itot else "—"} for x in _icap]),
            width="stretch", hide_index=True)
        st.caption(f"Indirecto total = **{fmt_mm(_itot)}** en {len(_icap)} capítulos.")
    else:
        st.info(f"Costo indirecto por **{fmt_pct(_ipct)} de ventas** = {fmt_mm(pg['indirectos'])}. "
                "Detállalo por capítulo desde el editor del modelo.")
    st.markdown("#### Curva S de avance de obra")
    d=R["distribucion"]
    _h=R.get("hitos") or {}
    _ic=[x.get("IC") for x in _h.values() if x.get("IC")]
    _base_obra=min(_ic) if _ic else None                 # inicio real de obra (dic-2025 en Navarra)
    st.plotly_chart(_charts.curva_obra_s(d["escalada"], d["acumulada"], fecha_base=_base_obra), width="stretch")
    _pico_txt=(f"{_base_obra.year+(_base_obra.month-1+d['pico_mes']-1)//12}-"
               f"{(_base_obra.month-1+d['pico_mes']-1)%12+1:02d}") if _base_obra else f"mes {d['pico_mes']}"
    st.caption("Curva S de avance de obra: barras = costo directo mensual (campana de Gauss); línea ámbar = "
               f"avance acumulado en %. La obra inicia {('en '+_base_obra.strftime('%b %Y')) if _base_obra else 'según cronograma'}.")

# ============ FLUJO DE CAJA ============
if seccion=="Flujo de caja":
    _ap=R.get("apalancamiento") or {}
    _h=R.get("hitos") or {}
    if _ap.get("operativo") and _h:
        _base=min(x["IV"] for x in _h.values())          # fecha real del mes 0 (inicio del proyecto)
        _en_ejecucion = _base < date(2026,5,1)           # proyecto ya arrancó (caso Navarra)
        _desde=None
        if _en_ejecucion:
            _solo_futuro=st.toggle("Mostrar solo la caja de aquí en adelante (desde hoy)", value=True,
                                   help="Este proyecto ya está en ejecución. Activa para ver solo el flujo futuro.")
            if _solo_futuro: _desde=date(2026,5,1)
        _audit=_ap.get("fiducia_real")
        ft=st.tabs(["🏗️ FC del Proyecto (sin financiación)","💰 FC del Inversionista (apalancado)"])
        with ft[0]:
            st.plotly_chart(_charts.flujo_caja_waterfall(
                _ap["operativo"], _ap["acumulado"], _ap.get("saldo_credito"),
                fecha_base=_base, tope_anio=2030, desde=_desde,
                titulo="Flujo de caja del proyecto (operativo, sin apalancar)"), width="stretch")
            cc=st.columns(4)
            kpi(cc[0],"TIR del proyecto",fmt_pct(_ap.get("tir_proyecto")),("auditado · fiducia" if _audit else "modelo"),GREEN if _audit else MUTED)
            kpi(cc[1],"VPN del proyecto",fmt_mm(_ap.get("vpn_proyecto")),("@TIO · auditado" if _audit else "@TIO · prelim."),GREEN if _audit else AMBER)
            kpi(cc[2],"Necesidad máx de caja",fmt_mm(_ap.get("max_necesidad_caja")))
            kpi(cc[3],"Crédito constructor máx",fmt_mm(_ap.get("credito_max")))
            st.caption("**Sin apalancar** — mide la bondad **intrínseca** del proyecto. Barras = flujo neto mensual "
                       "(🟢 caja / 🔴 requiere financiación) · línea oscura = caja acumulada · ámbar punteada = saldo "
                       "de crédito. " + ("TIR/VPN **auditados** (FCL de fiducia)." if _audit else "TIR/VPN del modelo (preliminar)."))
        with ft[1]:
            _eq=_ap.get("flujo_equity") or []
            _eqacum=[]; _s=0.0
            for x in _eq: _s+=x; _eqacum.append(_s)
            st.plotly_chart(_charts.flujo_caja_waterfall(
                _eq, _eqacum, _ap.get("saldo_credito"),
                fecha_base=_base, tope_anio=2030, desde=_desde,
                titulo="Flujo de caja del inversionista (socio CG, apalancado)"), width="stretch")
            cc=st.columns(4)
            kpi(cc[0],"TIR del inversionista",fmt_pct(_ap.get("tir_equity")),("auditado · fiducia" if _audit else "equity apalancado"),GREEN if _audit else MUTED)
            if _audit and _ap.get("vpn_socio") is not None:
                kpi(cc[1],"VPN del socio CG",fmt_mm(_ap.get("vpn_socio")),"@TIO · auditado",GREEN)
            else:
                kpi(cc[1],"Aportes de equity",fmt_mm(_ap.get("aportes_total")),"capital propio",MUTED)
            kpi(cc[2],"Crédito constructor máx",fmt_mm(_ap.get("credito_max")))
            kpi(cc[3],"Intereses del crédito",fmt_mm(_ap.get("intereses_total")))
            st.caption("**Apalancado** — retorno al **equity de CG** tras el crédito constructor (aportes + crédito "
                       "neto − intereses). El crédito eleva la TIR del socio por encima de la del proyecto. "
                       + ("Cifras **auditadas** (waterfall de fiducia)." if _audit else "Modelo preliminar."))
        st.caption(f"Eje en fechas reales, {'desde hoy (may-2026)' if _desde else f'desde {_base:%b %Y}'} hasta 2030. "
                   "El detalle del crédito constructor y de la fiducia está en **Apalancamiento**.")
    else:
        st.plotly_chart(_charts.flujo_caja_waterfall(fl["flujo"], fl["acumulado"], fl.get("saldo_credito")), width="stretch")
        st.caption("Flujo mensual del proyecto.")

# ============ COSTO DE CAPITAL (WACC) ============
if seccion=="Costo de capital":
    from cg_engine import modelo as _modelo
    st.markdown("### 📐 Costo de Capital (WACC)")
    st.caption("Rentabilidad mínima exigida al proyecto. Build-up CAPM de mercado emergente "
               "(metodología Damodaran / CESLA): beta del sector comparable EE.UU. → desapalancar con "
               "**beta de deuda** → reapalancar a la estructura de Colombia → Ke USD → **+ riesgo país (EMBI)** "
               "→ paridad de inflación a COP → WACC. Reproduce la hoja k.beta auditada (Navarra 21,54%).")
    wcfg = par.setdefault("financiero",{}).setdefault("wacc",{})
    _defw = {"beta_us":1.29,"kd_us":9.335,"tax_us":13.3,"de_us":21.56,"tax_col":33.0,"de_col":233.3,
             "rf":0.12,"rm":12.44,"rp":3.14,"inf_col":5.1,"inf_us":2.9,"tasa_d":15.0,"spread":10.43,"eq_w":30.0}
    for _k,_v in _defw.items(): wcfg.setdefault(_k,_v)
    if ES_EDITOR:
        with st.expander("✏️ Parámetros del costo de capital (editar)", expanded=True):
            st.markdown("**Comparable EE.UU.** (sector Engineering/Construction · fuente: Damodaran)")
            e1=st.columns(4)
            wcfg["beta_us"]=e1[0].number_input("Beta apalancado βl (US)", value=float(wcfg["beta_us"]), step=0.01, format="%.4f")
            wcfg["kd_us"]=e1[1].number_input("Costo deuda US kd (%)", value=float(wcfg["kd_us"]), step=0.05, format="%.3f",
                help="De aquí sale la beta de la deuda βd = (kd − Rf)/(Rm − Rf).")
            wcfg["tax_us"]=e1[2].number_input("Impuesto US (%)", value=float(wcfg["tax_us"]), step=0.1, format="%.1f")
            wcfg["de_us"]=e1[3].number_input("Estructura D/E US (%)", value=float(wcfg["de_us"]), step=0.5, format="%.2f")
            st.markdown("**Mercado**")
            e2=st.columns(2)
            wcfg["rm"]=e2[0].number_input("Rentabilidad del mercado Rm (%)", value=float(wcfg["rm"]), step=0.1, format="%.2f")
            wcfg["rf"]=e2[1].number_input("Tasa libre de riesgo Rf (%)", value=float(wcfg["rf"]), step=0.01, format="%.2f")
            st.markdown("**Colombia**")
            e3=st.columns(4)
            _eq=e3[0].number_input("Equity en la estructura (%)", value=float(wcfg.get("eq_w",30.0)), step=1.0,
                min_value=1.0, max_value=99.0, format="%.1f",
                help="Peso del capital propio. Deuda y D/E se derivan (Equity 30% → Deuda 70% → D/E 233%).")
            wcfg["eq_w"]=_eq; wcfg["de_col"]=((100-_eq)/_eq*100 if _eq else 0.0)
            wcfg["tax_col"]=e3[1].number_input("Impuesto Colombia (%)", value=float(wcfg["tax_col"]), step=0.5, format="%.1f")
            wcfg["tasa_d"]=e3[2].number_input("Tasa deuda Colombia (%)", value=float(wcfg["tasa_d"]), step=0.5, format="%.2f")
            wcfg["spread"]=e3[3].number_input("Spread deuda (%)", value=float(wcfg["spread"]), step=0.1, format="%.2f")
            e4=st.columns(2)
            wcfg["inf_col"]=e4[0].number_input("Inflación Colombia EA (%)", value=float(wcfg["inf_col"]), step=0.1, format="%.2f")
            wcfg["inf_us"]=e4[1].number_input("Inflación EE.UU. EA (%)", value=float(wcfg["inf_us"]), step=0.1, format="%.2f")
            st.markdown("**Riesgo país — EMBI Colombia**")
            wcfg["rp"]=st.number_input("Riesgo país (EMBI, %)", value=float(wcfg["rp"]), step=0.01, format="%.2f",
                help="Spread EMBI Colombia (JP Morgan). 1% = 100 puntos básicos.")
            st.info("📡 **EMBI Colombia de referencia:** ~**2,0%** (≈200 pb; en abril-2026 tocó 219 pb, mínimo en 5 años). "
                    "El valor de la hoja era 3,14% (314 pb, may-2023). "
                    "Fuentes: [Banco de la República](https://www.banrep.gov.co/es/taxonomy/term/7611) · "
                    "[BCRP serie diaria](https://estadisticas.bcrp.gob.pe/estadisticas/series/diarias/resultados/PD04715XD/html) · "
                    "[CESLA](https://www.cesla.com). Actualízalo con el dato vigente al día de la evaluación.")
    else:
        st.info("🔒 Modo consulta: los parámetros del costo de capital los edita el editor del modelo.")
    d=_modelo.calcular_wacc(wcfg, detalle=True)
    st.markdown("#### Cadena de cálculo")
    col=st.columns(2)
    with col[0]:
        st.markdown("**Beta**")
        st.dataframe(pd.DataFrame([
            ("Beta apalancado βl (US)", f"{wcfg['beta_us']:.4f}"),
            ("Beta de la deuda βd", f"{d['beta_d']:.4f}"),
            ("Beta desapalancado βu", f"{d['beta_u']:.4f}"),
            ("Beta reapalancado Colombia βl₂", f"{d['beta_l']:.4f}"),
        ], columns=["Concepto","Valor"]), width="stretch", hide_index=True)
    with col[1]:
        st.markdown("**Costo de recursos propios**")
        st.dataframe(pd.DataFrame([
            ("Ke USD (CAPM)", fmt_pct(d['ke_usd'])),
            ("(+) Riesgo país (EMBI)", fmt_pct(d['rp'])),
            ("Ke USD + riesgo país", fmt_pct(d['ke_usd_rp'])),
            ("Paridad de inflación (RPLP)", fmt_pct(d['rplp'])),
            ("Ke en COP", fmt_pct(d['ke_cop'])),
        ], columns=["Concepto","Valor"]), width="stretch", hide_index=True)
    st.markdown("#### Resultado")
    kk=st.columns(4)
    kpi(kk[0],"Ke COP (recursos propios)", fmt_pct(d['ke_cop']), f"E = {d['we']*100:.0f}%", TEAL)
    kpi(kk[1],"Kd COP (deuda)", fmt_pct(d['kd_cop']), f"D = {d['wd']*100:.0f}%", AMBER)
    kpi(kk[2],"Kd después de impuestos", fmt_pct(d['kd_cop']*(1-d['t_col'])), f"escudo fiscal {d['t_col']*100:.0f}%", MUTED)
    kpi(kk[3],"WACC", fmt_pct(d['wacc']), "rentabilidad mínima", GREEN)
    st.caption(f"**WACC = E·Ke$COP + D·Kd·(1−t)** = {d['we']*100:.0f}%·{d['ke_cop']*100:.2f}% + "
               f"{d['wd']*100:.0f}%·{d['kd_cop']*100:.2f}%·(1−{d['t_col']*100:.0f}%) = **{fmt_pct(d['wacc'])}**. "
               "El WACC es la tasa de descuento del VPN del proyecto (sección **Apalancamiento**).")

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
        _hh=R.get("hitos") or {}
        _b=min((x["IV"] for x in _hh.values()), default=None)
        n=max([i for i,v in enumerate(op) if abs(v)>1],default=0)+2
        if _b is not None:
            xs=_charts._eje_fechas(_b, n)
            lim=[i for i,dd in enumerate(xs) if dd.year<=2030]
            if lim: n=lim[-1]+1; xs=xs[:n]
        else:
            xs=list(range(1,n+1))
        fig2=go.Figure(); fig2.add_scatter(x=xs,y=ac[:n],name="Operativo acumulado",line=dict(color=INK,width=2))
        fig2.add_scatter(x=xs,y=sc[:n],name="Saldo crédito constructor",line=dict(color=AMBER,dash="dot"))
        fig2.update_layout(title="Caja acumulada y saldo de crédito (mensual)",height=340,xaxis_title="")
        if _b is not None: fig2.update_xaxes(dtick="M6", tickformat="%b %Y")
        st.plotly_chart(fig2, width="stretch")
        st.caption("Crédito constructor: cobertura (~80%) del costo de obra, amortizado con las subrogaciones; los aportes cubren el resto.")

# ============ VALOR GANADO (EVM) ============
if seccion=="Valor Ganado":
    st.markdown("### 📈 Valor Ganado (EVM)")
    st.caption("Earned Value Management — estándar PMI. Compara lo **planeado** (PV), lo **ejecutado** "
               "(EV) y lo **gastado** (AC) para medir eficiencia de costo (CPI) y cronograma (SPI).")
    ev=_evm.calcular_evm(par, R)   # fecha de corte por defecto (cg_engine.config.FECHA_CORTE_EVM)
    if not ev:
        st.info("Para ver el Valor Ganado, ingresa el **% de avance real** y el **costo real** de cada etapa "
                "en 📝 **Datos del proyecto → ③ Etapas** (columnas *Avance real* y *Costo real*).")
    else:
        _verde=GREEN; _rojo=RED; _amb=AMBER
        k=st.columns(4)
        cpi=ev.get("CPI"); spi=ev.get("SPI")
        kpi(k[0],"Avance de obra", fmt_pct(ev["avance_global"]))
        kpi(k[1],"CPI (costo)", f"{cpi:.2f}" if cpi else "n/d",
            ("eficiente" if cpi and cpi>=1 else "sobrecosto") if cpi else "", _verde if cpi and cpi>=1 else _rojo)
        kpi(k[2],"SPI (cronograma)", f"{spi:.2f}" if spi else "n/d",
            ("adelantado" if spi and spi>=1 else "atrasado") if spi else "", _verde if spi and spi>=1 else _rojo)
        kpi(k[3],"EAC (costo final est.)", fmt_mm(ev.get("EAC")),
            ("ahorro" if (ev.get("VAC") or 0)>=0 else "sobrecosto"),
            _verde if (ev.get("VAC") or 0)>=0 else _rojo)
        st.markdown(_evm.estado_en_palabras(ev))
        st.plotly_chart(_charts.valor_ganado_s(ev, fecha_base=ev.get("base_obra")), width="stretch")
        k2=st.columns(4)
        kpi(k2[0],"PV · Valor Planeado", fmt_mm(ev["PV"]))
        kpi(k2[1],"EV · Valor Ganado", fmt_mm(ev["EV"]))
        kpi(k2[2],"AC · Costo Real", fmt_mm(ev["AC"]))
        kpi(k2[3],"BAC · Presupuesto", fmt_mm(ev["BAC"]))
        st.caption("PV (teal) = costo directo planeado acumulado · EV (verde) = avance real valorado al "
                   "presupuesto · AC (rojo) = costo realmente gastado · EAC (ámbar) = proyección del costo final.")

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
        _h=R.get("hitos") or {}
        _base_v=min((x["IV"] for x in _h.values()), default=None)   # inicio de ventas real (mes 0)
        st.plotly_chart(_charts.recaudo_stacked(sepr, cir, subr, fecha_base=_base_v, tope_anio=2030), width="stretch")
        cc=st.columns(4)
        kpi(cc[0],"Separación",fmt_mm(sum(sepr))); kpi(cc[1],"Cuota inicial",fmt_mm(sum(cir)))
        kpi(cc[2],"Subrogación",fmt_mm(sum(subr))); kpi(cc[3],"Recaudo total",fmt_mm(sum(tot)))
        st.caption("Separación diferida + cuota inicial (venta → escrituración) + subrogación (a la entrega).")

# ============ ESCENARIOS ============
if seccion=="Escenarios":
    et=st.tabs(["📊 Escenarios","🗺️ Sensibilidad 2D (precio vs costo)"])
    with et[0]:
        esc=R["escenarios"]
        st.plotly_chart(_charts.escenarios_barras(esc), width="stretch")
        st.caption("Optimista: +5% precio, −2% costo · Pesimista: −10% precio, +5% costo. "
                   "Barras = utilidad operativa; etiqueta = utilidad y margen.")
    with et[1]:
        from cg_engine import modelo as _modelo
        _pe=copy.deepcopy(par)
        _pe.setdefault("ventas_miles", sum(e.get("ventas_miles",0) for e in _pe.get("etapas",[])))
        pasos=[-0.10,-0.05,0.0,0.05,0.10]
        # matriz de margen %: filas = variación de costo, columnas = variación de precio
        mat=[[_modelo._correr(_pe, dp, dc)["margen"]*100 for dp in pasos] for dc in pasos]
        st.plotly_chart(_charts.heatmap_sensibilidad([p*100 for p in pasos],[c*100 for c in pasos], mat), width="stretch")
        st.caption("Cada celda = margen operativo resultante al variar precio (eje X) y costo directo "
                   "(eje Y). Verde = sano · blanco = punto de quiebre · rojo = pérdida. La celda central es la base.")

# ============ MONTE CARLO (riesgo probabilístico) ============
if seccion=="Monte Carlo":
    from cg_engine import modelo as _modelo
    st.markdown("### 🎲 Simulación Monte Carlo — riesgo de la TIR y el VPN")
    st.caption("En vez de un solo número, simulamos miles de escenarios variando al azar **precio de venta**, "
               "**costo directo** y **ritmo de ventas (unidades/mes)**. La salida es la **TIR** y el **VPN del "
               "proyecto** — lo que mueve la decisión del comité — con su rango probable y la probabilidad de "
               "superar la tasa objetivo (TIO).")
    _audit = bool((par.get("fiducia") or {}).get("fcl_proyecto"))
    if _audit:
        st.info("ℹ️ Este proyecto tiene **TIR auditada de fiducia** (cifra fija). La simulación usa la **TIR del "
                "modelo** (que sí responde a las variables), no la auditada — sirve para ver el **riesgo relativo**, "
                "no para reemplazar la cifra de decisión.")
    c1,c2,c3,c4 = st.columns(4)
    n_sims = c1.select_slider("Simulaciones", options=[200,300,500,1000], value=300)
    rp = c2.slider("Precio (±%)", 5, 25, 15, 1)
    rc = c3.slider("Costo directo (±%)", 5, 20, 10, 1)
    rv = c4.slider("Ritmo de ventas (±%)", 0, 40, 25, 5,
                   help="Variación de las unidades vendidas por mes. Más ventas/mes → equilibrio y obra antes "
                        "→ escrituración antes → la caja entra antes → la TIR sube.")
    @st.cache_data(show_spinner="Simulando escenarios (TIR/VPN)…")
    def _mc(_parjson, n, dp, dc, dv):
        return _modelo.montecarlo_tir(json.loads(_parjson), n=n,
                                      rango_precio=(-dp/100, dp/100), rango_costo=(-dc/100, dc/100),
                                      rango_ventas=(-dv/100, dv/100))
    mc=_mc(json.dumps(par, ensure_ascii=False, sort_keys=True, default=str), n_sims, rp, rc, rv)
    st_t = mc["stats_tir"]; sv = mc["stats_vpn"]; se = mc["stats_equity"]; hurdle = mc["hurdle"]

    if not st_t.get("n"):
        st.warning("No se pudo simular la TIR: el proyecto necesita **etapas con fecha de inicio y ritmo de "
                   "ventas** (hitos) para construir el flujo. Revisa **Cronograma** y **Datos del proyecto**.")
    else:
        tT, tV, tE = st.tabs(["📈 TIR del proyecto", "💵 VPN del proyecto", "🏦 TIR del inversionista (socio)"])
        # ---- TIR del proyecto ----
        with tT:
            st.plotly_chart(_charts.montecarlo_hist(
                mc["tir_proyecto"], st_t["p10"], st_t["p50"], st_t["p90"], umbral=hurdle, es_pct=True,
                titulo="Monte Carlo — distribución de la TIR del proyecto",
                nombre_x="TIR", label_umbral=f"Bajo la TIO ({hurdle*100:.0f}%)"), width="stretch")
            kk=st.columns(4)
            kpi(kk[0],"Pesimista (P10)", fmt_pct(st_t["p10"]), "1 de cada 10 peor",
                RED if st_t["p10"]<hurdle else AMBER)
            kpi(kk[1],"Central (P50)", fmt_pct(st_t["p50"]), "mediana", TEAL)
            kpi(kk[2],"Optimista (P90)", fmt_pct(st_t["p90"]), "1 de cada 10 mejor", GREEN)
            _ph=mc["prob_tir_hurdle"]
            kpi(kk[3],f"Prob. TIR > TIO ({hurdle*100:.0f}%)", f"{_ph*100:.0f}%",
                ("alta" if _ph>=0.9 else "moderada" if _ph>=0.7 else "baja"),
                GREEN if _ph>=0.9 else (AMBER if _ph>=0.7 else RED))
            st.markdown(f"**Lectura:** en **{st_t['n']}** simulaciones, la TIR del proyecto cae con ~80% de "
                        f"probabilidad entre **{st_t['p10']*100:.1f}%** (P10) y **{st_t['p90']*100:.1f}%** (P90), "
                        f"con mediana **{st_t['p50']*100:.1f}%**. Probabilidad de superar la TIO "
                        f"({hurdle*100:.0f}%): **{_ph*100:.0f}%**.")
        # ---- VPN del proyecto ----
        with tV:
            _vmm=[v/1_000_000 for v in mc["vpn_proyecto"]]      # miles COP → mil M para el eje
            st.plotly_chart(_charts.montecarlo_hist(
                _vmm, sv["p10"]/1e6, sv["p50"]/1e6, sv["p90"]/1e6, umbral=0.0, es_pct=False,
                titulo="Monte Carlo — distribución del VPN del proyecto (@TIO)",
                nombre_x="VPN", unidad="mil M", label_umbral="VPN negativo"), width="stretch")
            kk=st.columns(4)
            kpi(kk[0],"Pesimista (P10)", fmt_mm(sv["p10"]), "1 de cada 10 peor",
                RED if sv["p10"]<0 else AMBER)
            kpi(kk[1],"Central (P50)", fmt_mm(sv["p50"]), "mediana", TEAL)
            kpi(kk[2],"Optimista (P90)", fmt_mm(sv["p90"]), "1 de cada 10 mejor", GREEN)
            _pv=mc["prob_vpn_pos"]
            kpi(kk[3],"Prob. VPN > 0", f"{_pv*100:.0f}%",
                ("alta" if _pv>=0.9 else "moderada" if _pv>=0.7 else "baja"),
                GREEN if _pv>=0.9 else (AMBER if _pv>=0.7 else RED))
            st.markdown(f"**Lectura:** el VPN @TIO cae con ~80% de probabilidad entre **{fmt_mm(sv['p10'])}** (P10) "
                        f"y **{fmt_mm(sv['p90'])}** (P90), con mediana **{fmt_mm(sv['p50'])}**. "
                        f"Probabilidad de VPN positivo: **{_pv*100:.0f}%**.")
        # ---- TIR del inversionista (equity apalancado) ----
        with tE:
            if se.get("n"):
                st.plotly_chart(_charts.montecarlo_hist(
                    mc["tir_equity"], se["p10"], se["p50"], se["p90"], umbral=hurdle, es_pct=True,
                    titulo="Monte Carlo — distribución de la TIR del inversionista (socio, apalancado)",
                    nombre_x="TIR socio", label_umbral=f"Bajo la TIO ({hurdle*100:.0f}%)"), width="stretch")
                kk=st.columns(3)
                kpi(kk[0],"Pesimista (P10)", fmt_pct(se["p10"]), "1 de cada 10 peor",
                    RED if (se["p10"] or 0)<hurdle else AMBER)
                kpi(kk[1],"Central (P50)", fmt_pct(se["p50"]), "mediana", TEAL)
                kpi(kk[2],"Optimista (P90)", fmt_pct(se["p90"]), "1 de cada 10 mejor", GREEN)
                st.caption("TIR del **socio apalancado** (equity): es más volátil que la del proyecto porque el "
                           "crédito constructor amplifica el resultado (apalancamiento).")
            else:
                st.info("La TIR del inversionista no converge en este proyecto (flujo de equity sin cambio de signo).")

        st.caption(f"Supuestos: precio ±{rp}%, costo directo ±{rc}% y ritmo de ventas ±{rv}% (distribución "
                   "uniforme), semilla fija (reproducible). Al variar el ritmo de ventas, la **escrituración sigue "
                   "a la obra** (entregas tras construir), por eso vender más rápido adelanta la caja y sube la TIR. "
                   "El motor recalcula hitos→recaudo→flujo apalancado en cada escenario; **no** altera el modelo "
                   "guardado ni la cifra auditada.")

# ============ SENSIBILIDAD ============
if seccion=="Sensibilidad":
    s=R["sensibilidades"]; base=R["pyg"]["util_oper"]
    # agrupar +/- por variable para el tornado (delta_pos/delta_neg respecto a la base)
    filas=[
        {"variable":"Precio de venta ±10%", "delta_pos":s.get("Precio +10%",0), "delta_neg":s.get("Precio -10%",0)},
        {"variable":"Costo directo ±10%",   "delta_pos":s.get("Costo directo -10%",0), "delta_neg":s.get("Costo directo +10%",0)},
    ]
    st.plotly_chart(_charts.tornado(filas, base, kpi_nombre="utilidad operativa"), width="stretch")
    st.caption("Tornado: impacto en la utilidad operativa al mover cada variable ±10%. La barra más larga "
               "= variable más sensible. Verde favorable / rojo desfavorable; la línea vertical es la base.")

# ============ MONITOR DE EJECUCIÓN (operativo, por torre) ============
if seccion=="Monitor de ejecución":
    st.markdown("### 🏗️ Monitor de Ejecución — seguimiento operativo")
    _nombre=meta.get("nombre","")
    if _nombre not in _nav.PROYECTOS_CON_MONITOR:
        st.info(f"**{_nombre}** aún no tiene datos operativos de comité cargados. El Monitor de Ejecución "
                "está disponible para proyectos en obra con seguimiento (hoy: **Navarra Apartamentos**).")
        st.caption("Esta vista es operativa (por torre) y NO altera el modelo financiero auditado.")
    else:
        st.caption("Datos de los **Comités de Gerencia (Feb–Abr 2026)**. Vista por torre (951 und en 4 etapas), "
                   "alineada con el modelo financiero auditado (951 und / TIR 37.6%).")
        # --- alertas activas ---
        _act=[a for a in _nav.NAVARRA_ALERTAS if a["estado"]=="Activa"]
        st.markdown(f"#### ⚠️ Alertas activas ({len(_act)})")
        render_alertas(_nav.NAVARRA_ALERTAS, solo_activas=True)

        tabs=st.tabs(["📊 Avance de obra","💰 Ejecución presupuestal","🏦 Crédito constructor","📋 Variaciones"])
        # ---- Tab avance ----
        with tabs[0]:
            real,banco=_nav.avance_ultimo()
            cortes=[{"periodo":p,"real":v["ejecutado"],"plan":v.get("programado")}
                    for p,v in _nav.NAVARRA_AVANCE_OBRA.items() if "bancolombia" not in p]
            plan_ult=next((c["plan"] for c in reversed(cortes) if c["plan"] is not None), None)
            kk=st.columns(4)
            kpi(kk[0],"Avance real (Torre 1)", f"{real:.1f}%", "Comité Abr 2026", GREEN)
            kpi(kk[1],"Avance programado", f"{plan_ult:.1f}%" if plan_ult else "n/d", "curva S plan", MUTED)
            kpi(kk[2],"Avance Bancolombia", f"{banco:.1f}%", "metodología bancaria", MUTED)
            _spi=(real/plan_ult) if plan_ult else None
            kpi(kk[3],"SPI (avance)", f"{_spi:.2f}" if _spi else "n/d",
                ("adelantado" if _spi and _spi>=1 else "atrasado") if _spi else "", GREEN if _spi and _spi>=1 else RED)
            st.plotly_chart(_charts.avance_real_vs_programado(cortes), width="stretch")
            rows=[{"Período":c["periodo"],"Real %":f"{c['real']:.1f}%",
                   "Plan %":(f"{c['plan']:.1f}%" if c["plan"] else "—"),
                   "Δ":(f"{c['real']-c['plan']:+.1f}%" if c["plan"] else "—"),
                   "Fuente":_nav.NAVARRA_AVANCE_OBRA[c["periodo"]].get("fuente","—")} for c in cortes]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        # ---- Tab ejecución presupuestal (EVM real por partida) ----
        with tabs[1]:
            PR=_nav.NAVARRA_PRESUPUESTO_T1; parts=PR["partidas"]
            bac=sum(p["base"] for p in parts); ac=sum(p["ejecutado"] for p in parts)
            eac=sum(p["proy_act"] for p in parts); aseg=sum(p["asegurado"] for p in parts)
            real_av,_=_nav.avance_ultimo(); ev=real_av/100.0*bac      # valor ganado = %avance × BAC
            cpi=(ev/ac) if ac else None; vac=bac-eac
            st.caption(f"Control de presupuesto Torre 1 · corte {PR['fecha_corte']} · valores en **millones COP**.")
            e=st.columns(5)
            kpi(e[0],"Presupuesto base (BAC)", f"${bac:,.0f} M".replace(",", "."), "planeado", MUTED)
            kpi(e[1],"Ejecutado (AC)", f"${ac:,.0f} M".replace(",", "."), f"{ac/bac*100:.0f}% del BAC", MUTED)
            kpi(e[2],"Proyectado final (EAC)", f"${eac:,.0f} M".replace(",", "."),
                ("ahorro" if vac>=0 else "sobrecosto"), GREEN if vac>=0 else RED)
            kpi(e[3],"CPI (eficiencia costo)", f"{cpi:.2f}" if cpi else "n/d",
                ("eficiente" if cpi and cpi>=1 else "sobrecosto") if cpi else "", GREEN if cpi and cpi>=1 else RED)
            kpi(e[4],"Variación final (VAC)", f"${vac:,.0f} M".replace(",", "."),
                ("bajo presupuesto" if vac>=0 else "sobre presupuesto"), GREEN if vac>=0 else RED)
            st.plotly_chart(_charts.variaciones_waterfall(parts), width="stretch")
            st.plotly_chart(_charts.presupuesto_barras(parts), width="stretch")
            st.markdown("##### Detalle por capítulo")
            dfp=pd.DataFrame([{"Capítulo":p["capitulo"],"Base":p["base"],"Ejecutado":p["ejecutado"],
                               "Asegurado":p["asegurado"],"Proyectado":p["proy_act"],
                               "Δ vs base":p["proy_act"]-p["base"]} for p in parts])
            st.dataframe(dfp, width="stretch", hide_index=True)
            st.caption("EAC (proyectado) vs BAC (base): VAC = "
                       f"${vac:,.0f} M ({'ahorro' if vac>=0 else 'sobrecosto'} proyectado). ".replace(",", ".")
                       + "EV (valor ganado) = avance real 42.0% × BAC. Aprovechable también en 📈 Valor Ganado.")
        # ---- Tab crédito ----
        with tabs[2]:
            cc=_nav.NAVARRA_CREDITO_CONSTRUCTOR
            st.markdown("##### 🏗️ Torre 1 — crédito constructor")
            t1=st.columns(3)
            kpi(t1[0],"Monto autorizado", f"${cc['torre_1']['monto_autorizado_mm']:,} M".replace(",", "."), "Bancolombia", GREEN)
            kpi(t1[1],"Avance requerido", f"{cc['torre_1']['avance_requerido_pct']:.2f}%", "Castillo Medina", MUTED)
            kpi(t1[2],"Estado", "✅ Autorizado", cc['torre_1']['fecha_autorizacion'], GREEN)
            st.markdown("##### 🏗️ Torres 2A/2B — crédito en trámite")
            t2=st.columns(3)
            kpi(t2[0],"Días en trámite", f"{_nav.dias_tramite_t2()} días", "desde 09-ene-2026 (en vivo)", RED)
            kpi(t2[1],"Saldo preventas", f"${cc['torre_2a_2b']['saldo_encargo_preventas_mm']:,} M".replace(",", "."), "disponible", MUTED)
            kpi(t2[2],"Crédito puente req.", f"${cc['torre_2a_2b']['credito_puente_requerido_mm']:,} M".replace(",", "."), "apalancamiento", RED)
            pend=cc['torre_2a_2b']['tramites_pendientes']
            st.warning(f"⚠️ {len(pend)} trámites pendientes — fecha crítica **16-jun-2026**")
            st.dataframe(pd.DataFrame([{"Actividad":t["actividad"],"Fecha límite":t["fecha_fin"],"Estado":t["estado"]} for t in pend]),
                         width="stretch", hide_index=True)
        # ---- Tab variaciones ----
        with tabs[3]:
            v=_nav.NAVARRA_VARIACIONES
            ic={"Alto":"🔴","Medio":"🟡","Bajo":"⚪"}
            c1,c2=st.columns(2)
            with c1:
                st.markdown(f"##### 🔴 Sobrecostos ({len(v['sobrecostos'])})")
                for s in v["sobrecostos"]:
                    st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;padding:9px 11px;margin-bottom:6px;">'
                        f'<b style="font-size:12px;color:#991B1B;">{ic.get(s["impacto"],"⚪")} {s["partida"]}</b>'
                        f'<div style="font-size:11px;color:#7F1D1D;margin-top:2px;">{s["descripcion"]}</div>'
                        f'<div style="font-size:10px;color:#9CA3AF;margin-top:3px;">{", ".join(s["meses"])} · {s["impacto"]}</div></div>',
                        unsafe_allow_html=True)
            with c2:
                st.markdown(f"##### 🟢 Ahorros ({len(v['ahorros'])})")
                for a in v["ahorros"]:
                    st.markdown(f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:6px;padding:9px 11px;margin-bottom:6px;">'
                        f'<b style="font-size:12px;color:#14532D;">{ic.get(a["impacto"],"⚪")} {a["partida"]}</b>'
                        f'<div style="font-size:11px;color:#166534;margin-top:2px;">{a["descripcion"]}</div>'
                        f'<div style="font-size:10px;color:#9CA3AF;margin-top:3px;">{", ".join(a["meses"])} · {a["impacto"]}</div></div>',
                        unsafe_allow_html=True)

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
st.caption(f"Aplicativo v2.36.0 · motor v{ENGINE_V} · datos: {_origen}{_diag} · CG Constructora")
