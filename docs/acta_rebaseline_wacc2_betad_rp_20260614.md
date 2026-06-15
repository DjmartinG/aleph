# Acta de re-baseline — WACC: beta de deuda (BBB) + riesgo país (Colombia BB-) · 14-jun-2026

**Decisión:** dejar el WACC defendible corrigiendo la **beta de la deuda** (`kd_us`) y actualizando el
**riesgo país** (`rp`) a la calificación soberana actual de Colombia. **Aprobada EXPLÍCITAMENTE por
Martín (Dirección Financiera)** ANTES de aplicar, tras ver el antes/después y elegir el paquete
"beta_d BBB + rp a BB- → ~18,71%". Cierra el afinamiento que el acta de M1
(`acta_rebaseline_wacc_20260614.md`) dejó pendiente ("bajar kd_us… afinamiento futuro").

## El defecto (real)

El motor calcula la beta de la deuda con la fórmula de Damodaran `beta_d = (kd_us − rf) / prima_mercado`
(= *spread de default ÷ ERP*). Tras la recalibración M1 (rf 0,12→4,30; prima de mercado 12,32→4,23%), el
`kd_us` heredado de 9,335% quedó descalibrado: el spread implícito (9,335 − 4,30 = **5,04%**) corresponde
a una calificación **CCC / casi-quiebra**, dando **`beta_d = 1,19`** — indefendible (la deuda tendría más
riesgo sistemático que el mercado entero). No era doble conteo de riesgo país; era calibración de `kd_us`.

## El arreglo (dos correcciones, cada riesgo en su canal)

1. **`kd_us`: 9,335% → 5,90%** (en los 6 JSON de proyecto + default de `finanzas.calcular_wacc`).
   Ancla el spread del comparable a **BBB** (grado de inversión, 1,60%), coherente con una homebuilder
   US de bajo apalancamiento (D/E 21,6%). → **`beta_d = 0,38`** (beta de deuda IG, normal).
2. **`rp`: 2,85% → 3,43%** (en los 6 JSON). Refleja la rebaja de **Colombia a BB-** (S&P, foreign
   currency, 8-abr-2026; Fitch BB dic-2025). El riesgo SOBERANO vive en `rp` (se suma al Ke), **no** en
   `beta_d` — meterlo en `beta_d` lo contaría DOS veces. `3,43%` es el spread de default BB- bajo la
   misma convención con que M1 fijó BB→2,85%. **[VALIDAR]** con la fuente Damodaran exacta del comité
   (rango BB-: 3,3–3,6%); el valor es trivialmente ajustable y mueve el WACC ±0,08 pp.

## Resultado

**WACC: 17,31% → 18,71%** (los 3 proyectos; mismo bloque de supuestos). Sube porque la beta de deuda
inflada estaba absorbiendo riesgo que le pertenece al equity: `beta_l` pasa de 1,41 a **2,35** (beta de
equity apalancada plausible para un desarrollador con 70% deuda) y `beta_u` baja de 1,27 a **1,15**
(más cerca del sector Damodaran homebuilding ~0,9–1,1). El 17,31% estaba **subestimado**.

## Cifras que CAMBIAN (verificado por diff estricto, 7 snapshots)

Solo campos del bloque WACC: `input_par.financiero.wacc.{rp, kd_us}` (kd_us nuevo, rp 2,85→3,43),
`result.flujo.wacc`, `result.apalancamiento.wacc` (17,31→18,71%) y `result.flujo.vpn_proyecto` (VPN
secundario descontado @WACC, se mueve con la tasa).

## Cifras INTACTAS (confirmado por el diff — NO cambiaron)

VPN @TIO (`apalancamiento.vpn_proyecto`, Navarra **18.280.687,67** = 18,28 mil M), TIR proyecto
**37,60%**, TIR socio OFICIAL **41,72%** (FCL fiducia), `tir_equity`, `flujo_equity`, `aportes_total`,
flujo de caja, costos, recaudo, crédito máx (49,3 mil M), hitos, P&G — **todo idéntico**. El WACC es
indicador de EXHIBICIÓN; las decisiones se descuentan a la TIO (15%), no al WACC.

## Sincronización colateral (test_anclas de app_streamlit)

`app_streamlit/tests/test_anclas.py` tenía los `ap_tir_equity` de los proyectos NO-fiducia con valores
VIEJOS: el fix de flujo_equity (PR #22, `acta_flujo_equity_20260614.md`, aprobado) regeneró los
snapshots pero no sincronizó esta copia → el suite app_streamlit estaba ROJO en `main` desde PR #22.
Se sincronizaron a los snapshots COMMITEADOS (verificado por `git diff`: el WACC no toca `tir_equity`):
dominica REAL −0,502256→0,688779 · torres REAL None→−0,236457 · navarra ilus. −0,287159→−0,339514 ·
dominica ilus. 0,014209→0,284826 · torres ilus. −0,218692→−0,286135. **No es una cifra nueva**: son los
valores ya aprobados en PR #22. Navarra REAL (override fiducia 41,72%) no cambia.

## Verificación

- Engine: 66 tests verdes (harness dorado con 7 snapshots regenerados).
- API: 65 verdes (`test_wacc_fiel_al_motor` actualizado a rango 0,18–0,19).
- app_streamlit: 75 verdes (test_anclas sincronizado; decisión TIR 37,60% / VPN@TIO 18,28 mil M intactas).

## Follow-ups (NO en este PR)

- `app_streamlit/app.py:252`: el template de "nuevo proyecto" aún trae WACC pre-M1 (`rf:0.12`,
  `kd_us:9.335`). App congelada por constitución; proyectos nuevos se crean por `/web` (usa el default
  5,9). Stale conocido, sin cobertura de test. Corregir aparte si se decide.
- Confirmar `rp` con la fuente Damodaran oficial del comité (hoy [VALIDAR] en 3,43%).
- `result.flujo.vpn_proyecto` sale muy negativo pese a TIR>WACC (posible periodicidad mensual vs tasa
  anual en el VPN secundario del módulo flujo). Métrica secundaria, pre-existente; revisar aparte.

## Reversión (si el comité lo pide)

Volver `kd_us` a 9,335 (o quitar el campo) y `rp` a 2,85 en los 6 JSON, revertir el default de
`finanzas.py` y regenerar: `PYTHONPATH=engine python app_streamlit/execution/snapshot_dorado.py`.
Reproducible al 100%.
