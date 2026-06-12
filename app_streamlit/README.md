# Aplicativo de Factibilidad — CG Constructora

Herramienta web de prefactibilidad/factibilidad financiera de proyectos inmobiliarios.
Multi-proyecto, versionada, con motor financiero en Python (fuente única de verdad).

> Nota: este repositorio público usa un **proyecto de ejemplo** con cifras ilustrativas.
> Los datos reales de cada proyecto se ingresan en la app (o se cargan en un despliegue privado).

## Arquitectura
- `engine/` — motor financiero (curvas PERT + modelo). **Toda la lógica vive aquí.**
- `app.py` — interfaz Streamlit (solo presentación).
- `proyectos/` — parámetros por proyecto (JSON, versionados).
- Directiva/SOP: documento interno (no incluido en este repo).

## Correr localmente
```bash
cd app_factibilidad
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
streamlit run app.py
```
Abre http://localhost:8501

## Desplegar (Streamlit Community Cloud)
1. Subir este repo a GitHub.
2. En share.streamlit.io → New app → seleccionar repo y `app_factibilidad/app.py`.
3. Deploy. El link se comparte con el equipo.

## Estándares
Modelación FAST/SMART (separación inputs/cálculo/salida, trazabilidad), versionado
semántico + CHANGELOG, docs-as-code. Enfoque híbrido (ver directiva).

## Versión
Fuente única en `cg_engine/__version__` (la leen `pyproject.toml` y el pie de la app). Historial en `CHANGELOG.md`.
