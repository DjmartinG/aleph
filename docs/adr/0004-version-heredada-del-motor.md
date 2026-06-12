# ADR-0004 — `aleph_engine` hereda la versión del motor (2.39.0)

**Estado:** Aceptado · 2026-06

## Contexto
Al extraer el motor `cg_engine` → `aleph_engine`, había que decidir su versión. El plan sugería
arrancar el paquete nuevo en `0.1.0`. Pero `aleph_engine` **es el mismo motor** (extracción tal cual,
sin cambios de lógica): el pie de la app Streamlit muestra `Aplicativo v2.39.0` y los snapshots dorados
se generaron con esa versión.

## Decisión
`aleph_engine.__version__ = "2.39.0"` — **hereda** la versión del motor extraído, en vez de reiniciar
en `0.1.0`. La versión es **fuente única** (la lee `pyproject.toml` vía `dynamic` y el pie de la app).

## Consecuencias
- (+) Continuidad: el pie de la app, los snapshots y el paquete dicen lo mismo; no hay "dos versiones".
- (+) Evita tener que separar artificialmente "versión del motor" de "versión de la app" en esta etapa.
- (−) El paquete no empieza en `0.x`: se asume que el versionado del motor sigue desde donde estaba.
- A futuro, si la app web y el motor evolucionan a ritmos distintos, podría introducirse un esquema de
  versiones separado (sería un ADR nuevo que supersede a este).
