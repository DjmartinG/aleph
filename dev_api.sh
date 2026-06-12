#!/usr/bin/env bash
# dev_api.sh — levanta la API FastAPI en local.
#   Uso:  ./dev_api.sh         (desde la raíz del monorepo)
#   Abre: http://localhost:8000/docs   (OpenAPI interactivo)
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python}"
if ! "$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 12)' 2>/dev/null; then
  PY="/c/Users/Usuario/AppData/Local/Programs/Python/Python312/python.exe"
fi

# Asegura el motor + deps de la API.
"$PY" -c "import aleph_engine" 2>/dev/null || "$PY" -m pip install -e ./engine
"$PY" -c "import fastapi, uvicorn" 2>/dev/null || { echo "==> instalando fastapi/uvicorn…"; "$PY" -m pip install "fastapi" "uvicorn[standard]"; }

echo "==> API en http://localhost:8000/docs  (Ctrl+C para parar)"
cd api
exec "$PY" -m uvicorn aleph_api.main:app --reload --port 8000
