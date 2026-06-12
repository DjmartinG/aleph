#!/usr/bin/env bash
# test.sh — corre TODA la red de pruebas del monorepo antes de desplegar.
#   Uso:  ./test.sh           (desde la raíz del monorepo)
#
# Replica lo que valida el CI (.github/workflows/ci.yml) más el harness del engine:
#   1) engine        → contrato Pydantic + harness dorado (skip hasta que se extraiga calcular)
#   2) app_streamlit → regresión de cifras (anclas/golden) + humo de la UI
#   3) ruff          → lint de correctitud de la app (igual que el CI)
#
# El SNAPSHOT DORADO es sagrado: si algo aquí se pone rojo, NO se despliega.
set -uo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python}"
if ! "$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 12)' 2>/dev/null; then
  PY="/c/Users/Usuario/AppData/Local/Programs/Python/Python312/python.exe"
fi

# Asegura las herramientas de prueba (no están en requirements.txt; el CI las instala aparte).
"$PY" -c "import pytest" 2>/dev/null || { echo "==> instalando pytest…"; "$PY" -m pip install -q pytest; }
# El motor (aleph_engine) debe estar instalado: la app, la API y el harness del engine lo importan.
"$PY" -c "import aleph_engine" 2>/dev/null || { echo "==> instalando el motor aleph_engine…"; "$PY" -m pip install -e ./engine; }
# Deps de la API (Fase 4a).
"$PY" -c "import fastapi, httpx" 2>/dev/null || { echo "==> instalando fastapi/httpx (API)…"; "$PY" -m pip install -q fastapi httpx; }

fail=0

echo ""
echo "================  1/4  engine (aleph_engine)  ================"
( cd engine && "$PY" -m pytest ) || fail=1

echo ""
echo "================  2/4  api (aleph_api)  ================"
( cd api && "$PY" -m pytest ) || fail=1

echo ""
echo "================  3/4  app_streamlit  ================"
( cd app_streamlit && "$PY" -m pytest ) || fail=1

echo ""
echo "================  4/4  ruff (engine + api + app)  ================"
if "$PY" -m ruff --version >/dev/null 2>&1; then
  ( "$PY" -m ruff check engine api app_streamlit ) || fail=1
else
  echo "(ruff no instalado — omitido; instala con: $PY -m pip install ruff)"
fi

echo ""
if [ "$fail" -eq 0 ]; then
  echo "✅  TODO VERDE — seguro para desplegar (./deploy_streamlit.sh)"
else
  echo "❌  Hay fallos arriba — NO desplegar hasta arreglarlos."
fi
exit "$fail"
