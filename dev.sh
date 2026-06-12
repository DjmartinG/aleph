#!/usr/bin/env bash
# dev.sh — levanta la app Streamlit en local para desarrollo.
#   Uso:  ./dev.sh            (desde la raíz del monorepo)
#   Abre: http://localhost:8501
#
# La constitución ALEPH manda mantener el Streamlit VIVO hasta tener paridad módulo a módulo en /web.
# Este script es el atajo para correrlo sin memorizar comandos (regla #5 de la migración).
set -euo pipefail
cd "$(dirname "$0")"

# Elige un Python 3.12+. Override con la variable PYTHON si hace falta.
PY="${PYTHON:-python}"
if ! "$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 12)' 2>/dev/null; then
  PY="/c/Users/Usuario/AppData/Local/Programs/Python/Python312/python.exe"
fi

# El motor vive en ./engine como paquete; la app lo importa. Asegúralo instalado (editable).
"$PY" -c "import aleph_engine" 2>/dev/null || { echo "==> instalando el motor aleph_engine…"; "$PY" -m pip install -e ./engine; }

echo "==> Streamlit en http://localhost:8501  (Ctrl+C para parar)"
cd app_streamlit
exec "$PY" -m streamlit run app.py --server.port=8501
