# Despliegue en Azure App Service + login de Microsoft (Entra ID)

Guía para el equipo de TI de CG. Objetivo: la app **no se duerme**, tiene **dominio propio** y el equipo
entra con su **cuenta de Microsoft de CG** (sin clave aparte). El código **no cambia**: la misma app de
Streamlit corre tal cual.

Resultado para el usuario: abre el link → "Continuar con Microsoft" (su cuenta CG) → adentro.
Los **1–2 editores** elevan a modo edición con la **clave de editor** dentro de la app.

---

## 1. Crear el App Service (Linux, Python) — ~5 min

**Portal:** Azure portal → *Create a resource* → *Web App*.
- **Publish:** Code · **Runtime stack:** Python 3.12 · **OS:** Linux
- **Pricing plan:** **Basic B1** (o superior) — *NO* uses Free F1: F1 se duerme. B1 (~USD 13/mes) está siempre activo.
- **Region:** la más cercana (p. ej. East US 2 / Brazil South).

**Equivalente Azure CLI:**
```bash
az group create -n rg-factibilidad -l brazilsouth
az appservice plan create -g rg-factibilidad -n plan-factibilidad --is-linux --sku B1
az webapp create -g rg-factibilidad -p plan-factibilidad -n cg-factibilidad --runtime "PYTHON:3.12"
```

## 2. Conectar el código (GitHub) — despliegue continuo

App Service → **Deployment Center** → Source: **GitHub** → repo **`DjmartinG/cg-factibilidad-app`**,
branch **`main`**. Cada push a `main` redespliega solo (igual que hoy en Streamlit Cloud).

> El repo ya trae `requirements.txt` y `startup.sh`. Asegúrate de que el build de paquetes corra:
> App settings → `SCM_DO_BUILD_DURING_DEPLOYMENT = true`.

## 3. Comando de arranque + WebSockets

App Service → **Configuration → General settings**:
- **Startup Command:** `startup.sh`
- **Web sockets:** **On**  ← imprescindible para Streamlit.

```bash
az webapp config set -g rg-factibilidad -n cg-factibilidad --startup-file "startup.sh"
az webapp config set -g rg-factibilidad -n cg-factibilidad --web-sockets-enabled true
```

## 4. Secretos como variables de entorno

App Service → **Settings → Environment variables (Application settings)** → agregar:

| Nombre | Valor |
|---|---|
| `SUPABASE_URL` | `https://jehkdhmngxvuvhxuhlan.supabase.co` |
| `SUPABASE_KEY` | *(la service_role del proyecto Supabase)* |
| `CLAVE_EDITOR` | *(la clave que tendrán los 1–2 editores)* |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

> `CLAVE_EQUIPO` **no es necesaria** aquí: el login de Microsoft (paso 5) ya controla quién entra.
> La app lee estos secretos desde variables de entorno automáticamente (no necesita `secrets.toml`).

```bash
az webapp config appsettings set -g rg-factibilidad -n cg-factibilidad --settings \
  SUPABASE_URL="https://jehkdhmngxvuvhxuhlan.supabase.co" \
  SUPABASE_KEY="<service_role>" \
  CLAVE_EDITOR="<clave-editor>" \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

## 5. Login de Microsoft (Easy Auth) — sin código

App Service → **Settings → Authentication** → **Add identity provider**:
- **Identity provider:** Microsoft
- **Tenant type:** Workforce · **App registration:** *Create new* (lo crea solo)
- **Supported account types:** **Current tenant — Single tenant** (solo CG).
- **Restrict access:** **Require authentication**
- **Unauthenticated requests:** **HTTP 302 redirect** (recomendado para sitios web).

Eso es todo: cualquier persona de la organización CG que abra el link entra; cualquiera fuera de CG es
rechazado. La app recibe la identidad del usuario por header `X-MS-CLIENT-PRINCIPAL-NAME` (ya está
contemplado en el código → entra como *consulta* automáticamente).

*(Opcional, para limitar a personas específicas y no a todo CG: Entra admin center → Enterprise applications
→ esta app → Properties → "Assignment required" = Yes → Users and groups → agregar solo a quienes deban entrar.)*

## 6. Dominio propio (opcional) — `factibilidad.cgconstructora.com`

App Service → **Custom domains** → Add → crear un **CNAME** en el DNS de cgconstructora.com apuntando a
`cg-factibilidad.azurewebsites.net` → App Service emite el certificado SSL gestionado (gratis).

---

## Verificación
1. Abre `https://cg-factibilidad.azurewebsites.net` en una ventana de incógnito → debe pedir login de Microsoft.
2. Entra con una cuenta **@cgconstructora.com** → carga el tablero (modo consulta), arriba dice "Conectado como …".
3. Una cuenta externa (otra organización / personal) debe ser **rechazada**.
4. Los 3 proyectos deben verse (vienen de Supabase vía las variables de entorno).

## Notas
- El **motor financiero** (Python) y los **datos** (Supabase) no cambian: esto solo mueve el *frontend* a un
  hosting estable con SSO. Si algún día se quiere volver a Streamlit Cloud, el código sigue siendo compatible.
- Si la app tarda en la primera carga tras un despliegue, es el arranque del contenedor (~30–60 s), no un error.
