# Plan de Migración ALEPH — PROMPT 1

> **Documento de arquitectura senior.** Entrega del PROMPT 1 de la migración ALEPH.
> Basado en auditoría del código real en `app_factibilidad/` (motor `cg_engine` v2.39.0, `app.py` monolito Streamlit, `storage.py` persistencia).
> Objetivo del PROMPT 1: dejar fotografiado el sistema actual (UI, cálculos, datos, persistencia) y trazar el plan de extracción a un monorepo `/engine /api /web /app_streamlit` **sin mover ninguna cifra dorada**.

---

## 0. Resumen ejecutivo (TL;DR)

- El **núcleo financiero ya está casi puro** en `cg_engine/` (finanzas, curvas, portafolio, ingresos, modelo, apalancamiento, evm). No está acoplado a Streamlit. Esta es la **mayor ventaja de la migración**: el grueso del trabajo de "extraer lógica de la UI" ya está hecho (refactor Fase 1, aprendizaje 2026-06-11).
- Existen **7 puntos de cálculo financiero todavía acoplados a `app.py`** que hay que extraer al engine antes de poder envolverlo en una API limpia.
- La **persistencia hoy** es una sola tabla plana `public.proyectos` (snapshot JSONB del `par`) con fallback a archivos locales "nunca se rompe".
- El destino es el modelo de la constitución ALEPH: `companies → projects(fase) → scenarios(draft/approved/baseline) → results_cache; actuals_*; audit_log`. El JSON actual entra **bit a bit** como `scenario v1 approved`.
- **Cifras doradas Navarra (test de aceptación de toda la migración):** TIR proyecto **37.60%**, VPN **18.3 mil M**, TIR socio **41.72%**, crédito máx **49.3 mil M**. Salen de `apalancamiento.flujo_apalancado` rama `fiducia_real=True`. Tolerancia de migración: **0.1%**.

---

## 1. Inventario de la UI Streamlit

Menú por áreas en `ui/nav.py:16-46`. El menú es **adaptativo al estado**: Seguimiento solo aparece en `construccion/entregado` (`nav.py:42`, `config.ESTADOS_CON_SEGUIMIENTO`); Administración solo si `PUEDE_INGRESAR` (`nav.py:44`). Wiring en `app.py:431-445`. Cálculo central: `R = calcular(copy.deepcopy(par))` en `app.py:469` es la **única** llamada al motor por render (`cg_engine/modelo.py:425`); casi todas las secciones consumen ese `R` precomputado.

| Sección | Área | Qué muestra | Funciones de motor que llama | ¿Edita? |
|---|---|---|---|---|
| **Inicio** | Tablero | Portada/bienvenida. Marca, propósito, 3 tarjetas "Cómo empezar" + 4 tarjetas de "Módulos del modelo". Sin KPIs ni gráficos. Única sección que NO renderiza el bloque de KPIs de cabecera ni el pie de exportar/guardar (`app.py:520`). | — (ninguna) | No |
| **Pipeline / Embudo** | Tablero | Vista de comité agrupada por estado del ciclo de vida. KPIs por estado, Funnel Plotly, tabla por proyecto. Itera todos vía `pipeline_datos()`. | `calcular`; `config` (`ESTADOS`, `ESTADO_LABEL`) — `app.py:561` | No |
| **Resumen ejecutivo** | Tablero | Cockpit por proyecto: 8 KPIs con semáforo, 2 gauges Plotly (TIR, margen), alertas de obra si hay monitor (Navarra). Distingue cifras auditadas fiducia vs modelo calibrado. | `calcular` — `app.py:591` | No |
| **Proyectos activos** | Tablero | Galería del portafolio: estado de obra Navarra, filtro por estado, tarjetas de proyecto, tabla consolidada con fila TOTAL. **Única sección con KPIs de cabecera CONSOLIDADOS** (`consolidado()`). "Abrir proyecto" cambia selección, no edita. | `calcular` — `app.py:482, 651` | No |
| **Portafolio (burbujas)** | Tablero | Mapa de valor: scatter de burbujas Plotly TIR vs margen, tamaño=ventas, color=tipo, cuadrantes. Usa `puntos_portafolio()`. | `calcular` — `app.py:629` | No |
| **Datos del proyecto** | Factibilidad | Solo lectura: 4 metrics + tabla urbanística (`R['urbanistico']`). La edición vive en Ingreso de datos. | `calcular` — `app.py:724` (`_sec_urbanistico:712`) | No |
| **Cronograma** | Factibilidad | 2 tabs. Cronograma: hitos por etapa, Gantt Plotly, ritmo, absorción. Ingresos: recaudo apilado (sep/CI/subrogación) + KPIs. Lee `R['hitos']`, `R['recaudo']`. | `calcular` — `app.py:1285` (`_sec_cronograma:1207`, `_sec_ingresos:1270`) | No |
| **Distribución costos** | Factibilidad | Solo lectura: presupuesto directo por capítulo (bottom-up o % ventas), indirectos, curva S de obra. Edición en Ingreso de datos (4c). | `calcular` — `app.py:982` | No |
| **P&G** | Factibilidad | Estado de resultados con % sobre ventas, 4 KPIs, memo de financieros/impuestos, dona reparto CG/socio. Lee `R['pyg']`, `R['apalancamiento']`. | `calcular` — `app.py:946` | No |
| **Costo de capital** | Factibilidad | WACC en solo lectura: build-up CAPM completo. Llama `calcular_wacc(detalle=True)` sobre `par['financiero']['wacc']`. | `calcular_wacc` (`modelo` re-export de `finanzas.calcular_wacc`), `calcular` — `app.py:1079-1092` | No |
| **Flujo de caja** | Factibilidad | 2 tabs (FC Proyecto sin financiación / FC Inversionista apalancado): waterfall Plotly + 4 KPIs cada uno. Toggle "solo caja futura". Fallback a flujo simple. Lee `R['apalancamiento']`, `R['hitos']`. | `calcular` — `app.py:1027` | No |
| **Apalancamiento** | Factibilidad | Crédito constructor + waterfall fiducia. Flujo operativo anual, KPIs auditados + tabla FCL anual si `fiducia_real`; KPIs del modelo si no. Lee `R['apalancamiento']`, `R['hitos']`. | `calcular` — `app.py:1123` | No |
| **Riesgo y sensibilidad** | Factibilidad | 4 tabs. Escenarios (barras), Sensibilidad 2D (heatmap celda a celda con `_correr`), Tornado (`R['sensibilidades']`), Monte Carlo (TIR/VPN/socio vía `montecarlo_tir` cacheado). | `calcular`; `modelo._correr` (`app.py:1402`); `modelo.montecarlo_tir` (`app.py:1316`) — sección `app.py:1389` | No |
| **Monitor de ejecución** | Seguimiento | Seguimiento por torre (datos comité Navarra). Solo `construccion/entregado` y con monitor. 4 tabs: avance, ejecución presupuestal, crédito, variaciones. **NO usa `cg_engine`**: consume `navarra_data` estático. | — (ninguna del núcleo financiero) — `app.py:1419` | No |
| **Valor Ganado** | Seguimiento | EVM: KPIs avance/CPI/SPI/EAC con semáforo, curva S de VG, KPIs PV/EV/AC/BAC. Requiere % avance real y costo real por etapa. | `calcular`; `evm.calcular_evm`; `evm.estado_en_palabras` — `app.py:1176-1196` | No |
| **Ingreso de datos** | Administración | **ÚNICO punto de captura** (`PUEDE_INGRESAR`). Expanders 1-7: generales+ESTADO, áreas/lote, etapas/producto/ventas+EVM, tipologías, costos, gastos fijos, presupuesto por capítulo, recaudo, financiero, WACC. Escribe en `st.session_state.par`. Guardado real en el pie común (Supabase) validando `schema.parse`. | `calcular`; `schema.parse` — `app.py:735-943` (editores `_editor_presupuesto:323`, `_editor_wacc:367`) | **Sí** |

**Pie común** (todas menos Inicio, `app.py:1523-1583`): export Excel + JSON (`download_button`) y botón "Crear/Guardar en la nube" → `schema.parse` (`1551`) → `slugify` → `guardar()`, solo si `PUEDE_INGRESAR` y `usando_supabase()`.

> **Nota ALEPH:** "Monitor de ejecución" NO toca `cg_engine` (consume `navarra_data`, datos de comité estáticos). Su lógica **no debe migrar al `aleph_engine`** sino a una **capa de datos operativos separada** (futuras tablas `actuals_*`).

---

## 2. Mapa de cálculos financieros

### 2.1 Núcleo puro en `cg_engine/` (no acoplado a UI)

| Bloque | `archivo:función` | ¿Acoplado UI? | Depende de |
|---|---|---|---|
| WACC (build-up CAPM) | `cg_engine/finanzas.py:calcular_wacc` | No | config |
| VPN | `cg_engine/finanzas.py:vpn` | No | — |
| TIR por periodo (brentq+scipy) | `cg_engine/finanzas.py:irr_periodo` | No | vpn |
| TIR anualización mensual→anual | `cg_engine/finanzas.py:irr_anual` | No | irr_periodo |
| TIR bisección (serie anual auditada fiducia) | `cg_engine/finanzas.py:irr_biseccion` | No | vpn |
| Curvas S: PERT/Normal/Triangular/Lineal/Gauss | `cg_engine/curvas.py:pert/normal/triangular/lineal/gauss` | No | — |
| Curva S: distribuir (total→serie) | `cg_engine/curvas.py:distribuir` | No | pert/gauss/normal/triangular/lineal |
| Escalado materiales–mano de obra | `cg_engine/curvas.py:escalar_mat_mo` | No | — |
| Calendario: EOMONTH, ritmo, hitos venta, portafolio multi-etapa | `cg_engine/portafolio.py:eomonth/generar_ritmo/hitos_ventas/calcular_portafolio` | No | config |
| Recaudo etapa / portafolio (sep/CI/subrogación) | `cg_engine/ingresos.py:recaudo_etapa/recaudo_portafolio` | No | portafolio, config |
| Helpers de flujo | `cg_engine/flujo.py:aplicar_gastos_fijos/acumular` | No | — |
| Costos: directos/indirectos/gastos fijos totales | `cg_engine/modelo.py:directos_total/indirectos_total/gastos_fijos_total` | No | — |
| P&G (UO, margen, renta, UDI, reparto CG/socio) | `cg_engine/modelo.py:pyg` | No | costos, config |
| Distribución de costos directos (curva+escalado) | `cg_engine/modelo.py:distribucion_costos` | No | curvas |
| Flujo de caja simple (PERT, crédito simple) | `cg_engine/modelo.py:flujo_caja` | No | pyg, curvas, flujo, WACC, irr_periodo, config |
| **Flujo apalancado / waterfall fiducia** (crédito constructor, subrogación, TIR/VPN proyecto+equity, FCL auditado) | `cg_engine/apalancamiento.py:flujo_apalancado` | No | recaudo, portafolio, pyg, curvas, finanzas, flujo, config |
| Wrappers hitos/recaudo | `cg_engine/modelo.py:_hitos/_recaudo` | No | portafolio / ingresos, config |
| Motor de un escenario | `cg_engine/modelo.py:_correr` | No | pyg |
| Escenarios (Base/Opt/Pes) | `cg_engine/modelo.py:escenarios` | No | _correr |
| Sensibilidades (Δ UO ±precio/costo) | `cg_engine/modelo.py:sensibilidades` | No | _correr, pyg |
| Percentil | `cg_engine/modelo.py:_percentil` | No | — |
| Monte Carlo del margen | `cg_engine/modelo.py:montecarlo` | No | _correr, _percentil |
| **Monte Carlo TIR/VPN** (recalcula hitos→recaudo→apalancado; ignora override fiducia) | `cg_engine/modelo.py:montecarlo_tir` | No | pyg, _hitos, _recaudo, flujo_apalancado, _percentil, normalizar_tipologias, config |
| Tipologías (ventas $/und o $/m²; regla VIS comunales) | `cg_engine/modelo.py:_ventas_tipologia/normalizar_tipologias` | No | — |
| Urbanístico | `cg_engine/modelo.py:_urbanistico` | No | pyg |
| **Orquestador** `calcular` | `cg_engine/modelo.py:calcular` | No | todos los anteriores |
| EVM (BAC/PV/EV/AC, CPI/SPI, EAC/VAC) + estado en palabras + curva PV | `cg_engine/evm.py:calcular_evm/_curva_planeada/estado_en_palabras` | No | `calcular`, config |

### 2.2 Cálculo financiero ACOPLADO a `app.py` (deuda técnica a extraer)

| Bloque | `archivo:función` (línea) | ¿Acoplado UI? | Depende de | Acción ALEPH |
|---|---|---|---|---|
| TIR anual **DUPLICADA** (bisección propia, para TIR equity del consolidado) | `app.py:_irr_anual` (l.184) | **Sí** | vpn | **Borrar** → usar `finanzas.irr_anual`/`irr_biseccion` |
| Consolidación de portafolio (suma operativo/equity/saldo en eje global epoch-2022; VPN suma; TIR ref ponderada por ventas; TIR equity vía `_irr_anual`; crédito máx pico) | `app.py:consolidado` (l.203-237) | **Sí** | `calcular`, `flujo_apalancado`, `_irr_anual` | Mover a `engine` (`portafolio.consolidar` / `aleph_engine.portfolio`) |
| Puntos de burbujas (TIR vs margen por proyecto, fallback TIR ref) | `app.py:puntos_portafolio` (l.239-255) | **Sí** | `calcular` | Mover a `engine` |
| Datos de pipeline/embudo (estado + TIR/VPN/ventas/und) | `app.py:pipeline_datos` (l.257-276) | **Sí** | `calcular`, config | Mover a `engine` |
| Merge de KPIs de decisión (el waterfall apalancado pisa `credito_max/VPN/intereses/TIR equity` del `flujo_caja` legacy) | `app.py:469-478` | **Sí** | `calcular`, `flujo_apalancado` | Mover la **regla de negocio** al engine (o consolidar dentro de `calcular`) |
| Heatmap 2D de margen (matriz `_correr` por celda precio×costo) | `app.py:1397-1403` | **Sí** | `_correr` | Mover a `modelo.heatmap_sensibilidad` (o reusar `montecarlo`) |
| EVM real Navarra **DUPLICADO** (BAC/AC/EAC/EV/CPI/VAC re-implementado sobre `NAVARRA_PRESUPUESTO_T1`, **ignora `cg_engine.evm`**) | `app.py:1456-1460` | **Sí** | `navarra_data.avance_ultimo` | Reconciliar: reusar `cg_engine.evm` sobre los datos de partidas |

### 2.3 Capa de datos operativos (NO núcleo financiero)

| Bloque | `archivo:función` | Destino ALEPH |
|---|---|---|
| Avance real último Navarra (% ejecutado, % bancolombia) | `navarra_data.py:avance_ultimo` | `app_streamlit` / tabla `actuals_*` (no al `aleph_engine`) |
| Días en trámite crédito T2 (`date.today - inicio`) | `navarra_data.py:dias_tramite_t2` | `app_streamlit` / capa operativa |

**Conclusión de altitud (cuánto ya está puro):** el **~90% del cálculo financiero ya vive desacoplado** en `cg_engine/` (todo §2.1, exportado vía `cg_engine/__init__.py`, versión única **2.39.0**). Solo restan **7 puntos en `app.py`** (§2.2) y la capa operativa `navarra_data` (§2.3). De los 7, dos son **duplicaciones a borrar** (`_irr_anual` ya existe en `finanzas`; el EVM real de Navarra debe reusar `cg_engine.evm`). Esto convierte la extracción a `aleph_engine` en un trabajo **acotado y de bajo riesgo**, no en una reescritura.

> **Reglas de dominio que NO se tocan** (aprendizajes 2026-06-11): (1) NO fusionar `flujo_caja` (PERT, vista simple) con `flujo_apalancado` (Gauss, waterfall auditado) — son modelos intencionalmente distintos (ver `flujo.py` docstring). (2) `FECHA_CORTE_EVM = 2026-05-01` es el corte de datos de comité, **NO** `date.today()`. (3) `montecarlo_tir` borra `par['fiducia']` a propósito para que la TIR responda a las variables. (4) El "lote breakeven / precio máx pagable" de `NORTE_TABLEROS.md` **no está implementado** — será nuevo en el engine.

---

## 3. Estructura del monorepo y plan de extracción

### 3.1 Árbol destino

```
aleph/
├── engine/                     # aleph_engine — renombrado de cg_engine, puro, SIN Streamlit
│   ├── aleph_engine/
│   │   ├── __init__.py         # __version__ (heredado: 2.39.0 → ENGINE_V) + re-exports
│   │   ├── config.py           # constantes, ESTADOS, umbrales, FECHA_CORTE_EVM (sin tocar)
│   │   ├── errors.py
│   │   ├── schema.py           # Pydantic v2, contrato del par (sin tocar)
│   │   ├── finanzas.py         # VPN, irr_periodo, irr_anual, irr_biseccion, calcular_wacc
│   │   ├── curvas.py           # PERT/Normal/Triangular/Lineal/Gauss, distribuir, escalar_mat_mo
│   │   ├── flujo.py            # aplicar_gastos_fijos, acumular
│   │   ├── portafolio.py       # eomonth, generar_ritmo, hitos_ventas, calcular_portafolio
│   │   │                       #   + NUEVO: consolidar() (extraído de app.consolidado)
│   │   ├── ingresos.py         # recaudo_etapa, recaudo_portafolio
│   │   ├── modelo.py           # pyg, costos, flujo_caja, escenarios, sensibilidades,
│   │   │                       #   montecarlo, montecarlo_tir, calcular, urbanístico
│   │   │                       #   + NUEVO: heatmap_sensibilidad(), puntos_portafolio(),
│   │   │                       #     pipeline_datos() (extraídos de app.py)
│   │   ├── apalancamiento.py   # flujo_apalancado (waterfall fiducia, cifras doradas)
│   │   └── evm.py              # calcular_evm, _curva_planeada, estado_en_palabras
│   ├── tests/                  # test_anclas.py (cifras doradas), test_finanzas, test_schema…
│   └── pyproject.toml          # paquete instalable, version dynamic = aleph_engine.__version__
│
├── api/                        # FastAPI — envuelve aleph_engine, sin reimplementar fórmulas
│   ├── app/
│   │   ├── main.py             # routers + CORS
│   │   ├── routers/            # portfolio, projects, scenarios
│   │   ├── deps.py             # storage facade (Supabase), cache de calcular()
│   │   ├── cache.py            # results_cache: hash(snapshot)+ENGINE_V
│   │   └── schemas_io.py       # modelos de respuesta (DTOs de §5)
│   └── tests/                  # tests de contrato (TIR/VPN dorados desde HTTP)
│
├── web/                        # front nuevo (SPA) — consume /api, pinta badges base_label
│   └── ...
│
└── app_streamlit/              # la app actual, replanteada como cliente del engine/api
    ├── app.py                  # UI; importa aleph_engine (no fórmulas inline)
    ├── ui/                     # nav.py, auth.py, format.py
    ├── charts.py
    ├── navarra_data.py         # capa operativa (datos comité) — NO al engine
    └── storage.py              # fachada compat → scenarios approved/baseline
```

### 3.2 Plan de extracción función por función, ORDENADO por dependencias (insumo PROMPT 3)

Cada paso es atómico, verificado contra `test_anclas` + `ruff` + `compileall`; se revierte si una cifra se mueve.

1. **`config.py`** — constantes (horizontes, `PCT_CI`, `SEP_UND_MILES`, `DIFERIDO_SEP`, `TASA_CREDITO_EA`, `COBERTURA_CC`, `TIO`, `RENTA`, `SPLIT_CG`, `FECHA_CORTE_EVM`, `ESTADOS`, umbrales). Sin dependencias, base de todo.
2. **`errors.py` + `schema.py`** — validación Pydantic en el borde. Independientes del cálculo.
3. **`finanzas.py`** — `vpn → irr_periodo → irr_anual`; `irr_biseccion`; `calcular_wacc`. Base matemática, **no importa otros módulos del motor** (rompe el ciclo).
4. **`curvas.py`** — `pert/normal/triangular/lineal/gauss → distribuir`; `escalar_mat_mo`. Solo `math`.
5. **`flujo.py`** — `aplicar_gastos_fijos`, `acumular`. Helpers compartidos, sin deps de cálculo.
6. **`portafolio.py`** — `eomonth`, `generar_ritmo`, `hitos_ventas`, `calcular_portafolio`. Depende de config.
7. **`ingresos.py`** — `recaudo_etapa`, `recaudo_portafolio`. Depende de portafolio + config.
8. **`modelo.py` costos/P&G** — `directos_total`, `indirectos_total`, `gastos_fijos_total`, `pyg`, `distribucion_costos`. Depende de curvas + flujo + config.
9. **`apalancamiento.py`** — `flujo_apalancado` (crédito/waterfall/TIR-VPN proyecto+equity/FCL fiducia). Depende de recaudo + hitos + P&G + curvas + finanzas + flujo + config. **Productor de cifras doradas.**
10. **`modelo.py` flujos/indicadores** — `flujo_caja`, `_hitos`, `_recaudo`, `_urbanistico`, tipologías. Depende de P&G + curvas + portafolio + ingresos + apalancamiento + finanzas.
11. **`modelo.py` orquestador** — `calcular` + `escenarios`/`sensibilidades`/`montecarlo`/`montecarlo_tir` + `_correr`/`_percentil`. Capa superior.
12. **`evm.py`** — `calcular_evm`, `_curva_planeada`, `estado_en_palabras`. Depende de `modelo.calcular` + config.
13. **DESACOPLAR de `app.py` al engine:**
    - `app.py:_irr_anual` → **borrar**, usar `finanzas.irr_anual`/`irr_biseccion`.
    - `app.py:consolidado` → `portafolio.consolidar` (consolidación en eje global epoch-2022).
    - `app.py:puntos_portafolio` → `modelo.puntos_portafolio`.
    - `app.py:pipeline_datos` → `modelo.pipeline_datos`.
    - Merge de KPIs `app.py:469-478` → regla dentro de `calcular`/`apalancamiento`.
    - Heatmap 2D `app.py:1397-1403` → `modelo.heatmap_sensibilidad`.
    - EVM real Navarra `app.py:1456-1460` → reusar `cg_engine.evm` sobre las partidas.
14. **`navarra_data.py`** (datos operativos + `avance_ultimo` + `dias_tramite_t2`) → va a `app_streamlit` / capa de datos operativos, **NO al `aleph_engine`**.

---

## 4. Datos

### 4.1 Contrato actual del JSON `par` (`cg_engine/schema.py` + `proyectos/1_navarra.json`)

El `par` es un dict **heterogéneo y evolutivo**, validado en el borde por Pydantic v2 con `model_config extra="allow"`: solo se exige lo estructural; el resto es opcional con defaults en `config.py`. **El motor NO usa el modelo**: tras `schema.parse(d)` se pasa el **mismo dict** a `calcular(d)` (`schema.py:111-117`; `modelo.py:425`).

**Campos del modelo `Proyecto` (`schema.py:98-108`):**
- `etapas: list[Etapa]` (min_length=1, **OBLIGATORIO**). Cada `Etapa` (`schema.py:85-95`): `cod`, `und`, `vmes`, `frec`, `pe_pct`, `sucesora` (cod de la predecesora; `null` en la raíz), `fecha_inicio` ISO. Extra consumido por el motor: `nom`, `metodo`, `precio`, `area_und`, `ventas_miles`, `emes`, `efrec`, `desfase`, `obra_offset`, `dur_obra`, `escrituracion`, `ic_offset`.
- `costos_pct` (**OBLIGATORIO**): `directos`, `indirectos`, `honorarios`, `util_lote`; extra: `recon_codensa`, `hon_construccion`, `hon_gerencia`, `hon_ventas`.
- `financiero` (**OBLIGATORIO**): contiene `wacc` (build-up CAPM, todos opcionales); extra: `renta`, `split_cg`, `pct_ci`, `sep_und_miles`, `tasa_credito_ea`, `cobertura_cc`, `tio`, `tir_apalancada_ref`, `diferido_sep`, `monto_cc_pct`.
- `lote_bruto_miles: float` (**OBLIGATORIO**).
- `meta` (opcional): `nombre`, `tipo` (VIS|VIP|No VIS), `unidades`, `estado` (validado contra `config.ESTADOS`, rechaza mal escritos); extra: `ubicacion`, `zona`, `moneda`.
- `schema_version: int = 1` (default; **HOY no se persiste** — ver riesgos).
- Extra a nivel raíz (no en el modelo, sí en el motor): `areas`, `cronograma`, `tipologias`, `directos_cap`, `indirectos_cap`, `gastos_fijos`, `fiducia`, `ventas_miles` (override), `_nota`.

**Salida de `calcular(par)` (`modelo.py:434-445`):** dict `R` con `meta, pyg, distribucion, flujo, escenarios, sensibilidades, urbanistico, hitos, recaudo, apalancamiento`. Este último trae las **cifras doradas** de Navarra.

### 4.2 Persistencia hoy (`storage.py` + `app.py`)

**Dos modos con fallback "nunca se rompe"** (`storage.py:1-12`):
- Si hay `SUPABASE_URL` + `SUPABASE_KEY` en secrets/env → lee/escribe en BD compartida.
- Si NO → archivos JSON locales: `proyectos_privados/` (`PRIV_DIR`, reales gitignored) con **prioridad** sobre `proyectos/` (`PROY_DIR`, ilustrativos públicos). Convención `1_navarra_REAL.json` oculta el público `1_navarra` (`storage.py:124-128`).
- Ante **cualquier** excepción de red en lecturas, cae al respaldo local (`except: pass` en `listar/cargar/es_real`, `storage.py:137-138,149-150,164-165`).

**Tabla `public.proyectos` — UNA SOLA TABLA, esquema plano** (`storage.py:10`):
- `slug` (PK), generado por `slugify()` (`storage.py:21-28`).
- `nombre` (texto), default = `data.meta.nombre` o slug.
- `es_real` (bool): separa real (privado) vs ilustrativo; gobierna el badge `🔒` (`app.py:502,709`).
- `data` (jsonb): el dict `par` COMPLETO embebido (snapshot del proyecto entero) — el contrato sin normalizar.
- `updated_by` (texto).
- `updated_at`: mencionado en el docstring pero **NO lo escribe el código** (lo pondría un default/trigger en BD).

**API** (`storage.py`): `listar()` → `[slug]`; `cargar(slug)` → `data jsonb`; `es_real(slug)` → bool; `guardar(slug, data, nombre, es_real_flag, by)` → **UPSERT** por slug (pisa la fila, sin historial); `usando_supabase()`, `diagnostico()`, `probar_conexion()`.

**Flujo de guardado** (`app.py:1543-1577`): solo `PUEDE_INGRESAR` y `usando_supabase()`; valida `schema.parse(par)` en el borde (si falla NO persiste, `app.py:1550-1553`); proyecto nuevo genera slug único; luego `guardar()` hace el upsert.

**`meta.estado` (ciclo de vida, `config.py:31-47`):** eje rector de la UI (no afecta cálculo). 4 estados: `prefactibilidad → aprobado → construccion → entregado`. `ESTADO_DEFAULT='construccion'`; `ESTADOS_CON_SEGUIMIENTO=(construccion, entregado)`. Umbrales del gate (provisionales, `config.py:52-54`): `UMBRAL_TIR_EQUITY 0.18`, `UMBRAL_VPN_MIN 0.0`, `UMBRAL_MARGEN_MIN 0.08`. **HOY el estado vive DENTRO de `data.jsonb` (meta.estado)**, no como columna.

### 4.3 Plan de migración de datos al modelo de la constitución

> **Nota:** el esquema LIVE de Supabase se confirma con `list_tables` en el **PROMPT 4**. Aquí se documenta lo conocido por `storage.py`.

**Principio rector:** el snapshot JSONB del `par` se preserva **bit a bit** como `scenario v1 approved`; ninguna cifra dorada se mueve. La tabla `proyectos` plana se conserva (read-only/deprecada) hasta validar.

**Modelo destino (tablas Supabase nuevas):**
1. `companies(id uuid PK, nombre, slug, created_at)`. **Seed:** una fila "CG Constructora".
2. `projects(id uuid PK, company_id FK, slug UNIQUE, nombre, es_real bool, fase text CHECK IN config.ESTADOS, created_at, updated_at, updated_by)`. La `fase` **sale de `meta.estado`** (hoy embebido) y se **promueve a columna de primera clase** (eje rector de la UI). Mapea 1:1 con la fila vieja.
3. `scenarios(id uuid PK, project_id FK, version int, status text CHECK IN ('draft','approved','baseline'), snapshot jsonb NOT NULL, label, created_at, created_by, UNIQUE(project_id,version))`. `snapshot` = el dict `par` COMPLETO sin tocar (mismo contrato de `schema.py`). Sugerencia: **partial unique** para garantizar a lo sumo un `baseline` activo por project.
4. `results_cache(id PK, scenario_id FK UNIQUE, engine_version text, inputs_hash text, results jsonb, computed_at)`. Guarda la salida de `calcular(par)`. **Clave de invalidación:** `hash(snapshot) + aleph_engine.__version__ (ENGINE_V)`. Es **caché derivada**: se puede borrar y recomputar; la fuente de verdad es el snapshot.
5. `actuals_*` (datos ex-post, **solo fases con seguimiento**, `config.py:47`): `actuals_evm(project_id, fecha_corte, pv, ev, ac, spi, cpi, fuente)` y `actuals_ventas/recaudo(project_id, periodo, und, valor)`. La `fecha_corte` **NO es hoy**: es `config.FECHA_CORTE_EVM=2026-05-01`.
6. `audit_log(id PK, entity_type, entity_id uuid, action, actor, diff jsonb, at timestamptz)`. Reemplaza el `updated_by/updated_at` plano por traza completa.

**Pasos de ejecución (idempotentes, reversibles):**
- **P0. Golden tests primero.** Clavar las cifras de los 3 proyectos (`tests/test_anclas.py` ya existe) ANTES de migrar; la migración no debe mover ninguna ancla.
- **P1.** Crear tablas nuevas (`apply_migration`) SIN tocar `proyectos`. Seed company "CG Constructora".
- **P2. ETL de importación** (script determinista en `execution/`): por cada fila de `proyectos` (o cada JSON local vía `storage.listar()/cargar()`) → INSERT `projects` (slug, nombre, es_real, `fase = data.meta.estado` o `config.ESTADO_DEFAULT`) → INSERT `scenarios(version=1, status='approved', snapshot=data tal cual, created_by=updated_by)`. Validar cada snapshot con `schema.parse()` (no persistir lo inválido). Reales: **Navarra/Dominica → `construccion`; Torres de Campiñas → `aprobado`** (aprendizaje 2026-06-11).
- **P3. Backfill `schema_version`.** El JSON actual no trae `schema_version`; estampar `schema_version=1` en el snapshot importado para versionar el contrato hacia adelante.
- **P4. Precomputar `results_cache`** corriendo `calcular(par)` sobre cada scenario v1; comparar TIR/VPN/crédito contra las cifras doradas (**gate de aceptación de la migración**, tolerancia 0.1%).
- **P5. Adaptar `storage.py` a fachada compat:** `cargar(slug)` → snapshot del scenario `approved`/`baseline` activo; `guardar(slug,data,...)` → **nuevo scenario `draft`** (no pisa el approved) + `audit_log`; `es_real`/`listar` leen `projects`. Mantener firmas para no tocar `app.py` masivamente.
- **P6. Backfill `audit_log`** con un evento `import_v1` por scenario. Dejar `proyectos` read-only de respaldo; eliminar tras validación.

---

## 5. Contrato inicial de la API de lectura (FastAPI sobre `aleph_engine`)

`{id}` de proyecto = `slug` de storage. `{id}` de escenario en v1 = `{slug}:base|optimista|pesimista` (hoy no hay tabla de escenarios; son derivados deterministas del `par`). Los GET son **lecturas baratas cacheables**; el único cálculo intensivo es `POST .../run`.

| Método | Ruta | Propósito | Response (claves principales) |
|---|---|---|---|
| GET | `/v1/portfolio` | Consolidado + pipeline/embudo (= `consolidado()` + `pipeline_datos()`). Filtro `?estado=`. | `{ consolidado:{n,unidades,ventas,util_oper,udi,margen,vpn,tir_ref,tir_eq,credito_max}, embudo:[{estado,label,count}…], items:[{slug,nombre,estado,estado_label,ubicacion,tipo,es_real,tir,tir_label('auditado'|'apalancada_ref'),vpn,ventas,und}] }` |
| GET | `/v1/projects/{id}` | Ficha: metadatos + estado + `par` + urbanístico + KPIs cabecera + secciones aplicables según estado (`ui.nav.grupos`). | `{ id, es_real, fuente('supabase'|'local'), meta, estado, estado_label, estado_color, secciones_aplicables[], urbanistico{…}, kpis_cabecera{ventas,util_oper,udi,margen_oper,tir,tir_label,vpn}, params:par }` |
| GET | `/v1/projects/{id}/scenarios` | Lista escenarios: `base` (par guardado) + `optimista`/`pesimista` (deltas fijos de `escenarios()`). | `{ project_id, scenarios:[{id:'base',tipo:'guardado',d_precio:0,d_costo:0,es_base:true},{id:'optimista',d_precio:+0.05,d_costo:-0.02},{id:'pesimista',d_precio:-0.10,d_costo:+0.05}], default:'base' }` |
| GET | `/v1/scenarios/{id}/results` | **Payload central**: indicadores con etiqueta de base (auditado/fiducia vs modelo), P&G, flujo (apalancado+simple), crédito, checks de conciliación. | `{ scenario_id, project_id, es_base, base_label('auditado_fiducia'|'modelo_aprobado'|'preliminar'), indicadores{tir_proyecto,tir_proyecto_label,vpn_proyecto,tio,tir_equity,tir_apalancada_ref,wacc,payback_mes,credito_max,credito_prom,intereses_total,max_necesidad_caja,valor_financiable,margen_oper,fiducia_real}, pyg{…}, flujo{apalancado:R['apalancamiento'],simple:R['flujo']}, credito{…}, distribucion{…}, checks:[{nombre,ok,valor,esperado}] }` |
| GET | `/v1/scenarios/{id}/sensitivity` | Sensibilidad determinista (sin Monte Carlo): tornado, escenarios, matriz 2D precio×costo. Barata/cacheable. | `{ scenario_id, escenarios{Base,Optimista,Pesimista}, tornado{base_util_oper,items[…]}, matriz_2d{pasos_precio:[-10,-5,0,5,10],pasos_costo:[…],margen_pct:[[5x5]]} }` |
| **POST** | `/v1/scenarios/{id}/run` | **Único cálculo intensivo**: Monte Carlo TIR/VPN (`montecarlo_tir`) o margen (`montecarlo`). Idempotente por `(par,n,rangos,seed)` → cacheable. No muta el `par`. | **req:** `{tipo:'tir'|'margen',n,rango_precio,rango_costo,rango_ventas,seed,escrituracion_sigue_obra}`. **res tir:** `{tir_proyecto[],tir_equity[],vpn_proyecto[],stats_tir{p10,p50,p90,media,std,n},stats_equity,stats_vpn,hurdle(=TIO),prob_tir_hurdle,prob_vpn_pos,n_validas,usa_tir_modelo:true}` |

**Etiqueta de base (`base_label`):** el motor NO devuelve etiqueta literal; la deriva de `apalancamiento['fiducia_real']` (bool). `True` ⇒ `auditado · fiducia` (TIR/VPN sobre FCL real, cifra fija); `False` ⇒ `modelo_aprobado` (TIR apalancada ref) / `preliminar` (VPN @WACC). Patrón en `app.py:509-516, 1046-1064, 1135-1140`. La API debe exponer `base_label` + `fiducia_real` + flag por indicador para que `/web` pinte el badge correcto.

**Test de contrato (cifras doradas, deben salir de `R['apalancamiento']` con `fiducia_real=True`):** TIR proyecto **37.60%**, VPN **18.3 mil M**, TIR socio **41.72%**, crédito máx **49.3 mil M**.

---

## 6. Riesgos y mitigaciones

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | **Greenfield / TIR −99%.** Proyectos sin obra (prefactibilidad) o con flujos degenerados pueden producir una TIR sin sentido (p. ej. −99%) que ensucie KPIs y rankings. | Flag **`is_greenfield`** en el resultado + **etiqueta "— greenfield"** en la UI/API; excluir esa TIR del consolidado ponderado y del semáforo; no aplicar el gate de aprobación a esos casos. |
| 2 | **Tolerancia de las cifras doradas.** Cualquier refactor o recompute podría mover una cifra auditada. | **Tolerancia dorada 0.1%**: `test_anclas` clava TIR/VPN/crédito de los 3 proyectos; cada paso de extracción y el ETL (P4) son gate. Se revierte si una cifra se mueve. |
| 3 | **Doble flujo proyecto/socio.** Confundir o exponer un solo flujo rompe el análisis de inversión. | **Siempre devolver ambos flujos** (proyecto sin financiación + inversionista apalancado) en `/results`; nunca fusionar `flujo_caja` con `flujo_apalancado`. |
| 4 | **Deploy ambiguo (`:latest`).** Imágenes mutables ocultan qué versión sirve cifras. | **Deploy por SHA**, no `:latest` (App Service → contenedor `az acr build`; `WEBSITES_PORT=8000`). `engine_version` (= `aleph_engine.__version__`) se persiste en `results_cache` para trazabilidad. |
| 5 | **Apagar el legacy demasiado pronto.** | **Paridad antes de apagar**: correr API/web nuevos contra `proyectos` plana en read-only y comparar contra Streamlit hasta cuadrar; recién entonces deprecar `proyectos`. |
| 6 | **`schema_version` no se persiste** (`schema.py:106` default 1, ningún JSON lo trae). | El ETL **estampa `schema_version=1`** en cada snapshot importado (P3) o se pierde la capacidad de versionar el contrato. |
| 7 | **`updated_at` no lo escribe el código** (`storage.py:175-178`); depende de un trigger en BD. | Garantizar `created_at/updated_at` con default/trigger en `projects`/`scenarios`, o se pierde la cronología. |
| 8 | **Estado duplicado** (`meta.estado` en jsonb vs columna `fase`). | **Fuente única: la columna `fase` manda**; el snapshot conserva `meta.estado` solo como histórico. Documentar la regla para evitar desincronización. |
| 9 | **`es_real` mal migrado** → datos reales expuestos como ilustrativos (o viceversa). | Preservar el flag 1:1; test del ETL que verifica `es_real` por slug; el badge `🔒` depende de él. |
| 10 | **Reales privados sin lugar en el destino** (la prioridad `proyectos_privados/` + convención `*_REAL` no existe en el modelo). | Decidir explícitamente: reales privados a Supabase **con RLS** (recomendado) o fuera de la BD. No migrar ciego. |
| 11 | **`guardar()` pisa la fila** (upsert sin historial) vs `scenarios` draft/approved/baseline. | La fachada compat (P5) **redirige `guardar` → nuevo `draft`**, nunca machaca el `approved`. |
| 12 | **`results_cache` sirviendo cifras viejas.** Es derivado; con `engine_version`/`inputs_hash` mal computados serviría cifras que no cuadran con las anclas. | Invalidar por `hash(snapshot) + ENGINE_V`; P4 compara contra doradas como gate. |
| 13 | **Aplanar el `par` heterogéneo** (`extra='allow'`: Dominica sin tipologías/fiducia, reales con `_nota/directos_cap`). | El modelo relacional **NO aplana**: esos campos quedan íntegros en el snapshot jsonb. |
| 14 | **`actuals_*` en fase equivocada.** Cargar reales para prefactibilidad/aprobado es un dato sin sentido. | Restricción: `actuals_*` solo para `construccion/entregado` (`config.py:47`). |
| 15 | **Fallback "nunca se rompe" enmascara errores.** Un error de la BD nueva caería silenciosamente al JSON local viejo, dando ilusión de éxito con data desactualizada. | **Desactivar/loggear el `except: pass`** durante el ETL y la fase de paridad; no migrar a ciegas sobre un swallow. |
| 16 | **EVM duplicado y reconciliación.** `cg_engine.evm` está desacoplado pero el Monitor recalcula EVM a mano (`app.py:1456-1460`). | Reusar `cg_engine.evm` sobre las partidas; eliminar la reimplementación para que haya una sola fuente de EVM. |

> **Ventaja estructural:** `cg_engine` ya está **casi puro** (§2). La migración es mayormente **renombrar + envolver + extraer 7 puntos**, no reescribir fórmulas. El riesgo dominante no es el cálculo (cubierto por `test_anclas`) sino la **migración de datos** (riesgos 6-15).

---

## 7. Estado vs el calendario de Fable y recomendación de arranque

### 7.1 Qué ya está hecho (adelanta el calendario)

- ✅ **`cg_engine` es un paquete instalable** (`pyproject.toml` dynamic version; `cg_engine/__init__.py` re-exporta `calcular`, `pyg`, `flujo_caja`, `escenarios`, `montecarlo`, `montecarlo_tir`, `calcular_wacc`, etc.). **Versión única 2.39.0**.
- ✅ **Núcleo desacoplado de Streamlit** (finanzas, curvas, portafolio, ingresos, modelo, apalancamiento, evm). El ciclo de import está roto (`finanzas.py` no importa otros módulos del motor).
- ✅ **`schema.py` Pydantic v2** valida el `par` en el borde (`extra='allow'`), con `meta.estado` contra `config.ESTADOS`.
- ✅ **`config.py`** sin números mágicos (constantes, estados, umbrales, `FECHA_CORTE_EVM`).
- ✅ **`tests/test_anclas.py` con cifras doradas** + CI en GitHub Actions: clava UO/TIR/VPN de los 3 proyectos reales. Red de seguridad lista para una migración segura.
- ✅ **`ui/nav.py`** ya separa el menú adaptativo al estado como **función pura testeable** (`grupos(estado, puede_ingresar)`).
- ✅ **`errors.py` + logging** en vez de swallows silenciosos en el motor.

### 7.2 Qué falta (honesto)

- ❌ **7 puntos de cálculo en `app.py`** (§2.2) aún acoplados — incluyen 2 duplicaciones (`_irr_anual`, EVM Navarra).
- ❌ **API FastAPI** (`/api`) y **front nuevo** (`/web`): no existen; hay que crearlos.
- ❌ **Modelo de datos destino** (companies/projects/scenarios/results/actuals/audit_log): no existe; hoy una sola tabla plana `proyectos`.
- ❌ **`schema_version` y `updated_at` no se persisten** hoy (riesgos 6-7).
- ❌ **Lote breakeven / precio máx pagable** (`NORTE_TABLEROS.md`): solo en doc de planeación, **sin implementar** en el engine.
- ❌ El contenedor desplegado puede ir **detrás de local**. Verificar versión servida antes de tocar.

### 7.3 Recomendación de arranque para PROMPT 2

1. **Congelar la red de seguridad**: confirmar que `test_anclas` pasa hoy con las 4 cifras doradas de Navarra (37.60% / 18.3 mil M / 41.72% / 49.3 mil M) y añadir, si faltan, las anclas de Dominica y Torres de Campiñas. Nada se mueve sin esto verde.
2. **Renombrar `cg_engine → aleph_engine`** como paso atómico puro (alias de compatibilidad temporal para `app.py`), manteniendo `__version__` como `ENGINE_V` y CI verde. Sin cambiar fórmulas.
3. **Extraer los 7 puntos de `app.py`** (§3.2 paso 13) al engine, uno por uno, cada uno verificado contra `test_anclas` — empezando por **borrar `_irr_anual`** (reusar `finanzas.irr_anual`) y mover `consolidado`/`puntos_portafolio`/`pipeline_datos`, que son lecturas puras de agregación.
4. **Levantar el esqueleto `/api`** (FastAPI) con **solo los GET de lectura** (§5) envolviendo `aleph_engine`, y un **test de contrato HTTP** que verifique las cifras doradas saliendo de `/v1/scenarios/{slug}:base/results`. La caché y `POST /run` van después.
5. **Diferir la migración de datos** (§4.3) hasta confirmar el esquema LIVE de Supabase con `list_tables` en el **PROMPT 4**; mientras tanto la API lee de `storage.py` sin tocar la tabla `proyectos`.

> **Norte:** extraer complejidad hacia código determinista (engine + tests dorados) primero; la API y el web son **adaptadores delgados** sobre un núcleo ya probado. Cada paso pequeño, CI verde, sin mover una sola cifra auditada.
