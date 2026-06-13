#!/usr/bin/env bash
# sync_docs.sh — Sincroniza la doctrina (Linux/macOS/Git Bash).
# CLAUDE.md es la ÚNICA fuente; AGENTS.md y GEMINI.md son COPIAS. Corre esto antes de commitear
# cualquier cambio de doctrina (o tras editar CLAUDE.md), para que las 3 queden idénticas.
set -euo pipefail
cd "$(dirname "$0")"
cp -f CLAUDE.md AGENTS.md
cp -f CLAUDE.md GEMINI.md
echo "OK: AGENTS.md y GEMINI.md regenerados desde CLAUDE.md (idénticos)."
