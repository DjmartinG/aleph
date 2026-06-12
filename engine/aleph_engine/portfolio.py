# -*- coding: utf-8 -*-
"""Agregaciones de PORTAFOLIO — lógica pura del motor (consolidado, burbujas, pipeline).

Extraído de `app.py` (§3.2 paso 13). La app solo CARGA los proyectos (almacenamiento), los calcula y
pasa los resultados a estas funciones; el FORMATO (es-CO) y el caché (`st.cache_data`) se quedan en la
app. Sin Streamlit, sin almacenamiento, sin formato.

Entrada común `items`: lista de `(slug, par, R)` donde
  - `slug`: identificador del proyecto (la app usa la clave de almacenamiento),
  - `par`:  dict del proyecto,
  - `R`:    resultado de `calcular(par)`.
Las cifras se devuelven CRUDAS (números); la UI las formatea.
"""
from __future__ import annotations

from . import config
from .finanzas import irr_anual_biseccion


def consolidar(items):
    """Consolidado del portafolio en un eje GLOBAL absoluto (epoch ene-2022) para alinear proyectos
    que arrancan en años distintos. Devuelve totales, TIR ref ponderada por ventas, TIR equity
    consolidada y filas por proyecto (números crudos). Lógica idéntica a `app.consolidado`."""
    EPOCH = 2022
    N = 240
    oper = [0.0] * N
    equity = [0.0] * N
    saldo = [0.0] * N
    ventas = util = udi = vpn = und = 0.0
    n = 0
    filas = []
    tir_num = tir_den = 0.0
    for _slug, par, R in items:
        pg = R["pyg"]
        ap = R.get("apalancamiento") or {}
        mt = R["meta"]
        h = R.get("hitos") or {}
        ventas += pg["ventas"]
        util += pg["util_oper"]
        udi += pg["udi"]
        if ap.get("vpn_proyecto"):
            vpn += ap["vpn_proyecto"]
        tref = ap.get("tir_apalancada_ref")
        if tref:
            tir_num += pg["ventas"] * tref
            tir_den += pg["ventas"]                     # TIR ref ponderada por ventas
        und += sum(e.get("und", 0) or 0 for e in par.get("etapas", []))
        base = min((h[c]["IV"] for c in h), default=None)   # offset al eje global
        off = ((base.year - EPOCH) * 12 + (base.month - 1)) if base else 0
        o = ap.get("operativo") or []
        e = ap.get("flujo_equity") or []
        s = ap.get("saldo_credito") or []
        for m in range(max(len(o), len(e), len(s))):
            g = off + m
            if 0 <= g < N:
                if m < len(o):
                    oper[g] += o[m]
                if m < len(e):
                    equity[g] += e[m]
                if m < len(s):
                    saldo[g] += s[m]
        filas.append({"nombre": mt.get("nombre", _slug),
                      "unidades": sum(x.get("und", 0) or 0 for x in par.get("etapas", [])),
                      "ventas": pg["ventas"], "util_oper": pg["util_oper"],
                      "margen": pg["margen_oper"], "credito_max": ap.get("credito_max", 0) or 0})
        n += 1
    return {"n": n, "unidades": int(und), "ventas": ventas, "util_oper": util, "udi": udi, "vpn": vpn,
            "margen": util / ventas if ventas else 0,
            "tir_ref": (tir_num / tir_den if tir_den else None),
            "tir_eq": irr_anual_biseccion(equity),
            "credito_max": max(saldo) if saldo else 0.0, "filas": filas}


def puntos_burbujas(items):
    """Puntos del gráfico de burbujas: un dict por proyecto {nombre, tir, margen, ventas, tipo, und}.
    Lógica idéntica a `app.puntos_portafolio`."""
    pts = []
    for _slug, par, R in items:
        pg = R["pyg"]
        ap = R.get("apalancamiento") or {}
        mt = R["meta"]
        tir = ap.get("tir_proyecto")
        if tir is None:
            tir = ap.get("tir_apalancada_ref")
        pts.append({"nombre": mt.get("nombre", _slug), "tir": tir, "margen": pg.get("margen_oper"),
                    "ventas": pg.get("ventas"), "tipo": mt.get("tipo", "No VIS"),
                    "und": sum(e.get("und", 0) or 0 for e in par.get("etapas", []))})
    return pts


def pipeline(items):
    """Un dict por proyecto con su ESTADO del ciclo de vida + métricas, para el embudo/pipeline y las
    tarjetas del Portafolio. Lógica idéntica a `app.pipeline_datos`."""
    out = []
    for slug, par, R in items:
        pg = R["pyg"]
        ap = R.get("apalancamiento") or {}
        mt = R["meta"]
        _m = par.get("meta", {}) or {}
        estado = _m.get("estado") or config.ESTADO_DEFAULT
        if estado not in config.ESTADOS:
            estado = config.ESTADO_DEFAULT
        tir = ap.get("tir_apalancada_ref") or ap.get("tir_proyecto")
        out.append({"slug": slug, "nombre": mt.get("nombre", slug), "estado": estado, "tir": tir,
                    "vpn": ap.get("vpn_proyecto"), "ventas": pg.get("ventas"),
                    "und": sum(e.get("und", 0) or 0 for e in par.get("etapas", [])),
                    "ubicacion": _m.get("ubicacion", ""), "tipo": _m.get("tipo", "")})
    return out
