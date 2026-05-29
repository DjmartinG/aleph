# -*- coding: utf-8 -*-
"""
Aplicativo de Prefactibilidad / Factibilidad — CG Constructora.
Capa de presentación (Streamlit). NO contiene lógica financiera: usa engine/ (fuente única).
v1.0.0
"""
import json, io, copy
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from engine import calcular, __version__ as ENGINE_V

st.set_page_config(page_title="Factibilidad CG", page_icon="🏗️", layout="wide")
PROY_DIR = Path(__file__).parent / "proyectos"
NAVY="#1F3864"; TEAL="#2E75B6"; GREEN="#375623"; AMBER="#BF9000"; RED="#C00000"

def fmt_mm(x): return f"${x/1000:,.0f} M" if x else "$0"
def fmt_pct(x): return f"{x*100:.2f}%" if x is not None else "n/d"

# ---------------- carga de proyectos ----------------
def listar_proyectos():
    return sorted(p.stem for p in PROY_DIR.glob("*.json"))
def cargar(nombre):
    return json.loads((PROY_DIR/f"{nombre}.json").read_text(encoding="utf-8"))

st.title("🏗️ Factibilidad de Proyectos — CG Constructora")
st.caption(f"Aplicativo v1.0.0 · motor v{ENGINE_V} · enfoque híbrido (modelo propio + TIR apalancada de referencia)")

# ---------------- sidebar: selección + edición ----------------
with st.sidebar:
    st.header("Proyecto")
    up = st.file_uploader("🔒 Cargar proyecto privado (.json)", type=["json"],
        help="Datos confidenciales: se cargan SOLO en tu sesión, no se guardan en el repositorio público.")
    if up is not None:
        if st.session_state.get("sel") != up.name:
            st.session_state.par = json.load(up); st.session_state.sel = up.name
        sel = up.name.replace(".json", "")
        st.success(f"🔒 Privado: {st.session_state.par.get('meta',{}).get('nombre', sel)}")
    else:
        proyectos = listar_proyectos()
        sel = st.selectbox("O usar un ejemplo", proyectos, index=0 if proyectos else None)
        if "par" not in st.session_state or st.session_state.get("sel") != sel:
            st.session_state.par = cargar(sel); st.session_state.sel = sel
    par = st.session_state.par

    st.subheader("Ventas por etapa (miles COP)")
    _pk = st.session_state.get("sel", "x")   # llave por proyecto: evita que los valores
    for i,e in enumerate(par["etapas"]):       # de un proyecto "se peguen" al cambiar a otro
        e["ventas_miles"] = st.number_input(e["nom"], value=float(e["ventas_miles"]),
                                             step=1_000_000.0, format="%.0f", key=f"et_{_pk}_{i}")
    st.subheader("Costos (% sobre ventas)")
    c=par["costos_pct"]
    c["directos"]   = st.slider("Directos", 0.30, 0.70, float(c["directos"]), 0.001)
    c["indirectos"] = st.slider("Indirectos", 0.05, 0.30, float(c["indirectos"]), 0.001)
    c["honorarios"] = st.slider("Honorarios", 0.05, 0.12, float(c["honorarios"]), 0.001)
    par["lote_bruto_miles"] = st.number_input("Lote bruto (miles COP)",
                                value=float(par["lote_bruto_miles"]), step=500_000.0, format="%.0f")
    st.subheader("Financiero")
    f=par["financiero"]
    f["tasa_credito_ea"] = st.slider("Tasa crédito E.A.", 0.08, 0.25, float(f["tasa_credito_ea"]), 0.005)
    f["split_cg"] = st.slider("Reparto utilidad CG", 0.0, 1.0, float(f["split_cg"]), 0.05)
    f["tir_apalancada_ref"] = st.number_input("TIR apalancada de referencia",
                                value=float(f.get("tir_apalancada_ref",0.2183)), step=0.01, format="%.4f")

# ---------------- cálculo ----------------
R = calcular(copy.deepcopy(par))
pg=R["pyg"]; fl=R["flujo"]; ur=R["urbanistico"]; meta=R["meta"]

# ---------------- KPIs ----------------
st.subheader(f"{meta.get('nombre','')} · {meta.get('ubicacion','')} · {meta.get('unidades','')} und")
k=st.columns(6)
k[0].metric("Ventas totales", fmt_mm(pg["ventas"]))
k[1].metric("Utilidad operativa", fmt_mm(pg["util_oper"]), fmt_pct(pg["margen_oper"]))
k[2].metric("UDI", fmt_mm(pg["udi"]))
k[3].metric("TIR apalancada (ref)", fmt_pct(fl["tir_apalancada_ref"]))
k[4].metric("VPN @WACC", fmt_mm(fl["vpn_proyecto"]))
k[5].metric("Crédito máx", fmt_mm(fl["credito_max"]))

tabs = st.tabs(["📊 P&G","🤝 Reparto","📈 Distribución costos","💵 Flujo de caja",
                "🎯 Escenarios","🌪️ Sensibilidad","🏙️ Urbanístico"])

with tabs[0]:
    df=pd.DataFrame([
        ("Ingresos por ventas",pg["ventas"]),("(+) Reconocimiento Codensa",pg["recon_codensa"]),
        ("(-) Costo lote",-pg["costo_lote"]),("(-) Costos directos",-pg["directos"]),
        ("(-) Costos indirectos",-pg["indirectos"]),("(-) Honorarios",-pg["honorarios"]),
        ("UTILIDAD OPERATIVA",pg["util_oper"]),("(-) Provisión renta",-pg["renta"]),
        ("UDI",pg["udi"]),
    ],columns=["Concepto","Miles COP"])
    df["% ventas"]=df["Miles COP"]/pg["ventas"]
    st.dataframe(df.style.format({"Miles COP":"{:,.0f}","% ventas":"{:.1%}"}),
                 width="stretch", hide_index=True)

with tabs[1]:
    rep=pd.DataFrame([
        ("Honorarios construcción",0,pg["hon_construccion"]),
        ("Honorarios gerencia",pg["hon_gerencia"],0),
        ("Honorarios comercialización",pg["hon_ventas"],0),
        ("Utilidad proyecto",pg["util_oper"]*par["financiero"]["split_cg"],pg["util_oper"]*(1-par["financiero"]["split_cg"])),
        ("Utilidad lote",pg["util_lote"],0),
    ],columns=["Concepto","CG","Socio"])
    st.dataframe(rep.style.format({"CG":"{:,.0f}","Socio":"{:,.0f}"}),width="stretch",hide_index=True)
    fig=go.Figure(data=[go.Pie(labels=["CG","Socio (TripleA)"],values=[pg["cg"],pg["socio"]],hole=.5,
                               marker_colors=[NAVY,AMBER])])
    fig.update_layout(title="Distribución de resultados",height=350)
    st.plotly_chart(fig,width="stretch")

with tabs[2]:
    d=R["distribucion"]; meses=list(range(1,len(d["escalada"])+1))
    fig=go.Figure()
    fig.add_bar(x=meses,y=d["escalada"],name="Costo mensual (PERT)",marker_color=TEAL)
    fig.add_scatter(x=meses,y=d["acumulada"],name="Acumulado",yaxis="y2",line=dict(color=NAVY,width=3))
    fig.update_layout(title=f"Distribución del costo directo — curva PERT (pico mes {d['pico_mes']})",
                      yaxis2=dict(overlaying="y",side="right"),height=400,xaxis_title="Mes de obra")
    st.plotly_chart(fig,width="stretch")
    st.caption(f"Escalación Materiales/MO (80/20): +{d['incremento']/1000:,.0f} M sobre el costo base.")

with tabs[3]:
    n=len([x for x in fl["flujo"] if abs(x)>1])+2
    meses=list(range(1,n+1))
    fig=go.Figure()
    fig.add_bar(x=meses,y=fl["flujo"][:n],name="Flujo mensual",marker_color=TEAL)
    fig.add_scatter(x=meses,y=fl["acumulado"][:n],name="Acumulado",line=dict(color=NAVY,width=3))
    fig.add_scatter(x=meses,y=fl["saldo_credito"][:n],name="Saldo crédito",line=dict(color=AMBER,dash="dot"))
    fig.update_layout(title="Flujo de caja del proyecto (costos por curva PERT)",height=420,xaxis_title="Mes")
    st.plotly_chart(fig,width="stretch")
    c=st.columns(4)
    c[0].metric("TIR proyecto (no apal.)",fmt_pct(fl["tir_proyecto"]))
    c[1].metric("Crédito constructor máx",fmt_mm(fl["credito_max"]))
    c[2].metric("Necesidad máx de caja",fmt_mm(fl["max_caja"]))
    c[3].metric("Intereses (prelim.)",fmt_mm(fl["intereses_total"]))
    st.info("La TIR de decisión es la **apalancada de referencia** (KPI superior). "
            "El flujo propio dimensiona el crédito; ver directiva (enfoque híbrido).")

with tabs[4]:
    esc=R["escenarios"]
    fig=go.Figure(data=[go.Bar(x=list(esc.keys()),y=[v["util_oper"] for v in esc.values()],
                  marker_color=[TEAL,GREEN,RED],text=[fmt_pct(v["margen"]) for v in esc.values()],textposition="outside")])
    fig.update_layout(title="Utilidad operativa por escenario",height=400)
    st.plotly_chart(fig,width="stretch")
    st.caption("Optimista: +5% precio, -2% costo · Pesimista: -10% precio, +5% costo")

with tabs[5]:
    s=R["sensibilidades"]; items=sorted(s.items(),key=lambda kv:kv[1])
    fig=go.Figure(data=[go.Bar(y=[k for k,_ in items],x=[v for _,v in items],orientation="h",
                  marker_color=[GREEN if v>=0 else RED for _,v in items])])
    fig.update_layout(title="Tornado — impacto en utilidad operativa (miles COP)",height=350)
    st.plotly_chart(fig,width="stretch")

with tabs[6]:
    u=R["urbanistico"]
    df=pd.DataFrame([
        ("Área lote bruta (m²)",u["lote_bruta"]),("Área lote útil (m²)",u["lote_util"]),
        ("Ratio bruta/útil",u["ratio_bruta_util"]),("Área construida (m²)",u["area_construida"]),
        ("Área vendible (m²)",u["area_vendible"]),("Índice de construcción",u["indice_construccion"]),
        ("Aprovechamiento",u["aprovechamiento"]),("Densidad (und/ha)",u["densidad_und_ha"]),
        ("Precio venta /m² (COP)",u["precio_m2_vend"]),("Costo directo /m² const (COP)",u["costo_dir_m2_const"]),
    ],columns=["Indicador","Valor"])
    st.dataframe(df.style.format({"Valor":"{:,.2f}"}),width="stretch",hide_index=True)

# ---------------- acciones: exportar + guardar versión ----------------
st.divider()
col1,col2=st.columns(2)
with col1:
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as xl:
        pd.DataFrame([{"Concepto":"Ventas","Miles COP":pg["ventas"]},
                      {"Concepto":"Utilidad operativa","Miles COP":pg["util_oper"]},
                      {"Concepto":"UDI","Miles COP":pg["udi"]},
                      {"Concepto":"CG","Miles COP":pg["cg"]},
                      {"Concepto":"Socio","Miles COP":pg["socio"]},
                      {"Concepto":"Credito max","Miles COP":fl["credito_max"]}]).to_excel(xl,sheet_name="Resumen",index=False)
        pd.DataFrame({"Mes":range(1,len(fl["flujo"])+1),"Flujo":fl["flujo"],
                      "Acumulado":fl["acumulado"],"SaldoCredito":fl["saldo_credito"]}).to_excel(xl,sheet_name="Flujo",index=False)
    st.download_button("📥 Exportar a Excel",buf.getvalue(),
        file_name=f"Factibilidad_{sel}_{date.today():%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with col2:
    par["_fecha"]=str(date.today())
    st.download_button("💾 Descargar proyecto (.json)",
        json.dumps(par, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"{sel}.json", mime="application/json",
        help="Guarda los parámetros editados en tu equipo (privado). No se sube al repositorio.")
