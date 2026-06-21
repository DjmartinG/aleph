# -*- coding: utf-8 -*-
"""Edición de tipologías — validación + NO-CORRUPCIÓN. El motor `normalizar_tipologias` deriva und/ventas
de la tabla; este suite prueba que (1) `validar_tipologias` atrapa los datos malformados, (2) editar la
tabla y dejar que el motor re-derive es un NO-OP exacto cuando no cambia nada (anti-bug del 2026-06-13),
(3) un cambio intencional SÍ se refleja, (4) la regla VIS (parqueaderos/depósitos = 0) y el método $/m².

Fixture ILUSTRATIVO inline SIN override de fiducia (lección crítica: la fiducia enmascara bugs de
cronograma → el round-trip daría verde falso). Precios en PESOS COP.
"""
import copy

import pytest

from aleph_engine import calcular, tipologias

# --- Fixture ilustrativo (No VIS) con tipologías: 2 etapas, apartamento + comercio + parqueadero ---
def _par_tipologias(tipo="No VIS"):
    return {
        "meta": {"nombre": "Tipologías Ejemplo", "tipo": tipo, "unidades": 0, "moneda": "miles COP"},
        "areas": {"m2_vendibles": 6000, "m2_construidos": 9000, "lote_bruta": 4000, "lote_util": 3200},
        "etapas": [
            {"cod": 1, "nom": "Etapa 1", "vmes": 8, "frec": 1, "pe_pct": 0.6, "fecha_inicio": "2026-01-01",
             "sucesora": None, "desfase": 0, "obra_offset": 1, "dur_obra": 18, "escrituracion": 22, "emes": 30, "efrec": 1},
            {"cod": 2, "nom": "Etapa 2", "vmes": 8, "frec": 1, "pe_pct": 0.6, "fecha_inicio": "2027-01-01",
             "sucesora": None, "desfase": 0, "obra_offset": 1, "dur_obra": 18, "escrituracion": 22, "emes": 30, "efrec": 1},
        ],
        "tipologias": [
            {"etapa": 1, "nombre": "Apto E1", "clase": "apartamento", "und": 40, "metodo": "$/und", "precio": 250_000_000, "area_und": 60},
            {"etapa": 1, "nombre": "Parqueadero E1", "clase": "parqueadero", "und": 30, "metodo": "$/und", "precio": 25_000_000, "area_und": 12},
            {"etapa": 2, "nombre": "Apto E2 ($/m²)", "clase": "apartamento", "und": 35, "metodo": "$/m²", "precio": 4_500_000, "area_und": 62},
        ],
        "costos_pct": {"directos": 0.55, "indirectos": 0.18, "honorarios": 0.08, "util_lote": 0.045},
        "lote_bruto_miles": 3_000_000,
        "cronograma": {"dur_obra": 30, "moda_pert": 18, "curva": "Gauss", "rel_materiales": 0.8, "ea_materiales": 0.06, "ea_mano_obra": 0.12},
        "financiero": {"renta": 0.35, "split_cg": 0.7, "pct_ci": 0.3, "sep_und_miles": 5000, "diferido_sep": 4,
                       "tasa_credito_ea": 0.155, "cobertura_cc": 0.8, "monto_cc_pct": 0.8, "tir_apalancada_ref": 0.2,
                       "wacc": {"beta_us": 0.91, "tax_us": 17, "de_us": 21.34, "tax_col": 33, "de_col": 233.3,
                                "rf": 4.3, "rm": 8.53, "rp": 3.43, "kd_us": 5.9, "inf_col": 5.1, "inf_us": 2.9,
                                "tasa_d": 15, "spread": 10.43, "eq_w": 30}},
    }


def _borrar_derivados(par):
    """Lo que hace la Server Action antes de re-inyectar tipologías: borra los derivados stale por etapa
    para que `normalizar_tipologias` mande y no sobrevivan valores viejos (bug ALTO del 2026-06-13)."""
    for e in par.get("etapas", []):
        for k in ("ventas_miles", "ventas_vivienda_miles", "ventas_adicional_miles", "und"):
            e.pop(k, None)


# ---------------------------------- validación ----------------------------------
def test_valida_ok():
    assert tipologias.validar_tipologias(_par_tipologias()) == []


def test_sin_tipologias_no_op():
    assert tipologias.validar_tipologias({"etapas": [{"cod": 1}]}) == []


@pytest.mark.parametrize("mut,frag", [
    (lambda t: t.update(etapa=99), "no existe"),
    (lambda t: t.update(clase="bodega"), "clase"),
    (lambda t: t.update(metodo="$/x"), "método"),
    (lambda t: t.update(und=-1), "und"),
    (lambda t: t.update(precio=0), "precio"),
    (lambda t: t.update(precio=250_000), "MILES"),          # gotcha 10x: precio en miles
])
def test_rechaza_malformados(mut, frag):
    par = _par_tipologias()
    mut(par["tipologias"][0])
    errs = tipologias.validar_tipologias(par)
    assert any(frag in e for e in errs), f"esperaba un error con {frag!r}; got {errs}"


def test_metodo_m2_exige_area():
    par = _par_tipologias()
    par["tipologias"][2]["area_und"] = 0       # $/m² sin área
    assert any("area_und" in e for e in tipologias.validar_tipologias(par))


# ---------------------------- NO-CORRUPCIÓN (round-trip) ----------------------------
def test_round_trip_sin_cambios_es_no_op():
    """Borrar los derivados + re-inyectar las MISMAS tipologías → cifras IDÉNTICAS (no se corrompe)."""
    base = calcular(copy.deepcopy(_par_tipologias()))
    edit = copy.deepcopy(_par_tipologias())
    _borrar_derivados(edit)                                  # simula la Server Action
    edit["tipologias"] = copy.deepcopy(_par_tipologias()["tipologias"])
    R = calcular(edit)
    for k in ("tir_proyecto", "tir_equity", "vpn_proyecto"):
        a, b = R["apalancamiento"][k], base["apalancamiento"][k]
        assert a == pytest.approx(b, rel=1e-9, abs=1e-9), f"{k} se movió: {a} vs {b}"
    assert R["pyg"]["ventas"] == pytest.approx(base["pyg"]["ventas"], rel=1e-9)


def test_cambio_de_precio_se_refleja():
    """Subir el precio de una tipología +10% → ventas suben y la TIR cambia (no se descarta en silencio)."""
    base = calcular(copy.deepcopy(_par_tipologias()))
    edit = copy.deepcopy(_par_tipologias())
    _borrar_derivados(edit)
    edit["tipologias"][0]["precio"] = int(250_000_000 * 1.10)
    R = calcular(edit)
    assert R["pyg"]["ventas"] > base["pyg"]["ventas"]


# ------------------------------- regla VIS + método -------------------------------
def test_regla_vis_silencia_adicionales():
    """No VIS: el parqueadero suma a ventas_adicional. VIS/VIP: es comunal → adicional = 0.
    `calcular()` muta el par in situ (normalizar_tipologias), así que se leen las etapas del par."""
    par_novis = copy.deepcopy(_par_tipologias("No VIS"))
    par_vis = copy.deepcopy(_par_tipologias("VIS"))
    no_vis = calcular(par_novis)
    vis = calcular(par_vis)
    e1_novis = next(e for e in par_novis["etapas"] if e["cod"] == 1)
    e1_vis = next(e for e in par_vis["etapas"] if e["cod"] == 1)
    assert e1_novis["ventas_adicional_miles"] > 0
    assert e1_vis["ventas_adicional_miles"] == 0
    # la VIS recauda menos (pierde el parqueadero) → ventas totales menores
    assert vis["pyg"]["ventas"] < no_vis["pyg"]["ventas"]
