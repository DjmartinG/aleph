# deploy_streamlit.ps1 — despliega la app Streamlit a Azure App Service con TAG = SHA (Windows / PowerShell).
#   Uso:  .\deploy_streamlit.ps1       (desde la raíz del monorepo, con la working tree LIMPIA)
#
# Equivalente nativo de deploy_streamlit.sh. tag = SHA del commit (deploy determinista, regla 4 de la
# migración): imagen trazable + tag único => App Service SIEMPRE re-baja la imagen (esquiva el gotcha
# del digest cacheado de ":latest").
#
# PROMPT 3 · bloque 2: la imagen BUNDLEA el motor aleph_engine (engine/) + la app (app_streamlit/) =>
# contexto de build = raíz del monorepo, Dockerfile = Dockerfile.streamlit.
$ErrorActionPreference = "Stop"

# Recursos Azure (de los aprendizajes 2026-06-11/12). Cámbialos aquí si migran:
$RG         = "Cg-factibilidad"
$APP        = "cg-factibilidad-app"
$ACR        = "cgfactibilidadacr"                    # nombre corto del registry (para `az acr build`)
$ACR_LOGIN  = "cgfactibilidadacr.azurecr.io"         # login server completo (para el nombre de imagen)
$IMAGE      = "cgapp"
$ACR_URL    = "https://cgfactibilidadacr.azurecr.io"
$URL        = "https://cg-factibilidad-app.azurewebsites.net"
$DOCKERFILE = "Dockerfile.streamlit"                 # en la raíz; bundlea engine/ + app_streamlit/
$CONTEXT    = "."                                     # contexto = raíz del monorepo

Set-Location -Path (& git rev-parse --show-toplevel)

# --- Prerrequisitos ---
if (-not (Get-Command az  -ErrorAction SilentlyContinue)) { Write-Host "Falta Azure CLI (az). Instálalo y corre 'az login'." -ForegroundColor Red; exit 1 }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Host "Falta git." -ForegroundColor Red; exit 1 }

# --- Gate: working tree limpia (el tag = SHA debe REPRESENTAR la imagen) ---
if (& git status --porcelain) {
  Write-Host "Hay cambios sin commitear. Haz commit antes de desplegar:" -ForegroundColor Red
  Write-Host "  el contenido que se sube a ACR debe coincidir con el commit que da el tag."
  & git status --short
  exit 1
}

$Tag = (& git rev-parse --short=12 HEAD).Trim()
$Ver = (Select-String -Path "engine\aleph_engine\__init__.py" -Pattern '\d+\.\d+\.\d+' | Select-Object -First 1).Matches[0].Value
$Img = "$ACR_LOGIN/$IMAGE`:$Tag"

Write-Host "==> Proyecto:  $APP"
Write-Host "==> Commit:    $(& git rev-parse HEAD)"
Write-Host "==> Imagen:    $Img     (versión app: v$Ver)`n"

# --- 1) Build en ACR (en la nube; no requiere Docker local) ---
Write-Host "==> [1/4] Construyendo imagen en ACR (contexto = raíz, $DOCKERFILE)…" -ForegroundColor Cyan
az acr build --registry $ACR --image "$IMAGE`:$Tag" --file $DOCKERFILE $CONTEXT
if ($LASTEXITCODE -ne 0) { throw "Falló az acr build" }

# --- Captura la imagen ACTUAL (destino de rollback si el deploy nuevo falla) ---
$PrevImg = (az webapp config container show --resource-group $RG --name $APP `
  --query "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value | [0]" -o tsv)

# --- 2) Apuntar App Service al tag EXACTO (no :latest) ---
Write-Host "==> [2/4] Apuntando App Service a $Img…" -ForegroundColor Cyan
az webapp config container set --resource-group $RG --name $APP `
  --container-image-name "$ACR_LOGIN/$IMAGE`:$Tag" --container-registry-url $ACR_URL
if ($LASTEXITCODE -ne 0) { throw "Falló az webapp config container set" }

# --- 3) Reiniciar ---
Write-Host "==> [3/4] Reiniciando…" -ForegroundColor Cyan
az webapp restart --resource-group $RG --name $APP

# --- 4) Verificación ---
# OJO: la app corre detrás de Easy Auth (login de Microsoft) -> un health check ANONIMO devuelve la
# pagina de login (200/302) AUNQUE el contenedor este roto = falso positivo. Verificamos por el ESTADO
# del App Service + confirmacion visual en el navegador (donde si tienes sesion).
Write-Host "==> [4/4] Esperando arranque del contenedor (~40s)…" -ForegroundColor Cyan
Start-Sleep -Seconds 40
$Estado = az webapp show --resource-group $RG --name $APP --query state -o tsv 2>$null

Write-Host ""
Write-Host "OK Deploy enviado.  App Service: $Estado" -ForegroundColor Green
Write-Host "   URL:     $URL"
Write-Host "   Imagen:  $Img"
Write-Host ""
Write-Host "   VERIFICA TU (no se puede automatizar tras Easy Auth):" -ForegroundColor Yellow
Write-Host "     1) Abre $URL con tu cuenta CG."
Write-Host "     2) Confirma el pie:  «Aplicativo v$Ver»."
Write-Host "     3) Revisa el tablero de Navarra: cifras identicas a antes (TIR proyecto 37.60%, etc.)."
Write-Host ""
Write-Host "   Si la app NO carga / queda en error -> ROLLBACK a la imagen anterior:"
if ($PrevImg -and $PrevImg -ne "$ACR_LOGIN/$IMAGE`:$Tag") {
  Write-Host "     az webapp config container set -g $RG -n $APP --container-image-name `"$PrevImg`" --container-registry-url $ACR_URL"
} else {
  Write-Host "     (imagen previa no detectada; mira el portal -> Deployment Center para el tag anterior)"
}
Write-Host "     az webapp restart -g $RG -n $APP"
Write-Host ""
Write-Host "   Arranque lento o con error? Mira los logs:  az webapp log tail -g $RG -n $APP"
