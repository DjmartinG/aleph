# ALEPH — monorepo

Plataforma de evaluación financiera de proyectos inmobiliarios de **CG Constructora S.A.S.**
Migración Streamlit → arquitectura de 3 capas por **estrangulamiento progresivo**.
Documento gobernante: `CLAUDE.md` (§ALEPH). Plan de migración: `directives/plan_migracion.md`.
Biblioteca de prompts por fase: `directives/prompts_migracion_v3.md`.

## Estructura
| Carpeta | Qué es |
|---|---|
| `engine/` | `aleph_engine`: motor financiero **puro** (Python). Fuente única de la verdad. |
| `api/` | FastAPI sobre el motor + Supabase. Contrato OpenAPI versionado. |
| `web/` | Next.js + TS + Tailwind + shadcn/ui. UI profesional (solo presenta). |
| `app_streamlit/` | La app Streamlit **actual**, en producción hasta tener paridad. No se le añade funcionalidad nueva. |

## Reglas de oro
- **Snapshot dorado sagrado** (`app_streamlit/tests/golden/`): la migración NO mueve cifras (tolerancia 0.1%).
- **Deploy por SHA** del commit, nunca `:latest`.
- **Paridad antes de apagar** un módulo de Streamlit.

## Dónde vive el código
**Fuera de OneDrive** (`C:\Code\aleph`) — OneDrive sincroniza `.git` y puede corromperlo. Respaldo: GitHub.
