#!/usr/bin/env bash
# deploy_streamlit.sh — despliega la app Streamlit a Azure App Service con TAG = SHA del commit.
#   Uso:  ./deploy_streamlit.sh        (desde la raíz del monorepo, con la working tree LIMPIA)
#
# Por qué tag = SHA (constitución §migración, regla 4 "DEPLOY DETERMINISTA"):
#   - La imagen queda etiquetada con el commit exacto → reproducible y trazable (nunca ":latest").
#   - Cada deploy usa un tag ÚNICO → App Service SIEMPRE baja la imagen nueva. Esto ESQUIVA el gotcha
#     conocido: con ":latest", App Service cachea el digest viejo y `restart` no re-baja la imagen.
#
# PROMPT 3 · bloque 2: la imagen ahora BUNDLEA el motor `aleph_engine` (engine/) + la app
# (app_streamlit/). Por eso el contexto de build es la RAÍZ del monorepo y el Dockerfile es
# `Dockerfile.streamlit`.
#
# Flujo: gate de working-tree limpia → az acr build (en la nube, sin Docker local) → captura de la
#        imagen ACTUAL (para rollback) → container set al tag exacto → restart → health check
#        (rollback automático sugerido si falla).
#
# Recursos Azure (de los aprendizajes 2026-06-11/12). Cámbialos aquí si migran:
RG="Cg-factibilidad"
APP="cg-factibilidad-app"
ACR="cgfactibilidadacr"                          # nombre corto del registry (para `az acr build`)
ACR_LOGIN="cgfactibilidadacr.azurecr.io"         # login server completo (para el nombre de imagen)
IMAGE="cgapp"
ACR_URL="https://cgfactibilidadacr.azurecr.io"
URL="https://cg-factibilidad-app.azurewebsites.net"
DOCKERFILE="Dockerfile.streamlit"                # en la raíz; bundlea engine/ + app_streamlit/
CONTEXT="."                                      # contexto = raíz del monorepo

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# --- Prerrequisitos ---
command -v az  >/dev/null 2>&1 || { echo "❌ Falta Azure CLI (az). Instálalo y corre 'az login'."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Falta git."; exit 1; }

# --- Gate: working tree limpia (el tag = SHA debe REPRESENTAR la imagen que se construye) ---
if [ -n "$(git status --porcelain)" ]; then
  echo "❌ Hay cambios sin commitear. Haz commit antes de desplegar:"
  echo "     el contenido que se sube a ACR debe coincidir con el commit que da el tag."
  git status --short
  exit 1
fi

TAG="$(git rev-parse --short=12 HEAD)"
VER="$(grep -oE '[0-9]+\.[0-9]+\.[0-9]+' engine/aleph_engine/__init__.py | head -1)"
IMG="$ACR_LOGIN/$IMAGE:$TAG"

echo "==> Proyecto:  $APP"
echo "==> Commit:    $(git rev-parse HEAD)"
echo "==> Imagen:    $IMG     (versión app: v$VER)"
echo ""

# --- 1) Build en ACR (en la nube; no requiere Docker local) ---
echo "==> [1/4] Construyendo imagen en ACR (contexto = raíz, $DOCKERFILE)…"
az acr build --registry "$ACR" --image "$IMAGE:$TAG" --file "$DOCKERFILE" "$CONTEXT"

# --- Captura la imagen ACTUAL del App Service (destino de rollback si el deploy nuevo falla) ---
PREV_IMG="$(az webapp config container show --resource-group "$RG" --name "$APP" \
  --query "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value | [0]" -o tsv 2>/dev/null || true)"

# --- 2) Apuntar App Service al tag EXACTO (no :latest) ---
echo "==> [2/4] Apuntando App Service a $IMG…"
az webapp config container set \
  --resource-group "$RG" --name "$APP" \
  --container-image-name "$ACR_LOGIN/$IMAGE:$TAG" \
  --container-registry-url "$ACR_URL"

# --- 3) Reiniciar ---
echo "==> [3/4] Reiniciando…"
az webapp restart --resource-group "$RG" --name "$APP"

# --- 4) Verificación ---
# OJO: la app corre detrás de Easy Auth (login de Microsoft) → un health check ANÓNIMO devuelve la
# página de login (200/302) AUNQUE el contenedor esté roto = falso positivo. Por eso verificamos por
# el ESTADO del App Service + confirmación visual en el navegador (donde sí tienes sesión).
echo "==> [4/4] Esperando arranque del contenedor (~40s)…"
sleep 40
ESTADO="$(az webapp show --resource-group "$RG" --name "$APP" --query state -o tsv 2>/dev/null || echo '?')"

echo ""
echo "✅ Deploy enviado.  App Service: $ESTADO"
echo "   URL:     $URL"
echo "   Imagen:  $IMG"
echo ""
echo "   VERIFICA TÚ (no se puede automatizar tras Easy Auth):"
echo "     1) Abre $URL con tu cuenta CG."
echo "     2) Confirma el pie:  «Aplicativo v$VER»."
echo "     3) Revisa el tablero de Navarra: cifras idénticas a antes (TIR proyecto 37.60%, etc.)."
echo ""
echo "   Si la app NO carga / queda en error → ROLLBACK a la imagen anterior:"
if [ -n "${PREV_IMG:-}" ] && [ "$PREV_IMG" != "$ACR_LOGIN/$IMAGE:$TAG" ]; then
  echo "     az webapp config container set -g $RG -n $APP --container-image-name \"$PREV_IMG\" --container-registry-url $ACR_URL"
else
  echo "     (imagen previa no detectada; míra el portal → Deployment Center para el tag anterior)"
fi
echo "     az webapp restart -g $RG -n $APP"
echo ""
echo "   ¿Arranque lento o con error? Mira los logs:  az webapp log tail -g $RG -n $APP"
