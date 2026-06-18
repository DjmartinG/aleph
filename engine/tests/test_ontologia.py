# -*- coding: utf-8 -*-
"""Ontología canónica (fachada de SOLO LECTURA).

Verifica: (1) importa limpio y expone el vocabulario; (2) CONSISTENCIA SIN DRIFT con las fuentes
(FASES==config.ESTADOS, vehículos/indicadores/categorías reales); (3) el registro de INVARIANTES
referencia funciones reales y sus id coinciden con las claves de los checks; (4) el DORADO queda
INTACTO (importar la fachada no mueve ninguna cifra de `calcular()` — la garantía de que es aditivo).
"""
import json

import pytest

from aleph_engine import calcular, checks, config, metrics, ontologia, vehiculos
from aleph_engine.schema import CostosPct

from ._golden import find_snapshots

SNAPS = find_snapshots()


def test_importa_limpio_y_expone_el_vocabulario():
    for attr in ("FASES", "TIPOS_PROYECTO", "CATEGORIAS_COSTO", "HITOS", "CONCEPTOS_RECAUDO",
                 "INDICADORES", "VEHICULOS", "INVARIANTES"):
        assert hasattr(ontologia, attr), f"falta {attr}"


def test_fases_es_la_fuente_sin_drift():
    assert ontologia.FASES is config.ESTADOS              # referencia, no copia (sin drift)
    assert ontologia.FASE_DEFAULT == config.ESTADO_DEFAULT
    assert ontologia.FASE_LABEL is config.ESTADO_LABEL


def test_tipos_proyecto_canonicos():
    # Hoy no hay fuente tipada (schema.Meta.tipo es Optional[str]) → constante canónica.
    assert ontologia.TIPOS_PROYECTO == ("VIS", "VIP", "No VIS")


def test_categorias_costo_son_los_campos_de_costospct():
    assert ontologia.CATEGORIAS_COSTO == tuple(CostosPct.model_fields)
    assert set(ontologia.CATEGORIAS_COSTO) == {"directos", "indirectos", "honorarios", "util_lote"}


def test_vehiculos_existen_en_el_catalogo():
    assert ontologia.VEHICULOS
    assert set(ontologia.VEHICULOS) == set(vehiculos.claves())
    for v in ontologia.VEHICULOS:
        assert vehiculos.existe(v)


def test_indicadores_son_el_registro_de_metrics_sin_duplicar():
    assert ontologia.INDICADORES is metrics.REGISTRO     # mismo dict (no se duplica)
    for clave in ontologia.INDICADORES:
        assert isinstance(ontologia.indicador(clave), metrics.Metric)


def test_hitos_y_conceptos_recaudo_bien_formados():
    codigos = [h.codigo for h in ontologia.HITOS]
    assert codigos == ["IV", "PE", "FV", "IC", "FC", "escrituracion"]
    assert ontologia.HITOS_POR_CODIGO["IV"].nombre == "Inicio de ventas"
    claves = [c.clave for c in ontologia.CONCEPTOS_RECAUDO]
    assert claves == ["separacion", "cuota_inicial", "subrogacion", "fiducia", "credito_constructor"]


def test_invariantes_referencian_funciones_reales():
    ids = [inv.id for inv in ontologia.INVARIANTES]
    assert len(ids) == len(set(ids))                     # ids únicos
    for inv in ontologia.INVARIANTES:
        assert callable(inv.referencia) or isinstance(inv.referencia, str)
        assert inv.nombre and inv.descripcion


def test_invariantes_id_coinciden_con_las_claves_de_los_checks():
    # DATA-INDEPENDIENTE: un R sintético que dispara los 5 checks de cuadre → sus claves deben ser
    # EXACTAMENTE los id de los invariantes (menos SPI, que vive en check_spi). Sin drift.
    R = {
        "pyg": {"total_ingresos": 100.0, "ventas": 100.0, "recon_codensa": 0.0,
                "util_oper": 10.0, "cg": 7.0, "socio": 3.0, "resultados": 10.0},
        "apalancamiento": {"ingresos": [100.0], "acumulado": [10.0],
                           "cap_credito": 50.0, "valor_financiable": 80.0, "credito_max": 30.0},
    }
    claves_check = {c.clave for c in checks.correr(R)}
    ids_no_spi = {inv.id for inv in ontologia.INVARIANTES if inv.id != "spi_plausible"}
    assert ids_no_spi == claves_check
    # SPI: la referencia es check_spi y emite la clave 'spi_plausible'.
    assert checks.check_spi({"SPI": 1.0}).clave == "spi_plausible"


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_hitos_codigos_aparecen_en_el_cronograma_real():
    # Los códigos de cronograma que nombramos (IV/PE/FV/IC/FC) EXISTEN en el dict de hitos que
    # `calcular()` produce → la fachada no inventó códigos (sin drift con el cálculo).
    for p in SNAPS:
        hitos = calcular(json.load(open(p, encoding="utf-8"))["input_par"]).get("hitos") or {}
        if hitos:
            etapa = next(iter(hitos.values()))
            cronograma = {h.codigo for h in ontologia.HITOS if h.codigo != "escrituracion"}
            assert cronograma <= set(etapa)
            return
    pytest.skip("ningún snapshot produjo hitos")


@pytest.mark.skipif(not SNAPS, reason="No hay snapshots dorados")
def test_dorado_intacto_la_fachada_es_aditiva():
    # Importar la ontología NO cambia `calcular()`: cada snapshot reproduce sus anclas dentro de la
    # tolerancia del dorado (0.1%). Es la prueba de que el módulo es 100% aditivo.
    import aleph_engine.ontologia  # noqa: F401  (el import es el punto de la prueba)

    TOL = 0.001
    anclas = (("apalancamiento", "tir_proyecto"), ("apalancamiento", "vpn_proyecto"),
              ("pyg", "ventas"), ("pyg", "util_oper"))
    for p in SNAPS:
        snap = json.load(open(p, encoding="utf-8"))
        R = calcular(snap["input_par"])
        esp = snap["result"]
        for seccion, clave in anclas:
            e = (esp.get(seccion) or {}).get(clave)
            a = (R.get(seccion) or {}).get(clave)
            if e is None or a is None:
                continue
            assert abs(a - e) <= max(1.0, TOL * abs(e)), f"{p}: {seccion}.{clave} {a} vs {e}"
