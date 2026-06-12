# Instrucciones para el Agente
	
> Este archivo está replicado en CLAUDE.md, AGENTS.md y GEMINI.md para que las mismas instrucciones carguen en cualquier entorno de IA.

---

## ALEPH — Constitución del producto (v3 · MIGRACIÓN · jun-2026)

> **DOCUMENTO GOBERNANTE.** Léelo antes de cualquier trabajo de ALEPH. Reemplaza como norte estratégico a los planes Streamlit-internos previos (`app_factibilidad/NORTE_TABLEROS.md`, `REESTRUCTURACION.md`), que pasan a ser **contexto histórico**. Las **cifras doradas** y los **gotchas operativos** viven en «Aprendizajes del Agente» (abajo) y siguen vigentes.

ALEPH es la plataforma de evaluación financiera de proyectos inmobiliarios de CG Constructora S.A.S. (hoy "Factibilidad CG" en Streamlit). DECISIÓN ESTRATÉGICA: migrar a arquitectura profesional de 3 capas por **ESTRANGULAMIENTO PROGRESIVO**. Prohibido el big-bang: la app Streamlit sigue funcionando en producción hasta que la UI nueva tenga paridad módulo a módulo. Cada fase termina con algo desplegado y usable.

### Arquitectura objetivo (monorepo)
```
/engine   → `aleph_engine`: paquete Python PURO. Toda la lógica financiera.
            Sin imports de Streamlit/FastAPI/Supabase. Modelos Pydantic.
            Cobertura de tests obligatoria para toda función financiera.
/api      → FastAPI. Expone el motor y los datos (Supabase/Postgres).
            Contrato OpenAPI versionado. Auth: valida tokens de Entra ID
            (mismo tenant que hoy). Autorización por rol.
/web      → Next.js (App Router) + TypeScript + Tailwind + shadcn/ui.
            SOLO presenta: ningún cálculo financiero en el frontend.
            Gráficos: Recharts (o Tremor). Auth: NextAuth con proveedor
            Microsoft Entra ID.
/app_streamlit → la app actual. Se toca SOLO para: (a) consumir el motor
            extraído, (b) redirigir a la UI nueva cuando un módulo migre.
            No se le añade funcionalidad nueva.
```

### Reglas innegociables de la migración
1. **SNAPSHOT DORADO AUTOMÁTICO:** antes de extraer cualquier cálculo, generar tests que congelen los resultados actuales de Navarra Apartamentos (TIR proyecto 37.60%, VPN @TIO 18.3 mil M, TIR socio 41.72%, ventas 229.7 mil M, costo directo 143.5 mil M, exposición máx −71.0 mil M, crédito máx 49.3 mil M, y el flujo mensual completo). La migración no valida estas cifras: garantiza que NO CAMBIEN. Desviación > 0.1% rompe el build.
2. **PARIDAD ANTES DE APAGAR:** un módulo de Streamlit solo se retira cuando su equivalente en /web está desplegado y verificado.
3. **SUPABASE:** única base de datos de ambas UIs durante la transición. Revisar `list_tables` antes de toda migración de esquema. Migraciones versionadas. RLS por rol (admin edita, gerencia lee).
4. **DEPLOY DETERMINISTA:** imágenes Docker etiquetadas con SHA del commit (nunca `:latest`). /api y /app_streamlit en Azure App Service (ACR); /web en Vercel (o Azure SWA si se exige todo-Azure). Versión visible en el footer de ambas UIs.
5. **El usuario (Martin) NO es desarrollador:** cada fase debe incluir instrucciones de verificación manual simples (qué abrir, qué comparar) y scripts (`deploy.sh`, `dev.sh`) para no depender de comandos memorizados.

### Dominio financiero (no simplificar)
- Modelo mensual en COP corrientes. **Doble flujo SIEMPRE:** proyecto (desapalancado) e inversionista (apalancado), cada uno con indicadores.
- Esquema colombiano: separación + cuotas fraccionadas + contra escritura; recaudo en fiducia hasta punto de equilibrio; crédito constructor con desembolsos contra avance (~80% costo obra), intereses, amortización por subrogaciones.
- WACC build-up Damodaran (beta desapalancada→reapalancada, EMBI, paridad de inflación) y curva S de Gauss: **YA EXISTEN en el código Streamlit — extraer tal cual, no reescribir de memoria.**
- Indicadores mínimos: VPN, TIR proyecto, TIR inversionista/socio, múltiplo de equity, margen sobre ventas, yield on cost, incidencia del lote, costo directo/m², exposición máxima de caja y su mes, punto de equilibrio, payback.

### Gobernanza de cifras
- Diccionario único de indicadores en engine (`metrics.py`): clave, nombre, ETIQUETA DE BASE, definición, función. UI consume solo de aquí vía API.
- **Ninguna cifra sin etiqueta de base:** "TIR proyecto", "TIR apal. ref.", "TIR socio" — nunca "TIR" a secas. Proyectos greenfield: flag `is_greenfield` → mostrar "— greenfield", jamás TIR −99%.
- Checks de cuadre calculados en el motor y expuestos por la API: P&G suma al total, recaudo = ventas, flujo final ≈ utilidad, crédito cuadra, SPI plausible (0.4–2.0). La UI muestra el estado de checks en cada módulo.

### Modelo de datos objetivo
`companies` → `projects` (con fase del ciclo de vida: prefactibilidad, factibilidad, aprobado, preventas, construccion, entregas, liquidacion, cerrado) → `scenarios` (versionados: draft/approved/baseline; snapshot JSONB inmutable al aprobar; un solo baseline por proyecto) → `results_cache`. `actuals_*` para ejecutados (campo `source`: manual|excel|erp|crm). `audit_log` de todo cambio de supuestos. El JSON actual de cada proyecto se migra como escenario v1 approved.

### Diseño visual (la app entra por los ojos — nivel Linear/Mercury/Tremor)
- Design tokens centralizados (`web/styles`): base zinc/slate, acento teal CG #0E5E59 (tomar el exacto del logo), ámbar CG secundario, semántica verde/ámbar/rojo SOLO para estados. Dark y light mode desde el día uno.
- Tipografía: Inter (o Geist). `font-variant-numeric: tabular-nums` en TODO número. Cifras alineadas a la derecha. `fmt_cop()`/`fmt_pct()` es-CO únicos (miles con punto), compartidos vía librería del web.
- Componentes canon: `KpiCard` (valor + etiqueta de base + delta + estado), `ChecksBadge`, `PhaseBadge`, `DataTable` (densa, ordenable, export), `ChartCard` (gráfico + fuente + corte de datos). Construir UNA vez, reutilizar SIEMPRE.
- Layout: sidebar colapsable con grupos rotulados PROYECTO / PORTAFOLIO, breadcrumb Portafolio › {Proyecto} › {Módulo}, header permanente con Proyecto · Fase · Escenario vN (estado) · Corte de datos.
- Densidad financiera: mucha información, cero decoración. Animaciones sutiles (150-200ms). Estados de carga skeleton, nunca spinners gigantes.
- Accesibilidad AA de contraste. Responsive: dashboards usables en tablet (gerencia los verá en reuniones).

### Definición de "terminado" (toda fase)
Tests del motor verdes (incluido snapshot dorado) · checks de cuadre expuestos · ninguna cifra sin etiqueta en pantallas nuevas · desplegado con tag de commit y verificado en el footer · instrucciones de verificación manual entregadas a Martin.

---

## Aprendizajes del Agente (Mejora Continua)

> **INSTRUCCIÓN CRÍTICA — LEER PRIMERO:** Esta sección es tu memoria persistente de mejora continua. **Con cada ciclo de ejecución** (al completar una tarea, resolver un error, descubrir un patrón, o ajustar un flujo) **y con cada actualizacións de cualquier Markdown** (directivas, CLAUDE.md, AGENTS.md, GEMINI.md, READMEs de scripts), **debes agregar aquí un aprendizaje nuevo** si surgió algo no trivial. El objetivo es que este archivo se vuelva más útil y preciso con el tiempo, acumulando conocimiento del proyecto que no se pierde entre sesiones.
>
> **Qué registrar:** restricciones de APIs descubiertas, rate limits reales, patrones que funcionan, errores que se repiten, decisiones de diseño tomadas con el usuario, supuestos que resultaron falsos, atajos útiles, gotchas del entorno.
>
> **Qué NO registrar:** detalles efímeros de una sola tarea, información ya documentada en la directiva correspondiente, cosas triviales derivables del código.
>
> **Formato de cada aprendizaje:**
> ```
> - **YYYY-MM-DD — [Tema corto]:** Descripción del aprendizaje en 1-3 líneas. **Por qué importa:** consecuencia práctica o cómo aplicarlo en el futuro.
> ```
>
> **Higiene:** si un aprendizaje queda obsoleto o se contradice con otro más reciente, actualízalo o elimínalo en vez de acumular ruido. Mantén la lista ordenada por fecha (más recientes arriba). Si superas ~25 entradas, consolida las más antiguas o promuévelas a la directiva que corresponda.

### Registro de aprendizajes

- **2026-06-12 — Sacar el repo de OneDrive + montar el monorepo en `C:\Code\aleph`:** OneDrive sincronizando la carpeta `.git` la **corrompe** (apareció un `index.lock` colgado a media operación de git). **Solución:** mover el código FUERA de OneDrive vía **clon fresco de GitHub** a `C:\Code\aleph` (no se arrastra el `.git` corrupto; GitHub es la fuente de verdad) + copiar lo **local-only** que no está en GitHub (`proyectos_privados/`, snapshots reales, `.streamlit/secrets.toml`). En el mismo movimiento se reestructuró al **monorepo ALEPH**: la app actual → `app_streamlit/` (con `git mv`, historial intacto); se crearon `engine/ api/ web/` (esqueletos) y los docs subieron al **root del monorepo** (ahora SÍ versionados). El CI corre con `working-directory: app_streamlit`. La copia vieja en OneDrive queda de respaldo. **Por qué importa:** (1) **nunca** poner un repo git dentro de OneDrive/Dropbox; (2) el `Dockerfile` ahora está en `app_streamlit/` → el deploy debe usar contexto `#main:app_streamlit` con **tag=SHA**; (3) Martin reabre VS Code en `C:\Code\aleph`. **Verificado:** 73 tests verdes (incl. dorado).
- **2026-06-12 — PIVOTE ESTRATÉGICO: migrar de Streamlit a ALEPH (3 capas) por estrangulamiento:** Con Martin se decidió migrar de Streamlit a `/engine` (`aleph_engine`, Python puro) + `/api` (FastAPI) + `/web` (Next.js + TS + Tailwind + shadcn/ui), manteniendo el Streamlit **vivo en producción** hasta tener **paridad módulo a módulo** (NO big-bang). La **constitución gobernante** está arriba (§ALEPH). Arranque: **snapshot dorado automático** (las cifras de Navarra ya viven en `app_factibilidad/tests/test_anclas.py`) + extraer `cg_engine`→`aleph_engine` **tal cual** (no reescribir WACC/curva S/fiducia de memoria). **Por qué importa:** redefine TODO el plan — `NORTE_TABLEROS.md`/`REESTRUCTURACION.md` (Streamlit) pasan a histórico; deploy ahora **por SHA del commit**, no `:latest`; cada cifra en UI nueva lleva **etiqueta de base** (TIR proyecto/socio/ref, nunca "TIR" sola). **Pendiente decidir con Martin:** hosting de `/web` (Vercel vs Azure SWA por el "todo-Microsoft"), estructura del monorepo, y si se cierra primero el despliegue v2.39 de Streamlit.
- **2026-06-11 — Captura de datos = pestaña ADMIN-ONLY ("Ingreso de datos"); y la "cabida" HOY es decorativa (hallazgos de exploración multi-agente):** El usuario pidió una pestaña independiente **solo para los 2 admins** como único punto de input, con todos los datos en orden **empezando por la cabida urbanística del lote**. La exploración del código (4 agentes) reveló: (1) **la cabida es decorativa** — las áreas (`lote_bruta/util`, `m2_vendibles/construidos`) solo alimentan KPIs descriptivos en "Urbanístico"; el motor financiero NO las usa, el driver real es `etapas[].und × precio → ventas → P&G/flujo/TIR`. No existe estudio de cabida POT (índices/altura/aislamientos/cesiones). Ojo: `lote_bruto_miles` es un **valor monetario** (costo del lote), NO un área. (2) **Admin-only por persona EXIGE SSO**: hoy solo hay roles `editor`/`viewer` (no `admin`); el camino de contraseña es **anónimo** (clave compartida), la única identidad por-persona es el email del login Microsoft (`st.session_state['_ms_user']`, disponible gracias a Easy Auth) → solución: lista `ADMINS` de correos en secretos + helper `es_admin()` junto a `gate()`. (3) **Input disperso en 3 lugares** ("Datos del proyecto" + islas "Distribución de costos" y "Costo de capital"), **sin `st.form`** (todo muta `par` in-place) y **una sola** persistencia (botón que hace upsert del JSON entero a Supabase) → migrar = reubicar widgets, el guardado no cambia. (4) **Gate temporal**: sin `fecha_inicio` en la etapa raíz el motor apaga recaudo/TIR/VPN/EVM. (5) **Hueco**: un proyecto **nuevo no se puede guardar** en la nube hoy. **Decisiones del usuario:** acceso por **email/SSO**; cabida **reorganizar ahora** (cero riesgo) + **calculadora POT después** (paso dedicado, con red de pruebas, capacidad nueva del motor). **Por qué importa:** re-escopó la **Fase 2 Paso 1** en 1a (andamiaje + `es_admin()`), 1b (módulo Ingreso admin, validar con `schema.parse`, tapar hueco proyecto nuevo, consumo→solo-lectura), 1c (menú 19→14 + ciclo de vida), 1d (capítulos). Todo en `app_factibilidad/NORTE_TABLEROS.md` (§1b). **Admins definidos** (lista `ADMINS`): mgomez@cgconstructora.com (Martin Gómez G) y jgonzalez@cgconstructora.com (José Alfonso González).
- **2026-06-11 — El ESTADO del proyecto es el eje rector de la app (ciclo de vida, Fase 2 Paso 0):** Con el experto se definió que cada proyecto lleva un campo `estado` con 4 etapas de pipeline (`prefactibilidad → aprobado → construccion → entregado`) y que la UI se **adapta** al estado: pre-fact = decisión ir/no-ir (lote = SUPUESTO, sin Seguimiento, gate multicriterio), construcción/entregado = monitoreo plan vs real. Implementado como **dato** primero (lo más seguro): `config.ESTADOS`/etiquetas/umbrales de aprobación (TIR equity + VPN>0 a TIO + margen, provisionales), `Meta.estado` validado en `schema.py` (rechaza estados mal escritos, fuente única = `config.ESTADOS`), e inserción **quirúrgica de texto** del campo en los 6 JSON (sin reformatear → diff limpio en los públicos). NO toca el cálculo: 34 tests verdes. Estados reales hoy: Navarra/Dominica = construcción; Torres de Campiñas = **aprobado** (obra inicia 2026-07-15). La herramienta estrella de pre-fact será el **lote breakeven** (precio máx pagable para rendir el umbral) + evaluar un precio. **Por qué importa:** (1) el norte de tableros (`app_factibilidad/NORTE_TABLEROS.md` §0) gira en torno a esto — pipeline/embudo, filtro por estado, secciones que aparecen/ocultan según estado; (2) agregar un eje conceptual nuevo como CAMPO validado + tests, antes de tocar UI, mantiene el riesgo en cero. **Pendiente Fase 2:** andamiaje modular (`ui/`), reorganizar menú 19→14, Pipeline/Embudo, Decisión de inversión, Comparar candidatos.
- **2026-06-11 — Gotcha del Bash tool en Windows: NO usar here-strings de PowerShell (`@'...'@`):** El "Bash tool" corre **bash**, no PowerShell, aunque el entorno sea Windows. Pasar `git commit -m @'...'@` deja un `@` espurio al inicio y fin del mensaje (bash trata `@'` como literal + comilla simple). **Solución:** escribir el mensaje a un archivo (`.tmp/commitmsg.txt`) y `git commit -F` / `--amend -F`. **Por qué importa:** mensajes de commit/PR multilínea fiables sin contaminar el shell; el here-string `@'...'@` solo vale en el tool de PowerShell.
- **2026-06-11 — Reestructuración del motor con "golden tests primero" (Fase 1, sin romper nada):** Se refactorizó `engine/` → paquete **`cg_engine`** en 6 pasos atómicos (paquete instalable; TIR/VPN/WACC única en `finanzas.py` sin ciclo de import; `config.py` sin números mágicos; `errors.py` + logging en vez de swallows silenciosos; `schema.py` Pydantic validable en el borde; `flujo.py` helper compartido; versión única `cg_engine.__version__`) **sin cambiar una sola cifra auditada**. La clave: una **suite de anclas/golden tests** (Fase 0: `tests/test_anclas.py` + CI en GitHub Actions) que clava UO/TIR/VPN de los 3 proyectos reales ANTES de tocar el motor; cada paso se verifica contra ella + ruff + `compileall` + PR con CI verde, y se revierte si una cifra se mueve. **Juicio de experto sobre el consejo genérico (un diagnóstico automático sugirió ambas cosas, AMBAS habrían roto algo):** (1) la fecha de corte del EVM (`2026-05-01`) **NO** se cambia a `date.today()` — es el corte de los datos de comité, cambiarla daría un SPI falso; (2) `flujo_caja` (PERT, vista simple) y `flujo_apalancado` (Gauss, waterfall auditado que produce las anclas) **NO** se fusionan — son modelos intencionalmente distintos. **Por qué importa:** la red de pruebas convierte una refactorización riesgosa en segura y repetible (PR pequeño por paso, CI verde, merge con rebase); y el conocimiento del DOMINIO gana sobre el "best practice" genérico. Plan completo en `app_factibilidad/REESTRUCTURACION.md`. **Pendiente:** Fases 2-5 (UI modular, modelo de datos, puertos ERP/CRM, CI/CD+rotar secretos). El contenedor desplegado sigue en v2.35.0 — al desplegar la Fase 1 hay que reconstruir la imagen (`az acr build`).
- **2026-06-11 — Azure App Service: ir directo a CONTENEDOR Docker, NO al auto-build (Oryx):** Desplegar la app Streamlit en App Service Linux modo "Code" (Oryx) fue un infierno de horas: el build daba "successful" pero el runtime moría con `No module named streamlit` (el venv `antenv` del build NO se encuentra en runtime; `WEBSITE_RUN_FROM_PACKAGE` rompe el build de Python dejando wwwroot read-only; un Startup Command custom corre con el python del SISTEMA sin activar antenv). **Solución definitiva:** empaquetar en un **contenedor** (`Dockerfile` con `FROM python:3.12-slim` + `pip install -r requirements.txt` + `CMD streamlit run`) y construirlo con **`az acr build`** a un Azure Container Registry (build en la nube, sin Docker local), luego App Service apuntando a esa imagen (`az webapp config container set`, `WEBSITES_PORT=8000`, websockets+alwaysOn ON). Las librerías quedan horneadas: sin Oryx, sin venv que buscar. Además la instancia original `cg-factibilidad` quedó **corrupta** tras decenas de cambios (504 hasta con `python -m http.server`) → hubo que **recrear limpia** (`cg-factibilidad-app`, mismo plan B1, copiando los secrets de la vieja con `appsettings list ... -o json > s.json` + `set --settings @s.json`). URL nueva: `https://cg-factibilidad-app.azurewebsites.net`. **Por qué importa:** (1) para Streamlit/Python en Azure, ir derecho a contenedor evita TODA la clase de problemas de Oryx; (2) los logs de App Service Linux se atrasan/no refrescan (inútiles para depurar arranque) — el contenedor da control total; (3) si una instancia se "envenena" de tanto cambio, recrear es más rápido que depurar; (4) `--admin-enabled true` en el ACR + pasar user/pass al webapp es la vía simple de auth. **Estado (2026-06-11):** Easy Auth ✅, instancia vieja `cg-factibilidad` **borrada** ✅, contenedor **reconstruido a v2.38.0** desde GitHub `main` ✅ (`az acr build --registry cgfactibilidadacr --image cgapp:latest https://github.com/DjmartinG/cg-factibilidad-app.git` + `az webapp restart`; incluye Fase 1 + ciclo de vida + Ingreso admin + Monte Carlo). Lista `ADMINS` definida en Azure (mgomez@/jgonzalez@) → admin por email funciona en prod. Recursos reales: grupo `Cg-factibilidad`, plan `ASP-Cgfactibilidad-b208` (B1, 1 solo plan), registry `cgfactibilidadacr`, webapp `cg-factibilidad-app`. **GOTCHA de redespliegue (importante):** tras `az acr build ... cgapp:latest`, App Service **NO re-baja** la imagen `:latest` con un simple `az webapp restart` (cachea el digest viejo → la app sigue en la versión anterior). Hay que **forzar el pull** con `az webapp config container set -g Cg-factibilidad -n cg-factibilidad-app --container-image-name cgfactibilidadacr.azurecr.io/cgapp:latest --container-registry-url https://cgfactibilidadacr.azurecr.io` (mantiene las credenciales del registry, que viven como app settings aparte) y **luego** `az webapp restart`. Verificar por el pie `Aplicativo vX.Y.Z`. **Pendiente:** rotar `SUPABASE_KEY` (service_role expuesta en sesiones pasadas).
- **2026-06-10 — El ritmo de ventas mueve la TIR, no el margen (y expuso un bug de timing):** En el Monte Carlo de TIR/VPN (`engine.montecarlo_tir`), variar `vmes` cambia hitos PE→IC→FC y el recaudo, pero **NO el margen** (el margen solo depende de precio/costo, es total sin timing). Al simularlo apareció un resultado invertido (vender más rápido bajaba la TIR) porque la **escrituración** (offset fijo desde IV) no seguía a la obra: costos se adelantaban, el ingreso grande (subrogación) no. Fix: en la simulación, desplazar la escrituración por el mismo Δ de PE (mantener fija la brecha equilibrio→escrituración). Además, el MC **ignora el override de fiducia** (`par['fiducia']`) para que la TIR responda. **Por qué importa:** (1) si una variable solo afecta el timing, la salida del MC debe ser TIR/VPN, no margen; (2) sembrar `und=1` por etapa anula el efecto del ritmo (vende en el mes 0); (3) los shocks de un MC son un buen *test* de consistencia del modelo de tiempo.
- **2026-06-08 — Probar la app con AppTest sin quedar atrapado en el candado:** `gate()` hace `st.stop()` en la pantalla de login cuando `secrets.toml` tiene `CLAVE_EQUIPO` (caso local real). En `AppTest` eso hace que NINGUNA sección renderice (0 excepciones, pero contenido vacío → falso positivo). Saltar con `at.session_state['_rol']='editor'` ANTES de `at.run()`, y forzar la sección monkeypatcheando `streamlit_option_menu.option_menu=lambda *a,**k: '<Sección>'` antes de `AppTest.from_file`. **Por qué importa:** sin esto las pruebas validan el login, no la lógica; siempre setear rol y sección para probar de verdad.
- **2026-06-08 — Monte Carlo sin reescribir el motor:** `engine.montecarlo(par, n, rango_precio, rango_costo, seed)` itera `_correr()` (solo `pyg`, ~rápido: 500 sims <1s) y es determinista por `seed`. En la UI envolver en `@st.cache_data` keyado por `json.dumps(par, sort_keys=True)` + n + rangos (el dict no es hasheable). **Por qué importa:** análisis probabilístico (P10/P50/P90, prob margen>0) reutilizando la fuente única, con caché reproducible.
- **2026-05-28 — App de factibilidad (v1.0.0):** Aplicativo Streamlit multi-proyecto en `app_factibilidad/` (repo Git, tag v1.0.0). Motor en `engine/` (curvas PERT + modelo: P&G, reparto, flujo, escenarios). Proyecto Dominica validado al 99,87%. **Por qué importa:** es la herramienta operativa; agregar proyectos = un JSON en `proyectos/`.
- **2026-05-28 — Fuente única de verdad:** toda la lógica financiera vive en `app_factibilidad/engine/` (Python); la UI (Streamlit) solo presenta. NO duplicar fórmulas en JS/Excel. **Por qué importa:** consistencia y auditabilidad (estándar FAST de modelación).
- **2026-05-28 — Enfoque híbrido de factibilidad:** el modelo propio posee P&G/costos/crédito (crédito constructor calibrado = $29.601M, exacto al aprobado); la TIR APALANCADA de decisión (21,83%) se toma del modelo aprobado. **Por qué importa:** el revolving del crédito propio aún no replica el waterfall de fiducia; no comparar TIR no-apalancada vs apalancada.
- **2026-05-28 — Python del equipo:** está en `C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe`, NO en PATH (los stubs de Microsoft Store lo sombrean). **Por qué importa:** invocar siempre por ruta completa en scripts y comandos.
- **2026-05-28 — Leer .xlsx bloqueados / OneDrive solo-en-nube:** si Excel tiene el archivo abierto o OneDrive lo marca como placeholder, copiar primero con `Copy-Item` y leer la copia. **Por qué importa:** evita PermissionError y "file does not exist" al leer con openpyxl.

<!-- Agrega nuevas entradas arriba de esta línea. -->

---

Tú trabajas con una **metodología de 3 capas operativas** que separa responsabilidades para maximizar la confiabilidad. Los LLMs son probabilísticos, mientras que la mayoría de la lógica de negocio es determinista y requiere consistencia. Este sistema resuelve esa incompatibilidad.

## Metodología del Agente (capas operativas)

> ⚠️ Esto es **CÓMO** trabaja el agente (directiva → orquestación → ejecución). NO confundir con las 3 capas de **PRODUCTO** de ALEPH (`engine`/`api`/`web`, §ALEPH arriba), que es **QUÉ** construimos.

**Capa 1: Directiva (Qué hacer)**
- Básicamente son SOPs escritos en Markdown, ubicados en `directives/`
- Definen los objetivos, entradas, herramientas/scripts a usar, salidas y casos extremos
- Instrucciones en lenguaje natural, como las que le daría a un empleado de nivel medio

**Capa 2: Orquestación (Toma de decisiones)**
- Esta es tu función. Tu trabajo: enrutamiento inteligente.
- Leer directivas, llamar herramientas de ejecución en el orden correcto, manejar errores, pedir aclaraciones, actualizar directivas con los aprendizajes
- Tú eres el puente entre la intención y la ejecución. Por ejemplo, no inventes el ETL de migración por tu cuenta—lee `directives/plan_migracion.md`, define entradas/salidas y luego ejecuta el script determinista en `execution/`.

**Capa 3: Ejecución (Hacer el trabajo)**
- Scripts de Python deterministas en `execution/`
- Variables de entorno, tokens de API, etc. se almacenan en `.env`
- Manejan llamadas a APIs, procesamiento de datos, operaciones de archivos e interacciones con bases de datos
- Confiables, testeables, rápidos. Use scripts en vez de trabajo manual.

**Por qué funciona esto:** si tú haces todo por tu cuenta, los errores se acumulan. Un 90% de precisión por paso = 59% de éxito en 5 pasos. La solución es empujar la complejidad hacia código determinista. Así tú te concentras solo en la toma de decisiones.

## Principios de Operación

**1. Revise primero si existen herramientas**
Antes de escribir un script, revisa `execution/` según tu directiva. Solo crea scripts nuevos si no existe ninguno.

**2. Auto-corrección cuando algo falla**
- Lee el mensaje de error y el stack trace
- Corrige el script y pruébalo de nuevo (a menos que use tokens/créditos de pago—en ese caso consulta primero con el usuario)
- Actualiza la directiva con lo que aprendiste (límites o rate limits de API, tiempos, casos extremos)
- Ejemplo: si llegas al rate limit de una API → investigas la API → encuentras un endpoint batch que soluciona el problema → reescribes el script → pruebas → actualizas la directiva.

**3. Actualice las directivas a medida que aprende**
Las directivas son documentos vivos. Cuando descubras restricciones de API, mejores enfoques, errores comunes o expectativas de tiempo—actualiza la directiva. Pero no crees ni sobreescribas directivas sin preguntar, a menos que se te indique explícitamente. Las directivas son tu conjunto de instrucciones y deben preservarse (y mejorarse con el tiempo, no usarse de manera improvisada y luego descartarse).

## Ciclo de Auto-corrección

Los errores son oportunidades de aprendizaje. Cuando algo falla:
1. Corrija el problema
2. Actualice la herramienta
3. Pruebe la herramienta, asegúrese de que funcione
4. Actualice la directiva con el nuevo flujo
5. El sistema ahora es más robusto

## Organización de Archivos

**Estructura de directorios:**
- `.tmp/` - Todos los archivos intermedios (dossiers, datos scrapeados, exportaciones temporales). Nunca se suben al repositorio, siempre se regeneran.
- `execution/` - Scripts de Python (las herramientas deterministas).
- `directives/` - SOPs en Markdown (el conjunto de instrucciones).
- `.env` - Variables de entorno y claves de API.

**Principio clave:** Los archivos intermedios viven en `.tmp/` y pueden borrarse siempre. Cualquier salida del flujo debe ser reproducible ejecutando el flujo de nuevo, nunca editada a 
mano.


## Resumen

Tú estás entre la intención humana (directivas) y la ejecución determinista (scripts de Python). Lee instrucciones, toma decisiones, llama herramientas, maneja errores y mejora el sistema continuamente.

Se pragmático. Se confiable. Auto-corrígjete.

