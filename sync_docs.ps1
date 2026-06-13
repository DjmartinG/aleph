# sync_docs.ps1 — Sincroniza la doctrina (Windows / PowerShell).
# CLAUDE.md es la ÚNICA fuente; AGENTS.md y GEMINI.md son COPIAS. Corre esto antes de commitear
# cualquier cambio de doctrina (o tras editar CLAUDE.md), para que las 3 queden idénticas.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
Copy-Item -Path "CLAUDE.md" -Destination "AGENTS.md" -Force
Copy-Item -Path "CLAUDE.md" -Destination "GEMINI.md" -Force
Write-Host "OK: AGENTS.md y GEMINI.md regenerados desde CLAUDE.md (idénticos)." -ForegroundColor Green
