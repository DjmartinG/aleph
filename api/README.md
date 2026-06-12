# api — `aleph_api` (FastAPI)

Envuelve `aleph_engine` y expone el motor por HTTP. NO reimplementa fórmulas — solo lee proyectos,
corre `calcular()` y estructura la respuesta (indicadores **con etiqueta de base**, P&G, flujo, crédito,
checks de cuadre, sensibilidad).

> **Estado: PROMPT 4 · Fase 4a (lectura) + 4c (auth Entra ID).** Versión 0.1.0.
> Sin migración de esquema, sin tocar el Streamlit. Contrato en `../directives/plan_migracion.md` §5.

## Auth (Entra ID) — `auth.py`
Valida el **JWT de Entra ID** del header `Authorization: Bearer` (firma RS256 vía JWKS del tenant,
`aud`, `iss`, `exp`), con **PyJWT**. Es **config-driven**: se activa SOLO si están estas variables de
entorno (si no, la API queda abierta — útil en dev/CI):

| Variable | Qué es |
|---|---|
| `ENTRA_TENANT_ID` | GUID del tenant de Entra (el mismo del App Service actual). |
| `API_AUDIENCE` | audiencia que debe traer el token = App ID URI o client-id del **registro de app de la API**. |
| `ALEPH_ADMINS` | (opcional) correos admin separados por coma (rol admin si no viene en los claims). |
| `ALEPH_CORS_ORIGINS` | (opcional) orígenes permitidos del `/web` (coma-separados); por defecto `*`. |

**Lo que Martin configura en Entra (para 4d):** registrar una **app para la API** (exponer un scope /
App ID URI → ese es `API_AUDIENCE`); la app del `/web` pide un token para ese scope; poner las variables
de arriba como *Application settings* del App Service `cg-aleph-api`. `/version` queda público (health).

## Endpoints (v1)
| Método | Ruta | Qué devuelve |
|---|---|---|
| GET | `/version` | versión de la API + del motor |
| GET | `/v1/portfolio?estado=` | consolidado + embudo + items (pipeline) |
| GET | `/v1/projects/{slug}` | ficha: meta, estado, KPIs cabecera, `params` |
| GET | `/v1/projects/{slug}/scenarios` | base / optimista / pesimista (deltas) |
| GET | `/v1/scenarios/{slug}:base/results` | **indicadores (etiqueta de base) + P&G + flujo + crédito + checks** |
| GET | `/v1/scenarios/{slug}:base/sensitivity` | escenarios + tornado + heatmap 2D |
| POST | `/v1/scenarios/{slug}:base/run` | Monte Carlo TIR/VPN o margen (único cálculo intensivo) |

## Datos (`repo.py`)
Misma convención que `app_streamlit/storage.py`: si hay `SUPABASE_URL`+`SUPABASE_KEY` en el entorno
lee la tabla `proyectos`; si no, los JSON locales (`proyectos_privados/*_REAL.json` con prioridad sobre
`proyectos/*.json`). En dev/CI funciona sin Supabase.

## Correr en local
```bash
./dev_api.sh            # http://localhost:8000/docs  (OpenAPI interactivo)
# tests:
cd api && python -m pytest -q
```
Test de contrato: el `GET .../results` de Navarra devuelve **TIR proyecto 37.60%** (datos reales,
local) — **idéntico al snapshot dorado**; y la API expone exactamente lo que produce el motor.

## Pendiente (fases siguientes)
- **4b** migración de datos a `projects`/`scenarios` (Supabase). **4c** auth Entra ID + roles.
- **4d** deploy (App Service `cg-aleph-api`, tag=SHA, `/version`).
