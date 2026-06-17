# Hallazgo para el comité — Beta del sector del WACC (revisar fuente/vigencia)

**Fecha:** 2026-06-16 · **Origen:** verificación automática contra la fuente viva (Damodaran) al construir
la pestaña "Fuentes y metodología" (Fase 2). · **Naturaleza:** dato a confirmar por el comité. **NO se
cambió ninguna cifra**: el WACC y el dorado siguen idénticos hasta que el comité decida.

---

## 1. El hallazgo

El modelo usa **`beta_us = 1.29`** (beta apalancada del sector comparable de EE.UU.), insumo del build-up
CAPM del WACC. Al contrastarla en vivo con Damodaran (NYU Stern), se ve que **1.29 está por encima de
TODOS los sectores de construcción que Damodaran publica hoy**:

| Sector Damodaran (hoy) | Beta apalancada | D/E del sector | Beta desapalancada |
|---|---|---|---|
| **Homebuilding** | **0.91** | **21.34%** | 0.78 |
| Engineering/Construction | 1.21 | 14.01% | 1.09 |
| Construction Supplies | 1.15 | 17.62% | 1.02 |
| Building Materials | 1.11 | 26.00% | 0.93 |
| **Modelo ALEPH (`beta_us`)** | **1.29** | 21.56% | (→ `beta_u` ≈ 1.15) |

**Pista fuerte:** el **D/E del sector que usa el modelo (21.56%) calza casi exacto con Homebuilding
(21.34%)** → es muy probable que la fuente original haya sido **Homebuilding**. Pero la beta de
Homebuilding **hoy es 0.91**, no 1.29. La propia [acta de re-baseline del 14-jun-2026](acta_rebaseline_wacc2_betad_rp_20260614.md)
ya lo había anotado: *"beta_u baja a 1,15 (más cerca del sector Damodaran homebuilding ~0,9–1,1)"*.

**Pregunta para el comité:** ¿de qué **sector y de qué año** de Damodaran salió `beta_us = 1.29`? Hoy
está por encima de cualquier sector de construcción. Posibles explicaciones (a confirmar):
- Es de una **vigencia anterior** (Damodaran revisa sus betas cada enero; el valor pudo bajar desde la calibración).
- Es un **sector distinto** del que sugiere el D/E.
- Es una **elección conservadora** deliberada (mayor beta → mayor exigencia).

---

## 2. Por qué importa (impacto cuantificado en Navarra)

El WACC es **de exhibición** (las decisiones de inversión se descuentan a la TIO 15%), **pero es el
hurdle del Veredicto de Valor (EVA)**: un proyecto "genera valor" si su TIR supera el WACC, y
`valor_creado` es el VPN descontado al WACC. **Bajar la beta baja el WACC y hace que más proyectos
generen valor.**

| `beta_us` | Sector de referencia | WACC | Δ vs hoy |
|---|---|---|---|
| **1.29** | (actual del modelo) | **18.71%** | — |
| 1.21 | Engineering/Construction | 18.49% | −0.22 pp |
| 1.15 | (≈ beta_u objetivo) | 18.32% | −0.39 pp |
| 1.11 | Building Materials | 18.21% | −0.50 pp |
| **0.91** | **Homebuilding (hoy)** | **17.65%** | **−1.06 pp** |

Es decir: alinear a la beta actual de Homebuilding bajaría el WACC **~1 punto** (18.71% → 17.65%). Un
proyecto con TIR entre 17.65% y 18.71% **pasaría de "destruir" a "generar" valor** solo por este cambio.

---

## 3. Recomendación

1. **Confirmar la fuente y la vigencia** de `beta_us = 1.29` (qué sector y qué año de Damodaran). Es la
   pieza que falta para saber si está al día o quedó rezagada.
2. **Decidir conscientemente** entre dos posturas defendibles:
   - **Mantener 1.29** (postura **conservadora**: hurdle más exigente; menos proyectos "generan valor").
   - **Recalibrar** al sector vigente (Homebuilding 0.91, o un sector/mezcla que el comité valide).
3. Si se decide recalibrar, **es un re-baseline del dorado** (mueve el WACC y el EVA) → exige **acta +
   aprobación explícita** antes de aplicarlo. **NO se toca nada hasta esa decisión.**

> Ojo con el sesgo: recalibrar a la baja "mejora" el EVA de la cartera (más proyectos generan valor). Por
> eso la decisión debe basarse en **cuál beta es la correcta**, no en cuál conviene. Mantener 1.29 es
> conservador y defendible; alinearla a la fuente viva también — pero a conciencia.

---

*Este hallazgo lo destapó la verificación automática modelo-vs-fuente que ahora vive en la pestaña
"Fuentes y metodología" (riesgo país y prima de mercado ya muestran su dato vivo; la beta no se muestra
en vivo precisamente por esta ambigüedad de sector, que este memo busca resolver).*
