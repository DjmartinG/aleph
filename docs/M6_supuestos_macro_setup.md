# M6 — Supuestos macro: pasos para dejarlo VIVO en produccion

El codigo esta completo (conectores + persistencia + endpoints + cron). Faltan 3 pasos de entorno:

## 1) Crear la tabla en Supabase
SQL Editor del proyecto Supabase -> pegar y ejecutar `db/migrations/0003_supuestos_macro.sql`.
("Success. No rows returned" = OK, es DDL.)

## 2) Configurar el token del cron (estable y seguro)
- Generar un secreto fuerte (p.ej. en una terminal: `openssl rand -hex 32`).
- App Service del API (`cg-aleph-api`, RG Cg-factibilidad) -> Configuracion -> app setting
  **`ALEPH_REFRESH_TOKEN`** = ese secreto. Reiniciar el App Service.
- GitHub -> repo `aleph` -> Settings -> Secrets and variables -> Actions -> New repository secret:
  - **`ALEPH_REFRESH_TOKEN`** = el MISMO secreto.
  - **`ALEPH_API_URL`** = base del API (p.ej. `https://cg-aleph-api.azurewebsites.net`).

## 3) Redeploy del API
Cloud Shell (mismo metodo de `api/DEPLOY.md`) para activar los endpoints `/v1/macro*` y `/macro/cron-refresh`.

## Como funciona el flujo
- El **dia 1 de cada mes** (o a mano desde Actions -> "Refresco mensual..." -> Run workflow) el cron
  llama `POST /macro/cron-refresh` con el token -> corre los conectores y **PROPONE** los valores
  (estado `por_validar`, NO vigentes). No aplica nada solo.
- Tu revisas: `GET /v1/macro/pendientes` (admin) -> y apruebas: `POST /v1/macro/aprobar`
  (admin Entra) con `{"claves": ["banrep:trm", "damodaran:crp:colombia", ...]}` -> pasan a vigentes.
- Consulta: `GET /v1/macro` -> los supuestos vigentes.

Seguridad: el token solo autoriza PROPONER (radio de dano minimo); cambiar lo vigente exige Entra admin.
