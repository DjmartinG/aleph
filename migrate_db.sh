#!/usr/bin/env bash
# migrate_db.sh — corre el ETL de migración de datos (PROMPT 4 · Fase 4b).
#   Uso:  ./migrate_db.sh      (desde la raíz del monorepo)
#
# ANTES: aplica el esquema una vez (pega db/migrations/0001_aleph_schema.sql en el SQL Editor de
# Supabase). Este wrapper solo ejecuta el ETL. Usa SUPABASE_URL/KEY del entorno o de secrets.toml.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python}"
if ! "$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 12)' 2>/dev/null; then
  PY="/c/Users/Usuario/AppData/Local/Programs/Python/Python312/python.exe"
fi

"$PY" -c "import aleph_engine" 2>/dev/null || "$PY" -m pip install -e ./engine
"$PY" -c "import supabase" 2>/dev/null     || "$PY" -m pip install supabase

echo "==> Ejecutando ETL de migración (idempotente)…"
exec "$PY" db/etl_import_v1.py
