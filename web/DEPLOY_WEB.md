# Desplegar ALEPH /web en Vercel con login Microsoft Entra ID

Runbook para **Martin**. El `/web` (Next.js) se despliega en **Vercel**, exige
**login de Microsoft (Entra ID)** y consume el **API ya desplegado en Azure**
(`cg-aleph-api`). El navegador nunca ve cifras sin login; el `/web` reenvía el
token de Entra al API, que lo revalida.

```
Navegador ──login Microsoft──>  /web (Vercel, Next.js)  ──Bearer token──>  API (Azure, cg-aleph-api)  ──>  motor + datos
```

> **Config-driven:** en local, sin las variables de Entra, la auth queda
> APAGADA (no hay login; el `/web` habla con el API local que también está
> abierto). Definir las variables de Entra en Vercel ENCIENDE el login. No hay
> cambios de código entre dev y prod, solo variables.

> ✅ **DESPLEGADO EL 2026-06-13.** En producción: `https://aleph-4iiv.vercel.app`.

## Valores reales de CG (ya creados — NO secretos, son IDs públicos)

| Qué | Valor |
|---|---|
| Tenant ID (`ENTRA_TENANT_ID`, base del ISSUER) | `5c0ceba8-4397-49c8-a9fb-832860708337` |
| App registration **del API** `ALEPH API` (`API_AUDIENCE` + base del scope) | `5dccc7aa-8c5b-4a53-a2fe-4826062af4e5` |
| App registration **del Web** `ALEPH Web` (`AUTH_MICROSOFT_ENTRA_ID_ID`) | `e91870a2-71a0-4a1c-9c7b-9007d6161c4b` |
| Dominio de producción en Vercel | `aleph-4iiv.vercel.app` |

> El **client secret** del `ALEPH Web` (`AUTH_MICROSOFT_ENTRA_ID_SECRET`) NO se
> documenta aquí: vive solo en Vercel. Si se pierde, se crea otro en
> *Certificates & secrets* del `ALEPH Web`.

---

## 0) Lo que necesitas a la mano

- Acceso de **administrador** al tenant de Entra ID (el MISMO de la app actual).
- El **Application (client) ID del API** (la app registration que ya usa
  `cg-aleph-api`). Lo necesitarás para el *scope* y la *audiencia*.
- El **Tenant ID** (Directory ID).
- La cuenta de **Vercel** conectada al repo de GitHub `DjmartinG/aleph`.
- **Azure Cloud Shell** (para tocar el App Service del API; aquí no hay `az` local).

---

## 1) Entra ID — App registration del **API** (verificar/ajustar)

Ya existe (la usa el API). Hay que confirmar tres cosas. Entra admin center →
**Identity → Applications → App registrations → [la app del API]**.

### 1.1 Expose an API → scope `access_as_user`
- **Expose an API**. Si no hay **Application ID URI**, pulsa **Add** y acepta el
  por defecto `api://<API_APP_ID>` (NO debe terminar en `/`).
- Si no existe el scope, **Add a scope**:
  - **Scope name:** `access_as_user`
  - **Who can consent:** *Admins and users*
  - **Admin consent display name/description:** "Acceder al API de ALEPH como el usuario"
  - **State:** Enabled
- Anota el **scope completo**: `api://<API_APP_ID>/access_as_user`.

### 1.2 ⚠️ Token v2 — `accessTokenAcceptedVersion = 2` (CRÍTICO)
El API valida el issuer **v2** (`https://login.microsoftonline.com/<tenant>/v2.0`).
Si el manifiesto deja la versión en `null`/`1`, los tokens salen **v1** con issuer
`https://sts.windows.net/<tenant>/` y **TODO da 401**.

- App del API → **Manifest**.
- Busca `accessTokenAcceptedVersion` (formato AAD) o `requestedAccessTokenVersion`
  (formato Microsoft Graph) y ponlo en **`2`**. **Save**.

### 1.3 Audiencia de los tokens v2
Con tokens **v2**, el claim `aud` del token **es el Application (client) ID del
API (un GUID)** — no la URI `api://...`. Por eso en el App Service (paso 3.2) la
variable `API_AUDIENCE` debe ser **ese GUID**, no `api://...`.

---

## 2) Entra ID — App registration del **WEB** (crear nueva)

Es una app registration DISTINTA, para que los usuarios inicien sesión en el `/web`.

1. **App registrations → New registration**
   - **Name:** `ALEPH Web`
   - **Supported account types:** *Accounts in this organizational directory only* (single tenant)
   - **Redirect URI:** plataforma **Web** →
     `https://<DOMINIO_VERCEL>/api/auth/callback/microsoft-entra-id`
     (pon primero el dominio que te dé Vercel; puedes añadir el dominio
     definitivo después en **Authentication → Add URI**).
   - **Register**.
2. Copia el **Application (client) ID** → será `AUTH_MICROSOFT_ENTRA_ID_ID`.
3. **Certificates & secrets → New client secret** → copia el **Value**
   inmediatamente (no se vuelve a mostrar) → será `AUTH_MICROSOFT_ENTRA_ID_SECRET`.
4. **API permissions → Add a permission → My APIs →** selecciona la app del **API**
   → **Delegated permissions** → marca **`access_as_user`** → **Add permissions**.
5. **Grant admin consent for [tenant]** → **Yes** (verifica el ✓ verde "Granted").

> Cuando el dominio final de Vercel esté listo, vuelve a **Authentication** del
> `ALEPH Web` y añade su redirect URI exacto (`.../api/auth/callback/microsoft-entra-id`).
> Si el redirect no coincide al carácter, Microsoft devuelve `AADSTS50011`.

---

## 3) Variables de entorno

### 3.1 En Vercel — proyecto `/web`
Project → **Settings → Environment Variables** (entorno **Production**, y
**Preview** si quieres que las preview también pidan login). Todas están
documentadas en [`.env.example`](.env.example).

| Variable | Valor | De dónde sale |
|---|---|---|
| `ALEPH_API_URL` | `https://cg-aleph-api.azurewebsites.net` | URL del App Service del API |
| `ALEPH_API_SCOPE` | `api://<API_APP_ID>/access_as_user` | scope del paso 1.1 |
| `AUTH_SECRET` | (cadena aleatoria) | genera con `npx auth secret` u `openssl rand -base64 33` |
| `AUTH_MICROSOFT_ENTRA_ID_ID` | client ID del **ALEPH Web** | paso 2.2 |
| `AUTH_MICROSOFT_ENTRA_ID_SECRET` | secret del **ALEPH Web** | paso 2.3 |
| `AUTH_MICROSOFT_ENTRA_ID_ISSUER` | `https://login.microsoftonline.com/<TENANT_ID>/v2.0` | tenant (SIN barra final) |
| `AUTH_URL` *(opcional, recomendado en prod)* | `https://<DOMINIO_VERCEL>` | el dominio canónico |

> `AUTH_URL` no es estrictamente necesario en Vercel (Auth.js confía en el host),
> pero fijarlo al dominio canónico evita sorpresas con el redirect.

### 3.2 En el App Service del **API** (verificar/setear en Cloud Shell)
El API debe quedar en **fail-closed** (exige auth) y con la audiencia v2 correcta.

```bash
# Encuentra el grupo de recursos del API si no lo recuerdas:
az webapp list --query "[?name=='cg-aleph-api'].{rg:resourceGroup}" -o table

RG=<grupo_de_recursos_del_API>     # probablemente Cg-factibilidad

az webapp config appsettings set -g $RG -n cg-aleph-api --settings \
  ENTRA_TENANT_ID="<TENANT_ID>" \
  API_AUDIENCE="<API_APP_ID>" \
  ALEPH_AUTH_REQUIRED="true"
# API_AUDIENCE = Application (client) ID del API (GUID), NO api://...  (tokens v2)

# Verifica:
az webapp config appsettings list -g $RG -n cg-aleph-api \
  --query "[?name=='ENTRA_TENANT_ID' || name=='API_AUDIENCE' || name=='ALEPH_AUTH_REQUIRED']" -o table
```

> Opcional (defensa extra): `ALEPH_ALLOWED_AZP="<WEB_APP_CLIENT_ID>"` restringe
> que SOLO el `/web` pueda llamar al API. `ALEPH_ADMINS="correo1,correo2"` marca
> admins. No CORS: el `/web` llama al API desde el servidor (no desde el navegador).

---

## 4) Desplegar en Vercel

1. Vercel → **Add New… → Project** → importa `DjmartinG/aleph`.
2. **Root Directory:** `web`  ← clave (el repo es un monorepo; Vercel auto-detecta
   Next.js dentro de `web/`). No hace falta `vercel.json`.
3. **Environment Variables:** pega las del paso 3.1.
4. **Deploy.** Cuando termine, copia el dominio (`https://<algo>.vercel.app`) y:
   - si difiere del que registraste, añádelo en el redirect URI del `ALEPH Web`
     (paso 2 / nota) **y** en `AUTH_URL`, y **redeploy**.

---

## 5) Cómo verificar (end to end)

1. Abre `https://<DOMINIO_VERCEL>/` en una ventana de incógnito.
   → Debe **redirigir al login de Microsoft** (no debe mostrar cifras sin login).
2. Inicia sesión con una cuenta del tenant.
   → Vuelve al **dashboard de Portafolio** con las cifras (Navarra, consolidado…).
3. Entra a un proyecto (p. ej. `/proyectos/navarra`): la ficha carga resultados.
4. Prueba el API directo SIN token (debe rechazar):
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" https://cg-aleph-api.azurewebsites.net/v1/portfolio
   # Esperado: 401  (y /version responde 200, es público)
   ```
   Si da **200**, el API está abierto → revisa `ALEPH_AUTH_REQUIRED`/`API_AUDIENCE` (paso 3.2).
5. (Opcional) Verifica el footer de versión del `/web`.

---

## 6) Rollback en Vercel (promover el despliegue anterior)

Si un deploy sale mal, **no** hay que revertir git: Vercel guarda todos los
despliegues y puedes volver al anterior en segundos.

1. Vercel → proyecto `/web` → pestaña **Deployments**.
2. Localiza el último despliegue **Ready** que funcionaba (por fecha/commit).
3. Menú **⋯ → Promote to Production** (o **Rollback** si aparece).
4. Confirma. El dominio de producción apunta de inmediato al despliegue anterior.

> El rollback de Vercel cambia a qué build apunta el dominio; no toca el código
> del repo ni el API. Para corregir de raíz, arregla, commitea y vuelve a desplegar.

---

## 7) Checklist final

- [ ] API: `accessTokenAcceptedVersion = 2` en el manifiesto (1.2).
- [ ] API: scope `access_as_user` expuesto (1.1).
- [ ] API App Service: `ENTRA_TENANT_ID`, `API_AUDIENCE`(=GUID del API), `ALEPH_AUTH_REQUIRED=true` (3.2).
- [ ] Web app registration: redirect URI `.../api/auth/callback/microsoft-entra-id`, secret, permiso `access_as_user`, **admin consent** (2).
- [ ] Vercel: Root Directory=`web` + las 6–7 variables (3.1).
- [ ] Verificación end-to-end (5) + `curl /v1/portfolio` sin token = 401.

## Troubleshooting

| Síntoma | Causa probable | Arreglo |
|---|---|---|
| API responde **401** con token válido | Token **v1** (issuer `sts.windows.net`) | `accessTokenAcceptedVersion=2` (1.2) |
| API responde **401**, "audience" | `API_AUDIENCE` ≠ GUID del API | poner el **Application (client) ID** del API, no `api://...` (3.2) |
| API responde **503** | `ALEPH_AUTH_REQUIRED=true` pero falta `ENTRA_TENANT_ID`/`API_AUDIENCE` | setéalas (3.2) |
| `AADSTS50011` redirect mismatch | redirect URI no coincide exacto | añade `https://<dominio>/api/auth/callback/microsoft-entra-id` (2) |
| `AADSTS65001` consent required | falta admin consent del permiso al API | **Grant admin consent** (2.5) |
| Bucle de login / "sesión expiró" repetido | el access token no se acepta en el API | revisa 1.2 + 3.2 (v2 + audiencia) |
| Login OK pero el dashboard no carga datos | `ALEPH_API_URL` mal, o el API caído | verifica la URL y `GET /version` del API |
| Vercel: build **falla en ~2 s** (`framework=other`) | Root Directory quedó en `./`, no en `web` | Project → Settings → Build and Deployment → **Root Directory = `web`** (+ Framework = Next.js) → Redeploy |
| No encuentro `requestedAccessTokenVersion` en el manifiesto | el manifiesto está en formato **AAD Graph** | edita **`accessTokenAcceptedVersion`** (en la raíz) = `2`; pista: si ves `replyUrlsWithType` es AAD Graph |
| El API no aparece en **"Mis API"** al dar permiso | propagación de Entra (app recién creada) | usa la pestaña **"API usadas en mi organización"** y busca por el **GUID** del API |
| No encuentro el "Id. de aplicación (cliente)" | abriste la **Aplicación web** (App Service), no el **Registro de aplicaciones** | el client ID vive en **Microsoft Entra ID → Registros de aplicaciones** (mismo nombre, recurso distinto) |
