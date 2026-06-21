# -*- coding: utf-8 -*-
"""Estudio de mercado — contraste de supuestos vs comparables + veredicto. ADITIVO (dorado intacto)."""
from aleph_engine import mercado

# Proyecto: precio/m² 4.0M, 2 etapas con vmes (promedio ponderado por unidades = 15).
R = {"urbanistico": {"precio_m2_vend": 4_000_000}}
PAR = {"etapas": [{"vmes": 15, "und": 300}, {"vmes": 15, "und": 300}]}


def test_sin_datos():
    r = mercado.evaluar(PAR, R)
    assert r["disponible"] is False and r["veredicto"]["nivel"] == "sin_datos" and r["items"] == []


def test_en_mercado():
    par = {**PAR, "mercado": {"precio_m2_mercado": 3_900_000, "absorcion_mercado_und_mes": 15}}
    r = mercado.evaluar(par, R)
    assert r["veredicto"]["nivel"] == "en_mercado" and r["veredicto"]["n_alerta"] == 0
    assert len(r["items"]) == 2


def test_precio_sobre_mercado():
    # 4.0M / 3.4M = +17.6% > 10% → alerta
    par = {**PAR, "mercado": {"precio_m2_mercado": 3_400_000}}
    r = mercado.evaluar(par, R)
    it = next(i for i in r["items"] if i["sentido"] == "precio")
    assert it["estado"] == "alerta" and it["desviacion"] > 0
    assert r["veredicto"]["nivel"] == "revisar"


def test_precio_bajo_mercado_tambien_alerta():
    # vender 20% por DEBAJO del comparable también es señal (valor dejado en la mesa)
    par = {**PAR, "mercado": {"precio_m2_mercado": 5_000_000}}
    r = mercado.evaluar(par, R)
    it = next(i for i in r["items"] if i["sentido"] == "precio")
    assert it["estado"] == "alerta" and it["desviacion"] < 0


def test_ritmo_optimista():
    # proyecto 15 und/mes vs absorción de mercado 10 → +50% → optimista (alerta)
    par = {**PAR, "mercado": {"absorcion_mercado_und_mes": 10}}
    r = mercado.evaluar(par, R)
    it = next(i for i in r["items"] if i["sentido"] == "ritmo")
    assert it["estado"] == "alerta" and it["desviacion"] > 0


def test_ritmo_conservador_ok():
    # vender más LENTO que el mercado NO es alerta (conservador)
    par = {**PAR, "mercado": {"absorcion_mercado_und_mes": 30}}
    r = mercado.evaluar(par, R)
    it = next(i for i in r["items"] if i["sentido"] == "ritmo")
    assert it["estado"] == "ok" and it["desviacion"] < 0


def test_ritmo_ponderado_por_unidades():
    par = {"etapas": [{"vmes": 10, "und": 100}, {"vmes": 20, "und": 300}],
           "mercado": {"absorcion_mercado_und_mes": 17.5}}
    r = mercado.evaluar(par, R)
    it = next(i for i in r["items"] if i["sentido"] == "ritmo")
    assert it["proyecto"] == 17.5   # (10*100 + 20*300) / 400 = 17.5


def test_referencia_contexto():
    par = {**PAR, "mercado": {"precio_m2_mercado": 3_900_000, "oferta_competencia": "alta", "fuente": "Galería 2026"}}
    r = mercado.evaluar(par, R)
    assert r["referencia"] == {"oferta_competencia": "alta", "fuente": "Galería 2026"}
