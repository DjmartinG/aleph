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
```

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
0. **Fundamento (al inicio de Fase 2):** agregar el campo **`estado`** al contrato (`schema.py`) con default sensato para los 6 proyectos actuales, y los **umbrales de aprobación** a `config.py`. Es pequeño y habilita todo lo demás.
1. **Fase 2 — Modularizar la UI hacia este menú** (las ~14 páginas + componentes/servicios), incluyendo: la reorganización, el **eje de ciclo de vida** (Pipeline/Embudo + filtro por estado + UI adaptativa), la **Decisión de inversión pre-fact** (#1), la **Sensibilidad equity** (#2), **Comparar proyectos/candidatos** (#3), y los arreglos de UX/escala (formato único, carga batch, invalidación dirigida, spinners). *Todo verificado contra las anclas + humo de UI.*
2. **Fase 3 — Modelo de datos** (Supabase): habilita Seguimiento real/multi-proyecto + trazabilidad rica de la decisión (histórico aprobar/rechazar, quién/cuándo).
3. **Capítulos de Seguimiento** (#4 Plan vs Real, #6 Informe de ventas) + **#5 Balance General**.
4. **Fase 4 — Puertos ERP/CRM**.
