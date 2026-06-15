# Runbook — Sincronizar el WACC 18.71% (y M1-M8) en producción · jun-2026

**Objetivo:** que prod muestre el WACC re-baselizado (18.71%) y el resto del trabajo M1-M8, sin mover el
dorado. Lo corre **Martín** (el agente no tiene `az`). Diseñado y verificado adversarialmente.

## Por qué hacen falta DOS cosas (no solo el redeploy)

Prod lee el `par` de cada proyecto desde **`scenarios.snapshot` en Supabase** (modelo objetivo), y el API
**recalcula en vivo** con el motor desplegado (`build.cargar_calcular` NO usa caché). Hay dos desfases:

| Desfase | Qué arregla | Cómo se arregla |
|---|---|---|
| **Código** (motor de prod es pre-M1-M8) | `tir_equity` (fix flujo_equity PR#22), exención VIS, vehículos, etc. | **Redeploy** del API |
| **Dato** (snapshot congelado por el ETL del 12-jun, pre-M1) | inputs del WACC (`rf/rm/rp/kd_us`) | **Refresco** (crea scenario v2 approved) |

> **El WACC 18.71% sale del DATO** (kd_us=5.9 y rp=3.43 van explícitos en el par v2; la fórmula no cambió),
> así que el refresco lo muestra **aunque el motor sea viejo**. Pero `tir_equity`/VIS dependen del CÓDIGO →
> el redeploy es **obligatorio**. **Si refrescas el dato sin redeployar = estado Frankenstein** (WACC bien,
> `tir_equity`/VIS viejos). Por eso el orden es **REDEPLOY primero, REFRESCO después**.

---

## Paso 0 (opcional) — ver qué tiene prod hoy

Pega en el **SQL Editor de Supabase** (read-only):

```sql
select p.slug, s.version, s.status,
       s.snapshot->'financiero'->'wacc'->>'rf'    as rf,
       s.snapshot->'financiero'->'wacc'->>'rp'    as rp,
       s.snapshot->'financiero'->'wacc'->>'kd_us' as kd_us
from scenarios s join projects p on p.id = s.project_id
where p.slug in ('1_navarra','2_dominica','3_torres_campinas')
order by p.slug, s.version desc;
```

Si solo aparece `version=1` con `rf=0.12` (o `rp=2.85`, `kd_us` vacío) → confirma que prod está pre-cambio.

---

## Paso 1 — REDEPLOY del API (Azure Cloud Shell, Bash)

Trae el motor M1-M8 (incluye el fix de flujo_equity y el WACC). SHA = `2c533db` (el commit del re-baseline;
o el HEAD actual de main: `git rev-parse --short main`).

```bash
RG=Cg-factibilidad; APP=cg-aleph-api; ACR=cgfactibilidadacr
ACR_LOGIN=cgfactibilidadacr.azurecr.io; SHA=2c533db
az acr build --registry $ACR --image alephapi:$SHA \
  --file Dockerfile.api https://github.com/DjmartinG/aleph.git#main
az webapp config container set -g $RG -n $APP \
  --container-image-name $ACR_LOGIN/alephapi:$SHA \
  --container-registry-url https://$ACR_LOGIN
az webapp restart -g $RG -n $APP
```

**Verifica** (públicos, no exponen cifras):

```bash
curl -fsS https://cg-aleph-api.azurewebsites.net/version       # {"version":"0.1.0","engine_version":"2.39.0"}
curl -fsS https://cg-aleph-api.azurewebsites.net/health/data   # {data_source:supabase, project_count:3, read_model:scenarios}
```

> Tras este paso, prod sigue leyendo el par v1 (WACC viejo, que es exhibición) PERO ya con el motor nuevo →
> `tir_equity`/VIS quedan CORRECTOS. Nunca hay cifras de decisión viejas. El WACC se corrige en el Paso 2.

---

## Paso 2 — REFRESCO del dato (tu terminal local, en `c:\Code\aleph`)

Crea un **scenario v2 approved** por proyecto con el `par` actual (de tus `*_REAL.json` locales). Las
credenciales las toma de `app_streamlit/.streamlit/secrets.toml` (o de `SUPABASE_URL`/`SUPABASE_KEY`).

```powershell
# una sola vez (si no están):
pip install -e ./engine ; pip install supabase

# 2a) GATE DORADO local (sin tocar Supabase): confirma que los 3 dan WACC 18.71% y decisión intacta
python db/refresh_scenarios.py --check-only

# 2b) DRY-RUN (no escribe): muestra qué versión crearía en cada proyecto
python db/refresh_scenarios.py

# 2c) APLICAR (escribe scenarios v2 approved). Aborta solo si el gate dorado no cuadra.
python db/refresh_scenarios.py --apply
```

El script es **idempotente** (si el par vigente ya es el actual, hace SKIP) y **aborta antes de escribir**
si alguna cifra no reproduce el golden. Respeta la inmutabilidad (inserta v2, no edita v1).

---

## Paso 3 — Verificar el WACC 18.71% en prod

`/v1` está cerrado por auth Entra (no hay CLI pública para el WACC). Verifica en la **UI logueado**:

1. Abre el `/web` (Vercel) y entra con tu cuenta Microsoft.
2. Navega a **Navarra → Costo de capital** → debe decir **WACC 18.71%** (antes 17.31% o 21.54%).
3. Confirma que TIR proyecto sigue **37.60%** y TIR socio **41.72%** (dorado intacto).

---

## Rollback (si algo sale mal)

**Del redeploy** (API no arranca / cifras raras) — vuelve al tag anterior:

```bash
az webapp config container set -g Cg-factibilidad -n cg-aleph-api \
  --container-image-name cgfactibilidadacr.azurecr.io/alephapi:db47a7e \
  --container-registry-url https://cgfactibilidadacr.azurecr.io
az webapp restart -g Cg-factibilidad -n cg-aleph-api
```

**Del dato** (volver al WACC anterior) — el v2 es inmutable; NO lo borres a la ligera. La forma limpia es
**crear un v3** con el par viejo (revertir `kd_us`/`rp` en el JSON local y volver a correr el refresco). La
reversión total (borrar el v2) solo por SQL directo y auditándolo:
`delete from scenarios where project_id = (select id from projects where slug='1_navarra') and version = 2;`

---

## Notas

- Argos (4º proyecto, M8) NO está en prod (`project_count:3`); su alta es un paso aparte.
- El `kd_cop` (~27%) y el VPN secundario @WACC quedan como observaciones a validar (ver acta WACC2).
- Revertir el redeploy NO toca el dato; revertir el dato NO toca el código: son independientes.
