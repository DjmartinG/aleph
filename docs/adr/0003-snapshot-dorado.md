# ADR-0003 — Snapshot dorado como red de seguridad de la migración

**Estado:** Aceptado · 2026-06

## Contexto
La migración mueve y reorganiza la lógica financiera. El riesgo número uno es **cambiar una cifra
auditada sin darse cuenta** (TIR proyecto, VPN, crédito, flujo mensual…). Esas cifras gobiernan
decisiones de inversión reales; no pueden moverse "por accidente".

## Decisión
Antes de mover una sola línea del motor, **congelar** el resultado completo de `calcular()` (entrada +
salida: indicadores + flujo mensual + P&G + crédito) para los 3 proyectos reales en
`app_streamlit/tests/golden/*_snapshot.json`. Un **harness** re-ejecuta el motor sobre la entrada
congelada y compara TODA la salida con **tolerancia 0.1%**. Si cualquier cifra se mueve más de eso,
**rompe el build**. La migración no *valida* estas cifras: garantiza que **no cambien**.

Cifras ancla de Navarra (referencia): TIR proyecto 37.60% · VPN @TIO 18.3 mil M · TIR socio 41.72% ·
ventas 229.7 mil M · costo directo 143.5 mil M · exposición máx −71.0 mil M · crédito máx 49.3 mil M.

## Consecuencias
- (+) Convierte una refactorización riesgosa en una **segura y repetible**: cada paso se verifica.
- (+) Fuente única de cifras doradas; el harness del motor las **lee** desde un solo lugar (no se duplican).
- Los snapshots de proyectos **REALES** (`*_REAL_*`) son confidenciales (gitignored): corren en local;
  en CI corren los **ilustrativos** (regresión equivalente).
- Regla operativa: **el snapshot dorado es sagrado** — si se rompe, nada se mergea ni se despliega.
