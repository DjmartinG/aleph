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
from datetime import date
import plotly.graph_objects as go
import plotly.io as pio


def _eje_fechas(base, n):
    """Lista de n fechas mensuales a partir de `base` (1er día de cada mes)."""
    out = []
    for i in range(n):
        y = base.year + (base.month - 1 + i) // 12
        m = (base.month - 1 + i) % 12 + 1
        out.append(date(y, m, 1))
    return out

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
def flujo_caja_waterfall(flujo, acumulado, saldo_credito=None, fecha_base=None, tope_anio=None,
                         desde=None, titulo="Flujo de caja del proyecto"):
    """Barras verde/rojo del flujo neto mensual + acumulado + saldo de crédito + pico de exposición.

    Args:
        flujo: lista del flujo neto por mes (miles COP).
        acumulado: lista de la caja acumulada por mes.
        saldo_credito: lista del saldo de crédito constructor (opcional).
        fecha_base: date del primer mes (mes 0). Si se da, el eje X son FECHAS reales; si no, nº de mes.
        tope_anio: si se da (p.ej. 2030), recorta el eje al final de ese año.
        desde: date — si se da (con fecha_base), recorta el inicio a ese mes ("caja de aquí en adelante").
    """
    n = max(_recortar(flujo), _recortar(acumulado))
    i0 = 0
    if fecha_base is not None:
        fechas = _eje_fechas(fecha_base, n)
        if desde is not None:                           # arranca el eje en 'desde' (proyecto en ejecución)
            futuros = [i for i, d in enumerate(fechas) if (d.year, d.month) >= (desde.year, desde.month)]
            if futuros:
                i0 = futuros[0]
        if tope_anio:                                   # recorta hasta dic-tope_anio inclusive
            lim = [i for i, d in enumerate(fechas) if d.year <= tope_anio]
            if lim:
                n = lim[-1] + 1; fechas = fechas[:n]
        x = fechas[i0:n]; flujo = flujo[i0:n]; acumulado = acumulado[i0:n]
        if saldo_credito: saldo_credito = saldo_credito[i0:n]
        n = len(x); xtitle = ""; hov_x = "%{x|%b %Y}"
    else:
        x = list(range(1, n + 1)); xtitle = "Mes"; hov_x = "Mes %{x}"
    fig = go.Figure()
    colores = [GREEN if v >= 0 else RED for v in flujo[:n]]
    fig.add_bar(x=x, y=flujo[:n], name="Flujo neto mensual", marker_color=colores, opacity=0.85,
                hovertemplate=hov_x + "<br>Flujo: %{y:,.0f} mil COP<extra></extra>")
    fig.add_scatter(x=x, y=acumulado[:n], name="Caja acumulada", line=dict(color=INK, width=2.5),
                    hovertemplate=hov_x + ": %{y:,.0f} acum.<extra></extra>")
    if saldo_credito:
        fig.add_scatter(x=x, y=saldo_credito[:n], name="Saldo crédito constructor",
                        line=dict(color=AMBER, width=2, dash="dot"))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    # pico de exposición (mínimo del acumulado)
    sub = acumulado[:n]
    if sub:
        idx = min(range(len(sub)), key=lambda i: sub[i])
        if sub[idx] < -1:
            fig.add_annotation(x=x[idx], y=sub[idx],
                text=f"Exposición máx<br><b>{sub[idx]/1000:,.1f} mil M</b>".replace(",", "."),
                bgcolor="white", bordercolor=RED, borderwidth=1, font=dict(size=11, color=RED),
                showarrow=True, arrowhead=2, arrowcolor=RED)
    fig.update_layout(title=titulo, height=430, xaxis_title=xtitle, yaxis_title="Miles COP",
                      barmode="overlay")
    if fecha_base is not None:
        fig.update_xaxes(dtick="M6", tickformat="%b %Y")   # marca cada 6 meses
    return fig


# ----------------------------------------------------------------------------- curva S obra
def curva_obra_s(escalada, acumulada, fecha_base=None, titulo="Curva S de avance de obra (costo directo)"):
    """Campana de costo directo mensual (barras) + curva S de avance acumulado en % (eje der.).
    Si `fecha_base` (date del mes 0 de la OBRA) se da, el eje X son fechas reales."""
    n = min(_recortar(escalada), len(escalada))
    if fecha_base is not None:
        x = _eje_fechas(fecha_base, n); xtitle = ""; hov_x = "%{x|%b %Y}"
    else:
        x = list(range(1, n + 1)); xtitle = "Mes de obra"; hov_x = "Mes %{x}"
    total = (sum(escalada) or 1)                       # base del avance = costo directo total
    acum = []; run = 0.0
    for i in range(n):
        run += escalada[i] if i < len(escalada) else 0
        acum.append(run)
    avance = [(acum[i] / total) if total else 0 for i in range(n)]
    fig = go.Figure()
    fig.add_bar(x=x, y=escalada[:n], name="Costo directo mensual", marker_color=TEAL, opacity=0.85,
                hovertemplate=hov_x + ": %{y:,.0f} mil COP<extra></extra>")
    fig.add_scatter(x=x, y=avance, name="Avance acumulado", yaxis="y2",
                    line=dict(color=AMBER, width=3), fill="tozeroy", fillcolor="rgba(240,156,0,.08)",
                    hovertemplate=hov_x + ": %{y:.0%} avance<extra></extra>")
    # pico de la campana
    if escalada[:n]:
        pk = max(range(n), key=lambda i: escalada[i])
        etiqueta = (f"Pico obra<br>{x[pk]:%b %Y}" if fecha_base is not None else f"Pico obra<br>mes {pk+1}")
        fig.add_annotation(x=x[pk], y=escalada[pk], text=etiqueta,
                           showarrow=True, arrowhead=2, arrowcolor=TEAL, font=dict(size=11, color=TEAL),
                           bgcolor="white", bordercolor=TEAL, borderwidth=1)
    fig.update_layout(title=titulo, height=410, xaxis_title=xtitle, yaxis_title="Miles COP",
                      yaxis2=dict(overlaying="y", side="right", title="Avance", tickformat=".0%",
                                  range=[0, 1.05], showgrid=False))
    if fecha_base is not None:
        fig.update_xaxes(dtick="M3", tickformat="%b %Y")
    return fig


# ----------------------------------------------------------------------------- recaudo apilado
def recaudo_stacked(separacion, cuota_inicial, subrogacion, fecha_base=None, tope_anio=None,
                    titulo="Recaudo mensual por componente"):
    """Área apilada: separación (ámbar) + cuota inicial (teal) + subrogación (verde).
    Si `fecha_base` (date del mes 0) se da, el eje X son fechas; `tope_anio` recorta al fin de ese año."""
    n = max(_recortar(separacion), _recortar(cuota_inicial), _recortar(subrogacion))
    if fecha_base is not None:
        fechas = _eje_fechas(fecha_base, n)
        if tope_anio:
            lim = [i for i, d in enumerate(fechas) if d.year <= tope_anio]
            if lim:
                n = lim[-1] + 1; fechas = fechas[:n]
        x = fechas; xtitle = ""; hov_x = "%{x|%b %Y}"
    else:
        x = list(range(1, n + 1)); xtitle = "Mes"; hov_x = "Mes %{x}"
    fig = go.Figure()
    fig.add_scatter(x=x, y=separacion[:n], name="Separación", stackgroup="r",
                    line=dict(width=0.5, color=AMBER), fillcolor="rgba(240,156,0,.55)",
                    hovertemplate=hov_x + " · Separación: %{y:,.0f}<extra></extra>")
    fig.add_scatter(x=x, y=cuota_inicial[:n], name="Cuota inicial", stackgroup="r",
                    line=dict(width=0.5, color=TEAL), fillcolor="rgba(0,72,84,.55)",
                    hovertemplate=hov_x + " · Cuota inicial: %{y:,.0f}<extra></extra>")
    fig.add_scatter(x=x, y=subrogacion[:n], name="Subrogación (escrituración)", stackgroup="r",
                    line=dict(width=0.5, color=GREEN), fillcolor="rgba(30,135,75,.55)",
                    hovertemplate=hov_x + " · Subrogación: %{y:,.0f}<extra></extra>")
    fig.update_layout(title=titulo, height=400, xaxis_title=xtitle, yaxis_title="Miles COP")
    if fecha_base is not None:
        fig.update_xaxes(dtick="M6", tickformat="%b %Y")
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


# ----------------------------------------------------------------------------- valor ganado (EVM)
def valor_ganado_s(evm, fecha_base=None, titulo="Valor Ganado (EVM) — curvas S"):
    """3 curvas S del EVM: PV (planeado, teal), EV (ganado, verde), AC (costo real, rojo).
    `evm` = salida de engine.evm.calcular_evm. PV viene como serie acumulada mensual completa;
    EV y AC son puntos a la fecha de corte (línea recta desde el inicio hasta el corte)."""
    pv_acum = list(evm.get("curva_pv", []))
    n = len(pv_acum)
    if fecha_base is not None:
        x = _eje_fechas(fecha_base, n); hov = "%{x|%b %Y}"
    else:
        x = list(range(1, n + 1)); hov = "Mes %{x}"
    corte = evm.get("mes_corte")
    fig = go.Figure()
    # PV: curva S completa planeada
    fig.add_scatter(x=x, y=pv_acum, name="PV · Valor Planeado", line=dict(color=TEAL, width=3),
                    hovertemplate=hov + " · PV: %{y:,.0f}<extra></extra>")
    # EV y AC: rampa lineal desde el inicio hasta el punto de corte (lo ejecutado a la fecha)
    if corte is not None and 0 <= corte < n:
        xi = x[:corte + 1]
        ev_line = [evm["EV"] * (i / corte) if corte else evm["EV"] for i in range(corte + 1)]
        ac_line = [evm["AC"] * (i / corte) if corte else evm["AC"] for i in range(corte + 1)]
        fig.add_scatter(x=xi, y=ev_line, name="EV · Valor Ganado", line=dict(color=GREEN, width=3),
                        hovertemplate=hov + " · EV: %{y:,.0f}<extra></extra>")
        fig.add_scatter(x=xi, y=ac_line, name="AC · Costo Real", line=dict(color=RED, width=3, dash="dot"),
                        hovertemplate=hov + " · AC: %{y:,.0f}<extra></extra>")
        # línea vertical "hoy" (fecha de corte) — add_shape evita el bug de add_vline con fechas
        fig.add_shape(type="line", x0=x[corte], x1=x[corte], y0=0, y1=1, yref="paper",
                      line=dict(color=MUTED, width=1.5, dash="dash"))
        fig.add_annotation(x=x[corte], y=1, yref="paper", text="hoy", showarrow=False,
                           yanchor="bottom", font=dict(size=11, color=MUTED))
        # marcadores en el corte
        fig.add_scatter(x=[x[corte]] * 2, y=[evm["EV"], evm["AC"]], mode="markers", showlegend=False,
                        marker=dict(size=10, color=[GREEN, RED]),
                        hovertemplate="%{y:,.0f}<extra></extra>")
    # EAC: proyección del costo final (punteado teal hasta el fin)
    if evm.get("EAC") is not None and n:
        fig.add_scatter(x=[x[corte] if (corte is not None and corte < n) else x[0], x[-1]],
                        y=[evm["AC"], evm["EAC"]], name="EAC · costo final estimado",
                        line=dict(color=AMBER, width=2, dash="dot"),
                        hovertemplate="EAC: %{y:,.0f}<extra></extra>")
    fig.update_layout(title=titulo, height=430, xaxis_title="", yaxis_title="Miles COP")
    if fecha_base is not None:
        fig.update_xaxes(dtick="M3", tickformat="%b %Y")
    return fig


# ----------------------------------------------------------------------------- avance real vs programado
def avance_real_vs_programado(cortes, titulo="Avance de obra — real vs programado · Torre 1"):
    """Curva de avance REAL ejecutado vs PROGRAMADO (estándar PMI/Camacol).

    `cortes`: lista de dicts {periodo:'2026-02', real:7.25, plan:6.20|None}. Marca el último corte y
    pinta el área entre real y plan (verde si adelantado). El plan se interpola si falta algún punto."""
    cortes = [c for c in cortes if c.get("periodo")]
    xs = [c["periodo"] for c in cortes]
    real = [c.get("real") for c in cortes]
    plan = [c.get("plan") for c in cortes]
    # interpolar plan faltante de forma simple (lineal entre puntos conocidos / extrapola plano)
    kn = [(i, p) for i, p in enumerate(plan) if p is not None]
    plan_i = list(plan)
    if kn:
        for i in range(len(plan_i)):
            if plan_i[i] is None:
                prev = [k for k in kn if k[0] <= i]; nxt = [k for k in kn if k[0] >= i]
                if prev and nxt and prev[-1][0] != nxt[0][0]:
                    (i0, p0), (i1, p1) = prev[-1], nxt[0]
                    plan_i[i] = p0 + (p1 - p0) * (i - i0) / (i1 - i0)
                else:
                    plan_i[i] = (prev[-1][1] if prev else nxt[0][1])
    fig = go.Figure()
    # plan (base invisible para el relleno) + curva plan punteada
    fig.add_scatter(x=xs, y=plan_i, mode="lines", line=dict(color="rgba(0,0,0,0)"),
                    showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=xs, y=real, mode="lines+markers", name="Avance real ejecutado",
                    line=dict(color=TEAL, width=3), marker=dict(size=11, color=TEAL),
                    fill="tonexty", fillcolor="rgba(30,135,75,.15)",
                    hovertemplate="%{x}<br>Real: <b>%{y:.1f}%</b><extra></extra>")
    fig.add_scatter(x=xs, y=plan_i, mode="lines", name="Avance programado (curva S)",
                    line=dict(color=AMBER, width=2, dash="dot"),
                    hovertemplate="%{x}<br>Plan: %{y:.1f}%<extra></extra>")
    # anotación último corte real
    if real and real[-1] is not None:
        fig.add_annotation(x=xs[-1], y=real[-1], text=f"<b>{real[-1]:.1f}%</b><br>último corte",
                           bgcolor="white", bordercolor=TEAL, borderwidth=1, font=dict(size=11, color=TEAL),
                           showarrow=True, arrowhead=2, arrowcolor=TEAL, yshift=24)
    fig.update_layout(title=titulo, height=420, xaxis_title="Período",
                      yaxis=dict(title="Avance (%)", range=[0, 105], ticksuffix="%"))
    return fig
