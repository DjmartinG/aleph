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


def tesoreria(items):
    """Tesorería CONSOLIDADA del portafolio: la posición de CAJA y la FINANCIACIÓN (crédito) de TODOS
    los proyectos, alineados en el eje GLOBAL (epoch ene-2022, igual que `consolidar`) y sumadas mes a
    mes. Responde la pregunta de tesorería del CEO: ¿cuánta caja necesita la EMPRESA a la vez (sumando
    proyectos) y cuándo, y cuánto crédito carga en el tiempo?

    ADITIVO: agrega las series mensuales que cada `calcular()` ya produjo (`operativo`, `saldo_credito`);
    NO recalcula nada. La caja por proyecto en el eje global es la suma acumulada del `operativo`
    desplazado por el offset de su `base` (IV más temprano): 0 antes de arrancar, su valor final tras
    terminar. `items` = [(slug, par, R)]. Solo proyectos con cronograma datado (hitos)."""
    EPOCH, N = 2022, 240
    saldo = [0.0] * N
    por = []
    for slug, _par, R in items:
        ap = R.get("apalancamiento") or {}
        h = R.get("hitos") or {}
        o = ap.get("operativo") or []
        s = ap.get("saldo_credito") or []
        if not h or not o:
            continue
        base = min(h[c]["IV"] for c in h)
        off = (base.year - EPOCH) * 12 + (base.month - 1)
        caja_p = [0.0] * N
        acc = 0.0
        for g in range(N):
            if g < off:
                caja_p[g] = 0.0
            elif g - off < len(o):
                acc += o[g - off]
                caja_p[g] = acc
            else:
                caja_p[g] = acc                                   # terminado → queda en el valor final
        for m in range(len(s)):
            if 0 <= off + m < N:
                saldo[off + m] += s[m]
        nombre = (R.get("meta") or {}).get("nombre", slug)
        por.append({"nombre": nombre, "caja": caja_p})
    if not por:
        return {"disponible": False}

    caja = [sum(p["caja"][g] for p in por) for g in range(N)]
    # Ventana de tesorería = la fase de DÉFICIT/FINANCIACIÓN (la pregunta del CEO), no la cola de
    # escrituración tardía de un proyecto. Inicio: primer mes con déficit de caja o financiación
    # material; fin: hasta que la caja SALE del déficit (se recupera) + buffer. Series en miles COP.
    UMB = 1e6  # 1 mil M COP
    arranque = [g for g in range(N) if caja[g] < -UMB or saldo[g] > UMB]
    deficit = [g for g in range(N) if caja[g] < -UMB]
    ini = min(arranque) if arranque else 0
    fin = max(ini + 1, min(N, (max(deficit) + 8) if deficit else ini + 12))

    def _fecha(g):
        return f"{EPOCH + g // 12:04d}-{g % 12 + 1:02d}-01"

    caja_w, cred_w = caja[ini:fin], saldo[ini:fin]
    trough = min(range(len(caja_w)), key=lambda t: caja_w[t]) if caja_w else 0
    peak = max(range(len(cred_w)), key=lambda t: cred_w[t]) if cred_w else 0
    return {
        "disponible": True,
        "base_date": _fecha(ini),               # mes 0 de las series recortadas (calendario)
        "horizonte": fin - ini,
        "n": len(por),
        "caja": caja_w, "credito": cred_w,
        "exposicion_maxima": {"mes": trough, "valor": caja_w[trough] if caja_w else 0.0},
        "credito_maximo": {"mes": peak, "valor": cred_w[peak] if cred_w else 0.0},
        "por_proyecto": [{"nombre": p["nombre"], "caja": p["caja"][ini:fin]} for p in por],
    }


def capital(items):
    """Asignación de CAPITAL del portafolio: por proyecto, el equity PICO requerido (necesidad máxima
    de caja propia tras el crédito = `min(acum)`), el crédito máximo, el valor creado (EVA @WACC) y la
    EFICIENCIA de capital (valor creado / equity pico). Responde la pregunta del CEO con capital escaso:
    ¿dónde rinde más cada peso? Rankea los proyectos por eficiencia (los que más valor crean por peso
    de equity primero; greenfield sin veredicto al final).

    ADITIVO: reusa lo que `calcular()` ya produjo (`apalancamiento`), no recalcula. `items` = [(slug,
    par, R)]. Los totales son SUMAS de picos individuales (que NO coinciden en el tiempo → la necesidad
    SIMULTÁNEA real es la del consolidado de `tesoreria`, menor; se muestra el beneficio de cartera)."""
    filas = []
    eq_total = cr_total = vc_total = eq_eval = 0.0
    for slug, _par, R in items:
        ap = R.get("apalancamiento") or {}
        mt = R.get("meta") or {}
        equity = abs(ap.get("max_necesidad_caja") or 0.0)       # equity pico (caja propia, tras crédito)
        credito = ap.get("credito_max") or 0.0
        crea = ap.get("crea_valor")
        # El equity/crédito SÍ son válidos para greenfield; pero el VALOR (EVA) NO se juzga sin veredicto
        # (crea_valor None) → "— greenfield", consistente con la consolidación EVA del portafolio.
        vc = ap.get("valor_creado") if crea is not None else None
        eff = (vc / equity) if (vc is not None and equity > 0) else None
        filas.append({"slug": slug, "nombre": mt.get("nombre", slug), "tipo": mt.get("tipo"),
                      "equity_pico": equity, "credito_max": credito,
                      "valor_creado": vc, "crea_valor": crea, "eficiencia": eff})
        eq_total += equity
        cr_total += credito
        if vc is not None:
            vc_total += vc
            eq_eval += equity                                   # equity de los proyectos evaluables
    # Rankear por eficiencia descendente; greenfield (eficiencia None) al final.
    filas.sort(key=lambda f: (f["eficiencia"] is None, -(f["eficiencia"] or 0.0)))
    return {"filas": filas, "equity_total": eq_total, "credito_total": cr_total,
            "valor_creado_total": vc_total,
            "eficiencia_portafolio": (vc_total / eq_eval) if eq_eval else None,
            "n": len(filas)}


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
