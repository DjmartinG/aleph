# engine — `aleph_engine`

Paquete Python **PURO** con TODA la lógica financiera de ALEPH. Sin imports de Streamlit / FastAPI / Supabase.
Modelos Pydantic. Tests obligatorios para toda función financiera (incluido el **snapshot dorado**).

> **Estado: ESQUELETO montado (PROMPT 2.3).** Hoy el paquete contiene SOLO:
> - `aleph_engine/models.py` — contrato de datos del proyecto/supuestos (Pydantic v2), portado desde
>   `app_streamlit/cg_engine/schema.py`.
> - `aleph_engine/config.py` — réplica exacta del ciclo de vida (`ESTADOS`) que el contrato valida.
> - `tests/` — harness que **lee el snapshot dorado** (desde `app_streamlit/tests/golden/`, fuente única):
>   - `test_models_contra_snapshots.py` — el contrato acepta la entrada real de los 3 proyectos (**activo hoy**).
>   - `test_golden_harness.py` — re-ejecuta `aleph_engine.calcular()` y exige paridad de cifras (tol. 0.1%).
>     Se **salta** hasta que la lógica se extraiga; se activa solo en **PROMPT 3**.
>
> La extracción `app_streamlit/cg_engine` → `aleph_engine` (calcular/pyg/flujo/WACC/curva S/indicadores/EVM)
> ocurre **TAL CUAL** en **PROMPT 3** — no se reescribe de memoria.
> Constitución §ALEPH en `../CLAUDE.md`; plan función-por-función en `../directives/plan_migracion.md` §3.2.

## Correr los tests

```bash
# desde la raíz del monorepo:
./test.sh                 # corre engine + app_streamlit
# o solo el engine:
cd engine && python -m pytest -q
```

Hoy: **6 passed** (contrato contra los snapshots) **+ 6 skipped** (harness dorado, espera a PROMPT 3).
En CI solo existen los 3 snapshots ilustrativos (los `*_REAL_*` son confidenciales/gitignored) → 3 + 3.
