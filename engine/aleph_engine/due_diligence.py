# -*- coding: utf-8 -*-
"""Due Diligence + registro de riesgos del prefacto → veredicto de viabilidad CUALITATIVA.

Curso Camacol: M4 (legal), M5 (ambiental), M1/M5 (urbanístico/POT) + técnico y financiero/bancario.
Captura los estudios cualitativos como un registro estructurado (estado + impacto + mitigación) y
deriva un semáforo de viabilidad que ACOMPAÑA al veredicto financiero (no lo reemplaza).

DISEÑO:
  - El registro del analista vive en el `par` del escenario (`par['due_diligence']`), una lista de
    {frente, item, estado, impacto, mitigacion, nota}. Rida la infra de scenarios (versionado/audit);
    el MOTOR financiero lo IGNORA (no es cálculo) → `calcular()` y el dorado intactos.
  - Aquí se FUSIONA ese registro con una PLANTILLA canónica (el checklist estándar del prefacto): los
    ítems que el analista no haya llenado quedan en "pendiente". Es agregación descriptiva, no cálculo.

NOTA: la plantilla es un primer set para refinar con el comité (algunos ítems/impactos `[por validar]`).
La CAPTURA/edición de estados se hará en el Ingreso de datos (/web, fase posterior); hoy se LEE.
"""
from __future__ import annotations

FRENTES = (
    ("legal", "Legal"),
    ("ambiental", "Ambiental / ESG"),
    ("urbanistico", "Urbanístico / POT"),
    ("tecnico", "Técnico"),
    ("bancario", "Financiero / bancario"),
)

ESTADOS = ("ok", "alerta", "pendiente")
IMPACTOS = ("alto", "medio", "bajo")

# Checklist canónico del prefacto. `impacto` = peso por defecto en la viabilidad (si el analista no lo
# fija). Primer set — refinar con el comité.  # TODO [por validar]: lista definitiva por frente.
PLANTILLA = (
    {"frente": "legal", "item": "Estudio de títulos y tradición", "impacto": "alto"},
    {"frente": "legal", "item": "Saneamiento jurídico del predio", "impacto": "alto"},
    {"frente": "legal", "item": "Contratos típicos (promesa, fiducia, encargo)", "impacto": "medio"},
    {"frente": "legal", "item": "Riesgos legales / litigios / servidumbres", "impacto": "alto"},
    {"frente": "ambiental", "item": "Licencia y permisos ambientales", "impacto": "alto"},
    {"frente": "ambiental", "item": "Impactos ambientales y mitigación", "impacto": "medio"},
    {"frente": "ambiental", "item": "Sostenibilidad / ESG", "impacto": "bajo"},
    {"frente": "ambiental", "item": "Normativa ambiental aplicable", "impacto": "medio"},
    {"frente": "urbanistico", "item": "Uso del suelo permitido (POT)", "impacto": "alto"},
    {"frente": "urbanistico", "item": "Índice de construcción / aprovechamiento", "impacto": "alto"},
    {"frente": "urbanistico", "item": "Cesiones y obligaciones urbanísticas", "impacto": "medio"},
    {"frente": "tecnico", "item": "Estudio de suelos / geotecnia", "impacto": "alto"},
    {"frente": "tecnico", "item": "Disponibilidad de servicios públicos", "impacto": "medio"},
    {"frente": "tecnico", "item": "Licencia de construcción / diseños", "impacto": "medio"},
    {"frente": "bancario", "item": "Crédito constructor (aprobación)", "impacto": "alto"},
    {"frente": "bancario", "item": "Estructura fiduciaria / patrimonio autónomo", "impacto": "medio"},
)


def _clave(frente, item) -> str:
    return f"{frente}::{item}".strip().lower()


def _norm_estado(v) -> str:
    return v if v in ESTADOS else "pendiente"


def _norm_impacto(v, defecto) -> str:
    return v if v in IMPACTOS else defecto


def evaluar(par: dict) -> dict:
    """Fusiona el registro del analista (`par['due_diligence']`) con la plantilla y deriva el veredicto.

    Veredicto (semáforo): rojo = hay un riesgo de impacto ALTO en estado "alerta" (problema confirmado);
    ámbar = hay ítems abiertos (alerta o pendiente) sin rojo; verde = todo "ok".
    """
    reg = par.get("due_diligence") or []
    por_clave: dict[str, dict] = {}
    for r in reg:
        if isinstance(r, dict) and r.get("frente") and r.get("item"):
            por_clave[_clave(r["frente"], r["item"])] = r

    items: list[dict] = []
    usados: set[str] = set()
    for t in PLANTILLA:
        c = _clave(t["frente"], t["item"])
        usados.add(c)
        a = por_clave.get(c)
        items.append({
            "frente": t["frente"], "item": t["item"],
            "estado": _norm_estado(a.get("estado") if a else None),
            "impacto": _norm_impacto(a.get("impacto") if a else None, t["impacto"]),
            "mitigacion": (a.get("mitigacion") if a else "") or "",
            "nota": (a.get("nota") if a else "") or "",
            "del_analista": a is not None,
        })
    # Ítems adicionales que el analista agregó fuera de la plantilla.
    for r in reg:
        if not (isinstance(r, dict) and r.get("frente") and r.get("item")):
            continue
        c = _clave(r["frente"], r["item"])
        if c in usados:
            continue
        usados.add(c)
        items.append({
            "frente": r["frente"], "item": r["item"],
            "estado": _norm_estado(r.get("estado")), "impacto": _norm_impacto(r.get("impacto"), "medio"),
            "mitigacion": r.get("mitigacion") or "", "nota": r.get("nota") or "", "del_analista": True,
        })

    abiertos = [i for i in items if i["estado"] != "ok"]
    n_alertas = sum(1 for i in items if i["estado"] == "alerta")
    n_pendientes = sum(1 for i in items if i["estado"] == "pendiente")
    rojo = any(i["estado"] == "alerta" and i["impacto"] == "alto" for i in items)
    nivel = "rojo" if rojo else ("ambar" if abiertos else "verde")

    return {
        "frentes": [{"clave": k, "nombre": n} for k, n in FRENTES],
        "items": items,
        "veredicto": {
            "nivel": nivel,
            "n_items": len(items),
            "n_ok": len(items) - len(abiertos),
            "n_alertas": n_alertas,
            "n_pendientes": n_pendientes,
        },
    }
