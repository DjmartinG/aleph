# Changelog — App Factibilidad CG

Versionado semántico (MAJOR.MINOR.PATCH).

## [1.9.0] — 2026-05-29
### Cambiado (importante)
- **Toda la data se ingresa EN la plataforma** — se elimina la importación de archivos
  (Excel/JSON) como input (distorsionaba). Se conserva solo la **descarga de respaldo** (.json).
- Nueva **primera pestaña "📝 Datos del proyecto"** con 6 secciones plegables: Datos generales,
  Áreas y lote, Etapas/producto/ventas (tabla), Costos, Recaudo, Financiero (avanzado).
- **Precio de venta elegible por etapa**: $/m² × área **o** $/und (columna "Método precio").
- Sidebar: selector de proyecto + **"➕ Nuevo proyecto"** (en blanco) + descarga de respaldo.
  Se retiran cargador de archivos y sliders sueltos (ahora en la pestaña de datos).

## [1.8.0] — 2026-05-29
### Añadido
- **Editor de portafolio en la app** (pestaña ⚙️): tabla editable (`st.data_editor`) para
  agregar/editar/eliminar etapas con todos los parámetros APEX (unidades, ventas, ritmo,
  % equilibrio, sucesora, desfase, obra, escrituración) + fecha de inicio de la etapa raíz.
  La estructura del modelo es ahora autoservicio — sin editar JSON a mano.
### Cambiado
- Se retiran los inputs de ventas por etapa del sidebar (ahora se editan en el editor).

## [1.7.0] — 2026-05-29
### Cambiado
- **Crédito constructor calibrado**: ahora financia la **cobertura (~80%) del costo de obra**
  (no todos los déficits) y se **amortiza con las subrogaciones**; el interés corre sobre el
  saldo del crédito. Los aportes (equity) cubren el resto. Resultado: crédito máx e intereses
  realistas (intereses < utilidad), TIR equity calculable. Corrige el sobredimensionamiento
  del crédito/intereses de v1.5–1.6.
### Nota
- `G.Financieros` y el valor financiable del CC están vacíos/"Falta calcular" en el propio APEX;
  la cobertura del costo de obra es la mecánica estándar de crédito constructor aplicada aquí.

## [1.6.0] — 2026-05-29
### Añadido
- **Ensamblaje (Fase 5)**: vista de **flujo de caja consolidado anual** del portafolio (curva J),
  panel de **indicadores económicos** (TIR proyecto, VPN @WACC, WACC, payback) y detalle mensual
  de caja acumulada + saldo de crédito en la pestaña Apalancamiento.
- **Indicadores del Estado de Resultados** en P&G: margen de contribución, margen sobre costo,
  incidencias (directos / indirectos+lote).

## [1.5.0] — 2026-05-29
### Añadido
- **Apalancamiento APEX (Fase 4)** (`engine/apalancamiento.py`): ensambla el flujo operativo
  consolidado del portafolio (recaudo F2 − costos F3 por etapa, directos por curva Gauss sobre
  IC..FC) y aplica el waterfall de crédito — crédito constructor revolvente (tope = monto% ×
  valor financiable), activado por avance de obra y amortizado con subrogaciones; aportes cubren
  el residual. Indicadores: crédito máx, necesidad de caja, TIR proyecto.
- Nueva pestaña **🏦 Apalancamiento**: flujo operativo + saldo de crédito + indicadores.
### Nota
- Intereses y TIR apalancada son preliminares (la calibración fina requiere el cronograma de
  amortización de fiducia); la estructura del waterfall queda completa.

## [1.4.0] — 2026-05-29
### Añadido
- **Kernels de costos APEX (Fase 3)**: curva **Gauss** de avance de obra (k.Directo) en el
  motor (`engine/curvas.py`), usada para distribuir el costo directo. Aclaración: `k.Beta`
  es el kernel WACC/CAPM (ya en el motor), no la curva de costos.
- **Hitos de construcción IC/FC** (Inicio/Fin de Construcción) en el motor de portafolio
  y en la pestaña Cronograma — la obra arranca tras el Punto de Equilibrio y dura `dur_obra`.
### Cambiado
- Distribución de costos ahora usa la curva Gauss (antes PERT), fiel a APEX.

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
