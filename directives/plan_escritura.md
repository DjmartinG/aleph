# Directiva — Camino de ESCRITURA de ALEPH (Ingreso de datos)

> **Capa 1 (Directiva).** Plan de diseño del camino de escritura: pasar de un `/web` solo-lectura a
> uno que **crea y edita proyectos** (con validación, versionado y auditoría). Es el habilitador para
> **retirar Streamlit**. Diseñado con un workflow de 7 agentes (2 mapearon el estado actual, 5
> diseñaron: datos, API, seguridad, UX, roadmap) el 2026-06-13. **NO se toca el motor ni el dorado.**

## Objetivo
Que un **admin** pueda crear/editar un proyecto desde `/web` y **aprobarlo** (congelar su versión
oficial), reemplazando el único módulo de escritura del Streamlit (Ingreso de datos). Pensado para
**escalar**: multi-empresa, multi-usuario, auditable.

---

## Modelo de datos (objetivo, ya creado por `0001_aleph_schema.sql`)
```
companies → projects (con fase del ciclo de vida)
          → scenarios (versionados: draft → approved → baseline)
                       snapshot JSONB INMUTABLE al aprobar · un solo baseline por proyecto
          → results_cache (cifras del motor; clave = inputs_hash(snapshot)+engine_version)
          → actuals_* (datos ex-post de obra: avance/costo real — Fase 7)
          → audit_log (entity, action, actor=oid/email de Entra, diff, timestamp)
```
- **Editar un aprobado** = crear un escenario nuevo (version+1, draft) clonando el snapshot. Lo
  aprobado/baseline es **inmutable**.
- El JSON actual de cada proyecto **ya se migró** como escenario v1 approved (ETL `etl_import_v1.py`,
  Fase 4b — Navarra 37.60% idéntica, bit a bit).

## Decisiones clave de diseño (con su justificación)
1. **Validación = el motor.** El contrato del API reusa `aleph_engine.schema.parse()` (la MISMA
   compuerta que Streamlit) envuelto en un `field_validator` de Pydantic. Solo se añaden modelos de
   *sobre* (request/response) con `extra='forbid'`. Cero duplicación, cero datos malformados.
2. **Aprobar = el patrón del ETL ya probado.** `approve`: validar → `calcular(copia del par)` →
   snapshot inmutable + `results_cache` (engine_version + sha256 de inputs) + `audit_log`, **atómico
   vía RPC plpgsql** (una transacción, no varias llamadas REST).
3. **Inmutabilidad garantizada por la BD.** Trigger `BEFORE UPDATE` que rechaza cambios al
   snapshot/version cuando `status != 'draft'`. No es solo disciplina de app: es garantía dura.
4. **Concurrencia optimista (anti lost-update).** Columna `lock_version`/`updated_at` expuesta como
   **ETag**; las mutaciones exigen `If-Match`; `UPDATE ... WHERE lock_version = <esperado>`; 0 filas
   → **409/412 Conflict**. Nunca last-write-wins ciego (con varios admins se perderían cambios).
5. **Idempotencia.** Header `Idempotency-Key` + tabla `idempotency_keys` (TTL 24h) en POST creación y
   `:approve` (reintento misma key+body → respuesta cacheada; misma key+otro body → 409).
6. **Seguridad por roles.** 2 **app roles de Entra** en el app registration **del API** (no del Web):
   `admin` (crea/edita/aprueba) y `gerencia` (solo lectura), emitidos en el claim `roles`. El API
   aplica `require_admin` en **todos** los writes (gerencia = solo GET). **RLS en Supabase** queda
   *deny-by-default* como backstop; las políticas granulares por rol+`company_id` se diseñan y se
   activan en la Fase 4 (defensa en profundidad; la autorización primaria es del API).
7. **Auditoría confiable.** El actor (`oid`+`email` del JWT) lo escribe el API (no se confía en el
   cliente); además trigger `AFTER` que lee el actor de un GUC `app.actor` (`SET LOCAL`).
8. **PUT vs PATCH.** `PUT /v1/scenarios/{id}` reemplaza el snapshot entero (espeja el `st.form`);
   `PATCH` hace merge parcial por bloque (RFC 7386). Ambos **solo en draft**; el resultado mergeado
   se valida COMPLETO con `schema.parse` antes de persistir. approved/baseline → 409.

---

## Roadmap (8 fases · incremental · sin big-bang · estrangulamiento)
Cada fase termina **desplegada, verificable y con verificación simple de 3-5 pasos para Martin**.

| # | Fase | Qué entrega |
|---|---|---|
| **0** | Cerrar auth de `/v1` en prod | ✅ casi: Entra desplegado; falta `ALEPH_AUTH_REQUIRED=true` validado |
| **1** | **Cut-over de LECTURA a `scenarios.snapshot`** | API+Streamlit leen del modelo objetivo (baseline) en vez de `proyectos.data`, con `results_cache` primero. `proyectos` queda de espejo. Mismo dato → dorado verde por construcción. |
| **2** | **Escritura en el API** (draft→approve) | `POST /v1/projects`, `POST/PATCH /v1/scenarios/...`, `:approve`, `:baseline`. Cada write: valida con `schema.parse`, valida transición legal, audita, recomputa cache. Rol admin. **No** conectados a `/web` aún. |
| **3** | Concurrencia optimista + cache vivo | `If-Match`/version en PATCH → 409 si cambió; `results_cache` se recomputa al cambiar `inputs_hash`/`engine_version`. |
| **4** | RLS granular por rol en Supabase | Políticas por rol+`company_id`; el API pasa a token-on-behalf (deja `service_role` solo para ETL/batch). Defensa en profundidad. |
| **5** | **Ingreso de datos en `/web`** | Formularios server-action de los 8 bloques; validación cliente (zod) que espeja `schema.py`; **preview de cifras con etiqueta de base ANTES de aprobar**; cero cálculo en el front. Hito que habilita el corte. |
| **6** | Doble-escritura → corte de Streamlit-Ingreso | (6a) doble-escritura temporal a `scenarios` + espejo `proyectos`; (6b) Streamlit-Ingreso redirige a `/web` o read-only; (6c) cuando 0 escrituras por Streamlit (medible en `audit_log`), se deja de espejar. |
| **7** | Actuals / EVM / Monitor | `actuals_evm`/`actuals_recaudo` + carga (`fuente=manual\|excel\|erp\|crm`, `fecha_corte`). **Bloqueada por datos operativos**, no por código. EVM top-down (motor) vs comité bottom-up **sin fusionar**. |
| **8** | Multi-company + escala | Selección de company en `/web` (Entra→company), índices de escala, `results_cache` del portafolio consolidado. |

**Esfuerzo Fases 1-5 (lectura→escritura→`/web`):** ≈ 7-10 días, varias sesiones.

## Cómo NO romper el dorado (guardia permanente)
1. El motor `aleph_engine` **no se toca en ninguna fase** → `test_golden_harness` pasa por construcción.
2. Toda escritura pasa por `schema.parse(par)` ANTES de persistir.
3. El snapshot se guarda **bit a bit** (cero transformación).
4. Cada `approve` corre los **checks de cuadre** del motor (P&G suma, recaudo=ventas, flujo≈utilidad,
   SPI 0.4-2.0) y los guarda.
5. El CI corre engine+api+app (124 tests) en cada PR: desviación **>0.1% rompe el build**.

## Definición de "TERMINADO" por fase
(A) tests verdes incl. dorado · (B) checks de cuadre en verde en lo nuevo · (C) ninguna cifra sin
etiqueta de base · (D) desplegado con **tag=SHA** (nunca `:latest`), versión visible · (E)
verificación manual de 3-5 pasos para Martin (QUÉ abrir, QUÉ comparar, QUÉ valor esperar), con
verificación **independiente** (curl directo, no solo "responde 200": para escritura, confirmar que
la fila se creó Y que sus cifras cuadran).

## Lo que hace Martin (portal, requiere admin)
- Crear **2 app roles** (`admin`, `gerencia`) en el app registration **del API** en Entra y
  asignarlos a usuarios/grupos en *Enterprise applications → Users and groups* (Fase 2/4).
