# -*- coding: utf-8 -*-
"""Due diligence / registro de riesgos — fusión con la plantilla + veredicto cualitativo.

`due_diligence.evaluar` es ADITIVO (no lo llama `calcular()` → dorado intacto). Verifica el merge del
registro del analista con la plantilla canónica y la lógica del semáforo de viabilidad.
"""
from aleph_engine import due_diligence as dd


def test_plantilla_sola_todo_pendiente_ambar():
    r = dd.evaluar({})   # sin registro del analista
    assert r["veredicto"]["n_items"] == len(dd.PLANTILLA)
    assert all(i["estado"] == "pendiente" and not i["del_analista"] for i in r["items"])
    assert r["veredicto"]["n_ok"] == 0
    assert r["veredicto"]["n_pendientes"] == len(dd.PLANTILLA)
    # con pendientes pero sin alerta-alto → ámbar (due diligence en proceso)
    assert r["veredicto"]["nivel"] == "ambar"
    # 5 frentes
    assert [f["clave"] for f in r["frentes"]] == ["legal", "ambiental", "urbanistico", "tecnico", "bancario"]


def test_todo_ok_verde():
    reg = [{"frente": t["frente"], "item": t["item"], "estado": "ok"} for t in dd.PLANTILLA]
    r = dd.evaluar({"due_diligence": reg})
    assert r["veredicto"]["nivel"] == "verde"
    assert r["veredicto"]["n_ok"] == len(dd.PLANTILLA)
    assert all(i["del_analista"] for i in r["items"])


def test_alerta_alto_es_rojo():
    reg = [{"frente": "legal", "item": "Estudio de títulos y tradición", "estado": "alerta", "impacto": "alto",
            "mitigacion": "Sanear antes de prometer"}]
    r = dd.evaluar({"due_diligence": reg})
    assert r["veredicto"]["nivel"] == "rojo"
    it = next(i for i in r["items"] if i["item"] == "Estudio de títulos y tradición")
    assert it["estado"] == "alerta" and it["impacto"] == "alto" and it["del_analista"]
    assert "Sanear" in it["mitigacion"]


def test_alerta_medio_sin_alto_es_ambar():
    # una alerta de impacto MEDIO + el resto ok → ámbar (no rojo)
    reg = [{"frente": t["frente"], "item": t["item"], "estado": "ok"} for t in dd.PLANTILLA]
    reg[2] = {**reg[2], "estado": "alerta", "impacto": "medio"}
    r = dd.evaluar({"due_diligence": reg})
    assert r["veredicto"]["nivel"] == "ambar" and r["veredicto"]["n_alertas"] == 1


def test_item_custom_fuera_de_plantilla_se_agrega():
    reg = [{"frente": "legal", "item": "Pleito con vecino colindante", "estado": "alerta", "impacto": "alto"}]
    r = dd.evaluar({"due_diligence": reg})
    assert any(i["item"] == "Pleito con vecino colindante" and i["del_analista"] for i in r["items"])
    assert r["veredicto"]["n_items"] == len(dd.PLANTILLA) + 1
    assert r["veredicto"]["nivel"] == "rojo"


def test_normaliza_estado_e_impacto_invalidos():
    reg = [{"frente": "legal", "item": "Estudio de títulos y tradición", "estado": "raro", "impacto": "xx"}]
    r = dd.evaluar({"due_diligence": reg})
    it = next(i for i in r["items"] if i["item"] == "Estudio de títulos y tradición")
    assert it["estado"] == "pendiente"        # estado inválido → pendiente
    assert it["impacto"] == "alto"            # impacto inválido → defecto de la plantilla
