# api — FastAPI

Envuelve `aleph_engine` y los datos (Supabase/Postgres). Contrato **OpenAPI versionado**. Auth: valida
tokens de **Entra ID** (mismo tenant que el App Service actual). NO reimplementa fórmulas — solo expone el motor.

> **Estado:** esqueleto. Se construye en **PROMPT 4**. Contrato de lectura propuesto en
> `../directives/plan_migracion.md` §5. Deploy por SHA a un App Service nuevo `cg-aleph-api`.
