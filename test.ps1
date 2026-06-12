# test.ps1 — corre TODA la red de pruebas del monorepo antes de desplegar (Windows / PowerShell).
#   Uso:  .\test.ps1          (desde la raíz del monorepo)
#
# Equivalente nativo de test.sh. Valida lo mismo que el CI más el harness del engine:
#   1) engine  2) app_streamlit  3) ruff. El SNAPSHOT DORADO es sagrado: rojo => NO desplegar.
$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$ok = $false
try { & $Py -c "import sys; assert sys.version_info[:2] >= (3, 12)"; $ok = ($LASTEXITCODE -eq 0) } catch { $ok = $false }
if (-not $ok) { $Py = "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" }

# Asegura pytest (no está en requirements.txt).
& $Py -c "import pytest" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "==> instalando pytest…"; & $Py -m pip install -q pytest }
# El motor (aleph_engine) debe estar instalado: la app, la API y el harness del engine lo importan.
& $Py -c "import aleph_engine" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "==> instalando el motor aleph_engine…"; & $Py -m pip install -e ./engine }
# Deps de la API (Fase 4a).
& $Py -c "import fastapi, httpx" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "==> instalando fastapi/httpx (API)…"; & $Py -m pip install -q fastapi httpx }

$fail = 0

Write-Host "`n================  1/4  engine (aleph_engine)  ================" -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot "engine"); & $Py -m pytest; if ($LASTEXITCODE -ne 0) { $fail = 1 }; Pop-Location

Write-Host "`n================  2/4  api (aleph_api)  ================" -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot "api"); & $Py -m pytest; if ($LASTEXITCODE -ne 0) { $fail = 1 }; Pop-Location

Write-Host "`n================  3/4  app_streamlit  ================" -ForegroundColor Cyan
Push-Location (Join-Path $PSScriptRoot "app_streamlit"); & $Py -m pytest; if ($LASTEXITCODE -ne 0) { $fail = 1 }; Pop-Location

Write-Host "`n================  4/4  ruff (engine + api + app)  ================" -ForegroundColor Cyan
& $Py -m ruff --version 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
  & $Py -m ruff check engine api app_streamlit; if ($LASTEXITCODE -ne 0) { $fail = 1 }
} else {
  Write-Host "(ruff no instalado — omitido; instala con: $Py -m pip install ruff)"
}

Write-Host ""
if ($fail -eq 0) {
  Write-Host "OK  TODO VERDE — seguro para desplegar (.\deploy_streamlit.ps1)" -ForegroundColor Green
} else {
  Write-Host "FALLOS arriba — NO desplegar hasta arreglarlos." -ForegroundColor Red
}
exit $fail
