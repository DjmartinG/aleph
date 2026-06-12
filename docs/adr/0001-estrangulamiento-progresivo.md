# ADR-0001 — Migrar por estrangulamiento progresivo (no big-bang)

**Estado:** Aceptado · 2026-06

## Contexto
La herramienta operativa de factibilidad (hoy "Factibilidad CG") es una app Streamlit en producción
que el equipo usa para decisiones reales de inversión. Se quiere evolucionar a una arquitectura
profesional de 3 capas (motor puro + API + UI web), pero **no se puede parar la operación** ni
arriesgar las cifras auditadas (Navarra, Dominica, Torres de Campiñas).

## Decisión
Migrar por **estrangulamiento progresivo** (*strangler fig*), nunca big-bang:
- La app Streamlit sigue **viva en producción** hasta que la UI nueva tenga **paridad módulo a módulo**.
- Cada fase termina con algo **desplegado y verificable**.
- Un módulo de Streamlit se retira **solo** cuando su reemplazo está desplegado y verificado.

## Consecuencias
- (+) Riesgo bajo y reversible: siempre hay una versión funcionando.
- (+) Permite validar cada paso contra cifras reales antes de avanzar.
- (−) Durante la transición conviven dos UIs sobre un mismo motor (complejidad temporal aceptada).
- Implica un único motor compartido por ambas UIs → ver [ADR-0002](0002-monorepo-un-solo-repo.md) y
  el snapshot dorado como contrato de "no cambian las cifras" → ver [ADR-0003](0003-snapshot-dorado.md).
