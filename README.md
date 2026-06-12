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
| `docs/` | Decisiones de arquitectura (ADRs). Empieza en [docs/README.md](docs/README.md). |

## Scripts (desde la raíz del monorepo)
| Quiero… | Linux / Git Bash | Windows / PowerShell |
|---|---|---|
| Levantar la app en local (http://localhost:8501) | `./dev.sh` | `.\dev.ps1` |
| Correr TODAS las pruebas antes de desplegar | `./test.sh` | `.\test.ps1` |
| Desplegar Streamlit a Azure (tag = SHA del commit) | `./deploy_streamlit.sh` | `.\deploy_streamlit.ps1` |

- `test.sh` corre: **engine** (contrato + harness dorado) → **app_streamlit** (regresión de cifras + humo UI) → **ruff**.
- `deploy_streamlit.sh` exige **working tree limpia** (el tag = SHA debe representar la imagen), construye en
  ACR, apunta App Service al tag exacto (no `:latest` → fuerza el pull), reinicia y verifica salud. Confirma
  la versión en el pie: «Aplicativo vX.Y.Z». Requiere `az login` previo.

## Reglas de oro
- **Snapshot dorado sagrado** (`app_streamlit/tests/golden/`): la migración NO mueve cifras (tolerancia 0.1%).
- **Deploy por SHA** del commit, nunca `:latest`.
- **Paridad antes de apagar** un módulo de Streamlit.

## Dónde vive el código
**Fuera de OneDrive** (`C:\Code\aleph`) — OneDrive sincroniza `.git` y puede corromperlo. Respaldo: GitHub.
