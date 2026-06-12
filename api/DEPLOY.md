# Deploy del API (`cg-aleph-api`) — PROMPT 4 · Fase 4d

Despliega la API FastAPI (`aleph_api`) a un **App Service nuevo** (`cg-aleph-api`), reusando el grupo,
el plan B1 y el registry del Streamlit. La imagen (`Dockerfile.api`) bundlea el motor + la API.

> **Camino probado:** Azure **Cloud Shell** + `az acr build` desde GitHub (el repo `aleph` es público).
> No necesitas `az` local ni Docker. Mismo método con el que se desplegó el Streamlit.
> Alternativa local (si algún día tienes `az` instalado): `./deploy_api.sh` o `.\deploy_api.ps1`.

Recursos (mismos del Streamlit, App Service nuevo):

| | valor |
|---|---|
| Grupo (RG) | `Cg-factibilidad` |
| Plan | `ASP-Cgfactibilidad-b208` (B1, ya hospeda el Streamlit; puede tener varias apps) |
| Registry (ACR) | `cgfactibilidadacr` · login `cgfactibilidadacr.azurecr.io` |
| Imagen | `alephapi:<SHA>` |
| App Service | `cg-aleph-api` → `https://cg-aleph-api.azurewebsites.net` |

---

## Parte A — Registrar la app de la API en Entra ID (una sola vez)

Da los valores `ENTRA_TENANT_ID` + `API_AUDIENCE` que activan la auth (4c). Si aún no lo tienes listo,
puedes hacer la Parte B con la auth apagada y volver aquí después (ver nota al final de la Parte B).

1. Portal Azure → **Microsoft Entra ID** → **App registrations** → **New registration**.
   Nombre: `ALEPH API`. Cuenta: *Single tenant*. Crear.
2. En la app creada, anota el **Directory (tenant) ID** → ese es `ENTRA_TENANT_ID`.
3. **Expose an API** → *Add* un **Application ID URI** (acepta el sugerido `api://<client-id>`).
   Ese URI (o el client-id) es `API_AUDIENCE`.
4. **Add a scope** (p. ej. `access_as_user`) para que el `/web` pueda pedir el token más adelante.

(La validación del token —firma RS256 vía JWKS, `aud`, `iss`, `tid`, `exp`— ya está en `auth.py`.)

---

## Parte B — Primer deploy (Cloud Shell)

Abre **Azure Cloud Shell** (icono `>_` arriba en el portal; elige **Bash**). El `$SHA` lo sacas del
último commit en GitHub (o usa `main` para el tag y vuelve a etiquetar después si quieres trazar el SHA).

```bash
# 0) Variables (rellena los <...>; el SHA = commit corto que vas a desplegar)
RG=Cg-factibilidad
PLAN=ASP-Cgfactibilidad-b208
APP=cg-aleph-api
ACR=cgfactibilidadacr
ACR_LOGIN=cgfactibilidadacr.azurecr.io
SHA=<pega-el-SHA-corto-del-commit>        # p.ej. f8c0d0c… (12 chars)
IMG=$ACR_LOGIN/alephapi:$SHA

# 1) Construir la imagen en ACR DESDE GitHub (no sube nada local; el repo es público)
az acr build --registry $ACR --image alephapi:$SHA \
  --file Dockerfile.api https://github.com/DjmartinG/aleph.git#main

# 2) Credenciales del registry (para que el App Service pueda bajar la imagen)
ACR_USER=$(az acr credential show -n $ACR --query username -o tsv)
ACR_PASS=$(az acr credential show -n $ACR --query 'passwords[0].value' -o tsv)

# 3) Crear el App Service apuntando a la imagen
az webapp create -g $RG -p $PLAN -n $APP \
  --deployment-container-image-name $IMG \
  --docker-registry-server-user $ACR_USER \
  --docker-registry-server-password $ACR_PASS

# 4) App settings — PRIMER deploy con auth APAGADA (validar lectura primero; se cierra en la Parte B-2).
#    Solo puerto + datos (Supabase). SUPABASE_KEY = la service_role (la misma del Streamlit).
az webapp config appsettings set -g $RG -n $APP --settings \
  WEBSITES_PORT=8000 \
  SUPABASE_URL=https://jehkdhmngxvuvhxuhlan.supabase.co \
  SUPABASE_KEY=<service_role_key>

# 5) Reiniciar
az webapp restart -g $RG -n $APP
```

**Verificar (health check real — `/version` es público):**

```bash
curl -fsS https://cg-aleph-api.azurewebsites.net/version
# Esperado: {"name":"aleph-api","version":"0.1.0","engine_version":"2.39.0"}

# Con la auth apagada, /v1 también responde (lee los datos migrados):
curl -fsS https://cg-aleph-api.azurewebsites.net/v1/portfolio | head -c 400
```

También abre `https://cg-aleph-api.azurewebsites.net/docs` (OpenAPI interactivo).

---

## Parte B-2 — Cerrar la auth (después de validar la lectura)

Cuando `/version` y `/v1/portfolio` respondan bien, haz la **Parte A** (registrar la app en Entra) y
**cierra** la API añadiendo las 3 variables (queda *fail-closed*):

```bash
az webapp config appsettings set -g $RG -n $APP --settings \
  ENTRA_TENANT_ID=<tenant-id-de-la-Parte-A> \
  API_AUDIENCE=<api://client-id-de-la-Parte-A> \
  ALEPH_AUTH_REQUIRED=true \
  ALEPH_CORS_ORIGINS=https://cg-factibilidad-app.azurewebsites.net
az webapp restart -g $RG -n $APP

# Ahora /version sigue público, pero /v1 sin token => 401; con token Bearer de Entra => 200.
curl -fsS https://cg-aleph-api.azurewebsites.net/v1/portfolio   # debe dar 401 (sin token)
```

---

## Parte C — Redeploys (cada cambio nuevo)

```bash
RG=Cg-factibilidad; APP=cg-aleph-api; ACR=cgfactibilidadacr
ACR_LOGIN=cgfactibilidadacr.azurecr.io; SHA=<nuevo-SHA>
az acr build --registry $ACR --image alephapi:$SHA \
  --file Dockerfile.api https://github.com/DjmartinG/aleph.git#main
az webapp config container set -g $RG -n $APP \
  --container-image-name $ACR_LOGIN/alephapi:$SHA \
  --container-registry-url https://$ACR_LOGIN
az webapp restart -g $RG -n $APP
curl -fsS https://cg-aleph-api.azurewebsites.net/version   # confirma engine/version
```

El tag = SHA único hace que App Service SIEMPRE baje la imagen nueva (esquiva el digest cacheado).

## Parte D — Rollback / logs

```bash
# Volver al tag anterior (míralo en el portal → Deployment Center):
az webapp config container set -g $RG -n $APP \
  --container-image-name cgfactibilidadacr.azurecr.io/alephapi:<SHA_ANTERIOR> \
  --container-registry-url https://cgfactibilidadacr.azurecr.io
az webapp restart -g $RG -n $APP

# Logs en vivo (arranque/errores):
az webapp log tail -g $RG -n $APP
```
