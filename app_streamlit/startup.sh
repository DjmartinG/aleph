#!/bin/bash
# Comando de arranque de Streamlit para Azure App Service (Linux, Python).
# Se configura en: App Service -> Configuration -> General settings -> Startup Command = "startup.sh"
# Requiere: App Service -> Configuration -> General settings -> Web sockets = On.
# Los secretos (CLAVE_*, SUPABASE_*) van como Application settings (variables de entorno).
python -m streamlit run app.py \
  --server.port=8000 \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false \
  --browser.gatherUsageStats=false
