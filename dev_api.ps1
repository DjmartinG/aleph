# dev_api.ps1 — levanta la API FastAPI en local (Windows / PowerShell).
#   Uso:  .\dev_api.ps1        (desde la raíz del monorepo)
#   Abre: http://localhost:8000/docs   (OpenAPI interactivo)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$ok = $false
try { & $Py -c "import sys; assert sys.version_info[:2] >= (3, 12)"; $ok = ($LASTEXITCODE -eq 0) } catch { $ok = $false }
if (-not $ok) { $Py = "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" }

# Asegura el motor + las deps de la API.
& $Py -c "import aleph_engine" 2>$null; if ($LASTEXITCODE -ne 0) { & $Py -m pip install -e ./engine }
& $Py -c "import fastapi, uvicorn" 2>$null; if ($LASTEXITCODE -ne 0) { Write-Host "==> instalando fastapi/uvicorn…"; & $Py -m pip install "fastapi" "uvicorn[standard]" }

Write-Host "==> API en http://localhost:8000/docs  (Ctrl+C para parar)" -ForegroundColor Cyan
Set-Location -Path (Join-Path $PSScriptRoot "api")
& $Py -m uvicorn aleph_api.main:app --reload --port 8000
