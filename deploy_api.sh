#!/usr/bin/env bash
# deploy_api.sh — despliega la API FastAPI (`aleph_api`) a Azure App Service con TAG = SHA del commit.
#   Uso:  ./deploy_api.sh        (desde la raíz del monorepo, con la working tree LIMPIA)
#
# Hermano de deploy_streamlit.sh, para el API (PROMPT 4 · Fase 4d). tag = SHA (deploy determinista,
# regla 4): imagen trazable + tag único => App Service SIEMPRE re-baja la imagen (esquiva el digest
# cacheado de ":latest").
#
# La imagen (Dockerfile.api) BUNDLEA el motor (engine/) + la API (api/aleph_api/) => contexto = raíz.
# A diferencia del Streamlit, el API NO usa Easy Auth: /version es PÚBLICO => health check REAL.
#
# PRIMER deploy: si el App Service `cg-aleph-api` no existe, construye la imagen e imprime el runbook
# de provisión (ver api/DEPLOY.md). No setea secretos por su cuenta.
RG="Cg-factibilidad"
PLAN="ASP-Cgfactibilidad-b208"                   # plan B1 existente (puede hospedar varias apps)
APP="cg-aleph-api"                               # App Service NUEVO para la API
ACR="cgfactibilidadacr"                          # nombre corto del registry (para `az acr build`)
ACR_LOGIN="cgfactibilidadacr.azurecr.io"         # login server completo (para el nombre de imagen)
IMAGE="alephapi"
ACR_URL="https://cgfactibilidadacr.azurecr.io"
URL="https://cg-aleph-api.azurewebsites.net"
DOCKERFILE="Dockerfile.api"                      # en la raíz; bundlea engine/ + api/aleph_api/
CONTEXT="."                                      # contexto = raíz del monorepo

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# --- Prerrequisitos ---
command -v az  >/dev/null 2>&1 || { echo "❌ Falta Azure CLI (az). Usa Azure Cloud Shell (ver api/DEPLOY.md) o instala az + 'az login'."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Falta git."; exit 1; }

# --- Gate: working tree limpia (el tag = SHA debe REPRESENTAR la imagen que se construye) ---
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Hay cambios sin commitear. Haz commit antes de desplegar:"
  git status --short
  exit 1
fi

TAG="$(git rev-parse --short=12 HEAD)"
VER="$(grep -oE '[0-9]+\.[0-9]+\.[0-9]+' api/aleph_api/__init__.py | head -1)"
IMG="$ACR_LOGIN/$IMAGE:$TAG"

echo "==> Proyecto:  $APP"
echo "==> Commit:    $(git rev-parse HEAD)"
echo "==> Imagen:    $IMG     (versión API: v$VER)"
echo ""

# --- 1) Build en ACR (en la nube; no requiere Docker local) ---
echo "==> [1/4] Construyendo imagen en ACR (contexto = raíz, $DOCKERFILE)…"
az acr build --registry "$ACR" --image "$IMAGE:$TAG" --file "$DOCKERFILE" "$CONTEXT"

# --- ¿Existe el App Service? Si no, es el PRIMER deploy: provisión manual (una sola vez). ---
if ! az webapp show --resource-group "$RG" --name "$APP" --query name -o tsv >/dev/null 2>&1; then
  echo ""
  echo "==> El App Service '$APP' NO existe todavía (primer deploy)."
  echo "    La imagen YA quedó construida: $IMG"
  echo "    Provisiona el App Service UNA vez (rellena los secretos) — ver api/DEPLOY.md:"
  echo ""
  echo "    az webapp create -g $RG -p $PLAN -n $APP --deployment-container-image-name $IMG"
  echo "    az webapp config appsettings set -g $RG -n $APP --settings WEBSITES_PORT=8000 \\"
  echo "      SUPABASE_URL=<tu-url> SUPABASE_KEY=<service_role> \\"
  echo "      ENTRA_TENANT_ID=<guid-tenant> API_AUDIENCE=<app-id-uri-o-client-id> ALEPH_AUTH_REQUIRED=true"
  echo "    az webapp restart -g $RG -n $APP"
  echo ""
  echo "    Luego vuelve a correr este script para los redeploys (ya solo actualizará la imagen)."
  exit 0
fi

# --- 2) Apuntar App Service al tag EXACTO (no :latest) ---
PREV_IMG="$(az webapp config container show --resource-group "$RG" --name "$APP" \
  --query "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value | [0]" -o tsv 2>/dev/null || true)"
echo "==> [2/4] Apuntando App Service a $IMG…"
az webapp config container set \
  --resource-group "$RG" --name "$APP" \
  --container-image-name "$ACR_LOGIN/$IMAGE:$TAG" \
  --container-registry-url "$ACR_URL"

# --- 3) Reiniciar ---
echo "==> [3/4] Reiniciando…"
az webapp restart --resource-group "$RG" --name "$APP"

# --- 4) Health check REAL (/version es público; el API no tiene Easy Auth) ---
echo "==> [4/4] Verificando $URL/version (hasta ~90s)…"
OK=0
for _ in $(seq 1 18); do
  sleep 5
  if curl -fsS --max-time 8 "$URL/version" 2>/dev/null | grep -q '"aleph-api"'; then
    echo ""
    echo "✅ API viva.  $URL/version respondió:"
    curl -fsS --max-time 8 "$URL/version"; echo ""
    OK=1; break
  fi
done

echo ""
if [ "$OK" = "1" ]; then
  echo "   URL:     $URL/version   y   $URL/docs"
  echo "   Imagen:  $IMG"
  echo "   Confirma que version=v$VER."
else
  echo "❌ /version no respondió OK en el tiempo esperado."
  echo "   Logs:     az webapp log tail -g $RG -n $APP"
  echo "   ROLLBACK:"
  if [ -n "${PREV_IMG:-}" ] && [ "$PREV_IMG" != "$ACR_LOGIN/$IMAGE:$TAG" ]; then
    echo "     az webapp config container set -g $RG -n $APP --container-image-name \"$PREV_IMG\" --container-registry-url $ACR_URL"
    echo "     az webapp restart -g $RG -n $APP"
  else
    echo "     (imagen previa no detectada; revisa el portal → Deployment Center)"
  fi
fi
