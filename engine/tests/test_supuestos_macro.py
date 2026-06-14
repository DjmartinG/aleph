# -*- coding: utf-8 -*-
"""M0 (spec_pyg_dinamico.md) — el módulo de Supuestos Macro NO mueve cifras.

Verifica: (1) los defaults del registro == constantes de config (cero cifras nuevas);
(2) la precedencia del `resolver` (el `par` del proyecto manda; el macro rellena ausencias),
espejando los `fin.get(clave, config.DEFAULT)` de hoy; (3) que `Metric` admite los campos nuevos
sin romper su construcción posicional existente.
"""
from aleph_engine import config, metrics
from aleph_engine import supuestos_macro as sm


# --- (1) defaults idénticos a config (no se mueve ninguna cifra) ---
def test_defaults_espejan_config():
    esperado = {
        "tio": config.TIO,
        "renta": config.RENTA,
        "split_cg": config.SPLIT_CG,
        "tasa_credito_ea": config.TASA_CREDITO_EA,
        "cobertura_cc": config.COBERTURA_CC,
        "pct_ci": config.PCT_CI,
        "sep_und_miles": config.SEP_UND_MILES,
        "diferido_sep": config.DIFERIDO_SEP,
    }
    for clave, val in esperado.items():
        assert sm.default(clave) == val, f"default {clave} difiere de config"
        assert sm.REGISTRO[clave].valor == val


def test_default_clave_desconocida_es_none():
    assert sm.default("no_existe") is None


# --- (2) precedencia: par del proyecto > default macro (≡ fin.get(clave, default)) ---
def test_resolver_par_manda():
    fin = {"renta": 0.33, "tio": 0.18}
    assert sm.resolver(fin, "renta") == 0.33
    assert sm.resolver(fin, "tio") == 0.18


def test_resolver_macro_rellena_ausencias():
    fin = {"renta": 0.33}            # no trae 'tio' → cae al default macro (= config.TIO)
    assert sm.resolver(fin, "tio") == config.TIO
    assert sm.resolver({}, "split_cg") == config.SPLIT_CG
    assert sm.resolver(None, "renta") == config.RENTA


def test_resolver_espeja_fin_get():
    # Mismo resultado que el patrón disperso de hoy `fin.get(clave, config.X)`.
    for fin in ({}, {"renta": 0.30}, {"tio": 0.2, "split_cg": 0.6}):
        for clave, default_cfg in (("renta", config.RENTA), ("tio", config.TIO), ("split_cg", config.SPLIT_CG)):
            assert sm.resolver(fin, clave) == fin.get(clave, default_cfg)


def test_resolver_fallback_clave_no_registrada():
    assert sm.resolver({}, "clave_rara", fallback=7) == 7
    assert sm.resolver({"clave_rara": 9}, "clave_rara", fallback=7) == 9


# --- (3) Metric admite los campos nuevos sin romper lo existente ---
def test_metric_construccion_posicional_sigue_valida():
    m = metrics.Metric("k", "N", "base", "def", metrics.PCT, ("pyg", "ventas"), "pyg")
    assert m.estado_validacion == "vigente"
    assert m.fuente_normativa == ""


def test_metric_acepta_campos_nuevos():
    m = metrics.Metric("k", "N", "base", "def", metrics.PCT, ("pyg", "ventas"), "pyg",
                       estado_validacion="por_validar", fuente_normativa="ET 235-2")
    assert m.estado_validacion == "por_validar"
    assert m.fuente_normativa == "ET 235-2"


def test_registro_existente_intacto():
    # El registro de métricas sigue construyéndose (defaults nuevos no rompen nada).
    assert "tir_proyecto" in metrics.REGISTRO
    assert metrics.REGISTRO["tir_proyecto"].estado_validacion == "vigente"
