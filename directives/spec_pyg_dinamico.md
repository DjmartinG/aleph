# ALEPH — Spec maestra: P&G dinámico, costo de capital, tributación, Monte Carlo y UX (v1 · jun-2026)

> **Documento de especificación (Spec-Driven Development).** No es código ni una orden de "hazlo todo de una".
> Es el contrato de lo que vamos a construir, **por módulos independientes y verificables**, sobre el monorepo ALEPH.
> Subordinado a la **Constitución** (`CLAUDE.md §ALEPH`). Se ejecuta en el estilo de `directives/prompts_migracion_v3.md`:
> **plan primero → aprobación explícita → implementar → tests + gate dorado → verificar → commit por módulo.**
>
> Autor del encargo: Martín (Dirección Financiera, CG Constructora S.A.S.). Elaborado con investigación citada (jun-2026).

---

## 0. Cómo se usa este documento

1. **Es la fuente de la verdad del alcance.** Cada módulo (M0…M8) es un incremento **shippable** por estrangulamiento: termina con algo desplegado/usable y los tests verdes.
2. **No se implementa nada sin antes ratificar la spec del módulo** (sección 6). Para los módulos que **mueven cifras** (M1 costo de capital, M2 tributación), se exige **aprobación explícita de Martín** y un **re-baseline dorado** documentado.
3. **Orden sugerido por dependencia y riesgo**, no obligatorio: M0 → M6 → M1 → M2 → M3 → M4 → M5 → M7 → M8. Se puede reordenar salvo donde se indique dependencia dura.
4. Cada módulo trae: **objetivo · valor de decisión · alcance (in/out) · código a tocar · contrato de datos · criterios de aceptación (testables) · pruebas · riesgos · prompt de ejecución · definición de terminado**.

---

## 1. Visión: empezar por el P&G y devolvernos

El norte es un **P&G dinámico** que sea el **lienzo de decisión** de ALEPH, y desde él poder **devolvernos**:

- **Hacia adelante (inputs en vivo):** mover precio, ritmo de ventas, costo/m², apalancamiento, **vehículo jurídico** y **supuestos tributarios** y ver el P&G y los KPIs recalcularse al instante (sin recrear el proyecto).
- **Hacia atrás (goal-seek):** fijar una **meta** sobre el P&G (margen neto, TIR socio, VPN, o "estructura de mínima tributación") y que el motor **resuelva el driver** necesario para alcanzarla.

El P&G debe llegar hasta **utilidad neta real después de impuestos**, y los impuestos dependen del **vehículo** y del tipo **VIS/No-VIS**. Hoy no es así (ver §2 hallazgos).

---

## 2. Principios y gobernanza (innegociables)

1. **Motor primero.** Toda lógica financiera nueva vive en `engine/aleph_engine` (fuente única). API y web **solo exponen**. Cero cálculo financiero en el frontend.
2. **Etiqueta de base obligatoria** (`metrics.py`): ninguna cifra sin su base — "TIR proyecto", "TIR socio CG", "Renta (VIS exenta)", "Kd banco X". Greenfield → "— greenfield", jamás −99%.
3. **Snapshot dorado sagrado, con re-baseline explícito y auditado.** Los módulos M1 y M2 **moverán cifras a propósito**. Eso **no** se hace en silencio: el dorado viejo se **archiva versionado (no se sobrescribe)**, se regenera la línea base (`app_streamlit/tests/golden/`, `engine/tests/test_golden_harness.py`) en un commit dedicado, con un **acta de cambio** que liste **cada** cifra que cambia (Navarra/Dominica/TDC) con su delta y el porqué, y **un test compara dorado viejo vs nuevo y FALLA si cambia cualquier cifra NO listada en el acta** (evita el falso negativo de un cambio colateral oculto). Cualquier otra desviación > 0,1% sigue rompiendo el build.
4. **Checks de cuadre siempre verdes** (`checks.py`): P&G cuadra, recaudo = ingresos, flujo final = utilidad, reparto = resultados, crédito cuadra. Se extienden a los conceptos nuevos (después de impuestos, vehículo).
5. **Deploy por SHA**, versión en el pie. API en Azure (manual), web en Vercel (auto).
6. **Caveat tributario (legal/financiero).** ALEPH **modela y compara** estructuras como **soporte de decisión, no como asesoría tributaria**. Toda estructura concreta debe validarla el **contador/abogado tributarista** de CG. Se trata de **planeación legítima (elusión legal), nunca evasión**. Cada supuesto fiscal sensible se marca `[VALIDAR]` en la UI con su fuente normativa.
7. **Hallazgos que motivan esta spec (verificados en el código y con investigación citada):**
   - **Tributación VIS aplicada de forma plana (a revisar).** `modelo.py::pyg` hace `renta = fin.get("renta", config.RENTA) * reint_sin_lote` — **35% plano para todos**, sin distinguir VIS. La utilidad de la **primera venta VIS puede ser renta exenta** (ET 235-2 num.4, vía fiducia con licencia VIS, plazo ≤10 años) y existir **devolución del IVA de construcción (tope 4% del valor de la vivienda)** (ET 850 par.2 / Dec. 096/2020), **`[VALIDAR vigencia post-Ley 2277/2022 y cupo]`**. Si la exención aplica a Navarra/TDC (VIS), el modelo hoy **sobre-grava** y **sub-estima** la TIR del socio. La constructora tributa **35% sin sobretasa** (la +5% es solo entidades financieras).
   - **Costo de capital: revisar CALIBRACIÓN de inputs, no la fórmula (corregido tras verificación adversarial).** `finanzas.py::calcular_wacc` suma el EMBI (`rp`) **una sola vez** en el Ke, con `rm` como retorno de mercado **maduro (US)** — es la metodología Damodaran estándar; **la fórmula NO tiene un doble conteo estructural** (no se eliminan términos). El problema real es de **dato**: `rf=0,12%`, `pm≈12,32%` (muy alto para un ERP maduro ~4,5–5,5%) y `kd_us=9,335` lucen mal calibrados y **pueden estar compensándose** para cuadrar el WACC dorado (21,54%). M1 **audita la hoja `k.beta`** y recalibra inputs uno a uno. La intuición de Martín («el riesgo país ya está en la tasa de interés») se resuelve en la sesión de Requirements de M1 con la hoja a la vista: el EMBI vive en el Ke y el país embebido en `kd_cop` es la pata de **deuda** — son patas distintas, no necesariamente un doble conteo. Decisión de política aparte: el **VPN se descuenta a TIO 15%** mientras el WACC es 21,54% → evaluar mantener **ambas** métricas (`VPN @TIO` y `VPN @WACC`).
   - **Un solo vehículo cableado.** La fiducia entra como **override auditado** (`apalancamiento.py`, `par['fiducia']`), no como vehículo intercambiable. No hay consorcio/UT/cuentas en participación/SAS/FCP como opción que cambie impuestos y flujo.

---

## 3. Flujo Spec-Driven por módulo (repetir en cada M)

Por cada módulo, en una sesión dedicada:

1. **Requirements** — afinar los **criterios de aceptación** (formato EARS / Dado-Cuando-Entonces) de la sección 6. Confirmar in/out de alcance.
2. **Design** — diseño técnico breve: qué funciones/archivos se tocan, contrato de datos (entrada/salida del motor), impacto en API y web, y **si mueve cifras** (→ plan de re-baseline).
3. **Tasks** — lista de tareas pequeñas y ordenadas. Plan primero; **aprobación de Martín** antes de codear los módulos que mueven cifras o tocan el camino crítico.
4. **Build** — implementar copiando lógica verbatim donde exista; cero reescritura de memoria del WACC/fiducia/curva S.
5. **Tests + gate dorado** — tests unitarios del concepto nuevo + `test.sh` completo (engine → app → ruff). Si el módulo mueve cifras: regenerar dorado + acta de cambio.
6. **Verify** — verificación adversarial (lente financiera/tributaria/UX según el módulo), idealmente con un subagente, antes de dar por terminado. Para UI: revisar el DOM, no solo el screenshot (gotcha visx conocido).
7. **Commit** por módulo (working tree limpia; tag = SHA si hay deploy). Actualizar el registro de aprendizajes de `CLAUDE.md`.

**Definición de terminado (toda fase):** tests verdes (incl. dorado o re-baseline aprobado) · checks de cuadre expuestos · ninguna cifra sin etiqueta en pantallas nuevas · desplegado/verificado · instrucciones de verificación manual para Martín.

---

## 4. Arquitectura de los módulos nuevos

```
engine/aleph_engine/
  supuestos_macro.py   (NUEVO)  → esquema + carga de parámetros macro (tasas, EMBI, IPC, ICOCED, betas…)
  tributario.py        (NUEVO)  → motor de impuestos por VEHÍCULO y VIS/No-VIS (renta, IVA-devolución, ICA, GMF…)
  vehiculos.py         (NUEVO)  → catálogo de vehículos y su efecto en flujo/impuestos/waterfall
  goal_seek.py         (NUEVO)  → resolver driver→meta sobre el P&G (búsqueda robusta)
  montecarlo.py        (EVOLUCIONA) → distribuciones por variable, forecasts, percentiles, tornado de varianza
  finanzas.py          (EDITA)  → calcular_wacc: país una vez, validar rf/rm, TIO vs WACC
  modelo.py            (EDITA)  → pyg: renta por vehículo + VIS exención + devolución IVA; P&G after-tax
  metrics.py           (EDITA)  → nuevas métricas con etiqueta (UDI VIS, Kd por banco, costo de capital por carril)
  config.py            (EDITA)  → mover supuestos a supuestos_macro; conservar defaults
api/aleph_api/
  build.py / main.py   (EDITA)  → exponer supuestos macro, tributario, vehículos, goal-seek, MC enriquecido
  conectores/          (NUEVO)  → Banrep SDMX, datos.gov.co Socrata, Damodaran xlsx, DANE (descarga)
web/src/
  components/views/    (EDITA)  → P&G como lienzo de decisión; selector de vehículo; sliders en vivo; goal-seek
  components/charts/   (EDITA)  → MC con bandas de certeza + tornado de varianza
db/ (Supabase)        → tablas: supuestos_macro (versionado), tabla_tasas_constructor (manual), vehiculo por escenario
```

---

## 5. Roadmap de módulos

| # | Módulo | Mueve cifras | Depende de | Valor |
|---|---|---|---|---|
| **M0** | Fundaciones: módulo Supuestos Macro (esquema + tabla editable) + scaffolding de tests | No | — | Desacopla supuestos; habilita todo lo demás |
| **M6** | Conectores de datos (Banrep/Socrata/Damodaran/DANE) + refresco programado | No | M0 | Datos "pro, estables, mantenibles" |
| **M1** | Costo de capital corregido (país una vez, validar rf/rm, TIO vs WACC) + re-baseline | **Sí** | M0 | Quita el doble conteo; WACC correcto |
| **M2** | Régimen tributario por vehículo + corrección VIS (P&G after-tax real) + re-baseline | **Sí** | M0 | "Pagar lo justo"; net income real |
| **M3** | Vehículos jurídico-financieros (selector + efecto en flujo/impuestos/waterfall) | Sí* | M2 | Comparar fiducia/consorcio/UT/cuentas/SAS/FCP |
| **M4** | Motor bidireccional: inputs en vivo (forward) + goal-seek ("devolvernos") | No** | M1,M2 | Decisión desde el P&G |
| **M5** | Monte Carlo Crystal Ball (distribuciones, forecasts, bandas, tornado de varianza) | No** | M1,M2 | Riesgo probabilístico serio |
| **M7** | UX sin fricción: lienzo de decisión liderado por P&G + auditoría/rediseño | No | M4 | Cero fricción de uso |
| **M8** | Argos (4º proyecto) + cierre de paridad | No | M2,M3 | Portafolio completo |

\* M3 mueve cifras solo al elegir un vehículo distinto del actual (la fiducia base no cambia). \*\* No tocan `calcular()` base → no rompen el dorado; agregan capacidades.

---

## 6. Especificación por módulo

### M0 · Fundaciones — módulo de Supuestos Macro

- **Objetivo.** Crear `supuestos_macro.py`: un **diccionario único y versionado** de parámetros macro (tasas, EMBI, IPC, ICOCED, betas Damodaran, SMMLV, tasas por banco) con `valor · fuente · fecha · método`. Migrar a él los supuestos hoy dispersos en `config.py` y en cada `par`, **sin alterar ninguna cifra** (los defaults reproducen lo actual).
- **Valor de decisión.** Una sola fuente de verdad de supuestos → habilita corregir el riesgo país una vez (M1), los conectores (M6) y la tabla de tasas por banco.
- **Alcance.** IN: esquema Pydantic del bloque macro; tabla `supuestos_macro` en Supabase (versionada, RLS lectura gerencia / edición admin); defaults = valores actuales; **extender el dataclass `Metric` (`metrics.py`) con `estado_validacion` y `fuente_normativa`** para que el `[VALIDAR]` sea exigible por test (lo usan M1/M2). OUT: aún sin conectores (M6) ni cambio de fórmulas (M1/M2).
- **Precedencia (clave para no mover cifras).** El `par` del proyecto **manda** sobre el default macro: el macro **solo rellena ausencias** (igual que `fin.get(...)` hoy). Test que lo verifica.
- **Código.** `engine/aleph_engine/supuestos_macro.py` (nuevo), `config.py` (re-export para no romper API), `metrics.py` (campos nuevos en `Metric`), `db/migrations/000X_supuestos_macro.sql`.
- **Criterios de aceptación.**
  - Dado el snapshot actual, **cuando** se calcula con los supuestos cargados desde `supuestos_macro`, **entonces** TIR/VPN/WACC de Navarra/Dominica/TDC son **idénticos** (gate dorado intacto, < 0,1%).
  - **El `par` del proyecto tiene precedencia; el macro solo rellena ausencias** (test).
  - Cada parámetro expone `fuente` y `fecha`; `Metric` admite `estado_validacion`/`fuente_normativa`.
- **Pruebas.** `test_supuestos_macro.py` (defaults == config previa); gate dorado verde.
- **Riesgos.** Romper imports → mitigar con re-exports.
- **Prompt de ejecución.** "M0 de `directives/spec_pyg_dinamico.md`: crea el módulo Supuestos Macro (esquema + tabla versionada + migración de los supuestos actuales como defaults idénticos). Plan primero. No muevas ninguna cifra: el dorado debe quedar intacto."
- **Terminado.** Tests verdes, dorado intacto, tabla en Supabase, supuestos con etiqueta de fuente.

### M6 · Conectores de datos + refresco programado

- **Objetivo.** Alimentar Supuestos Macro automáticamente desde fuentes estables; lo no automatizable, como tabla manual con compuerta de revisión.
- **Alcance / contrato (de la investigación citada).**
  - **Automatizable:** **Banrep SDMX** (`totoro.banrep.gov.co/nsi-jax-ws/rest/...`) → IBR, DTF, TES, TRM, **EMBI** (gratis, sin licencia J.P. Morgan), inflación. **datos.gov.co Socrata** → usura/IBC SFC, y **tasa de vivienda VIS/No-VIS por banco** (datasets `w9zh-vetq` histórico + `qzsc-9esp` reciente, semanal, CC BY-SA). **Damodaran** `ctryprem.xlsx` (URL fija, anual) → betas/ERP/CRP del WACC.
  - **Semi/manual:** **DANE** (ICOCED para costos de vivienda — sucesor del ICCV desde 2022; **ICOCIV es obras civiles, no vivienda**) por descarga de anexos. **FNA** (tasas propias). **Camacol Coordenada Urbana** y **La Galería** = **suscripción**, importación manual.
  - **Tabla manual editable** `tasa_constructor` (`banco → indicador IBR/DTF → spread pactado → vigencia`) — la tasa real del crédito constructor **no se publica por banco**; la mantiene el área financiera. Idem **carriles de costo de capital alternativo**: deuda mezzanine (spread paramétrico) y equity FCP (benchmark oportunista 18–25% USD, preferred 7–10%), **etiquetados como estimado/benchmark**.
- **Código.** `api/aleph_api/conectores/` (banrep_sdmx, socrata, damodaran, dane); tarea programada **mensual** (con compuerta: propone valores, Martín aprueba antes de aplicar).
- **Criterios de aceptación.** Cada conector trae valor + fecha + fuente; falla → conserva el último bueno y marca "desactualizado"; nada se aplica sin aprobación. El EMBI y betas alimentan M1.
- **Riesgos.** SUAMECA es JS-render → pegar al endpoint SDMX, no al HTML; cachear catálogo de dataflows. Rezago semanal de Socrata → usar `qzsc-9esp` para lo reciente.
- **Prompt.** "M6: implementa los conectores Banrep SDMX, datos.gov.co Socrata (usura + vivienda por banco), Damodaran xlsx y descarga DANE ICOCED, alimentando Supuestos Macro con compuerta de revisión mensual. Verifica que cada endpoint responde de verdad."
- **Terminado.** Conectores probados contra endpoints reales, refresco con aprobación, tasas por banco visibles.

### M1 · Costo de capital — auditoría de calibración (NO "quitar un doble conteo")

> Corregido tras verificación adversarial: la fórmula de `calcular_wacc` suma el EMBI **una sola vez**; el problema es de **inputs**, no estructural. **No se eliminan términos de la fórmula.**

- **Objetivo.** (a) **Auditar y recalibrar** los inputs del build-up contra la hoja `k.beta`: `rf` (0,12% es anómalo), `rm`/`pm` (12,32% alto para ERP maduro), `kd_us` (9,335). (b) Confirmar que `rm` es **ERP maduro (US)** y que el EMBI entra una sola vez. (c) Decisión de **política** separada: tasa de descuento del VPN (TIO hurdle vs WACC).
- **Riesgo central.** `rf` bajo y `pm` alto **pueden compensarse** para cuadrar el WACC dorado (21,54%); recalibrar "limpio" puede mover el WACC de forma **material e imprevisible**. Por eso se recalibra **input por input**, documentando el delta de cada uno.
- **TIO vs WACC (no destructivo).** **Mantener ambas** métricas etiquetadas: `VPN @TIO` (hurdle de política, status quo) y `VPN @WACC` (costo de capital). **No reemplazar** la etiqueta `@TIO` (es cifra dorada).
- **Mueve cifras → re-baseline auditado.** Aprobación de Martín + acta que lista **cada** cifra que cambia con su delta; dorado viejo archivado + test de diff (ver §2.3).
- **Código.** `finanzas.py::calcular_wacc`, `metrics.py` (etiquetas + `VPN @WACC`), `supuestos_macro` (inputs auditables: rf, rm, pm, kd_us, EMBI), pestaña Costo de capital.
- **Criterios de aceptación (testables).**
  - Dado rf, rm(maduro) y CRP conocidos, `Ke_COP` = build-up Damodaran con CRP sumado **una vez**; test compara contra el valor calculado a mano.
  - Cada input expone fuente y fecha (Supuestos Macro/Damodaran/Banrep); `kd_us` incluido.
  - Ambas patas en COP; `VPN @TIO` y `VPN @WACC` visibles y etiquetadas.
  - Re-baseline: test "dorado viejo vs nuevo solo cambia lo del acta" verde.
- **Prompt.** "M1: NO quites términos de `calcular_wacc` (no hay doble conteo estructural). Audita la hoja k.beta y recalibra rf/rm/pm/kd_us uno a uno; añade `VPN @WACC` junto a `VPN @TIO` sin reemplazarlo. Prepárame el acta de re-baseline (cada cifra y su delta) y el test de diff dorado, y espera mi aprobación antes de tocar el dorado."
- **Terminado.** Inputs recalibrados y documentados, ambas VPN etiquetadas, re-baseline auditado con acta + test de diff, pie verificado.

### M2 · Régimen tributario por vehículo + corrección VIS

- **Objetivo.** Llevar el P&G a **utilidad neta real después de impuestos**, con impuestos **dependientes de vehículo y de VIS/No-VIS**. Reemplazar el `renta = 0.35 × reintegro` plano.
- **Reglas (de la investigación — TODAS `[VALIDAR vigencia post-Ley 2277/2022]`).**
  - **VIS primera venta:** utilidad potencialmente **renta exenta** (ET 235-2 num.4) **si** se estructura en fiducia con licencia VIS, plazo ≤10 años, ejecución 100% por el PA. `[VALIDAR vigencia/plazos: la Ley 2277/2022 recortó rentas exentas — confirmar para la fecha de licencia de cada proyecto]`. `[VALIDAR]` límite 40% solo personas naturales; persona jurídica (SAS CG) exención plena.
  - **Devolución de IVA VIS:** devolución del **IVA pagado en la construcción** (materiales/insumos), con **tope del 4% del valor de la vivienda** (ET 850 par.2 / Dec. 096/2020) — **no** un crédito automático sobre la escritura. `[VALIDAR base, vigencia y cupo presupuestal a la fecha de los proyectos]`.
  - **No-VIS:** renta **35%** plena, sin devolución.
  - Constructora **35% sin sobretasa** (la +5% es solo financieras). **Ganancia ocasional 15%** como palanca (venta de SPV >2 años) `[VALIDAR Art. 869 abuso]`. ICA territorial (Pereira ≠ Bogotá), GMF 4×1000 en fiducia, retención, registro — Fase 2 del motor fiscal.
- **Fases del motor fiscal (recomendación).** **Fase 1 (material):** renta con exención VIS + devolución IVA VIS + 35% No-VIS + ICA + GMF + retención. **Fase 2:** ganancia ocasional, registro, delineación, predial, plusvalía, sobretasas.
- **Mueve cifras → re-baseline.** Navarra/TDC (VIS) cambiarán al alza tras impuestos. Aprobación + acta.
- **Código.** `tributario.py` (nuevo, motor por vehículo/VIS), `modelo.py::pyg` (sustituye la línea de renta; P&G after-tax con desglose de impuestos), `metrics.py` (UDI con etiqueta "VIS exenta"/"No-VIS 35%"), `checks.py` (cuadre after-tax).
- **Criterios de aceptación.**
  - Proyecto VIS en fiducia → renta sobre utilidad VIS = **0** (exenta), con devolución IVA 4% reflejada; cada cifra etiquetada y con nota `[VALIDAR]` + fuente.
  - Proyecto No-VIS → 35%.
  - Cambiar `tipo` o `vehículo` propaga consistentemente a P&G, flujo y reparto (checks verdes).
  - Re-baseline aprobado con acta antes/después.
- **Prompt.** "M2: crea `tributario.py` (motor de impuestos por vehículo y VIS/No-VIS, Fase 1 material) y conéctalo en `pyg` reemplazando la renta plana. Refleja la renta exenta VIS y la devolución de IVA 4%. Marca cada supuesto fiscal con `[VALIDAR]` y su norma. Mueve cifras: acta de re-baseline + mi aprobación antes del dorado."
- **Terminado.** P&G after-tax correcto por tipo, etiquetado, caveat visible, dorado re-baselizado.

### M3 · Vehículos jurídico-financieros

- **Objetivo.** Convertir el vehículo en una **opción de escenario** que cambia impuestos, flujo y waterfall: **fiducia inmobiliaria, encargo fiduciario de preventas, consorcio, unión temporal, cuentas en participación, SAS/SPV, FCP** (y derecho de superficie como avanzado `[VALIDAR]`).
- **Reglas clave.** Fiducia = transparente (ET 102) y **requisito de la exención VIS**. Consorcio/UT = no contribuyentes (ET 18), cada socio declara su parte. **Cuentas en participación = transparencia plena post-reforma 2022 → no ahorra impuestos** (valor: confidencialidad). SAS = 35% pleno. FCP = diferimiento (ET 23-1) `[VALIDAR]`.
- **Código.** `vehiculos.py` (catálogo + efecto), `tributario.py` (consume vehículo), `apalancamiento.py` (waterfall según vehículo), schema (`par['vehiculo']`).
- **Resolución de un riesgo (override de fiducia).** El override auditado (`par['fiducia']`) **solo** lo usa el vehículo "**fiducia base**" (por eso reproduce las cifras doradas). **Cualquier otro vehículo recalcula el waterfall desde cero** (no usa el override, que congela hitos) y por tanto **requiere su propio golden test** — el dorado actual NO cubre waterfalls no-fiducia.
- **Criterios de aceptación.** Selector de vehículo por escenario; cada vehículo aplica su tratamiento fiscal y de waterfall; comparador "estructura A vs B" sobre el mismo proyecto; **la fiducia base reproduce las cifras actuales (no-op, dorado intacto)**; cada vehículo no-fiducia tiene golden test propio.
- **Prompt.** "M3: añade el catálogo de vehículos y su efecto en impuestos/flujo/waterfall; selector por escenario y comparador. La fiducia base no debe mover cifras."
- **Terminado.** Comparación de vehículos funcionando, fiducia base intacta, etiquetas + `[VALIDAR]`.

### M4 · Motor bidireccional (inputs en vivo + goal-seek)

- **Objetivo.** (a) **Forward:** sliders/campos editables sobre el P&G que recalculan al instante (precio, ritmo, costo, apalancamiento, vehículo, supuestos). (b) **Backward:** `goal_seek.py` resuelve el driver para una meta (margen neto, TIR socio, VPN, mínima tributación).
- **Código.** `goal_seek.py` (búsqueda robusta reutilizando `finanzas`/`modelo`, determinista), API `POST …/solve` y `…/recalc`, web (panel de control + affordance de meta).
- **Criterios de aceptación.** Recalcular en vivo < ~1 s para los drivers principales; goal-seek converge o reporta "no alcanzable en el rango"; no toca `calcular()` base (dorado intacto); cada resultado con etiqueta.
- **Prompt.** "M4: implementa el recálculo en vivo del P&G y el goal-seek (driver→meta). No cambies las fórmulas base; orquesta sobre el motor existente."
- **Terminado.** Forward y backward operativos desde el P&G, sin romper dorado.

### M5 · Monte Carlo estilo Crystal Ball

- **Objetivo.** Elevar el MC actual a metodología Crystal Ball.
- **Alcance.** **Distribuciones por variable** (triangular/PERT desde `benchmarks_cg` + macro; normal/lognormal donde haya datos); **forecasts**: TIR proyecto, TIR socio, VPN, margen, exposición máxima, mes breakeven; **salidas**: histograma, percentiles P5/P50/P95, **bandas de certeza** (prob. TIR ≥ hurdle, prob. VPN<0), media/mediana/σ, y **tornado de contribución a la varianza** (gráfico insignia). **Fase 2:** correlaciones entre variables (costo↔ICOCED, ventas↔precio).
- **Código.** `montecarlo.py` (evoluciona; respeta el aprendizaje de timing: la escrituración sigue al PE; el MC ignora override de fiducia para que responda), API `POST …/run`, web (charts visx).
- **Criterios de aceptación.** Determinista por `seed`; 1.000 corridas en tiempo razonable; cada salida etiquetada; tornado de varianza correcto; no rompe dorado.
- **Prompt.** "M5: evoluciona el Monte Carlo a Crystal Ball (distribuciones por variable, forecasts, percentiles, bandas de certeza, tornado de varianza). Correlaciones en fase 2."
- **Terminado.** MC probabilístico completo, etiquetado, reproducible.

### M7 · UX sin fricción

- **Objetivo.** Rediseñar hacia un **lienzo de decisión único liderado por el P&G**, reduciendo el salto entre 5 pestañas, con el panel de inputs (forward) y la meta (goal-seek) a la vista.
- **Método.** Auditoría con skills de diseño (design-critique, accessibility-review AA, ux-copy) + rediseño respetando el design system canon (KpiCard, ChecksBadge, etc.). Verificar por DOM (no solo screenshot — gotcha visx).
- **Criterios de aceptación.** Recorrido de decisión en ≤ 2 clics desde el P&G; estados de carga skeleton; AA de contraste; responsive tablet; código de colores vs base.
- **Prompt.** "M7: audita ALEPH con las skills de diseño y propón el rediseño del lienzo de decisión liderado por el P&G, dentro del design system."
- **Terminado.** Auditoría + rediseño entregados y verificados.

### M8 · Argos (4º proyecto) + cierre de paridad

- **Objetivo.** Montar **Argos** (CG + Conaltura 50/50, Fontibón, prefactibilidad, propuestas escalonadas) en ALEPH usando la skill `modelador-prefactibilidad-cg` + el flujo de alta existente.
- **Criterios de aceptación.** Argos visible en portafolio con etiqueta "prefactibilidad" e `is_greenfield` donde aplique (sin TIR −99%); advertir que existen múltiples propuestas escalonadas (el parser lee la principal).
- **Prompt.** "M8: monta Argos en ALEPH desde su Excel vía la skill de prefactibilidad; respeta greenfield y la advertencia de propuestas múltiples."
- **Terminado.** Portafolio de 4 proyectos consistente.

---

## 7. Matriz de fuentes de datos (consolidada)

| Fuente | Series | Acceso | Endpoint / nota | Cadencia | Costo |
|---|---|---|---|---|---|
| **Banco de la República** | IBR, DTF, TES, TRM, **EMBI**, inflación | **API SDMX** | `totoro.banrep.gov.co/nsi-jax-ws/rest/data/...`; catálogo en `suameca.banrep.gov.co/buscador-de-series/` | Diaria–reunión | Gratis |
| **datos.gov.co (Socrata)** | Usura/IBC SFC; **tasa vivienda VIS/No-VIS por banco**; comercial por banco | **API SODA** | `datos.gov.co/resource/w9zh-vetq.json` (hist.) + `qzsc-9esp` (reciente) | Semanal | Gratis (CC BY-SA) |
| **Damodaran (NYU)** | Betas sector, ERP, CRP/default spread | **Excel URL fija** | `stern.nyu.edu/~adamodar/pc/datasets/ctryprem.xlsx` | Anual (enero) | Gratis |
| **DANE** | IPC, **ICOCED** (vivienda; ex-ICCV), IPVN, CEED, ELIC; *ICOCIV = obras civiles* | Descarga Excel + microdatos | `dane.gov.co/.../precios-y-costos/...`; `microdatos.dane.gov.co` | Mensual/trim. | Gratis |
| **SFC** | Usura, IBC, certifica TRM | Boletín / vía Socrata | Formato **414** (ex-088) | Mensual | Gratis |
| **FNA** | Tasas VIS/No-VIS propias | Sitio (scrape ligero) | `fna.gov.co/sobre-el-fna/tasas` | Esporádica | Gratis |
| **Camacol – Coordenada Urbana** | Ventas, lanzamientos, **absorción** por proyecto/ciudad | Portal | sin API | Mensual | **Suscripción** |
| **La Galería Inmobiliaria** | Censo vivienda nueva, precios, absorción | Portal | sin API | Mensual | **Suscripción** |
| **SNR** | Transacciones inmobiliarias | Observatorio + descarga | `supernotariado.gov.co/observatorio-de-datos...` | Periódica | Gratis |
| **Tasa constructor (CG)** | Spread pactado por banco | **Tabla manual** | área financiera (cartas de aprobación) | — | — |
| **FCP / mezzanine** | Costo de capital alternativo | **Benchmark/manual** | oportunista 18–25% USD; preferred 7–10% (sin cifra pública por fondo CO) | — | — |

---

## 8. Apéndice tributario (resumen — soporte de decisión, no asesoría)

- **Renta jurídica:** 35%, **sin** sobretasa para constructora.
- **VIS primera venta:** **renta exenta** (ET 235-2 num.4) vía **fiducia** (licencia VIS, ≤10 años, ejecución 100% por PA) + **devolución IVA 4%** (ET 850 par.2 / Dec. 096/2020). **No-VIS:** sin beneficios.
- **Vehículos:** fiducia (transparente ET 102, requisito VIS); consorcio/UT (no contribuyentes ET 18); **cuentas en participación (transparencia plena post-2022 → sin ahorro fiscal)**; SAS (35%); FCP (diferimiento ET 23-1).
- **Otros:** ganancia ocasional 15% (venta SPV >2 años, `[VALIDAR]` abuso ET 869); ICA territorial (Pereira ≠ Bogotá); GMF 4×1000 (alto en fiducia, gestionar cuentas marcadas); registro/beneficencia ~2,4–2,8% (comprador); IVA: la venta del inmueble **no causa IVA**.
- **Puntos `[VALIDAR]` con asesor:** límite 40% PN vs PJ en exención VIS; exención GMF del PA; registro en aporte/restitución del lote; tarifa ICA constructora Pereira; renta del derecho de superficie; estructura FCP (ET 23-1); recaracterización por abuso.

---

## 9. Riesgos transversales y caveats

- **No-asesoría tributaria/legal:** todo lo fiscal es soporte de decisión; valida el contador/tributarista de CG. Planeación legítima, nunca evasión.
- **Cifras de fondos privados:** no públicas; usar benchmarks etiquetados, nunca inventar.
- **Dorado:** M1 y M2 mueven cifras a propósito → re-baseline aprobado con acta; cualquier otra desviación rompe el build.
- **Datos:** Banrep SDMX (no HTML); Socrata con rezago; Camacol/Galería de pago.
- **Verificación:** preferir revisión adversarial con subagente y, en UI, inspección por DOM.

---

### Registro de decisiones (este encargo)
- Dirección del modelo: **bidireccional** (inputs en vivo + goal-seek), P&G como lienzo.
- Datos: **híbrido con refresco programado mensual** y compuerta de revisión; núcleo automatizable Banrep/Socrata/Damodaran.
- Riesgo país: **Damodaran USD, país una sola vez**, validar rf/rm, reconciliar TIO/WACC.
- Tributario: **motor por vehículo + corrección VIS**, por fases (material → completo).
- Vehículos: fiducia, encargo de preventas, consorcio, UT, cuentas en participación, SAS, FCP (+ derecho de superficie avanzado).
- UX: **auditoría + rediseño** del lienzo de decisión.
- Argos: **incluido**.
