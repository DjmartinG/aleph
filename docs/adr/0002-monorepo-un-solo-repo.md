# ADR-0002 — Monorepo en UN solo repositorio (`aleph`)

**Estado:** Aceptado · 2026-06

## Contexto
ALEPH tiene cuatro piezas: el motor (`engine/aleph_engine`), la API (`api/`), la web (`web/`) y la app
Streamlit actual (`app_streamlit/`). El plan original contemplaba un repositorio **nuevo y separado**
llamado `aleph`. Para entonces ya existía el repo `cg-factibilidad-app` con la app y, sobre él, se
había construido el motor extraído y el andamiaje del monorepo (con historia de commits).

## Decisión
Mantener **un solo repositorio monorepo** que contiene las cuatro piezas, y **renombrar** el repo de
GitHub `cg-factibilidad-app` → **`aleph`** (GitHub conserva la historia y deja redirects), en vez de
crear un repo nuevo desde cero.

## Consecuencias
- (+) Un solo lugar para motor + UIs: cambios atómicos y CI único; la app Streamlit y la web futura
  comparten **el mismo `aleph_engine`** durante toda la transición (clave para el estrangulamiento).
- (+) Renombrar (no recrear) **preserva los commits** y no rompe enlaces (redirects automáticos).
- (−) El contexto de build de la imagen Streamlit debe abarcar `engine/` + `app_streamlit/`
  (ver [ADR-0005](0005-deploy-por-sha-imagen-bundle.md)).
- **Crítico:** el repositorio NUNCA va dentro de OneDrive/SharePoint — la sincronización corrompe la
  carpeta `.git` (se observó dos veces). Vive en `C:\Code\aleph` (fuera de OneDrive); GitHub es la
  fuente de verdad.
