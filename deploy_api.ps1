# deploy_api.ps1 — despliega la API FastAPI (`aleph_api`) a Azure App Service con TAG = SHA (Windows / PowerShell).
#   Uso:  .\deploy_api.ps1        (desde la raíz del monorepo, con la working tree LIMPIA)
#
# Despliegue del API (PROMPT 4 · Fase 4d). tag = SHA del commit (deploy
# determinista, regla 4): imagen trazable + tag único => App Service SIEMPRE re-baja la imagen.
#
# La imagen (Dockerfile.api) BUNDLEA el motor (engine/) + la API (api/aleph_api/) => contexto = raíz.
# A diferencia del Streamlit, el API NO usa Easy Auth: /version es PÚBLICO => health check REAL.
#
# PRIMER deploy: si el App Service `cg-aleph-api` no existe, este script construye la imagen e imprime
# el runbook de provisión (ver api/DEPLOY.md). No setea secretos por su cuenta.
$ErrorActionPreference = "Stop"

# Recursos Azure (reusa el grupo/plan/registry del Streamlit; el App Service es nuevo: cg-aleph-api).
$RG         = "Cg-factibilidad"
$PLAN       = "ASP-Cgfactibilidad-b208"              # plan B1 existente (puede hospedar varias apps)
$APP        = "cg-aleph-api"                          # App Service NUEVO para la API
$ACR        = "cgfactibilidadacr"                     # nombre corto del registry (para `az acr build`)
$ACR_LOGIN  = "cgfactibilidadacr.azurecr.io"          # login server completo (para el nombre de imagen)
$IMAGE      = "alephapi"
$ACR_URL    = "https://cgfactibilidadacr.azurecr.io"
$URL        = "https://cg-aleph-api.azurewebsites.net"
$DOCKERFILE = "Dockerfile.api"                        # en la raíz; bundlea engine/ + api/aleph_api/
$CONTEXT    = "."                                     # contexto = raíz del monorepo

Set-Location -Path (& git rev-parse --show-toplevel)

# --- Prerrequisitos ---
if (-not (Get-Command az  -ErrorAction SilentlyContinue)) { Write-Host "Falta Azure CLI (az). Usa Azure Cloud Shell (ver api/DEPLOY.md) o instala az + 'az login'." -ForegroundColor Red; exit 1 }
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Host "Falta git." -ForegroundColor Red; exit 1 }

# --- Gate: working tree limpia (el tag = SHA debe REPRESENTAR la imagen) ---
if (& git status --porcelain) {
  Write-Host "Hay cambios sin commitear. Haz commit antes de desplegar:" -ForegroundColor Red
  & git status --short
  exit 1
}

$Tag = (& git rev-parse --short=12 HEAD).Trim()
$Ver = (Select-String -Path "api\aleph_api\__init__.py" -Pattern '\d+\.\d+\.\d+' | Select-Object -First 1).Matches[0].Value
$Img = "$ACR_LOGIN/$IMAGE`:$Tag"

Write-Host "==> Proyecto:  $APP"
Write-Host "==> Commit:    $(& git rev-parse HEAD)"
Write-Host "==> Imagen:    $Img     (versión API: v$Ver)`n"

# --- 1) Build en ACR (en la nube; no requiere Docker local) ---
Write-Host "==> [1/4] Construyendo imagen en ACR (contexto = raíz, $DOCKERFILE)…" -ForegroundColor Cyan
az acr build --registry $ACR --image "$IMAGE`:$Tag" --file $DOCKERFILE $CONTEXT
if ($LASTEXITCODE -ne 0) { throw "Falló az acr build" }

# --- ¿Existe el App Service? Si no, es el PRIMER deploy: provisión manual (una vez). ---
$existe = az webapp show --resource-group $RG --name $APP --query name -o tsv 2>$null
if (-not $existe) {
  Write-Host "`n==> El App Service '$APP' NO existe todavía (primer deploy)." -ForegroundColor Yellow
  Write-Host "    La imagen YA quedó construida: $Img"
  Write-Host "    Provisiona el App Service UNA vez (rellena los secretos) — ver api/DEPLOY.md (Parte B).`n"
  Write-Host "    Flags VIGENTES (no uses --deployment-container-image-name; está deprecado):"
  Write-Host "    az webapp create -g $RG -p $PLAN -n $APP --container-image-name $Img ``"
  Write-Host "      --container-registry-url $ACR_URL --container-registry-user <ACR_USER> --container-registry-password <ACR_PASS>"
  Write-Host "    az webapp config appsettings set -g $RG -n $APP --settings WEBSITES_PORT=8000 ALEPH_DATA_REQUIRED=true ``"
  Write-Host "      SUPABASE_URL=<tu-url> SUPABASE_KEY=<service_role>     # (auth Entra: Parte B-2 de DEPLOY.md)"
  Write-Host "    az webapp restart -g $RG -n $APP"
  Write-Host "`n    Verifica con /health/data (project_count>0), no solo /version. Luego re-corre este script para redeploys." -ForegroundColor Yellow
  exit 0
}

# --- 2) Apuntar App Service al tag EXACTO (no :latest) ---
$PrevImg = (az webapp config container show --resource-group $RG --name $APP `
  --query "[?name=='DOCKER_CUSTOM_IMAGE_NAME'].value | [0]" -o tsv)
Write-Host "==> [2/4] Apuntando App Service a $Img…" -ForegroundColor Cyan
az webapp config container set --resource-group $RG --name $APP `
  --container-image-name "$ACR_LOGIN/$IMAGE`:$Tag" --container-registry-url $ACR_URL
if ($LASTEXITCODE -ne 0) { throw "Falló az webapp config container set" }

# --- 3) Reiniciar ---
Write-Host "==> [3/4] Reiniciando…" -ForegroundColor Cyan
az webapp restart --resource-group $RG --name $APP

# --- 4) Health check REAL (/version es público; el API no tiene Easy Auth) ---
Write-Host "==> [4/4] Verificando $URL/version (hasta ~90s)…" -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 18; $i++) {
  Start-Sleep -Seconds 5
  try {
    $r = Invoke-RestMethod -Uri "$URL/version" -TimeoutSec 8 -ErrorAction Stop
    if ($r.name -eq "aleph-api") {
      Write-Host "`nOK API viva.  /version => name=$($r.name) version=$($r.version) engine=$($r.engine_version)" -ForegroundColor Green
      $ok = $true; break
    }
  } catch { }
}

Write-Host ""
if ($ok) {
  # Health de DATOS: /version NO prueba que lea Supabase. Confirmar project_count>0 (la imagen no trae respaldo local).
  $count = -1
  try { $count = [int](Invoke-RestMethod -Uri "$URL/health/data" -TimeoutSec 8 -ErrorAction Stop).project_count } catch { }
  if ($count -ge 1) {
    Write-Host "OK DATOS.  /health/data => project_count=$count" -ForegroundColor Green
  } else {
    Write-Host "AVISO: el contenedor arrancó pero /health/data no reporta proyectos (project_count=$count)." -ForegroundColor Yellow
    Write-Host "       Revisa SUPABASE_URL/KEY en app settings y los logs (az webapp log tail -g $RG -n $APP)."
  }
  Write-Host "   URL:     $URL/version  ·  $URL/health/data  ·  $URL/docs"
  Write-Host "   Imagen:  $Img"
  Write-Host "   Confirma que version=v$Ver."
} else {
  Write-Host "   /version no respondió OK en el tiempo esperado." -ForegroundColor Red
  Write-Host "   Logs:     az webapp log tail -g $RG -n $APP"
  Write-Host "   ROLLBACK:"
  if ($PrevImg -and $PrevImg -ne "$ACR_LOGIN/$IMAGE`:$Tag") {
    Write-Host "     az webapp config container set -g $RG -n $APP --container-image-name `"$PrevImg`" --container-registry-url $ACR_URL"
    Write-Host "     az webapp restart -g $RG -n $APP"
  } else {
    Write-Host "     (imagen previa no detectada; revisa el portal -> Deployment Center)"
  }
}
