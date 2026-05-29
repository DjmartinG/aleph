# -*- coding: utf-8 -*-
"""
Aplicativo de Prefactibilidad / Factibilidad — CG Constructora.
Capa de presentación (Streamlit). NO contiene lógica financiera: usa engine/ (fuente única).
Identidad de marca CG: teal #004854 + ámbar #F09C00. v1.1.0
"""
import json, io, copy
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
from engine import calcular, __version__ as ENGINE_V

# ---------------- marca CG ----------------
TEAL="#004854"; AMBER="#F09C00"; INK="#13262B"; MUTED="#6B7280"
GREEN="#1E874B"; RED="#C0392B"; BORDER="#E6E9EF"
HERE=Path(__file__).parent; PROY_DIR=HERE/"proyectos"; LOGO=HERE/"assets"/"logo_cg.png"
_icon = str(LOGO) if LOGO.exists() else "🏗️"
st.set_page_config(page_title="Factibilidad CG", page_icon=_icon, layout="wide")

# ---------------- plantilla Plotly CG ----------------
pio.templates["cg"]=go.layout.Template(layout=dict(
    font=dict(family="Inter, sans-serif", color=INK, size=13),
    paper_bgcolor="white", plot_bgcolor="white",
    colorway=[TEAL, AMBER, GREEN, MUTED, RED, "#0E7C86"],
    margin=dict(l=54, r=24, t=54, b=44),
    xaxis=dict(gridcolor="#EEF1F5", zerolinecolor=BORDER),
    yaxis=dict(gridcolor="#EEF1F5", zerolinecolor=BORDER),
    legend=dict(orientation="h", y=-0.2),
    title=dict(font=dict(size=15, color=TEAL)),
))
pio.templates.default="cg"

# ---------------- CSS de marca ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp { font-family:'Inter',-apple-system,sans-serif; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stStatusWidget"] { visibility:hidden; height:0; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#F7F9FA; border-right:1px solid #E6E9EF; }
.block-container { padding-top:1.3rem; max-width:1300px; }
h1 { color:#004854; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; }
h2,h3 { color:#13262B; font-weight:700; }
.brandbar { height:4px; background:linear-gradient(90deg,#004854 0%,#F09C00 100%); border-radius:4px; margin:.4rem 0 1rem; }
.kpi { background:#fff; border:1px solid #E6E9EF; border-radius:14px; padding:12px 14px;
       box-shadow:0 1px 2px rgba(16,24,40,.05); min-height:104px; }
.kpi .l { font-size:.64rem; font-weight:600; letter-spacing:.04em; text-transform:uppercase; color:#6B7280; min-height:1.9em; }
.kpi .v { font-size:1.22rem; font-weight:700; color:#004854; margin-top:6px; line-height:1.15; white-space:nowrap; }
.kpi .s { font-size:.74rem; font-weight:600; margin-top:3px; }
.stTabs [data-baseweb="tab"] { font-weight:600; }
.stTabs [aria-selected="true"] { color:#004854 !important; }
[data-testid="stMetricValue"] { color:#004854; }
</style>
""", unsafe_allow_html=True)

def fmt_mm(x): return f"${x/1000:,.0f} M" if x else "$0"
def fmt_pct(x): return f"{x*100:.2f}%" if x is not None else "n/d"
def kpi(col, label, value, sub="", sub_color=MUTED):
    s = f'<div class="s" style="color:{sub_color}">{sub}</div>' if sub else ''
    col.markdown(f'<div class="kpi"><div class="l">{label}</div><div class="v">{value}</div>{s}</div>',
                 unsafe_allow_html=True)
def cargar(n): return json.loads((PROY_DIR/f"{n}.json").read_text(encoding="utf-8"))
def listar(): return sorted(p.stem for p in PROY_DIR.glob("*.json"))

# ---------------- sidebar ----------------
with st.sidebar:
    if LOGO.exists(): st.image(str(LOGO), width=150)
    st.markdown("### Proyecto")
    up = st.file_uploader("🔒 Cargar proyecto privado (.json)", type=["json"],
        help="Datos confidenciales: se cargan SOLO en tu sesión, no se guardan en el repositorio público.")
    if up is not None:
        if st.session_state.get("sel") != up.name:
            st.session_state.par = json.load(up); st.session_state.sel = up.name
        sel = up.name.replace(".json","")
        st.success(f"🔒 Privado: {st.session_state.par.get('meta',{}).get('nombre', sel)}")
    else:
        proys = listar()
        sel = st.selectbox("O usar un ejemplo", proys, index=0 if proys else None)
        if "par" not in st.session_state or st.session_state.get("sel") != sel:
            st.session_state.par = cargar(sel); st.session_state.sel = sel
    par = st.session_state.par

    st.markdown("###### Ventas por etapa (miles COP)")
    _pk = st.session_state.get("sel","x")
    for i,e in enumerate(par["etapas"]):
        e["ventas_miles"] = st.number_input(e["nom"], value=float(e["ventas_miles"]),
            step=1_000_000.0, format="%.0f", key=f"et_{_pk}_{i}")
    st.markdown("###### Costos (% sobre ventas)")
    c=par["costos_pct"]
    c["directos"]   = st.slider("Directos", 0.30, 0.70, float(c["directos"]), 0.001)
    c["indirectos"] = st.slider("Indirectos", 0.05, 0.30, float(c["indirectos"]), 0.001)
    c["honorarios"] = st.slider("Honorarios", 0.05, 0.12, float(c["honorarios"]), 0.001)
    par["lote_bruto_miles"] = st.number_input("Lote bruto (miles COP)",
        value=float(par["lote_bruto_miles"]), step=500_000.0, format="%.0f")
    st.markdown("###### Financiero")
    f=par["financiero"]
    f["tasa_credito_ea"] = st.slider("Tasa crédito E.A.", 0.08, 0.25, float(f["tasa_credito_ea"]), 0.005)
    f["split_cg"] = st.slider("Reparto utilidad CG", 0.0, 1.0, float(f["split_cg"]), 0.05)
    f["tir_apalancada_ref"] = st.number_input("TIR apalancada de referencia",
        value=float(f.get("tir_apalancada_ref",0.20)), step=0.01, format="%.4f")

# ---------------- cálculo ----------------
R = calcular(copy.deepcopy(par)); pg=R["pyg"]; fl=R["flujo"]; meta=R["meta"]

# ---------------- encabezado ----------------
hc1,hc2 = st.columns([1,9])
if LOGO.exists():
    hc1.image(str(LOGO), width=78)
hc2.markdown("<h1>Factibilidad de Proyectos</h1>", unsafe_allow_html=True)
hc2.caption(f"CG Constructora · {meta.get('nombre','')} · {meta.get('ubicacion','')} · {meta.get('unidades','')} unidades")
st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)

# ---------------- KPIs ----------------
k=st.columns(6)
kpi(k[0],"Ventas totales", fmt_mm(pg["ventas"]))
kpi(k[1],"Utilidad operativa", fmt_mm(pg["util_oper"]), fmt_pct(pg["margen_oper"]), GREEN)
kpi(k[2],"UDI", fmt_mm(pg["udi"]))
kpi(k[3],"TIR apalancada (ref)", fmt_pct(fl["tir_apalancada_ref"]), "modelo aprobado", MUTED)
kpi(k[4],"VPN @WACC", fmt_mm(fl["vpn_proyecto"]))
kpi(k[5],"Crédito máx", fmt_mm(fl["credito_max"]))
st.write("")

tabs = st.tabs(["📊 P&G","🤝 Reparto","📈 Distribución costos","💵 Flujo de caja",
                "🎯 Escenarios","🌪️ Sensibilidad","🏙️ Urbanístico"])

with tabs[0]:
    df=pd.DataFrame([
        ("Ingresos por ventas",pg["ventas"]),("(+) Reconocimiento Codensa",pg["recon_codensa"]),
        ("(-) Costo lote",-pg["costo_lote"]),("(-) Costos directos",-pg["directos"]),
        ("(-) Costos indirectos",-pg["indirectos"]),("(-) Honorarios",-pg["honorarios"]),
        ("UTILIDAD OPERATIVA",pg["util_oper"]),("(-) Provisión renta",-pg["renta"]),("UDI",pg["udi"]),
    ],columns=["Concepto","Miles COP"]); df["% ventas"]=df["Miles COP"]/pg["ventas"]
    st.dataframe(df.style.format({"Miles COP":"{:,.0f}","% ventas":"{:.1%}"}), width="stretch", hide_index=True)

with tabs[1]:
    s=par["financiero"]["split_cg"]
    fig=go.Figure(data=[go.Pie(labels=["CG","Socio"],values=[pg["cg"],pg["socio"]],hole=.55,
                  marker_colors=[TEAL,AMBER])]); fig.update_layout(title="Distribución de resultados",height=360)
    st.plotly_chart(fig, width="stretch")

with tabs[2]:
    d=R["distribucion"]; m=list(range(1,len(d["escalada"])+1))
    fig=go.Figure(); fig.add_bar(x=m,y=d["escalada"],name="Costo mensual",marker_color=TEAL)
    fig.add_scatter(x=m,y=d["acumulada"],name="Acumulado",yaxis="y2",line=dict(color=AMBER,width=3))
    fig.update_layout(title=f"Distribución del costo directo — curva PERT (pico mes {d['pico_mes']})",
                      yaxis2=dict(overlaying="y",side="right",showgrid=False),height=420,xaxis_title="Mes de obra")
    st.plotly_chart(fig, width="stretch")

with tabs[3]:
    n=len([x for x in fl["flujo"] if abs(x)>1])+2; m=list(range(1,n+1))
    fig=go.Figure(); fig.add_bar(x=m,y=fl["flujo"][:n],name="Flujo mensual",marker_color=TEAL)
    fig.add_scatter(x=m,y=fl["acumulado"][:n],name="Acumulado",line=dict(color=INK,width=3))
    fig.add_scatter(x=m,y=fl["saldo_credito"][:n],name="Saldo crédito",line=dict(color=AMBER,dash="dot"))
    fig.update_layout(title="Flujo de caja del proyecto (costos por curva PERT)",height=430,xaxis_title="Mes")
    st.plotly_chart(fig, width="stretch")
    cc=st.columns(4)
    kpi(cc[0],"TIR proyecto (no apal.)",fmt_pct(fl["tir_proyecto"]))
    kpi(cc[1],"Crédito constructor máx",fmt_mm(fl["credito_max"]))
    kpi(cc[2],"Necesidad máx de caja",fmt_mm(fl["max_caja"]))
    kpi(cc[3],"Intereses (prelim.)",fmt_mm(fl["intereses_total"]))

with tabs[4]:
    esc=R["escenarios"]
    fig=go.Figure(data=[go.Bar(x=list(esc.keys()),y=[v["util_oper"] for v in esc.values()],
        marker_color=[TEAL,GREEN,RED],text=[fmt_pct(v["margen"]) for v in esc.values()],textposition="outside")])
    fig.update_layout(title="Utilidad operativa por escenario",height=400)
    st.plotly_chart(fig, width="stretch")
    st.caption("Optimista: +5% precio, −2% costo · Pesimista: −10% precio, +5% costo")

with tabs[5]:
    s=R["sensibilidades"]; it=sorted(s.items(),key=lambda kv:kv[1])
    fig=go.Figure(data=[go.Bar(y=[k for k,_ in it],x=[v for _,v in it],orientation="h",
        marker_color=[GREEN if v>=0 else RED for _,v in it])])
    fig.update_layout(title="Tornado — impacto en utilidad operativa (miles COP)",height=360)
    st.plotly_chart(fig, width="stretch")

with tabs[6]:
    u=R["urbanistico"]
    df=pd.DataFrame([
        ("Área lote bruta (m²)",u["lote_bruta"]),("Área lote útil (m²)",u["lote_util"]),
        ("Ratio bruta/útil",u["ratio_bruta_util"]),("Área construida (m²)",u["area_construida"]),
        ("Área vendible (m²)",u["area_vendible"]),("Índice de construcción",u["indice_construccion"]),
        ("Aprovechamiento",u["aprovechamiento"]),("Densidad (und/ha)",u["densidad_und_ha"]),
        ("Precio venta /m² (COP)",u["precio_m2_vend"]),("Costo directo /m² const (COP)",u["costo_dir_m2_const"]),
    ],columns=["Indicador","Valor"])
    st.dataframe(df.style.format({"Valor":"{:,.2f}"}), width="stretch", hide_index=True)

# ---------------- acciones ----------------
st.markdown('<div class="brandbar"></div>', unsafe_allow_html=True)
a1,a2=st.columns(2)
with a1:
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as xl:
        pd.DataFrame([{"Concepto":"Ventas","Miles COP":pg["ventas"]},
            {"Concepto":"Utilidad operativa","Miles COP":pg["util_oper"]},
            {"Concepto":"UDI","Miles COP":pg["udi"]},{"Concepto":"CG","Miles COP":pg["cg"]},
            {"Concepto":"Socio","Miles COP":pg["socio"]},
            {"Concepto":"Credito max","Miles COP":fl["credito_max"]}]).to_excel(xl,sheet_name="Resumen",index=False)
        pd.DataFrame({"Mes":range(1,len(fl["flujo"])+1),"Flujo":fl["flujo"],
            "Acumulado":fl["acumulado"],"SaldoCredito":fl["saldo_credito"]}).to_excel(xl,sheet_name="Flujo",index=False)
    st.download_button("📥 Exportar a Excel", buf.getvalue(),
        file_name=f"Factibilidad_{sel}_{date.today():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with a2:
    par["_fecha"]=str(date.today())
    st.download_button("💾 Descargar proyecto (.json)",
        json.dumps(par,ensure_ascii=False,indent=2).encode("utf-8"),
        file_name=f"{sel}.json", mime="application/json",
        help="Guarda los parámetros editados en tu equipo (privado). No se sube al repositorio.")
st.caption(f"Aplicativo v1.1.0 · motor v{ENGINE_V} · enfoque híbrido · CG Constructora")
