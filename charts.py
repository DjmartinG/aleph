# -*- coding: utf-8 -*-
"""
Gráficos financieros de nivel institucional para Factibilidad CG.

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


# ----------------------------------------------------------------------------- presupuesto vs ejecutado
def presupuesto_barras(partidas, top=14, titulo="Presupuesto base vs ejecutado — por capítulo"):
    """Barras horizontales: base (BAC, teal) vs ejecutado (AC). `partidas`: lista de dicts con
    'capitulo','base','ejecutado'. Toma las `top` de mayor base. Ejecutado en rojo si > base."""
    ps = sorted([p for p in partidas if p.get("base", 0) > 0], key=lambda p: p["base"])[-top:]
    cap = [p["capitulo"] for p in ps]
    base = [p["base"] for p in ps]; ejec = [p["ejecutado"] for p in ps]
    fig = go.Figure()
    fig.add_bar(y=cap, x=base, orientation="h", name="Presupuesto base", marker_color=TEAL, opacity=0.55,
                hovertemplate="%{y}<br>Base: $%{x:,.0f} M<extra></extra>")
    fig.add_bar(y=cap, x=ejec, orientation="h", name="Ejecutado",
                marker_color=[RED if e > b else GREEN for e, b in zip(ejec, base)],
                hovertemplate="%{y}<br>Ejecutado: $%{x:,.0f} M<extra></extra>")
    fig.update_layout(title=titulo, barmode="overlay", height=max(360, len(ps) * 30 + 120),
                      xaxis_title="Millones COP", legend=dict(orientation="h", y=1.04))
    return fig


def variaciones_waterfall(partidas, titulo="Variaciones presupuestales (base → proyectado)"):
    """Waterfall: del presupuesto BASE total a la PROYECCIÓN ACTUAL, capítulo a capítulo.
    Ahorros (proy<base) en verde, sobrecostos (proy>base) en rojo. `partidas` con 'base','proy_act'."""
    deltas = [(p["capitulo"], p.get("proy_act", 0) - p.get("base", 0)) for p in partidas]
    deltas = [d for d in deltas if abs(d[1]) >= 1]
    deltas.sort(key=lambda d: d[1])                     # ahorros primero, sobrecostos al final
    base_total = sum(p.get("base", 0) for p in partidas)
    x = ["BASE total"] + [d[0] for d in deltas] + ["PROYECTADO"]
    measure = ["absolute"] + ["relative"] * len(deltas) + ["total"]
    y = [base_total] + [d[1] for d in deltas] + [0]
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measure, x=x, y=y,
        connector={"line": {"color": "#E2E8F0"}},
        decreasing={"marker": {"color": GREEN}},        # proy<base = ahorro
        increasing={"marker": {"color": RED}},          # proy>base = sobrecosto
        totals={"marker": {"color": TEAL}},
        hovertemplate="%{x}<br>%{y:,.0f} M<extra></extra>"))
    fig.update_layout(title=titulo, height=430, yaxis_title="Millones COP", xaxis_tickangle=-40)
    return fig


# ----------------------------------------------------------------------------- escenarios (grouped)
def escenarios_barras(esc, titulo="Escenarios — utilidad operativa y margen"):
    """Barras por escenario (Base teal / Optimista verde / Pesimista rojo). `esc`: dict
    {nombre:{util_oper, margen, ventas}}."""
    col = {"Base": TEAL, "Optimista": GREEN, "Pesimista": RED}
    nombres = list(esc.keys())
    fig = go.Figure(go.Bar(
        x=nombres, y=[esc[k]["util_oper"] for k in nombres],
        marker_color=[col.get(k, TEAL) for k in nombres],
        text=[f"{esc[k]['util_oper']/1000:,.0f} mil M · {esc[k]['margen']*100:.1f}%".replace(",", ".") for k in nombres],
        textposition="outside",
        hovertemplate="%{x}<br>Utilidad: %{y:,.0f} mil COP<extra></extra>"))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    fig.update_layout(title=titulo, height=420, yaxis_title="Utilidad operativa (miles COP)")
    return fig


# ----------------------------------------------------------------------------- heatmap sensibilidad 2D
def heatmap_sensibilidad(precio_vars, costo_vars, matriz_margen,
                         titulo="Mapa de sensibilidad — margen operativo (precio vs costo)"):
    """Heatmap 2D: eje X variación de precio, eje Y variación de costo directo, celda = margen %.
    Verde (alto) → blanco (cero) → rojo (negativo). `matriz_margen` en % (filas=costo, cols=precio)."""
    escala = [[0.0, RED], [0.4, "#FCA5A5"], [0.5, "#FFFFFF"], [0.6, "#86EFAC"], [1.0, GREEN]]
    fig = go.Figure(go.Heatmap(
        z=matriz_margen,
        x=[f"Precio {v:+.0f}%" for v in precio_vars],
        y=[f"Costo {v:+.0f}%" for v in costo_vars],
        colorscale=escala, zmid=0,
        text=[[f"{v:.1f}%" for v in fila] for fila in matriz_margen],
        texttemplate="%{text}", textfont=dict(size=12),
        hovertemplate="%{y} · %{x}<br>Margen: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="Margen %")))
    fig.update_layout(title=titulo, height=420, xaxis_title="Variación de precio",
                      yaxis_title="Variación de costo directo")
    return fig


# ----------------------------------------------------------------------------- cockpit (velocímetro)
def cockpit_gauge(valor, titulo, rango=(0, 1), zonas=((0, 0.2, RED), (0.2, 0.3, AMBER), (0.3, 1, GREEN)),
                  es_pct=True):
    """Velocímetro ejecutivo (go.Indicator) de un KPI con zonas verde/ámbar/rojo (marca CG).
    `zonas`: lista de (desde, hasta, color). La aguja/barra toma el color de la zona donde cae el valor."""
    lo, hi = rango
    v = valor if valor is not None else lo
    suaves = {RED: "#FBE3E0", AMBER: "#FDEFD2", GREEN: "#DCF0E4"}
    steps = [dict(range=[a, b], color=suaves.get(c, "#EEF1F5")) for a, b, c in zonas]
    barcol = TEAL
    for a, b, c in zonas:
        if a <= v < b: barcol = c
    if v >= hi: barcol = zonas[-1][2]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=v,
        number=dict(font=dict(size=30, color=INK), valueformat=(".1%" if es_pct else ",.0f")),
        title=dict(text=titulo, font=dict(size=13, color=TEAL)),
        gauge=dict(
            axis=dict(range=[lo, hi], tickformat=(".0%" if es_pct else ",.0f"),
                      tickfont=dict(size=10, color=MUTED)),
            bar=dict(color=barcol, thickness=0.30),
            bgcolor="white", borderwidth=0, steps=steps,
            threshold=dict(line=dict(color=INK, width=2), thickness=0.78, value=v))))
    fig.update_layout(height=240, margin=dict(l=22, r=22, t=46, b=8))
    return fig


# ----------------------------------------------------------------------------- burbujas de portafolio
def bubbles_portafolio(puntos, tir_refs=(0.20, 0.30), margen_refs=(0.03, 0.05),
                       x_clip=(-0.20, 0.70), titulo="Portafolio CG — TIR vs margen operativo"):
    """Mapa de valor del portafolio: X=TIR del proyecto, Y=margen operativo, tamaño=ventas, color=tipo.
    Cuadrantes Estrella / Crecimiento / Vigilancia / Revisar con líneas de referencia. Proyectos con
    TIR < x_clip[0] (outlier muy negativo, p.ej. greenfield) se recortan al borde y se anotan, para no
    aplastar el eje. `puntos`: lista de dicts {nombre, tir(0..1|None), margen(0..1), ventas(miles), tipo}.
    """
    xlo, xhi = x_clip[0] * 100, x_clip[1] * 100
    norm = []; outliers = []
    for p in puntos:
        tir = p.get("tir")
        if tir is None:
            continue
        x = tir * 100; y = (p.get("margen") or 0) * 100
        rec = {**p, "_x": max(xlo, min(xhi, x)), "_y": y, "_tir_real": x}
        if x < xlo:
            outliers.append(rec)
        norm.append(rec)
    if not norm:
        return go.Figure().update_layout(title=titulo, height=470)
    ventas = [max(0.0, p.get("ventas") or 0) for p in norm]
    vmax = max(ventas) or 1
    sizeref = 2.0 * vmax / (95.0 ** 2)
    fig = go.Figure()
    grupos = {}
    for p in norm:
        tipo = "VIS" if str(p.get("tipo", "")).strip().upper() == "VIS" else "No VIS"
        grupos.setdefault(tipo, []).append(p)
    colores = {"VIS": TEAL, "No VIS": AMBER}
    for tipo, pts in grupos.items():
        fig.add_scatter(
            x=[p["_x"] for p in pts], y=[p["_y"] for p in pts], mode="markers+text",
            text=[p.get("nombre", "") for p in pts], textposition="top center",
            textfont=dict(size=11, color=INK), name=tipo,
            marker=dict(size=[max(0.0, p.get("ventas") or 0) for p in pts], sizemode="area",
                        sizeref=sizeref, sizemin=9, color=colores[tipo], opacity=0.80,
                        line=dict(width=1.4, color="white")),
            customdata=[[(p.get("ventas") or 0) / 1_000_000, p["_tir_real"], p["_y"]] for p in pts],
            hovertemplate="<b>%{text}</b><br>TIR: %{customdata[1]:.1f}%<br>"
                          "Margen: %{customdata[2]:.1f}%<br>Ventas: %{customdata[0]:,.1f} mil M<extra></extra>")
    for xr in tir_refs:
        fig.add_vline(x=xr * 100, line=dict(color=MUTED, width=1, dash="dot"))
    for yr in margen_refs:
        fig.add_hline(y=yr * 100, line=dict(color=MUTED, width=1, dash="dot"))
    cuad = [(0.99, 0.97, "right", "top", "★ Estrella", GREEN),
            (0.99, 0.03, "right", "bottom", "Crecimiento", TEAL),
            (0.01, 0.97, "left", "top", "Vigilancia", AMBER),
            (0.01, 0.03, "left", "bottom", "Revisar", RED)]
    for xp, yp, xa, ya, txt, col in cuad:
        fig.add_annotation(x=xp, y=yp, xref="paper", yref="paper", text=txt, showarrow=False,
                           xanchor=xa, yanchor=ya, font=dict(size=10, color=col), opacity=0.7)
    for p in outliers:
        fig.add_annotation(x=p["_x"], y=p["_y"], text=f"TIR {p['_tir_real']:.0f}%", showarrow=True,
                           arrowhead=2, arrowcolor=RED, ax=30, ay=0, font=dict(size=10, color=RED),
                           bgcolor="white", bordercolor=RED, borderwidth=1)
    fig.update_layout(title=titulo, height=470,
                      xaxis=dict(title="TIR del proyecto (%)", range=[xlo - 4, xhi + 4], ticksuffix="%"),
                      yaxis=dict(title="Margen operativo (%)", ticksuffix="%"))
    return fig


# ----------------------------------------------------------------------------- monte carlo (histograma)
def montecarlo_hist(muestras, p10, p50, p90, umbral=0.0, es_pct=True,
                    titulo="Monte Carlo — distribución del margen operativo"):
    """Histograma de la distribución simulada. Resalta la zona < `umbral` (pérdida) en rojo y marca
    P10 (ámbar) / P50 (tinta) / P90 (verde). `muestras` en fracción (margen 0..1) si `es_pct`,
    o en miles COP si no. Los bins se alinean entre la serie completa y la zona de pérdida."""
    datos = list(muestras)
    if not datos:
        return go.Figure().update_layout(title=titulo, height=430)
    lo, hi = min(datos), max(datos)
    size = (hi - lo) / 40 if hi > lo else (abs(hi) or 1) / 40 or 1
    binargs = dict(start=lo, end=hi + size, size=size)
    perdida = [v for v in datos if v < umbral]
    hov = ("Margen %{x:.1%}" if es_pct else "%{x:,.0f}") + "<br>%{y} escenarios<extra></extra>"
    fig = go.Figure()
    fig.add_histogram(x=datos, xbins=binargs, marker_color=TEAL, opacity=0.75,
                      name="Escenarios", hovertemplate=hov)
    if perdida:
        fig.add_histogram(x=perdida, xbins=binargs, marker_color=RED, opacity=0.85,
                          name="Zona de pérdida", hovertemplate=hov)
    _f = (lambda v: f"{v*100:.1f}%") if es_pct else (lambda v: f"{v/1000:,.0f} mil M".replace(",", "."))
    for val, col, lab in [(p10, AMBER, "P10"), (p50, INK, "P50"), (p90, GREEN, "P90")]:
        fig.add_vline(x=val, line=dict(color=col, width=2, dash="dash"),
                      annotation_text=f"{lab} {_f(val)}", annotation_position="top",
                      annotation_font_color=col, annotation_font_size=10)
    fig.update_layout(
        title=titulo, height=430, barmode="overlay",
        xaxis=dict(title=("Margen operativo" if es_pct else "Utilidad operativa (miles COP)"),
                   tickformat=(".0%" if es_pct else ",.0f")),
        yaxis_title="Frecuencia (nº de escenarios)")
    return fig
