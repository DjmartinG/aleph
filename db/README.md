# db — migración de datos (PROMPT 4 · Fase 4b)

Lleva los proyectos del modelo plano actual (tabla `proyectos`) al modelo de la constitución
(`companies` → `projects` → `scenarios` versionados → `results_cache` + `actuals_*` + `audit_log`).

| Archivo | Qué hace |
|---|---|
| `migrations/0001_aleph_schema.sql` | Crea las tablas nuevas (idempotente). **NO toca `proyectos`**. |
| `etl_import_v1.py` | Lee `proyectos`, valida, e importa cada uno como `project` + `scenario v1 approved` + `results_cache`. Idempotente. |

## Es SEGURO
- **Aditivo:** crea tablas nuevas; la tabla `proyectos` y el Streamlit siguen **igual** (compatibilidad).
- **Sin pérdida:** el `snapshot` del escenario guarda el `par` **bit a bit**; las cifras se recalculan
  con el **mismo motor** (`aleph_engine`) → imposible que la migración mueva una cifra dorada.
- **Idempotente:** re-ejecutar no duplica (upsert por slug + escenario v1 único por proyecto).

## Cómo ejecutarla (elige UN camino)

**A · Autocontenido (recomendado — no necesita conectar nada a Claude):**
1. En el **SQL Editor de Supabase** de tu proyecto, pega y corre `migrations/0001_aleph_schema.sql`.
2. Desde la raíz del repo:  `python db/etl_import_v1.py`
   (usa `SUPABASE_URL`/`SUPABASE_KEY` del entorno o de `app_streamlit/.streamlit/secrets.toml`).

**B · Vía MCP de Claude:** conecta la BD `jehkdhmngxvuvhxuhlan` a la integración Supabase de Claude.ai;
entonces el agente corre la migración con `apply_migration` y guía el ETL (versionado y reversible por MCP).

## Verificación (gate dorado)
El ETL imprime, por proyecto, **TIR proyecto · VPN · crédito máx**. Confirma que **Navarra dé
TIR proyecto 37.60%** (iguales a producción). Igual = migración correcta.

## Después (fases siguientes, NO en este paso)
- Adaptar `storage.py`/`repo.py` a fachada que lea de `scenarios` (cut-over) y escriba `draft` + `audit_log`.
- Políticas RLS granulares por rol cuando `/web` acceda con tokens de usuario.

> **Estado:** preparado, **NO ejecutado** (requiere acceso a la BD de la app). Nada corre hasta que tú
> apliques el SQL + el ETL (camino A) o conectes la BD al MCP (camino B).
