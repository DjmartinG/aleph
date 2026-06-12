# dev.ps1 — levanta la app Streamlit en local para desarrollo (Windows / PowerShell).
#   Uso:  .\dev.ps1          (desde la raíz del monorepo)
#   Abre: http://localhost:8501
#
# Equivalente nativo de dev.sh para no depender de Git Bash (regla #5 de la migración: Martin no es dev).
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Elige un Python 3.12+. Override con $env:PYTHON si hace falta.
$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$ok = $false
try { & $Py -c "import sys; assert sys.version_info[:2] >= (3, 12)"; $ok = ($LASTEXITCODE -eq 0) } catch { $ok = $false }
if (-not $ok) { $Py = "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" }

# El motor vive en .\engine como paquete; la app lo importa. Asegúralo instalado (editable).
& $Py -c "import aleph_engine" 2>$null
if ($LASTEXITCODE -ne 0) { Write-Host "==> instalando el motor aleph_engine…"; & $Py -m pip install -e ./engine }

Write-Host "==> Streamlit en http://localhost:8501  (Ctrl+C para parar)" -ForegroundColor Cyan
Set-Location -Path (Join-Path $PSScriptRoot "app_streamlit")
& $Py -m streamlit run app.py --server.port=8501
