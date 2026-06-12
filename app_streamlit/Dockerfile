# Imagen de contenedor para la app de Factibilidad CG (Streamlit).
# Empaqueta Python + librerías + el comando de arranque en una imagen reproducible.
# Evita el auto-instalador (Oryx) de Azure App Service: lo que se construye aquí corre
# idéntico en cualquier host (Azure App Service contenedor, Container Apps, local).
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias primero (capa cacheable: no reinstala si solo cambia el código).
COPY requirements.txt .
RUN pip install -r requirements.txt

# Resto del código.
COPY . .

# Streamlit escucha en 8000 (el puerto que sondea App Service vía WEBSITES_PORT=8000).
EXPOSE 8000

# Arranque directo de Streamlit. Sin venv que "buscar": las librerías ya están en la imagen.
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false", "--browser.gatherUsageStats=false"]
