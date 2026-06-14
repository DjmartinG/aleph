# -*- coding: utf-8 -*-
"""M2 (spec_pyg_dinamico.md) — exencion de renta VIS en el P&G.

VIS/VIP: la utilidad de la primera venta es renta EXENTA (ET 235-2 num.4) [VALIDAR vigencia 2277/2022];
los honorarios (servicios) siguen gravados por defecto. Flag vis_exime_honorarios -> exencion total.
Sintetico y CI-safe (no usa datos reales). NO afecta TIR/VPN (son antes de impuestos).
"""
from aleph_engine import modelo


def _par(tipo, **fin):
    return {
        "ventas_miles": 100000, "lote_bruto_miles": 8000,
        "costos_pct": {"directos": 0.50, "indirectos": 0.10, "honorarios": 0.05, "util_lote": 0.02,
                       "recon_codensa": 0.0, "hon_construccion": 0.035, "hon_gerencia": 0.030,
                       "hon_ventas": 0.015},
        "financiero": dict(renta=0.35, **fin), "meta": {"tipo": tipo},
    }


def test_vis_exime_utilidad_grava_honorarios():
    pg = modelo.pyg(_par("VIS"))
    assert pg["honorarios"] == 5000.0
    assert pg["renta"] == 0.35 * pg["honorarios"]          # solo honorarios gravados
    assert pg["udi"] == (pg["honorarios"] + pg["util_oper"]) - pg["renta"]


def test_no_vis_grava_todo():
    pg = modelo.pyg(_par("NO VIS"))
    assert pg["renta"] == 0.35 * (pg["honorarios"] + pg["util_oper"])   # base completa


def test_vis_exencion_total_con_flag():
    pg = modelo.pyg(_par("VIS", vis_exime_honorarios=True))
    assert pg["renta"] == 0.0
    assert pg["udi"] == pg["honorarios"] + pg["util_oper"]
