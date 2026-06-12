# ADR-0005 — Deploy por SHA del commit; la imagen empaqueta el motor

**Estado:** Aceptado · 2026-06

## Contexto
La app Streamlit se despliega como **contenedor** en Azure App Service (vía Azure Container Registry),
no en modo "Code" (el auto-instalador Oryx dio problemas irresolubles). Dos necesidades nuevas:
1. **Determinismo**: saber exactamente qué commit corre en producción.
2. Tras el monorepo, la app **importa `aleph_engine`** (que vive en `engine/`, fuera de `app_streamlit/`):
   la imagen debe incluir el motor.

## Decisión
- **Tag = SHA del commit**, nunca `:latest`. Cada deploy usa un tag único → App Service **siempre**
  baja la imagen nueva (esquiva el gotcha del digest cacheado de `:latest`). Gate: working-tree limpia.
- La imagen **empaqueta el motor**: el contexto de build es la **raíz del monorepo** y el Dockerfile
  (`Dockerfile.streamlit`) hace `COPY engine/ + pip install ./engine` además de copiar la app.
- El deploy (`deploy_streamlit.*`) captura la **imagen previa** antes de cambiar, para **rollback**
  inmediato si el health-check (`/_stcore/health`) falla.

## Consecuencias
- (+) Imagen reproducible y trazable por commit; contenedor **autocontenido** (motor + app + libs).
- (+) Rollback de un comando; verificación de salud automática.
- (−) Contexto de build más grande (raíz) → mitigado con `.dockerignore` (excluye `tests`, secretos,
  datos reales, `web`, `api`, caches).
- Recursos Azure (`cg-factibilidad-app`, registry `cgfactibilidadacr`) son independientes del **nombre**
  del repo de GitHub: renombrar el repo a `aleph` no los afecta.
