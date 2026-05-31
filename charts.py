# -*- coding: utf-8 -*-
"""
Gráficos financieros de nivel institucional para Factibilidad CG (APEX ARCHITECT®).

Adaptados a las estructuras REALES del motor (listas mensuales, no DataFrames) y a la
**marca CG aprobada** (teal #004854 + ámbar #F09C00), no a colores genéricos.

Convenciones de la industria (Bloomberg/IFRS, PMI/Camacol, fiduciaria CO):
  - flujo_caja_waterfall : barras verde/rojo por caja +/−, acumulado, saldo crédito, pico de exposición
  - curva_obra_s         : campana de costo directo + curva S de avance acumulado
  - recaudo_stacked      : área apilada separación/cuota inicial/subrogación
  - tornado              : sensibilidad unidimensional ordenada por impacto
  - escenarios_grouped   : barras agrupadas base/optimista/pesimista
  - gantt_etapas         : cronograma ventas (teal) + construcción (ámbar) por etapa

Todas devuelven un go.Figure listo para st.plotly_chart(fig, width="stretch").
"""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.io as pio

# ---- paleta CG (alineada con app.py) ----
TEAL = "#004854"; AMBER = "#F09C00"; INK = "#13262B"; MUTED = "#6B7280"
GREEN = "#1E874B"; RED = "#C0392B"; BORDER = "#E6E9EF"


def registrar_template() -> None:
    """Registra y activa la plantilla Plotly 'cg' (idempotente)."""
    pio.templates["cg"] = go.layout.Template(layout=dict(
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK),
        paper_bgcolor="white", plot_bgcolor="white",
        colorway=[TEAL, AMBER, GREEN, MUTED, RED, "#0E7C86"],
        xaxis=dict(gridcolor="#EEF1F5", linecolor=BORDER, tickfont=dict(size=11), zeroline=False),
        yaxis=dict(gridcolor="#EEF1F5", linecolor=BORDER, tickfont=dict(size=11),
                   zeroline=True, zerolinecolor="#CBD5E1", zerolinewidth=1.4),
        legend=dict(orientation="h", y=1.02, x=0, bgcolor="rgba(255,255,255,.9)",
                    bordercolor=BORDER, borderwidth=1, font=dict(size=11)),
        hoverlabel=dict(bgcolor="white", bordercolor=TEAL, font=dict(size=12, color=INK)),
        margin=dict(l=58, r=24, t=52, b=46),
        title=dict(font=dict(size=14, color=TEAL), x=0)))
    pio.templates.default = "cg"


def _recortar(series, extra=2):
    """Último índice con valor != 0 (+extra), para no graficar la cola de ceros."""
    nz = [i for i, v in enumerate(series) if abs(v) > 1]
    return (nz[-1] + extra) if nz else min(len(series), 12)


# ----------------------------------------------------------------------------- flujo de caja
def flujo_caja_waterfall(flujo, acumulado, saldo_credito=None, titulo="Flujo de caja del proyecto — mensual"):
    """Barras verde/rojo del flujo neto mensual + acumulado + saldo de crédito + pico de exposición.

    Args:
        flujo: lista del flujo neto por mes (miles COP).
        acumulado: lista de la caja acumulada por mes.
        saldo_credito: lista del saldo de crédito constructor (opcional).
    """
    n = max(_recortar(flujo), _recortar(acumulado))
    x = list(range(1, n + 1))
    fig = go.Figure()
    colores = [GREEN if v >= 0 else RED for v in flujo[:n]]
    fig.add_bar(x=x, y=flujo[:n], name="Flujo neto mensual", marker_color=colores, opacity=0.85,
                hovertemplate="Mes %{x}<br>Flujo: %{y:,.0f} mil COP<extra></extra>")
    fig.add_scatter(x=x, y=acumulado[:n], name="Caja acumulada", line=dict(color=INK, width=2.5),
                    hovertemplate="Mes %{x}: %{y:,.0f} acum.<extra></extra>")
    if saldo_credito:
        fig.add_scatter(x=x, y=saldo_credito[:n], name="Saldo crédito constructor",
                        line=dict(color=AMBER, width=2, dash="dot"))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    # pico de exposición (mínimo del acumulado)
    sub = acumulado[:n]
    if sub:
        idx = min(range(len(sub)), key=lambda i: sub[i])
        if sub[idx] < -1:
            fig.add_annotation(x=idx + 1, y=sub[idx],
                text=f"Exposición máx<br><b>{sub[idx]/1000:,.1f} mil M</b>".replace(",", "."),
                bgcolor="white", bordercolor=RED, borderwidth=1, font=dict(size=11, color=RED),
                showarrow=True, arrowhead=2, arrowcolor=RED)
    fig.update_layout(title=titulo, height=430, xaxis_title="Mes", yaxis_title="Miles COP",
                      barmode="overlay")
    return fig


# ----------------------------------------------------------------------------- curva S obra
def curva_obra_s(escalada, acumulada, titulo="Curva S de avance de obra (costo directo)"):
    """Campana de costo directo mensual (barras) + curva S de avance acumulado en % (eje der.)."""
    n = min(_recortar(escalada), len(escalada)); x = list(range(1, n + 1))
    total = (sum(escalada) or 1)                       # base del avance = costo directo total
    acum = []; run = 0.0
    for i in range(n):
        run += escalada[i] if i < len(escalada) else 0
        acum.append(run)
    avance = [(acum[i] / total) if total else 0 for i in range(n)]
    fig = go.Figure()
    fig.add_bar(x=x, y=escalada[:n], name="Costo directo mensual", marker_color=TEAL, opacity=0.85,
                hovertemplate="Mes %{x}: %{y:,.0f} mil COP<extra></extra>")
    fig.add_scatter(x=x, y=avance, name="Avance acumulado", yaxis="y2",
                    line=dict(color=AMBER, width=3), fill="tozeroy", fillcolor="rgba(240,156,0,.08)",
                    hovertemplate="Mes %{x}: %{y:.0%} avance<extra></extra>")
    # pico de la campana
    if escalada[:n]:
        pk = max(range(n), key=lambda i: escalada[i])
        fig.add_annotation(x=pk + 1, y=escalada[pk], text=f"Pico obra<br>mes {pk+1}",
                           showarrow=True, arrowhead=2, arrowcolor=TEAL, font=dict(size=11, color=TEAL),
                           bgcolor="white", bordercolor=TEAL, borderwidth=1)
    fig.update_layout(title=titulo, height=410, xaxis_title="Mes de obra", yaxis_title="Miles COP",
                      yaxis2=dict(overlaying="y", side="right", title="Avance", tickformat=".0%",
                                  range=[0, 1.05], showgrid=False))
    return fig


# ----------------------------------------------------------------------------- recaudo apilado
def recaudo_stacked(separacion, cuota_inicial, subrogacion, titulo="Recaudo mensual por componente"):
    """Área apilada: separación (ámbar) + cuota inicial (teal) + subrogación (verde)."""
    n = max(_recortar(separacion), _recortar(cuota_inicial), _recortar(subrogacion))
    x = list(range(1, n + 1))
    fig = go.Figure()
    fig.add_scatter(x=x, y=separacion[:n], name="Separación", stackgroup="r",
                    line=dict(width=0.5, color=AMBER), fillcolor="rgba(240,156,0,.55)")
    fig.add_scatter(x=x, y=cuota_inicial[:n], name="Cuota inicial", stackgroup="r",
                    line=dict(width=0.5, color=TEAL), fillcolor="rgba(0,72,84,.55)")
    fig.add_scatter(x=x, y=subrogacion[:n], name="Subrogación (escrituración)", stackgroup="r",
                    line=dict(width=0.5, color=GREEN), fillcolor="rgba(30,135,75,.55)")
    fig.update_layout(title=titulo, height=400, xaxis_title="Mes", yaxis_title="Miles COP")
    return fig


# ----------------------------------------------------------------------------- tornado
def tornado(filas, base, kpi_nombre="Utilidad operativa", titulo=None):
    """Sensibilidad unidimensional. `filas`: lista de dicts {variable, delta_pos, delta_neg}
    (deltas en miles COP respecto a la base). Ordena por impacto y pinta verde/rojo."""
    filas = sorted(filas, key=lambda r: abs(r.get("delta_pos", 0)) + abs(r.get("delta_neg", 0)))
    fig = go.Figure()
    for i, r in enumerate(filas):
        fig.add_bar(y=[r["variable"]], x=[r.get("delta_pos", 0)], orientation="h", base=base,
                    marker_color=GREEN, name="Favorable", showlegend=(i == 0),
                    hovertemplate=f"{r['variable']}<br>+: %{{x:,.0f}}<extra></extra>")
        fig.add_bar(y=[r["variable"]], x=[r.get("delta_neg", 0)], orientation="h", base=base,
                    marker_color=RED, name="Desfavorable", showlegend=(i == 0),
                    hovertemplate=f"{r['variable']}<br>−: %{{x:,.0f}}<extra></extra>")
    fig.add_vline(x=base, line_color=TEAL, line_width=1.5,
                  annotation_text=f"Base: {base/1000:,.1f} mil M".replace(",", "."),
                  annotation_position="top")
    fig.update_layout(title=titulo or f"Sensibilidad — {kpi_nombre}", barmode="overlay",
                      height=max(300, len(filas) * 56 + 110), xaxis_title="Miles COP")
    return fig


# ----------------------------------------------------------------------------- escenarios
def escenarios_grouped(escenarios, titulo="Análisis de escenarios — utilidad operativa y margen"):
    """`escenarios`: dict {nombre: {'util_oper':.., 'margen':..}}. Barras de utilidad + etiqueta de margen."""
    colores = {"Base": TEAL, "Optimista": GREEN, "Pesimista": RED}
    nombres = list(escenarios.keys())
    util = [escenarios[k].get("util_oper", 0) for k in nombres]
    marg = [escenarios[k].get("margen", 0) for k in nombres]
    fig = go.Figure(go.Bar(
        x=nombres, y=util, marker_color=[colores.get(k, TEAL) for k in nombres],
        text=[f"{u/1000:,.1f} mil M · {m*100:.1f}%".replace(",", ".") for u, m in zip(util, marg)],
        textposition="outside",
        hovertemplate="%{x}<br>Utilidad: %{y:,.0f} mil COP<extra></extra>"))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    fig.update_layout(title=titulo, height=420, yaxis_title="Utilidad operativa (miles COP)")
    return fig


# ----------------------------------------------------------------------------- gantt
def gantt_etapas(hitos, titulo="Cronograma de etapas — ventas y construcción"):
    """`hitos`: dict {cod: {nombre, IV, PE, FV, IC, FC}} con fechas date. Barra ventas (teal) +
    construcción (ámbar) por etapa, con marcas de equilibrio y entrega."""
    fig = go.Figure()
    cods = sorted(hitos, reverse=True)
    for c in cods:
        h = hitos[c]; y = h.get("nombre", f"Etapa {c}")
        if h.get("IV") and h.get("FV"):
            fig.add_scatter(x=[h["IV"], h["FV"]], y=[y, y], mode="lines",
                            line=dict(color=TEAL, width=14), name="Ventas", showlegend=(c == cods[0]),
                            hovertemplate=f"{y} · ventas<br>%{{x|%b %Y}}<extra></extra>")
        if h.get("IC") and h.get("FC"):
            fig.add_scatter(x=[h["IC"], h["FC"]], y=[y, y], mode="lines",
                            line=dict(color=AMBER, width=8), name="Construcción", showlegend=(c == cods[0]),
                            hovertemplate=f"{y} · obra<br>%{{x|%b %Y}}<extra></extra>")
        pts = [("Equilibrio", h.get("PE"), INK, "diamond"), ("Fin ventas", h.get("FV"), MUTED, "circle")]
        pts = [(nm, d, col, sym) for nm, d, col, sym in pts if d]
        if pts:
            fig.add_scatter(x=[p[1] for p in pts], y=[y] * len(pts), mode="markers", showlegend=False,
                            marker=dict(size=11, color=[p[2] for p in pts], symbol=[p[3] for p in pts]),
                            text=[p[0] for p in pts], hovertemplate="%{text}: %{x|%b %Y}<extra></extra>")
    fig.update_layout(title=titulo, height=140 + 70 * len(cods), xaxis_title="")
    return fig
