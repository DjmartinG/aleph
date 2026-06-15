# migrate_db.ps1 — corre el ETL de migración de datos (PROMPT 4 · Fase 4b) — Windows / PowerShell.
#   Uso:  .\migrate_db.ps1     (desde la raíz del monorepo)
#
# ANTES de correr esto: aplica el esquema una vez (pega db/migrations/0001_aleph_schema.sql en el
# SQL Editor de Supabase). Este wrapper solo ejecuta el ETL (lee `proyectos` → projects/scenarios).
# Usa SUPABASE_URL/KEY del entorno o de .streamlit/secrets.toml. Es idempotente.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Py = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$ok = $false
try { & $Py -c "import sys; assert sys.version_info[:2] >= (3, 12)"; $ok = ($LASTEXITCODE -eq 0) } catch { $ok = $false }
if (-not $ok) { $Py = "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" }

& $Py -c "import aleph_engine" 2>$null; if ($LASTEXITCODE -ne 0) { & $Py -m pip install -e ./engine }
& $Py -c "import supabase" 2>$null;     if ($LASTEXITCODE -ne 0) { & $Py -m pip install supabase }

Write-Host "==> Ejecutando ETL de migración (idempotente)…" -ForegroundColor Cyan
& $Py db/etl_import_v1.py
