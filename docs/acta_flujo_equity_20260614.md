# Acta de re-baseline — Fix del flujo de equity del socio (Nivel 2 #1) · 14-jun-2026

**Decisión:** corregir la construcción del `flujo_equity` (flujo de caja mensual del SOCIO apalancado)
en `apalancamiento.py`. **Aprobada EXPLÍCITAMENTE por Martín (Dirección Financiera)** ANTES de aplicar,
tras ver el antes/después y confirmar que las cifras de DECISIÓN no se mueven. Hallazgo de la auditoría
profunda (lente financiera, verificado adversarialmente).

## El defecto (real)

`flujo_equity[m]` se construía desde `operativo[m]` (= ingresos − costos), que **resta honorarios y
utilidad del lote como COSTO pero NUNCA los reincorpora al socio**, a diferencia de `retorno` (el flujo
del PROYECTO), que sí los reintegra (proporcional al recaudo). Consecuencia: `sum(flujo_equity)` de
Navarra era **−5.505 mil M** (negativo: el socio "nunca recupera su equity") → `irr` mensual = **−3,3%**,
frente a la TIR socio AUDITADA de **41,72%**.

En el camino FIDUCIA no afectaba las cifras de decisión (la TIR/VPN del socio se SOBRESCRIBEN con el FCL
auditado, `apalancamiento.py:190`). Pero la serie mensual rota viajaba a dos superficies de UI:
**el Monte Carlo "TIR socio"** (que hace `pop('fiducia')` → usa la serie mensual) y el **comparador de
vehículos** — mostrando un número absurdo (−3,3%).

## El fix

`flujo_equity[m] = retorno[m] + desembolso − amort − interes` (antes partía de `operativo[m]`). Es decir:
el flujo de equity apalancado = el RETORNO al socio (operativo + reintegros) + el crédito neto. Es la
definición correcta (equity apalancado = proyecto desapalancado + efecto del crédito).

## Cifras que CAMBIAN (verificado por diff estricto sobre los 7 snapshots)

Solo **3 campos** por snapshot, todos derivados del flujo de equity:
`apalancamiento.flujo_equity` (la serie), `apalancamiento.aportes_total` (= Σ flujos negativos del
socio) y `apalancamiento.tir_equity` (la TIR mensual CRUDA — en Navarra REAL ni eso, usa el override).

| Cifra | Antes | Después |
|---|---|---|
| `sum(flujo_equity)` Navarra | −5.505 mil M | **+31.083 mil M** |
| TIR socio MENSUAL (MC + vehículos) | −3,3% | **+14,36%** |
| TIR socio MENSUAL `sas_spv` | −6,1% | **+11,37%** |
| Golden de vehículos (`test_golden_vehiculos_navarra`) | −0,033042 / −0,061403 | **0,143556 / 0,113699** |

## Cifras INTACTAS (confirmado por el diff + `test_anclas` verde)

TIR proyecto **37,60%**, TIR socio OFICIAL **41,72%** (FCL fiducia auditado), VPN@TIO **18,28 mil M**,
flujo de caja del proyecto, recaudo, crédito, hitos, P&G, exposición máxima — **todo idéntico**. Las
decisiones de fiducia usan el FCL override, que el fix no toca.

## Matiz financiero (etiquetar en la UI)

El **14,36% mensual NO es el 41,72% oficial**: el modelo mensual recalculado es más CONSERVADOR que el
FCL anual auditado de la fiducia. El fix arregla que la TIR socio mensual sea **positiva y plausible**
(no que iguale al oficial; el Monte Carlo no puede usar el override). La gráfica MC "TIR socio" debe
seguir etiquetada como **"recálculo mensual, direccional"** (no la cifra oficial).

## Verificación

- Engine: 49 tests verdes (incl. harness dorado con snapshots regenerados + `test_anclas` intacto).
- 7 snapshots regenerados (`app_streamlit/execution/snapshot_dorado.py`); `test_golden_vehiculos_navarra`
  re-baselizado; `test_comparar_greenfield_no_crashea` ajustado (Torres ya no es degenerado en equity).
- Cifras de decisión confirmadas: TIR proyecto 37,60%, VPN@TIO 18,28 mil M, crédito máx 49,3 mil M.

## Reversión (si se requiere)

Volver `apalancamiento.py` a `flujo_equity[m] = operativo[m] + desembolso − amort − interes` y regenerar:
`PYTHONPATH=engine python app_streamlit/execution/snapshot_dorado.py`. Reproducible al 100%.

## Pendiente relacionado

Cablear el **test de gobernanza "diff dorado viejo-vs-nuevo"** que la spec exige (hoy ausente: la
verificación de re-baseline se hace ad-hoc). Es infra para el próximo re-baseline.
