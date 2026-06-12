# -*- coding: utf-8 -*-
"""Construcción de los payloads de la API a partir del resultado del motor (contrato §5).

NO calcula fórmulas: arma las respuestas desde `aleph_engine` (`calcular`, `metrics`, `checks`,
`portfolio`, `modelo`). Las cifras salen tal cual del motor; aquí solo se estructuran + se añaden las
**etiquetas de base** (gobernanza de cifras: nunca "TIR" a secas).
"""
from __future__ import annotations

from aleph_engine import calcular, checks, config, metrics, modelo, portfolio

from . import repo


def _estado(par: dict) -> str:
    e = (par.get("meta") or {}).get("estado") or config.ESTADO_DEFAULT
    return e if e in config.ESTADOS else config.ESTADO_DEFAULT


def _base_label(ap: dict) -> str:
    """Etiqueta de base del proyecto: si el waterfall de fiducia corrió, las cifras son auditadas."""
    return "auditado_fiducia" if ap.get("fiducia_real") else "modelo_aprobado"


def indicadores(R: dict) -> dict:
    """Indicadores de rentabilidad/caja CON etiqueta de base (TIR proyecto vs TIR socio, etc.)."""
    ap = R.get("apalancamiento") or {}
    pg = R.get("pyg") or {}
    return {
        "base_label": _base_label(ap),
        "fiducia_real": bool(ap.get("fiducia_real")),
        "tir_proyecto": ap.get("tir_proyecto"), "tir_proyecto_label": metrics.etiqueta("tir_proyecto"),
        "tir_socio": ap.get("tir_equity"), "tir_socio_label": metrics.etiqueta("tir_socio"),
        "tir_apalancada_ref": ap.get("tir_apalancada_ref"),
        "vpn_proyecto": ap.get("vpn_proyecto"), "vpn_label": metrics.etiqueta("vpn_proyecto"),
        "wacc": ap.get("wacc"), "tio": ap.get("tio"), "payback_mes": ap.get("payback_mes"),
        "credito_max": ap.get("credito_max"), "credito_prom": ap.get("credito_prom"),
        "intereses_total": ap.get("intereses_total"), "max_necesidad_caja": ap.get("max_necesidad_caja"),
        "valor_financiable": ap.get("valor_financiable"), "margen_oper": pg.get("margen_oper"),
    }


def _checks(R: dict) -> list[dict]:
    return [{"clave": c.clave, "nombre": c.nombre, "ok": c.ok, "detalle": c.detalle}
            for c in checks.correr(R)]


def project(slug: str, par: dict, R: dict) -> dict:
    """Ficha del proyecto (§5 GET /projects/{id})."""
    pg = R.get("pyg") or {}
    ap = R.get("apalancamiento") or {}
    estado = _estado(par)
    return {
        "id": slug, "es_real": repo.es_real(slug), "fuente": repo.fuente(),
        "meta": R.get("meta"), "estado": estado, "estado_label": config.ESTADO_LABEL.get(estado, estado),
        "urbanistico": R.get("urbanistico"),
        "kpis_cabecera": {
            "ventas": pg.get("ventas"), "util_oper": pg.get("util_oper"), "udi": pg.get("udi"),
            "margen_oper": pg.get("margen_oper"), "tir_proyecto": ap.get("tir_proyecto"),
            "tir_socio": ap.get("tir_equity"), "vpn_proyecto": ap.get("vpn_proyecto"),
        },
        "params": par,
    }


def results(slug: str, par: dict, R: dict) -> dict:
    """Payload central (§5 GET /scenarios/{id}/results): indicadores + P&G + flujo + crédito + checks."""
    return {
        "scenario_id": f"{slug}:base", "project_id": slug, "es_base": True,
        "base_label": _base_label(R.get("apalancamiento") or {}),
        "indicadores": indicadores(R),
        "pyg": R.get("pyg"),
        "flujo": {"apalancado": R.get("apalancamiento"), "simple": R.get("flujo")},
        "distribucion": R.get("distribucion"),
        "checks": _checks(R),
    }


def scenarios_list(slug: str) -> dict:
    """Escenarios deterministas del proyecto (§5 GET /projects/{id}/scenarios)."""
    return {
        "project_id": slug, "default": "base",
        "scenarios": [
            {"id": f"{slug}:base", "tipo": "guardado", "d_precio": 0.0, "d_costo": 0.0, "es_base": True},
            {"id": f"{slug}:optimista", "d_precio": 0.05, "d_costo": -0.02, "es_base": False},
            {"id": f"{slug}:pesimista", "d_precio": -0.10, "d_costo": 0.05, "es_base": False},
        ],
    }


def sensitivity(slug: str, par: dict) -> dict:
    """Sensibilidad determinista (§5 GET /scenarios/{id}/sensitivity): escenarios + tornado + heatmap."""
    pasos = [-0.10, -0.05, 0.0, 0.05, 0.10]
    return {
        "scenario_id": f"{slug}:base", "project_id": slug,
        "escenarios": modelo.escenarios(par),
        "tornado": modelo.sensibilidades(par),
        "matriz_2d": {
            "pasos_precio": [p * 100 for p in pasos], "pasos_costo": [p * 100 for p in pasos],
            "margen_pct": modelo.heatmap_sensibilidad(par, pasos),
        },
    }


def portafolio(items) -> dict:
    """Consolidado + embudo + items (§5 GET /portfolio). `items` = [(slug, par, R)]."""
    cons = portfolio.consolidar(items)
    pipe = portfolio.pipeline(items)
    cuenta: dict[str, int] = {}
    for d in pipe:
        cuenta[d["estado"]] = cuenta.get(d["estado"], 0) + 1
    embudo = [{"estado": e, "label": config.ESTADO_LABEL.get(e, e), "count": cuenta.get(e, 0)}
              for e in config.ESTADOS]
    consolidado = {k: v for k, v in cons.items() if k != "filas"}
    return {"consolidado": consolidado, "embudo": embudo, "items": pipe}


def run(par: dict, req: dict) -> dict:
    """Monte Carlo (§5 POST /scenarios/{id}/run): el único cálculo intensivo. No muta `par`."""
    tipo = (req or {}).get("tipo", "tir")
    n = int((req or {}).get("n", 300))
    seed = (req or {}).get("seed", 42)
    rp = tuple((req or {}).get("rango_precio", (-0.15, 0.15)))
    rc = tuple((req or {}).get("rango_costo", (-0.10, 0.10)))
    if tipo == "margen":
        return modelo.montecarlo(par, n=n, rango_precio=rp, rango_costo=rc, seed=seed)
    rv = tuple((req or {}).get("rango_ventas", (-0.30, 0.30)))
    sigue = bool((req or {}).get("escrituracion_sigue_obra", True))
    return modelo.montecarlo_tir(par, n=n, rango_precio=rp, rango_costo=rc, rango_ventas=rv,
                                 seed=seed, escrituracion_sigue_obra=sigue)


# ---------- helpers de carga ----------

def cargar_calcular(slug: str):
    """(par, R) del proyecto, o (None, None) si no existe."""
    par = repo.cargar(slug)
    if par is None:
        return None, None
    return par, calcular(par)


def items_portafolio():
    """[(slug, par, R)] de todos los proyectos disponibles (omite los que fallan)."""
    out = []
    for slug in repo.listar():
        try:
            par = repo.cargar(slug)
            out.append((slug, par, calcular(par)))
        except Exception:
            continue
    return out
