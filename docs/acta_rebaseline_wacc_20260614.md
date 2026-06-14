# Acta de re-baseline — Recalibración del WACC (Damodaran) · 14-jun-2026

**Decisión:** recalibrar el costo de capital (WACC) del portafolio a la metodología Damodaran,
corrigiendo inputs mal calibrados que se compensaban. Aprobada por Martín (Dirección Financiera).
Soporte para comité: `Aleph - Factibilidad Financiera CG/CG-FIN-WACC-20260614.docx`.
Hallazgo previo (auditoría M1): **no había doble conteo de riesgo país**; el problema era de calibración.

## Inputs cambiados (bloque `financiero.wacc`, idéntico en los 3 proyectos)

| Input | Antes | Después | Fuente |
|---|---|---|---|
| `rf` (tasa libre de riesgo) | 0,12% | **4,30%** | T-bond US (a confirmar a la fecha) |
| `rm` (→ prima de mercado madura = rm−rf) | 12,44% (pm 12,32%) | **8,53% (pm 4,23%)** | Damodaran: ERP total CO 7,08% − CRP 2,85% |
| `rp` (riesgo país / CRP) | 3,14% | **2,85%** | Damodaran Country Risk Premium (Colombia) |

`kd_us` **no se tocó** (queda en el default 9,335%). **Nota técnica:** bajar `kd_us` NO baja el WACC
(como sugería el paréntesis del memo): por el mecanismo de beta de deuda con D/E=233%, lo **subiría**
a ~18,7%. Se deja como afinamiento futuro, documentado.

## Resultado

**WACC: 21,54% → 17,31%** (los 3 proyectos; mismo bloque de supuestos).

## Cifras que cambiaron (verificado por diff estricto, 6 snapshots)

Solo 6 campos por snapshot: `input_par.financiero.wacc.{rf,rm,rp}`, `result.flujo.wacc`,
`result.apalancamiento.wacc` y `result.flujo.vpn_proyecto` (VPN secundario descontado @WACC).

## Cifras INTACTAS (confirmado por el diff — NO cambiaron)

VPN @TIO (`apalancamiento.vpn_proyecto`, Navarra 18,28 mil M), TIR proyecto (37,60%), TIR socio
(41,72%), `vpn_socio`, flujo de caja, costos, recaudo, crédito, hitos — **todo lo demás idéntico**.
El WACC es indicador de exhibición; las decisiones se descuentan a la TIO (15%), no al WACC.

## Verificación

- Engine: 38 tests verdes (incluye harness dorado con snapshots regenerados).
- API: 56 verdes (`test_wacc_fiel_al_motor` actualizado a rango 0,17–0,18).
- Golden app_streamlit: 6 verdes.

## Archivos tocados

6 JSON de proyecto (`proyectos/*.json` + `proyectos_privados/*_REAL.json`, campo `financiero.wacc`),
6 snapshots regenerados (`tests/golden/*_snapshot.json`), `api/tests/test_api.py` (rango del WACC).

## Reversión (si el comité lo pide)

Volver `rf/rm/rp` a `0.12/12.44/3.14` en los 6 JSON y regenerar:
`cd app_streamlit && python execution/snapshot_dorado.py`. Reproducible al 100%.
