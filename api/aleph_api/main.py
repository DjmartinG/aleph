# -*- coding: utf-8 -*-
"""App FastAPI de ALEPH (Fase 4a lectura + 4c auth). Expone el motor `aleph_engine` por HTTP.

Contrato §5 de `directives/plan_migracion.md`. La auth (Entra ID) se activa por configuración
(`auth.py`): sin `ENTRA_TENANT_ID`/`API_AUDIENCE` la API queda abierta (dev/CI). La migración de
datos a `projects`/`scenarios` llega en 4b.
"""
from __future__ import annotations

import logging
import os

from aleph_engine import __version__ as ENGINE_V
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__, auth, build, repo, write

log = logging.getLogger("aleph_api")

app = FastAPI(
    title="ALEPH API",
    version=__version__,
    description="API de lectura del motor de factibilidad de CG Constructora (sobre aleph_engine).",
)

# CORS: orígenes desde ALEPH_CORS_ORIGINS (coma-separados) o "*" si no se configura (dev).
_origins = [o.strip() for o in os.environ.get("ALEPH_CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware, allow_origins=_origins, allow_methods=["*"], allow_headers=["*"],
)

# Aviso de arranque: que no pase desapercibido un despliegue con la auth apagada.
if not auth.auth_enabled():
    if auth.auth_required():
        log.error("ALEPH_AUTH_REQUIRED=true pero la auth NO está configurada: las rutas /v1 devolverán 503.")
    else:
        log.warning("AUTH DESHABILITADA (sin ENTRA_TENANT_ID/API_AUDIENCE): API abierta — solo para dev/CI.")

# Router v1: TODO requiere usuario autenticado (no-op si la auth está deshabilitada en dev/CI).
v1 = APIRouter(prefix="/v1", dependencies=[Depends(auth.current_user)])


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
    """Salud + versión (público, sin auth — sirve de health check). No expone el estado de la auth."""
    return {"name": "aleph-api", "version": __version__, "engine_version": ENGINE_V}


@app.get("/health/data")
def health_data():
    """Salud de DATOS (público, sin auth ni cifras sensibles): fuente + nº de proyectos visibles.
    Permite verificar un deploy (`project_count` > 0) AUNQUE la auth de `/v1` esté cerrada — así no hay
    que exponer rutas confidenciales para confirmar que la API lee los datos. `data_source=supabase` con
    `project_count=0` delata una mala config de Supabase (configurada pero la consulta no trae filas)."""
    return {"data_source": repo.fuente(), "project_count": len(repo.listar()),
            "read_model": repo.read_model()}


@v1.get("/portfolio")
def get_portfolio(estado: str | None = Query(default=None)):
    items = build.items_portafolio()
    # Fail-loud en prod: sin la imagen no hay respaldo local, así que 0 proyectos = la fuente de datos
    # no respondió. Con ALEPH_DATA_REQUIRED=true devolvemos 503 en vez de un 200 con portafolio vacío.
    if repo.data_required() and not items:
        log.error("ALEPH_DATA_REQUIRED=true pero 0 proyectos disponibles (fuente=%s) → 503", repo.fuente())
        raise HTTPException(
            status_code=503,
            detail="Sin proyectos disponibles: la fuente de datos no respondió (revisar SUPABASE_URL/KEY).",
        )
    payload = build.portafolio(items)
    if estado:
        payload = {**payload, "items": [d for d in payload["items"] if d.get("estado") == estado]}
    return payload


@v1.get("/projects/{slug}")
def get_project(slug: str):
    par, R = _par_o_404(slug)
    return build.project(slug, par, R)


@v1.get("/projects/{slug}/scenarios")
def get_scenarios(slug: str):
    _par_o_404(slug)
    return build.scenarios_list(slug)


@v1.get("/scenarios/{scenario_id}/results")
def get_results(scenario_id: str):
    slug = _slug_de_escenario(scenario_id)
    par, R = _par_o_404(slug)
    return build.results(slug, par, R)


@v1.get("/scenarios/{scenario_id}/sensitivity")
def get_sensitivity(scenario_id: str):
    slug = _slug_de_escenario(scenario_id)
    par, _R = _par_o_404(slug)
    return build.sensitivity(slug, par)


@v1.get("/scenarios/{scenario_id}/schedule")
def get_schedule(scenario_id: str):
    slug = _slug_de_escenario(scenario_id)
    par, R = _par_o_404(slug)
    return build.schedule(slug, par, R)


@v1.get("/scenarios/{scenario_id}/wacc")
def get_wacc(scenario_id: str):
    slug = _slug_de_escenario(scenario_id)
    par, R = _par_o_404(slug)
    return build.wacc(slug, par, R)


@v1.post("/scenarios/{scenario_id}/run")
def post_run(scenario_id: str, req: dict | None = None):
    slug = _slug_de_escenario(scenario_id)
    par, _R = _par_o_404(slug)
    return build.run(par, req or {})


# ---------- Escritura (Fase 2): crear/editar borradores → aprobar → baseline ----------
# TODO write exige rol admin (`require_admin`); gerencia es solo-lectura. El `par` se valida con el
# contrato del motor (write._validar) antes de persistir. NO toca el motor (cifras intactas).

class ProjectCreate(BaseModel):
    par: dict
    slug: str | None = None
    nombre: str | None = None
    es_real: bool = False


class ScenarioWrite(BaseModel):
    par: dict


def _actor(user: auth.Principal) -> str | None:
    return user.email or user.oid


@v1.post("/projects")
def post_project(body: ProjectCreate, user: auth.Principal = Depends(auth.require_admin)):
    """Crea un proyecto NUEVO + su escenario v1 en borrador (admin)."""
    return write.crear_proyecto(body.par, slug=body.slug, nombre=body.nombre,
                                es_real=body.es_real, actor=_actor(user))


@v1.post("/projects/{project_id}/scenarios")
def post_scenario(project_id: str, body: ScenarioWrite, user: auth.Principal = Depends(auth.require_admin)):
    """Crea un escenario borrador NUEVO (siguiente versión) sobre un proyecto (admin)."""
    return write.nuevo_draft(project_id, body.par, actor=_actor(user))


@v1.put("/scenarios/{scenario_id}")
def put_scenario(
    scenario_id: str,
    body: ScenarioWrite,
    user: auth.Principal = Depends(auth.require_admin),
    if_match: str | None = Header(default=None, alias="If-Match"),
):
    """Reemplaza el snapshot de un borrador (solo si status=draft; approved/baseline → 409). Admin.
    Concurrencia optimista: enviar `If-Match: <updated_at>` → 409 si otro usuario editó entremedio."""
    return write.editar_draft(scenario_id, body.par, actor=_actor(user), if_match=if_match)


@v1.post("/scenarios/{scenario_id}/approve")
def post_approve(scenario_id: str, user: auth.Principal = Depends(auth.require_admin)):
    """Aprueba un borrador: valida → recalcula con el motor → congela snapshot + cache + audita (admin)."""
    return write.aprobar(scenario_id, actor=_actor(user))


@v1.post("/scenarios/{scenario_id}/baseline")
def post_baseline(scenario_id: str, user: auth.Principal = Depends(auth.require_admin)):
    """Fija un escenario aprobado como baseline (la versión oficial; uno por proyecto) (admin)."""
    return write.fijar_baseline(scenario_id, actor=_actor(user))


@v1.delete("/projects/{slug}")
def delete_project(slug: str, user: auth.Principal = Depends(auth.require_admin)):
    """Borra un proyecto COMPLETO (sus escenarios + cache) por slug. Irreversible. Audita. Solo admin."""
    return write.eliminar_proyecto(slug, actor=_actor(user))


app.include_router(v1)
