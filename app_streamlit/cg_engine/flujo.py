# -*- coding: utf-8 -*-
"""Utilidades compartidas de construcción de flujos de caja.

NOTA DE DISEÑO (importante para no romper cifras auditadas):
El motor tiene DOS modelos de flujo INTENCIONALMENTE distintos, y NO deben fusionarse:
  • `modelo.flujo_caja`        — vista simple del proyecto: ventana por offsets de etapa
                                  (ini_obra/dur/entrega), curva PERT, ingresos inline.
  • `apalancamiento.flujo_apalancado` — waterfall AUDITADO del portafolio (produce las anclas):
                                  ventana por hitos (IC/FC), curva Gauss, recaudo por kernel,
                                  y acumuladores extra (directos/obra financiable) para el crédito.
Solo se comparte aquí lo que es LITERALMENTE idéntico entre ambos (los gastos fijos y el acumulado).
"""


def aplicar_gastos_fijos(costos, par, N):
    """Suma al vector `costos` (longitud N, mutado in situ) los gastos fijos de estructura:
    monto mensual `valor_mes_miles` sobre su ventana [desde, hasta). Lógica idéntica en
    flujo_caja y flujo_apalancado → fuente única."""
    for g in par.get("gastos_fijos", []):
        vm = g.get("valor_mes_miles", 0) or 0
        d = int(g.get("desde", 0) or 0)
        h = g.get("hasta")
        h = int(h) if h is not None else d + 1
        for m in range(max(0, d), min(h, N)):
            costos[m] += vm
    return costos


def acumular(serie):
    """Suma acumulada de una serie (devuelve la lista de acumulados)."""
    acum = []
    s = 0.0
    for x in serie:
        s += x
        acum.append(s)
    return acum
