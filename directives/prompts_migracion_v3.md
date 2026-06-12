# ALEPH — Biblioteca de prompts de migración (v3 · jun-2026)

> Referencia de ejecución de la migración Streamlit → ALEPH (3 capas). La constitución
> gobernante vive en `CLAUDE.md` (§ALEPH). Aquí están los prompts por fase (Parte B) y la
> guía de ejecución en VS Code (Parte C), tal como los entregó Fable 5. **Una fase por sesión,
> en orden estricto. Plan primero. El snapshot dorado es sagrado.**

---

## PARTE B · Prompts por fase (uno por sesión, en orden estricto)

### PROMPT 1 — Auditoría y plano de migración
Lee la Constitución v3 en CLAUDE.md. Sesión de SOLO LECTURA (no modifiques código de producción):
1. Inventaria el repositorio actual: páginas Streamlit, funciones de cálculo, acceso a Supabase, estructura del JSON de proyecto.
2. Mapea cada cálculo financiero (WACC, curva S, flujos, crédito constructor, indicadores, EVM) a su archivo/función actual. Marca cuáles están acoplados a la UI.
3. Propón la estructura exacta del monorepo (/engine /api /web /app_streamlit) y el plan de extracción función por función, ordenado por dependencias.
4. Documenta el esquema actual de Supabase (list_tables) y el plan de migración al modelo de la constitución (projects/scenarios/results).
5. Define el contrato inicial de la API (endpoints, request/response) para las vistas de lectura: portafolio, proyecto, escenario, resultados, checks.
Entrega: `directives/plan_migracion.md` con todo lo anterior y riesgos.

### PROMPT 2 — Snapshot dorado + monorepo
Fase 1 según CLAUDE.md y directives/plan_migracion.md. Plan primero.
1. SNAPSHOT DORADO antes de mover nada: script que ejecute el cálculo actual (tal como está, acoplado) con los datos reales de Navarra y persista TODOS los resultados (indicadores + flujo mensual completo + P&G + crédito) en `tests/golden/navarra_snapshot.json`. Genera también snapshots de Dominica y Torres de Campiñas.
2. Reestructura el repositorio al monorepo de la constitución SIN romper la app Streamlit (debe seguir corriendo y desplegando igual).
3. Crea /engine con esqueleto del paquete `aleph_engine` (pyproject, modelos Pydantic del proyecto/supuestos basados en el JSON actual, carpeta de tests con el harness que compara contra los snapshots).
4. Scripts de desarrollo: `dev.sh` (levanta streamlit local), `test.sh`, `deploy_streamlit.sh` (build ACR con tag = SHA + container set + restart + verificación de versión).
Criterio de salida: la app Streamlit sigue idéntica en producción; los snapshots existen y el harness los lee; yo puedo correr test.sh y dev.sh sin ayuda.

### PROMPT 3 — Extracción del motor
Fase 2: extraer TODA la lógica financiera a `aleph_engine`, en el orden del plan de migración. Para cada bloque (calendario/curva S → ventas/recaudo/fiducia → costos → crédito constructor → flujos → P&G → WACC → indicadores → EVM → escenarios/sensibilidad/Monte Carlo):
1. Extrae a /engine con modelos Pydantic tipados (extraer tal cual la lógica — NO reescribir fórmulas de memoria).
2. Tests unitarios + el harness dorado debe seguir en verde tras cada bloque (tolerancia 0.1%).
3. Refactoriza la página Streamlit correspondiente para consumir el motor.
4. Commit por bloque.
Además: crea `aleph_engine/metrics.py` (diccionario de indicadores con etiquetas de base según la constitución) y `aleph_engine/checks.py` (checks de cuadre). Al final, ninguna fórmula financiera debe vivir en /app_streamlit.
Criterio de salida: harness dorado verde para los 3 proyectos; Streamlit funciona idéntico en producción consumiendo el motor; cobertura de tests del motor reportada.

### PROMPT 4 — API FastAPI
Fase 3: construir /api sobre el motor y Supabase. Plan primero.
1. Migración de datos: esquema projects/scenarios según la constitución; importar el JSON actual de cada proyecto como escenario v1 approved. El Streamlit sigue leyendo/escribiendo como hoy (compatibilidad por vista o adaptador — propón la opción más segura).
2. Endpoints v1 (lectura): GET /portfolio (resumen + pipeline), GET /projects/{id}, GET /projects/{id}/scenarios, GET /scenarios/{id}/results (indicadores con etiquetas + flujo + P&G + crédito + checks), GET /scenarios/{id}/sensitivity. POST /scenarios/{id}/run para recalcular.
3. Auth: validar JWT de Entra ID (mismo tenant del App Service actual); roles admin/gerencia desde claims o tabla de usuarios.
4. OpenAPI documentado; tests de integración; Dockerfile; `deploy_api.sh` (ACR tag=SHA → App Service nuevo cg-aleph-api); health check /version.
Criterio de salida: puedo abrir /docs de la API desplegada, autenticarme y obtener los resultados de Navarra idénticos al snapshot dorado.

### PROMPT 5 — Fundaciones de la UI profesional
Fase 4: crear /web (Next.js App Router + TypeScript + Tailwind + shadcn/ui). Esta fase define el ADN visual de Aleph — nivel Linear/Mercury. Plan y propuesta visual primero (descríbeme tipografía, espaciado, paleta exacta desde el logo CG, y muéstrame el código de los design tokens antes de construir páginas).
1. Design tokens + tema dark/light + Inter con tabular-nums + `fmt_cop()`/`fmt_pct()` es-CO en una librería compartida del web.
2. Componentes canon: KpiCard (valor, etiqueta de base, delta, estado semáforo), PhaseBadge, ChecksBadge, DataTable densa, ChartCard, Skeletons. Página /design-system que los exhiba todos (mi referencia visual).
3. Layout: sidebar colapsable (grupos PROYECTO/PORTAFOLIO), breadcrumb, header permanente (Proyecto · Fase · Escenario · Corte), command palette (cmd+k) para saltar entre proyectos/módulos.
4. Auth con NextAuth + Entra ID (mismo tenant); roles en sesión.
5. Cliente de API tipado generado desde el OpenAPI.
6. Deploy en Vercel (o Azure SWA si lo prefiero — pregúntame) con preview deployments por commit.
Criterio de salida: entro con mi cuenta CG a la URL nueva, veo el layout con datos reales mínimos (lista de proyectos) y la página /design-system; dark/light funcionan; se ve nivel producto, no prototipo.

### PROMPT 6 — Dashboards de lectura (el estreno con gerencia)
Fase 5: las 4 vistas de lectura, consumiendo la API:
1. PORTAFOLIO (home): KPIs consolidados, pipeline por fase (tarjetas por proyecto con TIR etiquetada, VPN, ventas, unidades, fase), exposición de caja agregada mes a mes (área apilada por proyecto), alertas activas de todos los proyectos.
2. TABLERO DE PROYECTO: KPIs con semáforos por umbral, gauges o barras de umbral, alertas con criticidad/fuente/responsable/fecha, mini flujo acumulado, estado de checks.
3. FLUJO DE CAJA: doble pestaña proyecto/inversionista, barras mensuales + caja acumulada + saldo de crédito, anotación de exposición máxima, toggle "desde hoy", tabla mensual exportable.
4. RIESGO: escenarios base/optimista/pesimista comparados, tornado, sensibilidad 2D (heatmap) — datos del endpoint de sensibilidad.
Paridad visual de datos contra Streamlit verificada para Navarra (mismos números, mejores ojos). Banner en Streamlit en estas 4 vistas: "Esta vista ya está disponible en Aleph → enlace".
Criterio de salida: demo completa con los 3 proyectos reales; gerencia puede usar SOLO la UI nueva para consultar.

### PROMPT 7 — Vistas financieras profundas
Fase 6: completar la lectura en /web:
1. P&G con filas que suman al total visible (partidas memo expandibles), indicadores del estado de resultados, reparto CG/socio (donut + tabla).
2. Distribución de costos: tabla WBS 28 capítulos con % e incidencias, curva S con pico de obra anotado.
3. Costo de capital: cadena de cálculo WACC completa (beta → Ke → WACC) como stepper visual + tarjetas de resultado.
4. Apalancamiento: flujo consolidado, caja acumulada vs saldo de crédito, tarjetas (crédito máx, necesidad máx, valor financiable, intereses).
5. Cronograma: absorción por etapa (barras) + acumulado vendido + entregas.
Todo con ChartCard (fuente + corte), checks visibles, export CSV/Excel por tabla.
Criterio de salida: cualquier análisis que hoy hago en Streamlit lo puedo hacer en Aleph con mejor visualización.

### PROMPT 8 — Captura y escenarios versionados
Fase 7: la escritura migra a /web (la fase más delicada — plan detallado y mi aprobación explícita):
1. API de escritura: PATCH de supuestos sobre el draft activo (autosave con debounce + audit_log), crear draft desde escenario, aprobar (snapshot inmutable con trigger), marcar baseline (solo construcción, único por proyecto).
2. UI Ingreso de datos: formularios por bloques (1-Datos generales, 2-Áreas y lote, 3-Tipologías/etapas, 4-Costos, 4b-Gastos, 4c-Presupuesto por capítulo, 5-Recaudo, 6-Financiero, 7-WACC) con grid editable tipo hoja de cálculo (tab entre celdas, pegar desde Excel), validación por esquema, indicador de completitud por bloque, recálculo automático al guardar (invalidación de results_cache).
3. Selector de escenario en el header + comparador de 2 escenarios lado a lado (deltas) + banner de borrador.
4. Solo admins escriben (rol); gerencia ve lectura.
Criterio de salida: modelo un cambio de supuestos completo en Aleph sin tocar Streamlit; apruebo un escenario y queda inmutable; el dorado sigue verde.

### PROMPT 9 — Prefactibilidad, seguimiento y PDF
Fase 8: las capacidades que faltan, ya nativas en Aleph:
1. PREFACTIBILIDAD: formulario rápido de un lote (áreas, $/m², %, plazos, tipo) → mismo motor con defaults CG → indicadores gruesos + VALOR RESIDUAL DEL LOTE (margen/TIR objetivo → precio máx del lote, total y /m², con mini-sensibilidad ±10% precio). Crea el proyecto en fase Pre-factibilidad (el embudo se llena). Promover a Factibilidad expande supuestos como escenario v1 draft.
2. SEGUIMIENTO: captura mensual de ejecutados por capítulo (source: manual|excel|erp), baseline congelado vs ejecutado vs EAC con varianzas y semáforos, curva EVM recalibrada (check de plausibilidad SPI), rolling forecast (real + re-proyección), cartera de recaudo.
3. PDF: informe ejecutivo 1-2 páginas (KPIs etiquetados, flujo, alertas, checks, hash del escenario) + paquete banco (anexos: P&G, curva S, crédito). Generación server-side desde la API.
Criterio de salida: evalúo un lote en <15 min; los 3 proyectos en obra reportan baseline vs real; el comité del lunes sale en PDF desde Aleph.

### PROMPT 10 — Apagado de Streamlit y endurecimiento
Fase 9 (solo cuando TODO lo anterior esté verificado):
1. Checklist de paridad módulo a módulo Streamlit vs Aleph; lo que falte, listarlo y decidir conmigo (migrar o retirar).
2. Redirigir el App Service de Streamlit a la URL de Aleph; conservar el contenedor apagado 1 mes como respaldo.
3. Endurecimiento: GitHub Actions CI/CD (test → build → deploy api y web), backups programados de Supabase + restore ensayado, monitoreo (alertas de error de la API), página /status con versión y salud.
4. Documentación final: README del monorepo, guía de operación para mí (cómo desplegar, cómo restaurar, cómo crear usuarios), y actualización de CLAUDE.md (la constitución pasa de "migración" a "operación").
Criterio de salida: Streamlit apagado sin pérdida funcional; CI/CD automático; sé operar el sistema sin asistencia.

---

## PARTE C · Guía de ejecución paso a paso en VS Code

### 0 · Preparación del entorno local (una vez, ~30 min)
La UI nueva necesita Node.js además de Python:
- Instala Node.js LTS (nodejs.org, versión 20+) y verifica: `node -v`, `npm -v`.
- Verifica Python: `python --version` (3.11+ recomendado).
- Instala las extensiones de VS Code: ESLint y Tailwind CSS IntelliSense.
- Crea cuenta en vercel.com con correo CG (gratis) — se conecta en Fase 4. Si la política exige todo-Azure, decirlo en el Prompt 5 y se usa Azure Static Web Apps.

### 1 · Inyección de la Constitución (una vez, ~10 min)
- Respaldo: `git add -A && git commit -m "checkpoint pre-migración Aleph v3"` y descarga el JSON de respaldo de cada proyecto.
- Pega la Constitución en CLAUDE.md (reemplaza la v2 si existía; instrucciones y aprendizajes no se tocan).
- Sesión nueva: comparar la constitución contra CLAUDE.md/AGENTS.md/directives, listar contradicciones, proponer resolución (producto/dominio → gana la constitución; metodología → ganan tus secciones). No modificar aún. Resolver y commit.
- Guardar la Parte B en `directives/prompts_migracion_v3.md` (este archivo).

### 2 · Rutina por fase (repítela 10 veces)
1. `/clear` → sesión limpia (la constitución se carga sola desde CLAUDE.md).
2. Shift+Tab hasta plan mode.
3. Pega el prompt de la fase. Revisa el plan como CFO: bases de cálculo, orden, riesgos. Aprueba solo cuando convenza.
4. Deja ejecutar. Concede permisos cuando los pida.
5. Prueba local antes de desplegar: Streamlit `./dev.sh` (localhost:8501); API `./dev_api.sh` (localhost:8000/docs); Web `cd web && npm run dev` (localhost:3000).
6. Verifica el criterio de salida. Pide evidencia: "muéstrame el harness dorado en verde", "dame la URL del preview".
7. Commit: `git add -A && git commit -m "Fase N: <resumen>"`.
8. Deploy con los scripts. Verifica la versión en el footer.
9. Prueba en producción con datos de Navarra.
10. Cierra: "Registra los aprendizajes de esta fase en CLAUDE.md según tu protocolo".

### 3 · Calendario realista
| Semana | Fases | Hito visible |
|---|---|---|
| 1 | Prompts 1-2 | Monorepo + snapshot dorado; Streamlit intacto |
| 2-3 | Prompt 3 | Motor extraído y testeado; Streamlit consume el motor |
| 3-4 | Prompt 4 | API desplegada con /docs |
| 4-5 | Prompt 5 | UI nueva con login CG y design system — primer "wow" |
| 5-7 | Prompts 6-7 | Gerencia consulta todo en Aleph |
| 7-9 | Prompt 8 | Captura y escenarios versionados en Aleph |
| 9-11 | Prompt 9 | Prefactibilidad + seguimiento + PDF |
| 12 | Prompt 10 | Streamlit apagado · Aleph 1.0 |

### 4 · Reglas de oro
1. Una fase por sesión; nunca dos a medias.
2. El snapshot dorado es sagrado: si se rompe, nada se mergea.
3. No dejes que el agente "mejore de paso" fuera del alcance de la fase.
4. **Paridad antes de apagar:** no retires nada de Streamlit hasta que su reemplazo esté verificado en producción.
5. **El design system es ley:** desde la Fase 4, toda pantalla nueva usa los componentes canon. Si una pantalla "se ve distinta", es un bug.
6. **Pide explicaciones:** terminar cada sesión con "explícame en 5 líneas qué construiste y por qué así".
