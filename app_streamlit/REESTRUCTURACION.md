# Plan de Reestructuración por Fases — App "Evaluación Financiera de Proyectos" (CG Constructora)

> **Documento para gerencia y equipo técnico.** Objetivo: llevar la app en producción (Streamlit + motor propio + Supabase + Azure) desde un estado funcional-pero-frágil hacia una arquitectura empresarial mantenible, **sin romper jamás las cifras auditadas** (anclas Navarra UO 11.362.332 / TIR 0,376 / VPN 18.280.687; Dominica TIR 0,5655) y **sin sobre-ingeniería** (escala real: 15-20 proyectos, ~10 usuarios internos).
>
> Generado a partir de un diagnóstico multi-agente del código real (motor, UI, datos, infra) el 2026-06-11.

## Principio rector: la red de seguridad va primero

**No se mueve una sola línea del motor hasta que existan golden tests que claven las cifras auditadas y pasen en verde contra el código actual tal cual está.** Toda fase posterior se valida corriendo esa suite. Si una ancla cambia, se revierte el paso. Esto convierte una refactorización riesgosa en una segura.

---

## FASE 0 — Blindaje del motor: golden tests + CI mínimo
**ESFUERZO: S** · **VA PRIMERO** porque es la red de seguridad de todo lo demás. Hoy las anclas viven solo como números en docstrings y se validan a mano con scripts fuera del repo. **No cambia ni una línea de lógica: solo añade pruebas.**

**Entregables:**
- `pyproject.toml` (pytest + ruff, fuente única de versión).
- `tests/test_anclas.py`: carga `par` reales (Navarra/Dominica), llama `engine.calcular(par)` y hace `assert` sobre UO/TIR/VPN auditados.
- `tests/fixtures/`: dicts `par` mínimos versionados (sin exponer los JSON confidenciales).
- `tests/test_ui_humo.py`: AppTest (rol inyectado + monkeypatch `option_menu`) → 0 excepciones en las ~19 secciones.
- `.github/workflows/ci.yml`: ruff → `compileall` (atrapa SyntaxError) → pytest, como *required check* en `main`.
- `.dockerignore` (hoy ausente): excluir secrets, `proyectos_privados/`, `*_REAL*.json`, `.git`, `tests/`.

---

## FASE 1 — Motor a paquete limpio, tipado y único (`cg_engine`)
**ESFUERZO: L** · Con la red de Fase 0 en verde, se toca el motor con confianza. El motor ya está bien desacoplado (no importa streamlit/pandas/plotly); falta consolidar duplicaciones y formalizar el contrato.

**Pasos atómicos (cada uno corre la suite de anclas):**
1. Mover a `src/cg_engine/` (sin tocar lógica), verificar anclas + `streamlit run` + rebuild.
2. `finanzas.py` — **una sola TIR/VPN/WACC**: hoy la TIR está en 3-4 implementaciones; probar que coinciden sobre los flujos reales y **recién entonces** unificar. Mover `calcular_wacc` aquí elimina el ciclo de import modelo↔apalancamiento.
3. `config.py` + `errors.py`: centralizar constantes mágicas (horizontes 96/180, defaults). Reemplazar `except Exception: return {}` por excepciones de dominio capturadas solo en la capa de servicios. Arreglar `evm.py` (`hoy` fijo → `date.today()`).
4. `schema.py` (Pydantic en el BORDE): modelos del dominio derivados de las claves reales; valida una vez al entrar; el motor sigue recibiendo dict. Añadir `schema_version`.
5. `flujo.py` — kernel único de flujo (unificar el bucle duplicado entre `flujo_caja` y `flujo_apalancado`, manteniendo curva/horizonte como parámetros).
6. `pyproject.toml` del motor: `cg_engine` instalable, `__version__` como **fuente única de versión** (hoy hay 3 distintas).

---

## FASE 2 — UI modular (Streamlit multipage + servicios + componentes)
**ESFUERZO: L** · Un `app.py` de 1.414 líneas es imposible de revisar/testear/integrar. Va después del motor porque la UI lo consumirá ya limpio.

**Entregables:**
- `app.py` mínimo (~80 líneas): config + tema + router.
- `pages/` (multipage nativo): un archivo por sección (lazy-load → deja de recalcular TODO el modelo en cada rerun).
- `services/`: único puente UI↔motor↔datos (`proyecto_service` con caché, `portafolio_service` — migra `consolidado`/`puntos_portafolio`/`_irr_anual` de la UI al motor, `auth_service` puro y testeable).
- `components/`: extraer el HTML/CSS inline (kpi, alertas, semáforos, formato).
- `state.py`: centralizar las 26 claves de `session_state`.
- `adapters/repo_proyectos.py`: `storage.py` como repositorio.

---

## FASE 3 — Modelo de datos profesional en Supabase
**ESFUERZO: M** · Enfoque **híbrido** (NO normalización total: el `data jsonb` se mantiene; se añaden columnas relacionales solo para identidad/gobernanza/permisos — normalizar obligaría a reescribir el motor).

**Entregables (3 anillos):**
- **Identidad/gobernanza:** `id uuid`, `slug` único, `schema_version`, `lock_version` (concurrencia optimista), y claves foráneas estables `erp_project_id`/`crm_opportunity_id`/`pa_nit` (para cruzar con sistemas externos).
- **Auditoría append-only:** `proyecto_versiones` (historial/revert/comparar), `corridas` (materializa UO/TIR/VPN + `motor_version` → las anclas pasan a ser filas consultables).
- **Identidad real:** tabla `usuarios` por email (el `X-MS-CLIENT-PRINCIPAL-NAME` de Entra que ya llega); `updated_by` deja de ser literal `'editor'`; RLS por email.
- Migración con golden assert inline (aborta si UO/TIR/VPN cambian). `guardar()` valida + UPDATE condicionado por `lock_version` + INSERT en versiones. `listar_ligero()` (hoy carga TODOS los proyectos solo para el selector). Crear proyecto en la nube (slugify). Fallback que marca su origen.

---

## FASE 4 — Arquitectura LISTA para ERP/CRM (puertos definidos, integraciones NO construidas)
**ESFUERZO: M** (solo andamiaje) · Patrón hexagonal liviano (puertos/adaptadores). **NO** API REST propia ni microservicios ni colas.

**Entregables:**
- Paquete `integracion/`: `puertos.py` (DTOs canónicos — `VentaUnidad`, `CostoEjecutado`, `AvanceObra`, `DesembolsoCredito`, `AsientoContable`); `adaptadores/` (placeholders documentados `sinco.py`/`siigo.py`/`crm.py`, firma `fetch()→list[DTO]`, soportar pull-API **y** ingest-de-archivo/Excel); `assembler.py` (`cargar_par(slug, fecha_corte)` rellena lo que el motor ya espera — `avance_real`, `costo_real` — sin tocar `calcular(par)`).
- Tablas hijas time-series en Supabase (creadas vacías): `ventas_real`, `costo_ejecutado`, `avance_obra`, `credito_mov`, `contabilidad_mov` con upsert idempotente; `proyecto_xref` (mapeo 1:N obra↔modelo).
- Migrar `navarra_data.py` (datos hardcodeados de un proyecto) a filas → el Monitor se vuelve multi-proyecto sin editar código.
- `test_assembler.py`: **no-regresión** — proyecto sin datos de integración == resultado de hoy.
- `directives/sincronizar_erp_crm.md`: endpoints, credenciales, cadencia, regla "real pisa supuesto solo para seguimiento, nunca para la factibilidad base".

---

## FASE 5 — CI/CD completo + rotación de secretos
**ESFUERZO: M** · Automatiza y endurece sobre toda la base.

**Entregables:**
- Pin de dependencias (`requirements.lock`) → build reproducible.
- `deploy.yml`: solo por tag `v*` con aprobación; OIDC GitHub↔Azure (sin secretos de larga vida) → `az acr build` → `az webapp config container set` → health check.
- Versión unificada (tag Git = imagen = `__version__` = CHANGELOG).
- **Rotar la `service_role` de Supabase** (bypassa RLS, no expira, vive en OneDrive): nuevas claves a GitHub Secrets + App Service, eliminar el JWT viejo.
- `USER` no-root en el Dockerfile.

---

## Principios de arquitectura
1. Fuente única de verdad (toda la matemática en `cg_engine/`).
2. Golden tests antes que refactor.
3. Las anclas son DATOS, no código (override de fiducia como dato; el motor es genérico).
4. Validar en el borde (Pydantic), no en el kernel (dicts puros).
5. Dependencias unidireccionales (`pages → services → cg_engine`; el motor no importa la app).
6. Separar supuestos (blob del usuario) de datos de origen (tablas hijas sincronizadas).
7. Puertos canónicos, adaptadores intercambiables (cambiar de ERP = otro adaptador).
8. Trazabilidad e idempotencia (versionado, identidad real, upsert idempotente).
9. Degradar visible, nunca en silencio.

## Qué NO hacer
- NO refactorizar el motor antes de tener los golden tests en verde.
- NO normalizar el dominio a tablas relacionales completas (obligaría a reescribir el motor).
- NO reescribir en React ni cambiar de framework.
- NO microservicios / Kubernetes / FastAPI propio / colas / webhooks always-on.
- NO construir los adaptadores ERP/CRM reales en este roadmap (solo puertos + assembler).
- NO desplegar a prod en cada push a `main` (solo tag `v*` con aprobación).
- NO tocar la rama del override de fiducia ni los slugs existentes.
- NO unificar la TIR antes de probar que las implementaciones coinciden.
- NO dejar la `service_role` en OneDrive.

## Secuencia
| Fase | Foco | Esfuerzo | Dependencia |
|------|------|----------|-------------|
| **0** | Golden tests + CI mínimo (red de seguridad) | **S** | Ninguna — empieza ya |
| **1** | Motor `cg_engine` limpio, tipado, TIR única | **L** | Fase 0 verde |
| **2** | UI modular (multipage + servicios + componentes) | **L** | Fase 1 |
| **3** | Datos Supabase (gobernanza/auditoría/identidad) | **M** | Fases 1 y 2 |
| **4** | Puertos ERP/CRM definidos (sin integraciones) | **M** | Fase 3 |
| **5** | CI/CD completo + rotación de secretos | **M** | Transversal |

**Camino crítico:** 0 → 1 → 2 → 3 → 4, con 5 como cierre transversal. Fase 0 es bloqueante y barata: debe hacerse de inmediato.
