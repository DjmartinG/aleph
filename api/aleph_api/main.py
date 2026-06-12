# -*- coding: utf-8 -*-
"""App FastAPI de ALEPH (Fase 4a — lectura). Expone el motor `aleph_engine` por HTTP.

Contrato §5 de `directives/plan_migracion.md`. Auth (Entra ID) y migración de datos llegan en fases
posteriores; por ahora es solo lectura sobre los datos actuales, sin tocar Supabase ni el Streamlit.
"""
from __future__ import annotations

from aleph_engine import __version__ as ENGINE_V
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import __version__, build

app = FastAPI(
    title="ALEPH API",
    version=__version__,
    description="API de lectura del motor de factibilidad de CG Constructora (sobre aleph_engine).",
)

# CORS abierto en Fase 4a (sin auth todavía). Se restringe al añadir Entra ID (Fase 4c).
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


def _slug_de_escenario(scenario_id: str) -> str:
    """`{slug}:base|optimista|pesimista` → slug. En Fase 4a solo se sirve la base."""
    return scenario_id.split(":", 1)[0]


def _par_o_404(slug: str):
    par, R = build.cargar_calcular(slug)
    if par is None:
        raise HTTPException(status_code=404, detail=f"Proyecto '{slug}' no encontrado")
    return par, R


@app.get("/version")
def version():
    return {"name": "aleph-api", "version": __version__, "engine_version": ENGINE_V}


@app.get("/v1/portfolio")
def get_portfolio(estado: str | None = Query(default=None)):
    items = build.items_portafolio()
    payload = build.portafolio(items)
    if estado:
        payload = {**payload, "items": [d for d in payload["items"] if d.get("estado") == estado]}
    return payload


@app.get("/v1/projects/{slug}")
def get_project(slug: str):
    par, R = _par_o_404(slug)
    return build.project(slug, par, R)


@app.get("/v1/projects/{slug}/scenarios")
def get_scenarios(slug: str):
    _par_o_404(slug)                       # 404 si no existe
    return build.scenarios_list(slug)


@app.get("/v1/scenarios/{scenario_id}/results")
def get_results(scenario_id: str):
    slug = _slug_de_escenario(scenario_id)
    par, R = _par_o_404(slug)
    return build.results(slug, par, R)


@app.get("/v1/scenarios/{scenario_id}/sensitivity")
def get_sensitivity(scenario_id: str):
    slug = _slug_de_escenario(scenario_id)
    par, _R = _par_o_404(slug)
    return build.sensitivity(slug, par)


@app.post("/v1/scenarios/{scenario_id}/run")
def post_run(scenario_id: str, req: dict | None = None):
    slug = _slug_de_escenario(scenario_id)
    par, _R = _par_o_404(slug)
    return build.run(par, req or {})
