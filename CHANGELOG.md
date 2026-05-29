# Changelog — App Factibilidad CG

Versionado semántico (MAJOR.MINOR.PATCH).

## [1.3.0] — 2026-05-29
### Añadido
- **Kernel de ingresos APEX (Fase 2)** integrado: recaudo mensual del portafolio por
  componente — separación diferida, cuota inicial (venta→escrituración) y subrogación
  (a la entrega). Reconcilia con el valor de contrato.
- Nueva pestaña **💰 Ingresos**: recaudo mensual apilado por componente + totales.

## [1.2.0] — 2026-05-29
### Añadido
- **Estructura de portafolio APEX (Fase 1)**: motor de hitos (`engine/portafolio.py`)
  integrado al modelo y a la app. Etapas secuenciales — cada etapa abre ventas cuando su
  sucesora alcanza el Punto de Equilibrio (PE = INT(unidades×%eq)+1, %eq por etapa).
- Nueva pestaña **🗓️ Cronograma**: tabla y línea de tiempo de hitos (Inicio Ventas /
  Punto de Equilibrio / Fin Ventas) por etapa.
- Esquema de proyecto ampliado con ritmo de ventas, %eq, sucesora y desfase.
- Validado 5/5 etapas contra APEX 20250701.xlsm.

## [1.1.0] — 2026-05-28
### Cambiado
- **Rediseño con identidad de marca CG**: logo en encabezado y barra lateral, favicon,
  paleta corporativa (teal #004854 + ámbar #F09C00), tipografía Inter.
- Tarjetas KPI con borde/sombra (no planas), barra de marca teal→ámbar.
- Gráficos Plotly con plantilla CG (paleta, ejes limpios).
- Se oculta el branding de Streamlit (menú, footer) para un look propio.
### Añadido
- Cargador de proyecto privado (.json) — datos confidenciales solo en sesión.
- Descarga de parámetros editados (.json) al equipo.
### Corregido
- Llaves de "ventas por etapa" por-proyecto (evita que valores se "peguen" al cambiar).

## [1.0.0] — 2026-05-28
### Añadido
- Motor financiero (`engine/`): P&G, reparto desarrollador/socio, distribución de costos
  por curva PERT + escalación Materiales/MO, flujo de caja del proyecto, escenarios,
  sensibilidades, índices urbanísticos y economía unitaria. Fuente única de verdad (Python).
- App Streamlit multi-proyecto con KPIs, gráficos interactivos (Plotly) y export a Excel.
- Proyecto de ejemplo (`proyectos/ejemplo.json`) con cifras ilustrativas.
- Enfoque híbrido: TIR apalancada de referencia como parámetro de decisión.
