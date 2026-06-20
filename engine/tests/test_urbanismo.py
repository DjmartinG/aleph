# -*- coding: utf-8 -*-
"""Viabilidad urbanística (POT) — comparación contra límites + veredicto. ADITIVO (dorado intacto)."""
from aleph_engine import urbanismo

URB = {"indice_construccion": 2.43, "densidad_und_ha": 339.6, "aprovechamiento": 0.727}


def test_sin_pot():
    r = urbanismo.evaluar(URB, {})
    assert r["disponible"] is False and r["veredicto"]["nivel"] == "sin_pot" and r["items"] == []


def test_cumple():
    # todos < 90% del máximo → cumple (índice 0.81, densidad 0.75, aprovechamiento 0.81)
    pot = {"indice_construccion_max": 3.0, "densidad_max_und_ha": 450, "aprovechamiento_max": 0.9}
    r = urbanismo.evaluar(URB, pot)
    assert r["veredicto"]["nivel"] == "cumple" and r["veredicto"]["n_excede"] == 0
    assert len(r["items"]) == 3 and all(i["cumple"] for i in r["items"])


def test_al_limite():
    # densidad 339.6 / 350 = 97% ≥ 90% → al límite (sin exceder)
    pot = {"indice_construccion_max": 3.0, "densidad_max_und_ha": 350, "aprovechamiento_max": 0.8}
    r = urbanismo.evaluar(URB, pot)
    assert r["veredicto"]["nivel"] == "al_limite" and r["veredicto"]["n_excede"] == 0


def test_excede():
    pot = {"indice_construccion_max": 2.0}   # real 2.43 > 2.0 → excede
    r = urbanismo.evaluar(URB, pot)
    assert r["veredicto"]["nivel"] == "excede" and r["veredicto"]["n_excede"] == 1
    it = r["items"][0]
    assert it["concepto"] == "Índice de construcción" and not it["cumple"]


def test_referencia_no_comparable():
    pot = {"indice_construccion_max": 3.0, "altura_max_pisos": 12, "cesion_min_pct": 0.17}
    r = urbanismo.evaluar(URB, pot)
    assert r["referencia"] == {"altura_max_pisos": 12, "cesion_min_pct": 0.17}


def test_greenfield_sin_areas():
    r = urbanismo.evaluar(None, {"indice_construccion_max": 3.0})
    assert r["veredicto"]["nivel"] == "sin_pot"   # sin urbanístico no hay nada que comparar
