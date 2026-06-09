# Changelog — App Factibilidad CG

Versionado semántico (MAJOR.MINOR.PATCH).

## [2.35.0] — 2026-06-09
### Seguridad (UX quick win 1/7 — blindaje del candado)
- **El gate nunca abre en modo editor sin clave.** Antes, sin `CLAVE_EQUIPO` ni SSO, caía en silencio a
  rol `editor` → una app desplegada sin clave quedaba **pública y editable sin contraseña**. Ahora ese caso
  cae a **modo solo lectura** y muestra un **aviso visible** ("Modo solo lectura · falta configurar clave").
  La edición requiere CLAVE_EDITOR o SSO de Microsoft. Hallazgo crítico de la auditoría UX (45 agentes).
### Verificación
- AppTest sin regresión (editor/viewer 0 excepciones). El cambio solo afecta el caso sin clave configurada.

## [2.34.0] — 2026-06-08
### Añadido (lista para Azure App Service + login de Microsoft, sin fricción)
- **Secretos portables:** `_secret` (app.py y storage.py) ahora lee de `st.secrets` y, si no está, de
  **variables de entorno** → la app corre igual en Streamlit Cloud o en cualquier host (Azure App Service,
  contenedores) sin tocar código.
- **SSO de Microsoft (Azure Easy Auth / Entra ID) soportado:** si la app corre detrás de App Service
  Authentication, el header `X-MS-CLIENT-PRINCIPAL-NAME` autentica al usuario → entra como **consulta sin
  clave** (login corporativo). La **clave de editor** sigue elevando a edición. El panel lateral muestra
  "Conectado como <email>".
- **`startup.sh`** (arranque de Streamlit para App Service) y **`DEPLOY_AZURE.md`** (guía paso a paso para
  TI: App Service B1 sin dormir, deploy desde GitHub, WebSockets, secretos como env vars, Easy Auth a un solo
  tenant, dominio propio).
### Contexto
- Decisión de infraestructura: mover el *frontend* a un hosting estable con login Microsoft (comité ve, 1–2
  editan), conservando el motor (Python) y los datos (Supabase) intactos. La migración la ejecuta TI con la guía.
### Verificación
- Sin regresión: AppTest 19 secciones 0 excepciones; el candado local sigue operativo (Easy Auth cae a
  fallback fuera de Azure). `startup.sh` validado.

## [2.33.0] — 2026-06-08
### Auditoría integral (multi-agente) + blindaje
- Auditoría integral del motor tras las fases 1–5 (13 agentes: 10 dimensiones + verificación adversarial +
  síntesis). **Veredicto: reconciliación OK** — las 3 cifras auditadas reconcilian exacto; todas las fases
  correctas. 2 bugs **latentes** confirmados y corregidos:
### Corregido
- **Regla VIS/No VIS movida al motor** (fuente única): `normalizar_tipologias` ahora lee `meta.tipo` y en
  **VIS/VIP** excluye parqueaderos/depósitos del ingreso (antes solo la UI filtraba → un JSON cargado por
  API/import inflaba ventas). Verificado: Navarra (VIS) + parqueaderos → ventas sin cambio; Dominica (No VIS)
  → suman.
- **`dur_obra=0` ya no rompe** `flujo_caja` (`dur=max(1, int(dur_obra or 24))`) — evita ZeroDivisionError
  ante una etapa con duración 0.
- Guarda local `V>0` en `apalancamiento` (`share = ventas/(V or 1)`), robustez ante ventas=0.
### Verificación
- Anclas intactas (dif 0 en los 3); los 2 fixes probados; AppTest 19 secciones: 0 excepciones. Motor v1.12.1.

## [2.32.0] — 2026-06-08
### Añadido (Fase 4 — indirectos a detalle + gastos financieros + impuestos)
- **Costos indirectos por capítulo** (`indirectos_cap`, bottom-up — mismo patrón que los directos):
  diseños, licencias, interventoría, pólizas, comisión fiduciaria, **predial**, **ICA**, etc. Si existe, el
  indirecto del P&G es su **suma**; si no, el % de ventas. `engine.indirectos_total`. Editor en
  Distribución costos; interactúa con el carve-out de gastos fijos. Motor v1.12.0.
- **Gastos financieros e impuestos (memo)** en el P&G: nuevo bloque que muestra los **intereses del crédito
  constructor** (no afectan la UO — son del inversionista; se ven en *FC del Inversionista*) y la **provisión
  de renta** (ya descontada en la UDI). Los impuestos operativos (predial, ICA) se cargan como capítulos del
  indirecto.
### Cierre del árbol de egresos
- Con esto el modelo cubre el árbol completo: **lote · directos (28 cap.) · indirectos (por capítulo) ·
  gastos fijos · honorarios · financieros · impuestos**, alimentando P&G y las 2 vistas del flujo.
### Verificación
- Anclas intactas (sin `indirectos_cap`): UO 11,36/11,25/6,17 mil M · TIR 0,376/0,5655/−0,9936. Indirecto
  bottom-up reconcilia exacto al total. AppTest 19 secciones + editor de indirectos (editor y consulta) +
  memo financiero en P&G: 0 excepciones.

## [2.31.0] — 2026-06-08
### Añadido (Fase 5 — flujo de caja reconectado + 2 vistas)
- **Flujo de caja** ahora con **dos vistas en tabs**: **🏗️ FC del Proyecto** (sin financiación — bondad
  intrínseca: TIR/VPN del proyecto, necesidad máx de caja) y **💰 FC del Inversionista** (apalancado —
  retorno al equity de CG tras el crédito: TIR del socio, aportes/VPN socio, crédito máx, intereses).
  Eje en fechas reales hasta 2030; en Navarra (en obra) toggle "solo de aquí en adelante".
### Cambiado (reconexión del detalle en el flujo apalancado)
- `apalancamiento.flujo_apalancado` ahora **respeta el carve-out de gastos fijos** (Fase 3): prorratea en
  obra solo el **indirecto restante** (`indirectos_otros`) y gasta los **gastos fijos mes a mes** en su
  ventana (los financia el equity, no el crédito); el **valor financiable** del crédito constructor pasa a
  `directos + indirectos_otros` (los gastos de estructura no son financiables). Motor v1.11.0.
### Verificación
- Anclas intactas en los 3 (sin gastos): TIR proyecto 0,376/0,5655/−0,9936 · TIR socio Navarra 0,4172 ·
  crédito máx Navarra $49.292 M. Carve-out: el costo total del flujo se preserva (solo cambia el timing) y
  el financiable baja por los gastos. AppTest 19 secciones + 2 vistas (Navarra y greenfield): 0 excepciones.

## [2.30.0] — 2026-06-08
### Añadido (Fase 2b — recaudo diferenciado de adicionales · Fase 3 — gastos fijos)
- **Fase 2b:** los **parqueaderos/depósitos** de No VIS ahora se recaudan en el **perfil de la cuota
  inicial** (venta→entrega), **sin subrogación** (no se hipotecan aparte). `normalizar_tipologias` separa
  por etapa `ventas_vivienda_miles` (recaudo completo) y `ventas_adicional_miles`; `ingresos.recaudo_etapa`
  recibe `adicional_miles`. Verificado: en Dominica 100 parqueaderos×$35M → +$3.500 M a cuota inicial, $0 a
  subrogación.
- **Fase 3:** nuevo capítulo **Gastos fijos de estructura** (`gastos_fijos`: {concepto, valor_mes_miles,
  desde, hasta}). `engine.gastos_fijos_total`; en el P&G se **tallan dentro de los indirectos** (carve-out:
  UO sin cambio si no superan el indirecto; el exceso baja la UO) y en el **flujo se gastan mes a mes** en su
  ventana (no prorrateados en obra). Editor «4b · Gastos fijos» en Datos del proyecto; el P&G desglosa el
  indirecto en *otros indirectos* + *gastos fijos*. Motor v1.10.0.
### Verificación
- Anclas intactas en los 3 (gf=0, adic=0 por ahora): UO 11,36/11,25/6,17 mil M · margen 4,95/8,62/2,56% ·
  TIR 0,376/0,5655/−0,9936 · VPN exactos. Carve-out probado (gastos ≤ indirecto → UO y flujo sin cambio,
  dif 0; gastos > indirecto → UO baja por el exceso). AppTest 19 secciones: 0 excepciones.

## [2.29.0] — 2026-06-08
### Añadido (Ingresos · Fase 2a — ventas por tipología de producto)
- Los **ingresos** pueden modelarse **por tipología** (`tipologias`: lista con {etapa, nombre, clase,
  und, metodo, precio, area_und}). El motor (`engine.normalizar_tipologias`) deriva por etapa las ventas
  (vivienda + adicionales) y las unidades de **vivienda** (las escriturables). Si no hay tipologías,
  comportamiento anterior intacto. Motor v1.9.0.
- **Regla CG VIS / No VIS** cableada por `meta.tipo`: en **VIS/VIP** (Navarra, Torres) los parqueaderos y
  depósitos son **comunales** → no se listan como ingreso; en **No VIS** (Dominica) van **por separado**
  (clases `parqueadero`/`deposito`). El editor restringe las clases según el tipo de proyecto.
- Nuevo editor **«3b · Tipologías y producto»** en Datos del proyecto (clase, unidades, método, precio COP,
  área). La tabla de etapas pasa a definir **tiempos**; las unidades y el precio salen de tipologías.
- Los 3 proyectos sembrados con 1 tipología «apartamento» por etapa (precio COP = ventas_miles·1000/und),
  reconciliando **exacto** las ventas auditadas (dif 0): Navarra 229.682 M · Dominica 130.492 M ·
  Torres 240.823 M; TIR 0,376 / 0,5655 / −0,9936 intactas.
### Notas
- Recaudo en esta fase: la **vivienda** lleva separación+cuota inicial+subrogación; los adicionales
  (No VIS) se aproximan en la cuota inicial (recaudo diferenciado fino → Fase 2b).
- Corregido: convención de precio de tipología en **COP** (la tabla de etapas tenía el precio en miles,
  inconsistencia heredada que las tipologías ya dejan bien).
### Verificación
- Reconciliación exacta desde Supabase (dif 0 en los 3); AppTest de 19 secciones (incl. editor de
  tipologías VIS y No VIS): 0 excepciones. Sincronizado a la nube.

## [2.28.0] — 2026-06-08
### Añadido (Egresos · Fase 1 — costo directo a 28 capítulos, bottom-up)
- El **costo directo** puede modelarse como **presupuesto por capítulos** (`directos_cap`: lista
  {capitulo, valor_miles}). Si existe, el directo del P&G es la **SUMA de capítulos** (bottom-up,
  presupuesto absoluto); si no, sigue el % de ventas (top-down). Motor: nueva `engine.directos_total`;
  `_correr` ahora escala el costo vía `_costo_scale` (respeta ambos modos). Motor v1.8.0.
- **Navarra sembrado con sus 28 capítulos reales** (Preliminares→Imprevistos), tomando el mix de la
  Torre 1 escalado ×6,26 (≈6 torres para 951 und) de modo que **suman exacto el directo auditado**
  ($143.474 M = 62,47% de ventas). Anclas intactas: **UO 11,36 mil M · margen 4,95% · TIR 0,376 · VPN
  18,28 mil M · TIR socio 0,4172**.
- **Distribución costos** ahora muestra el **presupuesto por capítulo** (editable para el editor; KPIs de
  total, $/m² construido e incidencia s/ ventas) sobre la curva S. Greenfield sin presupuesto cae al % de ventas.
### Verificación
- Reconciliación exacta (suma capítulos − directo = 0); retro-compatibilidad de escenarios/sensibilidad
  (Cd±10% = ±$14.347 M); AppTest de Distribución costos en editor y consulta, Navarra y greenfield: 0 excepciones.

## [2.27.0] — 2026-06-08
### Cambiado (arquitectura de navegación en 3 capas)
- El menú lateral pasa de lista plana (19 ítems) a **navegación de 2 niveles**: primero la **capa**
  (🧭 Tablero · 🧮 Factibilidad · 📡 Seguimiento), luego la sección de esa capa. Refleja la síntesis del
  modelo maestro (APEX): **Factibilidad = el plan (ex-ante)**, **Seguimiento = lo real (ex-post)**.
  - **Tablero:** Inicio · Cockpit · Proyectos activos · Portafolio (burbujas).
  - **Factibilidad:** Datos · Urbanístico · Cronograma · Ingresos · Distribución costos · P&G · Reparto ·
    Flujo de caja · Costo de capital · Apalancamiento · Escenarios · Monte Carlo · Sensibilidad.
  - **Seguimiento:** Monitor de ejecución · Valor Ganado.
- Sin renombrar ni eliminar secciones (solo reagrupar): cero cambio de cálculo. Las hojas "K." del modelo
  maestro quedan como **motor** (engine), no como pestañas. Cada capa recuerda su última sección (key por capa).
### Verificación
- AppTest sobre las **19 secciones** navegando por su capa: 0 excepciones.

## [2.26.0] — 2026-06-08
### Añadido (capítulo K. Betas — Costo de Capital / WACC)
- Nueva sección **"Costo de capital"** (antes de Apalancamiento): reproduce el build-up CAPM de mercado
  emergente (Damodaran/CESLA) — beta del comparable US → desapalancar **con beta de deuda** → reapalancar
  a Colombia → Ke USD → **+ riesgo país (EMBI)** → paridad de inflación a COP → WACC. Inputs editables
  (editor) / solo lectura (consulta); **riesgo país EMBI manual con ayuda** en pantalla (valor de
  referencia ~2,0% / fuentes BanRep · BCRP · CESLA).
### Corregido (metodología WACC alineada a la hoja auditada)
- `engine.calcular_wacc` ahora usa la **beta de la deuda** βd=(kd−Rf)/(Rm−Rf) en el des/reapalancamiento
  (antes Hamada simple con βd=0) y **compone** el costo de deuda Kd COP=(1+tasa)(1+spread)−1 (antes sumaba).
  Reproduce la hoja k.beta: **WACC Navarra 21,54%** (antes el motor daba 24,08%, ~2,5 pp de más). Esto
  sube el VPN@WACC preliminar de los greenfield (Dominica/Torres). Navarra mantiene su VPN auditado de
  fiducia (la WACC solo descuenta los VPN preliminares). Motor v1.7.0; nuevo parámetro `kd_us` (9,335).
### Verificación
- WACC reproducido eslabón a eslabón vs la hoja (βd 0,748 · βu 1,2047 · βl₂ 1,918 · Ke COP 29,60% · WACC
  21,54%, dif <0,02 pp). AppTest de la sección en rol **editor y consulta**: 0 excepciones; sin regresión
  en las demás secciones (menú 19:19).

## [2.25.0] — 2026-06-08
### Añadido (gráficos ejecutivos de decisión)
- **Cockpit ejecutivo** (nueva sección, tras *Inicio*): resumen 1-vistazo para comité con **8 KPIs con
  semáforo** (TIR, margen, utilidad, VPN, TIR equity, UDI, crédito máx, payback) por umbral de industria
  inmobiliaria CO (TIR 🟢≥30%/🟡20–30%, margen 🟢≥5%/🟡3–5%, payback 🟢≤36m) + **2 velocímetros**
  Plotly (TIR y margen). Donde hay FCL de fiducia, TIR/VPN son auditados; integra alertas de obra de Navarra.
- **Portafolio (burbujas)** (nueva sección): mapa de valor de los 3 proyectos — X=TIR, Y=margen,
  tamaño=ventas, color=tipo (VIS/No VIS), con cuadrantes **Estrella / Crecimiento / Vigilancia / Revisar**.
  Recorta y anota outliers de TIR negativa (Torres −99,4%) para no aplastar la escala. `charts.bubbles_portafolio`.
- **Monte Carlo** (nueva sección, junto a Escenarios): simulación probabilística del margen variando
  precio (±15%) y costo directo (±10%) uniformes; **histograma** con zona de pérdida en rojo + P10/P50/P90,
  tarjetas de escenarios y **probabilidad de margen > 0**. Sliders de nº de simulaciones (200/500/1000) y
  rangos, con caché y semilla fija (reproducible). Medido Navarra 500 sims: mediana **4,7%**, P10 **−0,2%**,
  P90 **9,6%**, prob(+) **89%**. `engine.montecarlo` (motor v1.6.0, fuente única) + `charts.montecarlo_hist`.
- `charts.cockpit_gauge` (velocímetro `go.Indicator` con zonas de marca CG).
### Verificación
- Diseño con panel multi-agente (5 agentes) sobre datos reales; cada gráfico medido contra el motor.
- AppTest sobre **13 secciones** (incl. las 3 nuevas) con el candado saltado: **0 excepciones**; Cockpit,
  Monte Carlo y Portafolio renderizan contenido real (Navarra TIR 37,6% auditada; Torres −99,4% recortada).

## [2.24.0] — 2026-06-07
### Añadido (sensibilidad pro + tornado)
- **Escenarios** ahora con 2 tabs: barras pro (utilidad+margen por escenario) y **mapa de sensibilidad
  2D** (heatmap precio×costo → margen operativo; verde sano / blanco quiebre / rojo pérdida; celda
  central = base 4.95% Navarra). `charts.escenarios_barras` y `charts.heatmap_sensibilidad`.
- **Sensibilidad** ahora con **tornado** (impacto ±10% de precio y costo en la utilidad operativa,
  ordenado por sensibilidad). `charts.tornado`.
### Corregido (dato operativo en vivo)
- **`días en trámite`** del crédito Torres 2A/2B ahora se **calcula en vivo** desde
  `fecha_inicio_tramite` (no más valor fijo que se desactualiza). `navarra_data.dias_tramite_t2()`.
  Alerta a2 ajustada a "más de 4 meses" (neutra).
### Verificación
- Auditoría read-only multi-agente (22 agentes): reconciliación numérica, código, UI, datos y
  seguridad — **sin hallazgos reales**. Los 3 proyectos reconcilian exacto; 0 secretos en el repo.

## [2.23.0] — 2026-05-31
### Añadido (ejecución presupuestal real Torre 1 — EVM + waterfall)
- Cargadas las **28 partidas** del Control de Presupuesto y Ejecución Torre 1 (corte 30/04/2026) en
  `navarra_data.py` (`NAVARRA_PRESUPUESTO_T1`): base/proy_ant/ejecutado/asegurado/proy_act. Totales
  cuadran con la imagen (Base $22.910 M · Ejecutado $9.115 M · Proyectado $23.542 M; dif <0.04% por
  redondeo de la imagen).
- Nuevo **tab "💰 Ejecución presupuestal"** en el Monitor: KPIs **BAC/AC/EAC/CPI/VAC**, **waterfall**
  de variaciones (base → proyectado, capítulo a capítulo, ahorros verdes / sobrecostos rojos), barras
  base vs ejecutado y tabla por capítulo. `charts.variaciones_waterfall` y `charts.presupuesto_barras`.
### Cambiado (marca)
- **Eliminada toda referencia a "APEX ARCHITECT"** (portada, captions y comentarios internos del
  motor). La herramienta queda como "Evaluación Financiera de Proyectos · CG Constructora".

## [2.22.0] — 2026-05-31
### Añadido (Monitor de Ejecución — seguimiento operativo por torre · 1ª entrega)
- Nueva sección **🏗️ Monitor de ejecución** y módulo **`navarra_data.py`** con datos reales de los
  Comités de Gerencia (Feb–Abr 2026). Capa **operativa** (por torre, 4 etapas/970 und) **separada** del
  modelo financiero auditado (3 etapas/951 und/TIR 37.6%) — no lo altera.
- **Panel de alertas** reutilizable (`render_alertas`): 5 alertas (4 activas) con severidad crítica/
  importante/info, en marca CG.
- **Tab Avance de obra:** curva **real vs programado** con los 3 cortes reales (Feb 7.25% · Mar 31.5%
  · Abr 42.01%), avance Bancolombia 59.57%, SPI, y tabla de cortes.
- **Tab Crédito constructor:** estado por torre (T1 autorizado $2.000 M · T2A/2B 136+ días en trámite,
  crédito puente $1.700 M) + tabla de los 7 trámites pendientes (fecha crítica 16-jun-2026).
- **Tab Variaciones:** 7 sobrecostos y 7 ahorros con impacto y meses.
- **Proyectos activos:** semáforo de estado por etapa (4 torres) + alertas activas de Navarra.
- Otros proyectos muestran "sin datos operativos aún". Pendiente (2ª tanda): waterfall de variaciones,
  EVM con presupuesto real por partida, comparativo Real vs Factibilidad (slides 7-12 por transcribir).

## [2.21.0] — 2026-05-31
### Añadido (Valor Ganado / EVM — Curva S, estándar PMI)
- Nueva sección **📈 Valor Ganado (EVM)** y motor **`engine/evm.py`**: a partir del costo directo
  planeado (curva Gauss) y del **% avance real + costo real por etapa**, calcula las **3 curvas S**
  (PV planeado · EV ganado · AC costo real), índices **CPI** (costo) y **SPI** (cronograma),
  varianzas CV/SV y proyección **EAC/ETC/VAC**.
- **Inputs nuevos** por etapa en 📝 Datos del proyecto → ③ Etapas: **"Avance real %"** (0–100) y
  **"Costo real (miles)"**. Si están vacíos, la sección invita a llenarlos (no rompe nada).
- KPIs con semáforo (CPI/SPI verde≥1, rojo<1), **EAC** vs presupuesto, y un **resumen en palabras**
  ("la obra va al X%, sobre/bajo presupuesto, adelantada/atrasada…").
- `charts.valor_ganado_s`: PV (teal), EV (verde), AC (rojo punteado), EAC (ámbar), línea "hoy" en la
  fecha de corte. Eje en fechas reales (anclado al inicio de obra). Motor v1.5.0.
### Nota
- Pedido prioritario del usuario. Navarra (en ejecución, obra desde dic‑2025) es el caso ideal de EVM.
  El mes de corte se calcula desde el inicio real de obra hasta hoy.

## [2.20.0] — 2026-05-31
### Cambiado (todos los gráficos mensuales en fechas reales)
- **Distribución costos** (curva S), **Ingresos** (recaudo apilado) y el mensual de **Apalancamiento**
  ahora usan **fechas reales** en el eje X (antes "mes 1,2,3…"). Curva S anclada al **inicio real de
  obra** (dic‑2025 en Navarra); recaudo y caja/crédito anclados al inicio de ventas, topados a 2030.
- **Flujo de caja — "caja de aquí en adelante":** para proyectos en ejecución (caso Navarra, arrancó
  2022) hay un **toggle** que recorta el eje desde el mes actual (may‑2026), activado por defecto.
  Así se ve solo la caja futura, no el histórico.
- `charts`: `curva_obra_s`/`recaudo_stacked` admiten `fecha_base` (+`tope_anio`); `flujo_caja_waterfall`
  admite `desde` (recorta el inicio). Verificado en los 3 proyectos.

## [2.19.0] — 2026-05-31
### Cambiado (flujo de caja en fechas reales)
- **El flujo de caja ahora usa FECHAS reales** en el eje X (antes "mes 1…90", confuso). Se ancla a
  la fecha del mes 0 del proyecto (inicio de ventas de la etapa raíz) y se **proyecta hasta dic‑2030**.
  Marcas cada 6 meses, formato "Mmm AAAA".
- Usa la serie del **waterfall apalancado** (`apalancamiento.operativo/acumulado/saldo_credito`) — la
  misma calibrada — en vez del `flujo_caja` legacy; KPIs de la sección alineados (TIR proyecto,
  crédito máx, necesidad de caja, intereses).
- `charts.flujo_caja_waterfall` admite `fecha_base` y `tope_anio`; rangos verificados: Navarra
  2022‑08→2030‑12, Dominica/Torres 2026‑01→2030‑12.

## [2.18.0] — 2026-05-31
### Conectado (gráficos pro a sus secciones — estable y verificado)
- **Flujo de caja** → waterfall (verde/rojo + caja acumulada + saldo de crédito + mes de exposición máx).
- **Distribución costos** → curva S (campana de costo directo + avance % en eje derecho).
- **Ingresos** → recaudo apilado por componente.
- **Cronograma** → **Gantt** por etapa (barra de ventas + barra de construcción) con marcas de equilibrio/fin.
- Integración hecha **una sección a la vez**, con `parse` tras cada edición y `AppTest` + render de las
  4 figuras con los 3 proyectos reales (0 excepciones). 5 usos de `charts` en `app.py`.
### Corregido (incidente 2.17.x)
- v2.17.0 subió `app.py` **corrupto** (`import charts` duplicado + línea truncada → `SyntaxError`).
  v2.17.1 lo restauró pero dejó `_charts.registrar_template()` **sin** su `import` → `NameError`
  (app en vivo caída). v2.17.3 (hotfix) agregó el import y restauró producción.
- *Lección reforzada:* una edición → `parse` → siguiente; `AppTest` **antes** de cada push; nunca
  batches grandes sin verificar; sin emojis en `python -c` (rompen cp1252 en Windows).

## [2.17.0] — 2026-05-31
### Añadido (módulo charts.py — gráficos financieros de nivel institucional)
- Nuevo módulo **`charts.py`** con gráficos estándar de la industria, vestidos con la **marca CG real**
  (teal #004854 + ámbar #F09C00), no colores genéricos. Adaptados a las estructuras reales del motor
  (listas mensuales). Funciones: `flujo_caja_waterfall`, `curva_obra_s`, `recaudo_stacked`,
  `tornado`, `escenarios_grouped`, `gantt_etapas`.
- **Flujo de caja** → waterfall: barras 🟢/🔴 según caja +/−, caja acumulada, **saldo de crédito
  constructor** (del waterfall apalancado) y anotación del **mes de exposición máxima**.
- **Distribución costos** → **curva S** (campana de costo directo + avance acumulado en %, eje
  derecho) con anotación del pico de obra.
- **Ingresos** → recaudo apilado por componente (separación/cuota inicial/subrogación) más limpio.
- **Cronograma** → **Gantt** por etapa (barra de ventas + barra de construcción) con marcas de
  equilibrio y fin de ventas.
### Nota
- Adoptado del prompt de refactor profesional, en modo **incremental** y conservando: motor auditado,
  candado de acceso, persistencia Supabase y navegación por menú lateral. NO se migró a `pages/`
  nativo (rompería el candado/menú). Bloque "eliminar sliders" ya estaba cumplido (0 sliders).

## [2.14.0] — 2026-05-30
### Añadido (Fase 2 — persistencia compartida en Supabase)
- **Capa `storage.py`:** lee/escribe los proyectos en **Supabase** si hay `SUPABASE_URL` +
  `SUPABASE_KEY` en `st.secrets`; si no, usa los archivos JSON locales (fallback). Ante cualquier
  error de red, cae al respaldo local → la app nunca se rompe.
- **Tabla `public.proyectos`** (slug · nombre · es_real · data jsonb · updated_at · updated_by) con
  **RLS activo y sin políticas públicas**: solo la clave secreta (servidor) accede; la clave pública
  no puede leer los datos reales.
- **Botón "☁️ Guardar en la nube"** (solo editor, solo con Supabase): persiste el proyecto para que
  **el equipo lo vea** al recargar ("uno ingresa, todos ven"). Refresca el consolidado al guardar.
- El pie indica el origen de datos: **☁️ nube (compartido)** o **💾 local**.
- `app.py` ahora importa `listar/cargar/es_real/guardar` desde `storage`. Dependencia: `supabase`.
- Script `execution/migrar_supabase.py` (fuera del repo) para sembrar la BD desde los JSON locales.

## [2.13.0] — 2026-05-30
### Añadido (Fase 1 — control de acceso)
- **Candado de equipo / editor.** Con `CLAVE_EQUIPO` en `st.secrets`, la app exige clave para VER
  el tablero (rol *viewer*, solo lectura). Con `CLAVE_EDITOR` se habilita el **modo editor** (único
  que puede ingresar/editar: "📝 Datos del proyecto", crear proyecto y descargar respaldo).
- **Sin sorpresas:** si NO hay `CLAVE_EQUIPO` (p. ej. en local), la app queda **abierta** con rol
  editor — subir el código NO bloquea a nadie hasta definir las claves en Streamlit Cloud.
- Panel lateral: indicador de rol, campo para **elevar a editor** y **cerrar sesión**.
- Plantilla `/.streamlit/secrets.toml.example` (claves de acceso + placeholder Supabase).
### Pendiente (Fase 2)
- Persistencia compartida en **Supabase** ("uno ingresa, todos ven"): crear el proyecto Supabase y
  cargar `SUPABASE_URL`/`SUPABASE_KEY` en secrets.

## [2.12.0] — 2026-05-30
### Cambiado (formato de cifras)
- **Cifras grandes en miles de millones** (`mil M`): `fmt_mm` ahora es adaptativo — ≥ mil millones
  COP muestra "$229.7 mil M"; cifras menores siguen en "$X M". Aplica a las tarjetas KPI y a la
  **tabla del Resumen financiero del portafolio** (columnas Ventas / Utilidad oper. / Crédito máx),
  para lectura consistente y clara. Separador de miles con punto (formato COP).

## [2.11.0] — 2026-05-30
### Validado EXACTO (TIR/VPN de Navarra contra el modelo aprobado)
- **FCL auditado de fiducia:** el motor acepta `par["fiducia"]` con el Flujo de Caja Libre anual
  real (hoja `FC LOTE CG -V2K`: Aportes → Devoluciones → Retornos → FCL). Cuando existe, la TIR/VPN
  del **proyecto** y del **socio** se calculan sobre esa serie a la TIO, en vez de la aproximación
  mensual. Campo `apalancamiento.fiducia_real = True`.
- **Navarra reproduce el Excel al peso (vía la app):** TIR proyecto **37.5975%** (=D113), VPN
  **$18.280.688** (=D114) @ TIO 15%; **TIR socio CG 41.7189%** (=D120), VPN socio **$9.885.116**
  (=D121); Σ FCL proyecto **$46.271.073** (=real). Verificado con `execution/validar_fcl_navarra.py`.
- **UI:** con datos de fiducia, los KPIs muestran TIR proyecto · VPN @TIO · TIR socio CG en verde
  **"auditado"**; la sección Apalancamiento añade la tabla **FCL año a año** (Proyecto / Socio CG).
- **Estado Navarra:** P&G reconciliado, calendario real, **TIR/VPN auditados exactos**. Crédito
  constructor mensual queda en 0.87× (aprox., no afecta la TIR/VPN auditada). **Navarra: cerrado.**

## [2.10.0] — 2026-05-30
### Calibrado (retorno al desarrollador y tasa de descuento — Navarra, medido)
- **Flujo de retorno al desarrollador** (criterio CG): TIR/VPN se calculan sobre los **REINTEGROS
  = honorarios + utilidad operativa + utilidad lote** (no sobre la utilidad operativa sola). Los
  honorarios y la utilidad del lote, que el flujo de obra resta como costo, **retornan** al
  desarrollador y se reincorporan a la curva de retorno. **Medido: $47.951 M = el real $47.949 M
  (1.00×).**
- **Tasa de descuento = TIO 15% EA** (tasa de oportunidad, fuente `PREFACTIBILIDAD.!D111`), NO el
  WACC Damodaran (~24%) que aplastaba el VPN. Configurable por `financiero.tio`.
- **Estado medido (Navarra):** crédito máx 0.87×, reintegros 1.00× (montos OK). **VPN y TIR del
  proyecto siguen bajos** (VPN −$1.8 M vs +$18.3 M; TIR 14% vs 37.6%) por un tema de **timing**: el
  lote se modela como salida íntegra en t0 (ago-2022) y se descuenta 8 años, mientras CG lo trata
  como **aporte con devolución + beneficio** (hoja `FC LOTE CG -V2K`: APORTES → RETORNOS → FCL). Ese
  detalle de fiducia no está completo en el dossier (celdas sin recalcular) — es el mismo punto que
  el propio APEX deja como "Falta calcular".
- **Conclusión:** crédito constructor **confiable**; **VPN/TIR del proyecto quedan PRELIMINARES**
  (no usar para decisión) — la TIR de decisión sigue siendo la **referencia del modelo aprobado**.

## [2.9.0] — 2026-05-30
### Calibrado PARCIAL (waterfall de crédito — Navarra, medido contra el Excel)
- **Crédito constructor:** ahora **desembolsa cobertura% (80%) del costo de obra mensual** dentro de
  la **ventana de construcción IC..FC** (antes desembolsaba 100% hasta el cupo y tomaba indirectos
  desde la preventa → adelantaba y sobredimensionaba el crédito). Indirectos se asignan a la obra.
- **Otros ingresos** (comercio + parqueaderos + recuperaciones + devolución IVA) entran a la caja
  proporcionales al recaudo (estaban en el P&G, faltaban en el flujo).
- **Resultado MEDIDO (Navarra) vs Excel real:** crédito máx **$49.292 M = 0.87×** ($56.827 M real;
  venía de 2.02× → **calibrado**). Pero el resto **NO calibra todavía**: crédito prom 1.43×,
  intereses 1.33×, **VPN proyecto −$24.854 M (real +$18.281 M)**, **TIR proyecto 3.5% (real 38%)**,
  **TIR equity −3.3% (real 42%)**.
- **Causa raíz identificada:** el flujo del proyecto resta los **honorarios** ($23.283 M) como costo,
  pero en el modelo CG son un **retorno al desarrollador** (Total Reintegros = honorarios + UO +
  utilidad lote = $48.080 M). Al tratarlos como costo, el flujo de retorno queda casi nulo → VPN/TIR
  rotos. Pendiente: modelar reintegros como retorno (próximo paso de calibración).
- **Estado:** crédito máx confiable; **VPN/TIR siguen PRELIMINARES** (no usar para decisión).
- *Nota de integridad:* la primera redacción de esta entrada traía cifras de VPN/TIR **fabricadas**
  (no medidas); se reemplazaron por las medidas reales.

## [2.8.0] — 2026-05-30
### Cambiado (waterfall de crédito — mecánica corregida, calibración EN CURSO)
- **Crédito constructor reespecificado** según la hoja `CALCULO COSTOS FINANCIEROS` de CG: el
  crédito **desembolsa el costo de obra (directos+indirectos)** hasta un **cupo = cobertura% ×
  (D+I)** y se **amortiza con las subrogaciones**; el interés corre sobre el saldo insoluto.
  (Antes desembolsaba solo 80% de los directos → subestimaba/desfasaba el saldo.)
- **Estado de la calibración (Navarra) — NO validada todavía:** la mecánica es ahora la correcta,
  pero las cifras aún sobreestiman: crédito máx **$81.995 M (1.44×** del real $56.827 M; venía de
  2.02×), crédito prom 1.32×, **intereses 2.10×**, **TIR equity −26 %** (debería ser ~+42 %). Falta
  iterar: base financiable real ($163.449 M, no D+I=$177.727 M), inclusión de otros ingresos en el
  flujo, y timing de subrogaciones/lote.
### Corregido (cableado de KPIs)
- La app mostraba el **`flujo_caja` legacy** (crédito crudo, sin calendario real) en vez del
  **waterfall**. Ahora el crédito máx, VPN, intereses y TIR de los KPIs y del consolidado salen de
  `apalancamiento`. (El VPN del portafolio sigue saliendo negativo → parte de la calibración
  pendiente, NO usar para decisión aún.)
- **Consolidado alineado por calendario absoluto** (epoch ene-2022): el pico de crédito del
  portafolio ya no suma picos de meses distintos.
### Motor v1.11.0
- `flujo_apalancado` expone `credito_prom`, `tir_apalancada_ref`; cupo = cobertura×(D+I).
### Nota
- La versión anterior de esta entrada afirmaba una validación exacta que era **incorrecta**; se
  corrigió con las cifras reales medidas. Hasta cerrar la calibración, crédito/VPN/TIR son
  **preliminares**.

## [2.7.0] — 2026-05-30
### Añadido (motor — calendario real por etapa)
- `engine/portafolio.py`: nueva opción **`ic_offset`** por etapa (meses desde el Inicio de Ventas
  hasta el Inicio de Obra). Permite fijar la **fecha real de inicio de construcción** en proyectos
  en ejecución donde la pre-venta antecede a la obra por años (p. ej. Navarra: Etapa 1 vendida
  2022-23, construida 2025-26). Por defecto (sin `ic_offset`) se mantiene la lógica anterior
  (obra arranca tras el Punto de Equilibrio). Combinable con `fecha_inicio` y `escrituracion`
  por etapa para modelar el calendario fiel de un proyecto en curso.

## [2.6.0] — 2026-05-30
### Añadido (consolidado del portafolio)
- En **🏢 Proyectos activos**, el encabezado muestra los **KPIs consolidados** del portafolio
  (suma de los proyectos listados): **Ventas totales · Utilidad operativa · UDI** (sumas,
  reconciliadas con lo real), **TIR apalancada** (referencia ponderada por ventas), **VPN @WACC**
  (suma) y **Crédito máx** (pico de la curva de crédito *sumada*, no la suma de picos).
- **Tabla financiera del portafolio** con ventas/utilidad/margen/crédito por proyecto + fila TOTAL.
- Consolidación correcta por tipo de métrica (aditivas se suman; el crédito usa el pico del saldo
  consolidado; la TIR no se promedia ingenuamente).
### Nota (honestidad de cifras)
- **Ventas/UO/UDI** están reconciliadas con las prefactibilidades reales (verde). **VPN y crédito
  máx** provienen del módulo de flujo/apalancamiento **en calibración** → se marcan **preliminar**
  (el crédito tiende a sobreestimarse porque la subrogación llega tarde). Próximo paso sugerido:
  calibrar el waterfall de crédito antes de usar esas cifras para decisión.

## [2.5.0] — 2026-05-30
### Añadido (datos reales privados)
- La app puede cargar **proyectos privados** desde `proyectos_privados/` (en `.gitignore`, no se
  publica). Tienen prioridad sobre los ilustrativos del mismo proyecto (que se ocultan localmente);
  el deploy público —sin esa carpeta— sigue mostrando solo cifras ilustrativas.
- Sello en el encabezado: **🔒 datos reales** vs *cifras ilustrativas*.
### Datos
- Cargadas las prefactibilidades **reales** de Navarra, Dominica y Torres de Campiñas (extraídas de
  los Excel con `execution/extraer_prefactibilidad.py` + `cargar_reales.py`). El motor **reconcilia
  exacto la utilidad operativa real** de los tres (otros ingresos —comercio/parqueaderos/IVA/
  recuperaciones— absorbidos para cerrar el P&G). Los datos reales NO están en el repo público.

## [2.4.0] — 2026-05-30
### Añadido (ritmo de ventas y entregas — paridad APEX R.ventas)
- **Cronograma** ahora muestra, además de los hitos: (1) tabla **Ritmo de ventas y entregas**
  (estilo hoja `R.ventas` de APEX — No · Etapa · Und · Ventas Cant/Frec · Entregas Cant/Frec) y
  (2) **Proyección de ventas y entregas**: unidades vendidas por mes por etapa (barras apiladas),
  entregas/mes y la **curva de absorción** acumulada. Es la vista de "lo que mueve los números".
- **Ritmo de entregas** modelado en el motor (`engine/ingresos.py`): las entregas se escalonan
  según *Cantidad/Frecuencia* desde el mes de escrituración (antes todo en un solo mes). Las
  **subrogaciones** (crédito hipotecario, ~70% del precio) ahora se reparten a medida que se
  entrega cada unidad → flujo de caja y amortización del crédito más realistas. Emparejamiento
  **venta → entrega en FIFO**; la cuota inicial corre de la venta a la entrega de esa unidad.
- Editor de etapas (📝 Datos del proyecto): nuevas columnas **Entr/mes** y **Frec ent (m)**.
### Nota
- Reconciliación verificada: recaudo total = valor de contrato en los 3 proyectos. El ritmo de
  entregas por defecto entrega todo en la escrituración (comportamiento previo) si no se define.

## [2.3.0] — 2026-05-30
### Cambiado (orden lógico del menú)
- **Reordenado el menú** al flujo de evaluación del modelo. Nuevo orden:
  Inicio · Proyectos activos · Datos del proyecto · **Urbanístico** · Cronograma · Ingresos ·
  Distribución costos · P&G · Reparto · Flujo de caja · Apalancamiento · Escenarios · Sensibilidad.
- **Urbanístico pasa a primero** entre los resultados: define áreas e índices, la base física
  de la que derivan los demás análisis. Luego Cronograma (tiempo) → Ingresos (recaudo) →
  Costos → P&G/Reparto (resultado) → Flujo/Apalancamiento (financiación) → Escenarios/Sensibilidad.
- La guía de módulos de la portada se reagrupa acorde (Portafolio · Definición · Resultados ·
  Flujo & Análisis).

## [2.2.0] — 2026-05-30
### Cambiado (orden lógico / UX)
- **Inicio = portada de bienvenida** (ya no tablero del proyecto): presenta la app, "Cómo
  empezar" (3 pasos) y la guía de **módulos** del modelo. Se retira el cronograma del portafolio
  y la tarjetas/caption del proyecto activo, que **duplicaban** la información de "Proyectos
  activos". La portada ya no muestra datos de un proyecto concreto.
- Los **KPIs y el encabezado del proyecto** (ventas, utilidad, TIR, VPN, crédito) y los botones
  de **exportación** solo aparecen **dentro de un proyecto** (cualquier sección distinta de
  Inicio), no en la portada — separa "anunciar" (Inicio) de "trabajar el proyecto".
- "Proyectos activos" queda como **único** lugar donde se despliega el portafolio (Navarra ·
  Dominica · Torres de Campiñas). Elimina la repetición Inicio ↔ Proyectos activos.

## [2.1.0] — 2026-05-29
### Añadido
- Sección **🏢 Proyectos activos** (portafolio CG): tarjetas + tabla resumen de los proyectos,
  con botón **Abrir** para cargar cada uno. Estilo de la hoja "Proyectos" de APEX.
- Proyectos activos de CG (plantillas): **Navarra Apartamentos · Dominica · Torres de Campiñas**
  (estructura y cifras ilustrativas; los datos reales se ingresan en plataforma).
- Selector de proyecto muestra el **nombre del proyecto** (no el nombre de archivo).

## [2.0.0] — 2026-05-29
### Cambiado (mayor — navegación)
- **Navegación por menú lateral (estilo APEX)** en vez de pestañas: menú vertical con iconos
  (Inicio · Datos · P&G · Reparto · Distribución · Flujo · Apalancamiento · Cronograma ·
  Ingresos · Escenarios · Sensibilidad · Urbanístico). Elimina el scroll horizontal.
- Nuevo **tablero de Inicio** ("Evaluación Financiera de Proyectos") con tarjetas agrupadas
  (Datos · Resultados · Flujo & Financiación · Análisis) + cronograma del portafolio — réplica
  del INICIO de APEX.
- Header + KPIs visibles en todas las secciones.
- Dependencia: `streamlit-option-menu`.

## [1.9.1] — 2026-05-29
### Corregido
- "Unidades totales" en Datos generales ya es un **conteo en vivo** (suma de las unidades por
  etapa) con guía clara. Las unidades se ajustan en la columna *Unidades* de la tabla de etapas.

## [1.9.0] — 2026-05-29
### Cambiado (importante)
- **Toda la data se ingresa EN la plataforma** — se elimina la importación de archivos
  (Excel/JSON) como input (distorsionaba). Se conserva solo la **descarga de respaldo** (.json).
- Nueva **primera pestaña "📝 Datos del proyecto"** con 6 secciones plegables: Datos generales,
  Áreas y lote, Etapas/producto/ventas (tabla), Costos, Recaudo, Financiero (avanzado).
- **Precio de venta elegible por etapa**: $/m² × área **o** $/und (columna "Método precio").
- Sidebar: selector de proyecto + **"➕ Nuevo proyecto"** (en blanco) + descarga de respaldo.
  Se retiran cargador de archivos y sliders sueltos (ahora en la pestaña de datos).

## [1.8.0] — 2026-05-29
### Añadido
- **Editor de portafolio en la app** (pestaña ⚙️): tabla editable (`st.data_editor`) para
  agregar/editar/eliminar etapas con todos los parámetros APEX (unidades, ventas, ritmo,
  % equilibrio, sucesora, desfase, obra, escrituración) + fecha de inicio de la etapa raíz.
  La estructura del modelo es ahora autoservicio — sin editar JSON a mano.
### Cambiado
- Se retiran los inputs de ventas por etapa del sidebar (ahora se editan en el editor).

## [1.7.0] — 2026-05-29
### Cambiado
- **Crédito constructor calibrado**: ahora financia la **cobertura (~80%) del costo de obra**
  (no todos los déficits) y se **amortiza con las subrogaciones**; el interés corre sobre el
  saldo del crédito. Los aportes (equity) cubren el resto. Resultado: crédito máx e intereses
  realistas (intereses < utilidad), TIR equity calculable. Corrige el sobredimensionamiento
  del crédito/intereses de v1.5–1.6.
### Nota
- `G.Financieros` y el valor financiable del CC están vacíos/"Falta calcular" en el propio APEX;
  la cobertura del costo de obra es la mecánica estándar de crédito constructor aplicada aquí.

## [1.6.0] — 2026-05-29
### Añadido
- **Ensamblaje (Fase 5)**: vista de **flujo de caja consolidado anual** del portafolio (curva J),
  panel de **indicadores económicos** (TIR proyecto, VPN @WACC, WACC, payback) y detalle mensual
  de caja acumulada + saldo de crédito en la pestaña Apalancamiento.
- **Indicadores del Estado de Resultados** en P&G: margen de contribución, margen sobre costo,
  incidencias (directos / indirectos+lote).

## [1.5.0] — 2026-05-29
### Añadido
- **Apalancamiento APEX (Fase 4)** (`engine/apalancamiento.py`): ensambla el flujo operativo
  consolidado del portafolio (recaudo F2 − costos F3 por etapa, directos por curva Gauss sobre
  IC..FC) y aplica el waterfall de crédito — crédito constructor revolvente (tope = monto% ×
  valor financiable), activado por avance de obra y amortizado con subrogaciones; aportes cubren
  el residual. Indicadores: crédito máx, necesidad de caja, TIR proyecto.
- Nueva pestaña **🏦 Apalancamiento**: flujo operativo + saldo de crédito + indicadores.
### Nota
- Intereses y TIR apalancada son preliminares (la calibración fina requiere el cronograma de
  amortización de fiducia); la estructura del waterfall queda completa.

## [1.4.0] — 2026-05-29
### Añadido
- **Kernels de costos APEX (Fase 3)**: curva **Gauss** de avance de obra (k.Directo) en el
  motor (`engine/curvas.py`), usada para distribuir el costo directo. Aclaración: `k.Beta`
  es el kernel WACC/CAPM (ya en el motor), no la curva de costos.
- **Hitos de construcción IC/FC** (Inicio/Fin de Construcción) en el motor de portafolio
  y en la pestaña Cronograma — la obra arranca tras el Punto de Equilibrio y dura `dur_obra`.
### Cambiado
- Distribución de costos ahora usa la curva Gauss (antes PERT), fiel a APEX.

## [1.3.0] — 2026-05-29
### Añadido
- **Kernel de ingresos APEX (Fase 2)** integrado: recaudo mensual del portafolio por
  componente — separación diferida, cuota inicial (venta→escrituración) y subrogación
  (a la entrega). Reconcilia con el valor de contrato.
- Nueva pestaña **💰 Ingresos**: recaudo mensual apilado por componente + totales.

## [1.2.0] — 2026-05-29
### Añadido
- **Estructura de portafolio APEX (Fase 1)**: motor de hitos (`engine/portafolio.py`)
  integrado al modelo y a la app. Etapas secuenciales — cada etapa abre ventas cuando su
  sucesora alcanza el Punto de Equilibrio (PE = INT(unidades×%eq)+1, %eq por etapa).
- Nueva pestaña **🗓️ Cronograma**: tabla y línea de tiempo de hitos (Inicio Ventas /
  Punto de Equilibrio / Fin Ventas) por etapa.
- Esquema de proyecto ampliado con ritmo de ventas, %eq, sucesora y desfase.
- Validado 5/5 etapas contra APEX 20250701.xlsm.

## [1.1.0] — 2026-05-28
### Cambiado
- **Rediseño con identidad de marca CG**: logo en encabezado y barra lateral, favicon,
  paleta corporativa (teal #004854 + ámbar #F09C00), tipografía Inter.
- Tarjetas KPI con borde/sombra (no planas), barra de marca teal→ámbar.
- Gráficos Plotly con plantilla CG (paleta, ejes limpios).
- Se oculta el branding de Streamlit (menú, footer) para un look propio.
### Añadido
- Cargador de proyecto privado (.json) — datos confidenciales solo en sesión.
- Descarga de parámetros editados (.json) al equipo.
### Corregido
- Llaves de "ventas por etapa" por-proyecto (evita que valores se "peguen" al cambiar).

## [1.0.0] — 2026-05-28
### Añadido
- Motor financiero (`engine/`): P&G, reparto desarrollador/socio, distribución de costos
  por curva PERT + escalación Materiales/MO, flujo de caja del proyecto, escenarios,
  sensibilidades, índices urbanísticos y economía unitaria. Fuente única de verdad (Python).
- App Streamlit multi-proyecto con KPIs, gráficos interactivos (Plotly) y export a Excel.
- Proyecto de ejemplo (`proyectos/ejemplo.json`) con cifras ilustrativas.
- Enfoque híbrido: TIR apalancada de referencia como parámetro de decisión.
