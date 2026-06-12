# engine — `aleph_engine`

Paquete Python **PURO** con TODA la lógica financiera de ALEPH. Sin imports de Streamlit / FastAPI / Supabase.
Modelos Pydantic. Tests obligatorios para toda función financiera (incluido el **snapshot dorado**).

> **Estado: PROMPT 3 · bloque 1 — motor MOVIDO (harness dorado VERDE).**
> La lógica financiera se trajo **tal cual** desde `app_streamlit/cg_engine` (solo imports relativos; deps:
> scipy con fallback, dateutil, pydantic). Módulos: `config`, `errors`, `schema`, `finanzas`, `curvas`,
> `flujo`, `portafolio`, `ingresos`, `modelo` (orquestador `calcular`), `apalancamiento` (waterfall fiducia,
> cifras doradas) y `evm`. Versión **heredada 2.39.0**. Además: `metrics.py` (diccionario único de
> indicadores con **etiqueta de base**) y `checks.py` (checks de cuadre) — registro/reconciliación, sin cálculos nuevos.
>
> Tests (`tests/`, leen los snapshots desde `app_streamlit/tests/golden/`, fuente única):
> - `test_golden_harness.py` — re-ejecuta `aleph_engine.calcular()` y exige paridad de cifras (tol. 0.1%). **VERDE.**
> - `test_models_contra_snapshots.py` — el contrato (`schema.parse`) acepta la entrada real de los 3 proyectos.
>
> Hoy: **12 passed** (6 dorado + 6 contrato). En CI solo existen los 3 snapshots ilustrativos
> (los `*_REAL_*` son confidenciales/gitignored) → 6 passed.

## Estado de la migración del motor
- ✅ **Bloque 1** — motor movido a `aleph_engine`; harness dorado verde. `app_streamlit` sigue usando su
  `cg_engine` (INTACTO) → la app es idéntica y desplegable. Hay, temporalmente, **dos copias** del motor
  (guardadas por el dorado en ambos lados).
- ⏳ **Bloque 2** — repuntar `app_streamlit` para consumir `aleph_engine` (bundle en la imagen Docker +
  ajuste del deploy), y **eliminar la copia** `cg_engine`. Después: extraer los 7 puntos de `app.py`
  (§3.2 de `../directives/plan_migracion.md`) + `metrics.py` (indicadores con etiqueta de base) + `checks.py`.

## Correr los tests

```bash
# desde la raíz del monorepo:
./test.sh                 # engine + app_streamlit + ruff
# o solo el engine:
cd engine && python -m pytest -q
```
