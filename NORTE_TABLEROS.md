# NORTE — Tableros y Capítulos · App "Evaluación Financiera de Proyectos" (CG Constructora)

> Diseño objetivo (arquitectura de información + UX) hacia el cual modularizar la UI (Fase 2).
> Generado por análisis multi-agente del código real (2026-06-11). Antecede a la modularización.

## Tesis
La app ya tiene el **esqueleto conceptual correcto** (3 capas: Portafolio → Plan → Real) y buenos activos de UX (Cockpit con semáforos, gráficos para decidir). El problema **no es de fondo sino de arquitectura de información**: 19 secciones planas donde el comité necesita ~14 bien jerarquizadas; 3 secciones de riesgo que dicen lo mismo; 2 secciones casi vacías inflando el menú; un consolidado que aún no escala.

**4 reglas que gobiernan el rediseño:**
1. **El estado del proyecto es el eje rector** (ver §0): un proyecto en pre-factibilidad se evalúa para **decidir** (ir/no-ir); uno en obra se **monitorea** (plan vs real). La UI se **adapta** al estado.
2. **Factibilidad = plan (ex-ante) · Seguimiento = real (ex-post)** — cada capítulo del plan tiene espejo en lo real.
3. **El comité decide equity:** "¿cuánto pongo, cuánto me rinde, cuán robusto es MI retorno apalancado?".
4. **No sobre-ingenierizar:** 15-20 proyectos × ~50-200 KB caben en memoria. Cachear bien, no construir un data-warehouse.

## 0. Ciclo de vida del proyecto (EJE RECTOR)

Todo proyecto lleva un campo **`estado`** con 4 etapas. El estado gobierna el **pipeline**, el **filtro** del portafolio y **qué se muestra** por proyecto.

```
PRE-FACTIBILIDAD  ──(aprobar + comprar lote)──▶  APROBADO  ──(inicia obra)──▶  CONSTRUCCIÓN  ──(entrega)──▶  ENTREGADO
   candidato                                       lote real,                    en ejecución,                  cerrado
   lote = SUPUESTO                                 plan final                    plan vs real                   plan vs real
   foco: DECISIÓN ir/no-ir                         (sin obra aún)                seguimiento vivo               cierre
   SIN seguimiento                                                                                                          
```

**Diferencias que la UI respeta:**

| | **Pre-factibilidad** | **Aprobado** | **Construcción / Entregado** |
|---|---|---|---|
| Lote | **supuesto** (a evaluar) | real / adquirido | real |
| Foco | **decisión ir/no-ir** vs umbral | plan final | monitoreo plan vs real |
| Seguimiento | **oculto** (sin datos reales) | oculto (sin obra) | **visible** |
| Sección "Decisión de inversión" | **visible** | histórico (ya decidida) | histórico |

**Pipeline / Embudo (Tablero):** vista de comité — cuántos proyectos hay en cada etapa y su TIR/VPN agregado. El estado además **filtra** el portafolio.

**Herramienta estrella de pre-factibilidad — el lote como variable:**
- **Precio máximo de lote (breakeven):** ¿hasta cuánto puedo pagar por el lote para que el proyecto aún rinda el umbral objetivo? → es el **techo de negociación**.
- **Evaluar un precio concreto:** ingreso un precio que me ofrecen y veo si pasa el umbral.

**Gate de aprobación — checklist multicriterio** (pasa de Pre-fact → Aprobado solo si cumple **todos**):
- TIR del inversionista (equity) ≥ umbral · **Y** · VPN > 0 a la TIO · **Y** · margen ≥ mínimo.
- Al **registrar la decisión** (aprobar/rechazar + fecha) el proyecto cambia de estado (la trazabilidad rica del histórico vive en el modelo de datos, Fase 3).

**Comparar candidatos de pre-factibilidad:** rankear los candidatos entre sí por rentabilidad → con presupuesto limitado, **cuál lote comprar primero**.

## 1. Menú objetivo (19 secciones planas → 14 jerarquizadas)

```
TABLERO (portafolio · multi-proyecto)
  · Inicio
  · Pipeline / Embudo       (NUEVO — funnel por estado: Pre-fact→Aprobado→Construcción→Entregado, con TIR/VPN por etapa)
  · Portafolio              (tabs: Tarjetas | Mapa de valor | Tabla rankeable | Consolidado) · FILTRO por estado
  · Comparar proyectos      (NUEVO — multiselect 2-4 → lado a lado; modo "candidatos pre-fact" rankea cuál lote comprar)

FACTIBILIDAD (plan de un proyecto — se ADAPTA al estado)
  ▸ Definición:    Resumen ejecutivo (ex-Cockpit) · Datos del proyecto (+ Urbanístico) · Cronograma (+ Ingresos)
  ▸ Costos/result: Distribución de costos · P&G (+ Reparto al final)
  ▸ Financiación:  Tasa de descuento (WACC) · Flujo de caja · Crédito y apalancamiento
  ▸ Riesgo:        Riesgo y sensibilidad (tabs: Escenarios | Sensibilidad 2D | Tornado proyecto | Tornado inversionista | Monte Carlo)
  ▸ Decisión:      Decisión de inversión [SOLO pre-fact] — precio máx de lote + evaluar precio + checklist multicriterio + registrar ir/no-ir

SEGUIMIENTO (real — SOLO Construcción/Entregado; OCULTO en Pre-fact/Aprobado)
  · Monitor de ejecución    (tabs: Avance | Presupuesto | Crédito | Variaciones | Ventas[NUEVO])
  · Plan vs Real            (NUEVO — comparativo financiero por etapa)
  · Valor Ganado (EVM)

ADMINISTRACIÓN (SOLO los 2 admins — por email/SSO; oculto para el resto)
  · Ingreso de datos        (NUEVO — ÚNICO punto de captura; bloques ordenados desde la cabida)
```

> **Principio nuevo:** la edición deja de estar dispersa. Hoy se captura en 3 lugares (Datos del proyecto + las islas "Distribución de costos" y "Costo de capital"). En el norte, **todo el input vive en ADMINISTRACIÓN → Ingreso de datos** (admin-only) y las secciones de consumo (Tablero/Factibilidad/Seguimiento) pasan a **solo-lectura**.

## 1b. ADMINISTRACIÓN → Ingreso de datos (admin-only)

Pestaña independiente, **solo para los 2 administradores**, único punto de captura. Bloques en **orden lógico, empezando por la cabida del lote** (cada uno un expander; sirve para crear y para editar):

| # | Bloque | Captura |
|---|---|---|
| 1 | **Cabida urbanística del lote** | identificación (nombre/ubicación/zona/tipo/estado) · áreas (`lote_bruta`, `lote_util`, `m2_construidos`, `m2_vendibles`) · **costo** del lote (`lote_bruto_miles`) · KPIs urbanísticos en vivo |
| 2 | **Producto y ventas** | etapas o tipologías: unidades, precio, método (`$/und` ó `$/m²`) → ventas · ritmo (`vmes`, `frec`, `pe_pct`) |
| 3 | **Cronograma** | `fecha_inicio` de la etapa raíz ⚠️ · secuenciamiento (`sucesora`/`desfase`) · obra (`obra_offset`/`ic_offset`/`dur_obra`) · escrituración/entregas · curva PERT/Gauss |
| 4 | **Costos** | toggle **top-down** (% de ventas) ⇄ **bottom-up** (capítulos `directos_cap`/`indirectos_cap`) · gastos fijos de estructura |
| 5 | **Financiero y recaudo** | cuota inicial (`pct_ci`), separación, diferido · crédito (`cobertura_cc`, `tasa_credito_ea`) · `split_cg`, `renta`, `tio` |
| 6 | **Costo de capital (WACC)** | los ~14 parámetros del CAPM (escala en **puntos %**, ojo distinta a costos) |
| 7 | **Overrides auditados** *(avanzado)* | `fiducia.*` (FCL anual real) · `tir_apalancada_ref` — sobreescriben TIR/VPN |
| 8 | **Seguimiento real** *(solo construcción/entregado)* | `avance_real` y `costo_real` por etapa (alimentan EVM) |

**Acceso (por email/SSO, decisión del usuario):** no hay rol "admin" hoy (solo editor/viewer). Se crea un helper `es_admin()` junto a `gate()` que compara el email del login Microsoft (`st.session_state['_ms_user']`) contra una lista `ADMINS` en secretos. La pestaña se muestra y su cuerpo se ejecuta **solo** si `es_admin()`. *(El camino de contraseña es anónimo — no distingue personas; por eso va por SSO.)*

**Reglas de seguridad del módulo:**
- ⚠️ **Gate temporal**: sin `fecha_inicio` válida en la etapa raíz, el motor apaga recaudo/TIR/VPN/EVM → el bloque 3 debe exigirla/avisarla.
- **Validar en el borde** con `schema.parse(par)` **antes** de guardar (atrapa typos/tipos antes de que corrompan una cifra).
- **No perder campos sin widget** (hay subestructuras y costos que hoy se preservan solo porque viven en `par`): la migración debe conservarlos.
- **Tapar el hueco**: hoy un proyecto **nuevo no se puede guardar** en la nube — el módulo debe permitirlo.
- Persistencia **sin cambios**: se reutiliza el botón único que sube el JSON entero a Supabase.

> **Cabida — alcance por fases (decisión del usuario):** *ahora* el bloque 1 reorganiza la captura actual (áreas descriptivas + KPIs), **cero riesgo** al cálculo auditado. *Después*, en un paso dedicado y con red de pruebas, se agrega la **calculadora de cabida POT** (lote + índices/altura/aislamientos/cesiones → m² construibles/vendibles y unidades potenciales que pre-llenan el modelo) — el "estudio de cabida" real, clave en pre-factibilidad. Es una **capacidad nueva del motor**, separada de lo que hoy se audita.

## 2. Cambios clave (hoy → propuesto)
- **Cockpit → "Resumen ejecutivo"**, movido a la cabecera de Factibilidad (es por-proyecto, vivía mal en la capa de portafolio).
- **Proyectos activos + Portafolio (burbujas) → "Portafolio"** con tabs (Tarjetas | Mapa de valor | Tabla | Consolidado).
- **Escenarios + Monte Carlo + Sensibilidad → "Riesgo y sensibilidad"** con tabs (3 secciones = 1 idea) + **agregar el Tornado del inversionista (equity)**.
- **Costo de capital → "Tasa de descuento (WACC)"**, movido **ANTES** de Flujo (la tasa se define antes de descontar).
- **Urbanístico → tab/expander** en Datos · **Ingresos → tab** en Cronograma · **Reparto → bloque final de P&G** (absorber las casi-vacías, no cortar la narrativa).
- **NUEVO: Comparar proyectos** (Tablero) y **Plan vs Real** (Seguimiento).
- Quitar el ruido técnico de Supabase de la pantalla de Datos.

## 3. Capítulos a incorporar (priorizados por valor/costo al comité)

| # | Capítulo | Esfuerzo | Valor | ¿Datos nuevos? | Cuándo |
|---|---|---|---|---|---|
| **0** | **Estado + Pipeline/Embudo + filtro** — el eje rector (§0) | S | **Máximo** | Solo el campo `estado` (al schema) | **PRIMERO** (Fase 2) |
| **1** | **Decisión de inversión (pre-fact)** — lote breakeven + evaluar precio + checklist multicriterio | M | **Máximo** | No (motor; umbrales a config) | **Fase 2** |
| **2** | **Sensibilidad del inversionista (equity)** — Tornado/MC sobre TIR del socio | S | Alto | No (motor ya tiene `tir_equity`/`vpn_socio`) | Fase 2 |
| 3 | **Comparar candidatos pre-fact** (ranking para comprar lote) | S | Alto | No | Fase 2 |
| 4 | **Plan vs Real financiero por etapa** | M | Alto (proyectos en obra) | Sí (real por etapa, hoy stub) | tras modelo de datos |
| 5 | **Balance General contable** | L | Medio | No (se deriva de P&G + flujo) | después |
| 6 | **Informe de ventas** (tab en Monitor) | M | Alto en obra | Sí (ventas reales) | tras modelo de datos |
| 7 | **Calculadora de cabida (POT)** — lote+normas → m² y unidades potenciales que pre-llenan el modelo | L | Alto (pre-fact) | Sí (normas POT + nuevo sub-modelo) | paso dedicado, con red de pruebas |

> **Clave de orden:** los capítulos de **Factibilidad** (#1, #3) salen del motor sobre el `par` actual → se pueden hacer YA. Los de **Seguimiento** (#2, #4) necesitan **datos reales** que hoy están hardcodeados en `navarra_data.py` → requieren primero el modelo de datos (migrar a tablas Supabase). **NO añadir más hardcode.**

## 4. UX / claridad visual
- **Centralizar el formato**: una sola `fmt_cop(x)` y `fmt_pct(x, dec=1)` usadas sin excepción (hoy hay 3-4 formatos distintos → resta credibilidad).
- **Spinners** en el consolidado/burbujas (`show_spinner="Consolidando portafolio…"`) — a 15-20 proyectos es "se colgó" vs "está calculando".
- **Burbujas**: a 15-20 proyectos las etiquetas se solapan → etiquetas en hover, no siempre visibles.

## 5. Escalabilidad a 15-20 proyectos (sin sobre-ingeniería)
- **Carga batch cacheada**: hoy el sidebar hace N round-trips a Supabase por render (uno por proyecto) + el consolidado y las burbujas recargan TODO otra vez. Crear `cargar_todos()` (1 sola query `select slug,nombre,es_real,data`) y reutilizarla.
- **Invalidación dirigida de caché**: al guardar, hoy se hace `cache_data.clear()` GLOBAL (borra todos los Monte Carlo de todos los proyectos). Invalidar solo lo del proyecto editado.
- **Filtros/orden/búsqueda** en Portafolio (por tipo VIS/No VIS, estado greenfield/obra, orden por TIR) + **Comparar proyectos**.
- 15-20 proyectos caben en memoria → NO se necesita data-warehouse ni precómputo.

## Ruta para ejecutar el norte
0. **Fundamento** — ✅ **HECHO** (Paso 0): campo **`estado`** validado en `schema.py` + **umbrales de aprobación** en `config.py`, asignados a los 3 proyectos. 34 tests verdes.
1. **Fase 2 — Modularizar la UI hacia este menú** (las ~14 páginas + componentes/servicios). Incluye, en pasos seguros encadenados:
   - **1a Andamiaje**: estructura `ui/{pages,components,services}`, `app.py` como orquestador delgado, **formato único** (`fmt_cop`/`fmt_pct`), capa de servicios (`cargar_todos()` batch + invalidación dirigida), y el helper **`es_admin()`** (email/SSO) junto a `gate()`.
   - **1b ADMINISTRACIÓN → Ingreso de datos** (admin-only): centralizar TODA la captura (las 3 islas de edición → un módulo ordenado desde la cabida), validar con `schema.parse` antes de guardar, tapar el hueco del proyecto nuevo, y dejar las secciones de consumo en **solo-lectura**.
   - **1c Reorganización del menú** (19→14, WACC antes de Flujo, Riesgo con tabs) + **eje de ciclo de vida** (Pipeline/Embudo + filtro por estado + UI adaptativa por estado).
   - **1d Capítulos de Factibilidad**: **Decisión de inversión pre-fact** (#1), **Sensibilidad equity** (#2), **Comparar proyectos/candidatos** (#3).
   - *Cada paso verificado contra las anclas + humo de UI; branch+PR+CI+merge.*
2. **Fase 3 — Modelo de datos** (Supabase): habilita Seguimiento real/multi-proyecto + trazabilidad rica de la decisión (histórico aprobar/rechazar, quién/cuándo).
3. **Capítulos de Seguimiento** (#4 Plan vs Real, #6 Informe de ventas) + **#5 Balance General**.
4. **Fase 4 — Puertos ERP/CRM**.
