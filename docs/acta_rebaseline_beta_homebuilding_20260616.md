# Acta de re-baseline — Beta del sector a Homebuilding (Damodaran, jun-2026)

**Fecha:** 2026-06-16 · **Aprobación:** Martín, explícita en sesión ("adelante", 2026-06-16). · **Mergea:** Martín, vía PR (gate dorado verde).

---

## 1. Decisión

Recalibrar la **beta del sector** del build-up del WACC de **`beta_us = 1.29` → `0.91`**, alineándola al
sector **Homebuilding** de Damodaran (NYU Stern, vigencia jun-2026). Es una **calibración estricta a la
metodología bottom-up de Damodaran** y a las condiciones de mercado vigentes, **independiente de su
efecto sobre el EVA**.

Origen del hallazgo: la verificación automática modelo-vs-fuente viva de la pestaña "Fuentes y
metodología" (ver `docs/hallazgo_beta_sector_20260616.md`) detectó que `beta_us = 1.29` estaba por
encima de **todos** los sectores de construcción que Damodaran publica hoy; el **D/E del sector del
modelo (21.56%) calza con Homebuilding (21.34%)**, confirmando que el sector de origen es Homebuilding,
cuya **beta apalancada hoy es 0.91** (no 1.29).

## 2. Inputs: viejo → nuevo (fuente · fecha)

| Input | Viejo | Nuevo | Fuente · fecha |
|---|---|---|---|
| `beta_us` (beta apalancada del sector) | 1.29 | **0.91** | Damodaran *Betas by Sector* / **Homebuilding**, jun-2026 |
| `de_us` (D/E del sector, desapalanca la beta) | 21.56% | **21.34%** | ídem (Homebuilding) |
| `tax_us` (tasa efectiva del sector) | 13.30% | **16.99%** | ídem (Homebuilding) |
| `rp` (riesgo país / CRP) | 3.43% | **3.43% (SIN CAMBIO)** | decisión del 14-jun (Colombia BB− de S&P, conservador) |

> **`rp` no se toca**: bajarlo a la calificación Baa3 de Damodaran (2.85%) sería otra decisión de comité.
> Se mantiene la postura conservadora aprobada. Método del WACC **intacto** (β de la deuda, EMBI/CRP,
> paridad de inflación USD→COP): se ajustan **inputs**, no la arquitectura.

## 3. Efecto (declaración transparente)

**WACC: 18.71% → 17.66% (−1.05 pp)** en los tres proyectos calibrados.

Una beta menor **reduce el WACC** y, en consecuencia, **mejora el EVA** (más valor creado). **El ajuste
se sostiene ÚNICAMENTE en método y fuente, no en el resultado deseado.** Esta franqueza es la protección
de gobierno corporativo: se documenta la dirección del efecto para que no quede duda de que la
recalibración responde al dato de mercado, no a la conveniencia del veredicto.

**Ningún proyecto cambia de veredicto** (genera↔destruye) — el efecto es solo de magnitud:

| Proyecto | Veredicto | `valor_creado` (viejo → nuevo) | `spread_valor` |
|---|---|---|---|
| Navarra | GENERA → GENERA | +13.9 → **+15.1** mil M | +18.88 → +19.94 pp |
| Dominica | GENERA → GENERA | +12.4 → +13.0 mil M | +37.84 → +38.89 pp |
| Torres | greenfield (sin veredicto) | −10.8 → −9.5 | — |
| Argos | **DESTRUYE → DESTRUYE** | −22.8 → −21.2 mil M | −10.80 → −9.74 pp |

## 4. Golden CORE — INTACTO (verificado por diff estricto)

Las cifras de **decisión NO cambian** (el WACC es de exhibición; las decisiones se descuentan @TIO 15%):
- **TIR proyecto** (Navarra REAL **37.60%**), **VPN@TIO** (**18.28 mil M**), flujo, recaudo y crédito:
  **idénticos** (diff < 1e-9).
- Verificación por `git diff` de los snapshots: **solo** se movieron `input_par.financiero.wacc.{beta_us,
  de_us, tax_us}`, `result.{flujo,apalancamiento}.wacc`, `result.flujo.vpn_proyecto` (VPN@WACC secundario)
  y las métricas EVA (`valor_creado`, `spread_valor`). **Cero cambios en cifras de decisión.**

## 5. Constancia técnica

- Cambio aplicado en los 7 JSON con bloque WACC (4 reales gitignored + 3 ilustrativos commiteados).
- Snapshots dorados regenerados (`engine/execution/snapshot_dorado.py`); el harness `engine/tests/` queda
  verde con el CORE intacto.
- Ancla del re-baseline: `engine/tests/test_finanzas.py::test_wacc_ancla_rebaseline_beta_homebuilding`
  (WACC ≈ 17.66%, beta 0.91, rp 3.43%).
- **Pendiente:** redeploy del API + refresco del escenario en Supabase para reflejar el nuevo WACC en
  producción (prod lee `scenarios.snapshot` congelado; ver `docs/runbook_sync_wacc_prod.md`).
