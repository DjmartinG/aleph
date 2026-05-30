# Changelog — App Factibilidad CG

Versionado semántico (MAJOR.MINOR.PATCH).

## [2.4.0] — 2026-05-30
### Añadido (ritmo de ventas y entregas — paridad APEX R.ventas)
- **Cronograma** ahora muestra, además de los hitos: (1) tabla **Ritmo de ventas y entregas**
  (estilo hoja `R.ventas` de APEX — No · Etapa · Und · Ventas Cant/Frec · Entregas Cant/Frec) y
  (2) **Proyección de ventas y entregas**: unidades vendidas por mes por etapa (barras apiladas),
  entregas/mes y la **curva de absorción** acumulada. Es la vista de "lo que mueve los números".
- **Ritmo de entregas** modelado en el motor (`engine/ingresos.py`): las entregas se escalonan
  según *Cantidad/Frecuencia* desde el mes de escrituración (antes todo en un solo mes). Las
  **subrogaciones** (crédito hipotecario, ~70% del precio) ahora se reparten a medida que se
  entrega cada unidad → flujo de caja y amortización del crédito más realistas. Emparejamiento
  **venta → entrega en FIFO**; la cuota inicial corre de la venta a la entrega de esa unidad.
- Editor de etapas (📝 Datos del proyecto): nuevas columnas **Entr/mes** y **Frec ent (m)**.
### Nota
- Reconciliación verificada: recaudo total = valor de contrato en los 3 proyectos. El ritmo de
  entregas por defecto entrega todo en la escrituración (comportamiento previo) si no se define.

## [2.3.0] — 2026-05-30
### Cambiado (orden lógico del menú)
- **Reordenado el menú** al flujo de evaluación del modelo. Nuevo orden:
  Inicio · Proyectos activos · Datos del proyecto · **Urbanístico** · Cronograma · Ingresos ·
  Distribución costos · P&G · Reparto · Flujo de caja · Apalancamiento · Escenarios · Sensibilidad.
- **Urbanístico pasa a primero** entre los resultados: define áreas e índices, la base física
  de la que derivan los demás análisis. Luego Cronograma (tiempo) → Ingresos (recaudo) →
  Costos → P&G/Reparto (resultado) → Flujo/Apalancamiento (financiación) → Escenarios/Sensibilidad.
- La guía de módulos de la portada se reagrupa acorde (Portafolio · Definición · Resultados ·
  Flujo & Análisis).

## [2.2.0] — 2026-05-30
### Cambiado (orden lógico / UX)
- **Inicio = portada de bienvenida** (ya no tablero del proyecto): presenta la app, "Cómo
  empezar" (3 pasos) y la guía de **módulos** del modelo. Se retira el cronograma del portafolio
  y la tarjetas/caption del proyecto activo, que **duplicaban** la información de "Proyectos
  activos". La portada ya no muestra datos de un proyecto concreto.
- Los **KPIs y el encabezado del proyecto** (ventas, utilidad, TIR, VPN, crédito) y los botones
  de **exportación** solo aparecen **dentro de un proyecto** (cualquier sección distinta de
  Inicio), no en la portada — separa "anunciar" (Inicio) de "trabajar el proyecto".
- "Proyectos activos" queda como **único** lugar donde se despliega el portafolio (Navarra ·
  Dominica · Torres de Campiñas). Elimina la repetición Inicio ↔ Proyectos activos.

## [2.1.0] — 2026-05-29
### Añadido
- Sección **🏢 Proyectos activos** (portafolio CG): tarjetas + tabla resumen de los proyectos,
  con botón **Abrir** para cargar cada uno. Estilo de la hoja "Proyectos" de APEX.
- Proyectos activos de CG (plantillas): **Navarra Apartamentos · Dominica · Torres de Campiñas**
  (estructura y cifras ilustrativas; los datos reales se ingresan en plataforma).
- Selector de proyecto muestra el **nombre del proyecto** (no el nombre de archivo).

## [2.0.0] — 2026-05-29
### Cambiado (mayor — navegación)
- **Navegación por menú lateral (estilo APEX)** en vez de pestañas: menú vertical con iconos
  (Inicio · Datos · P&G · Reparto · Distribución · Flujo · Apalancamiento · Cronograma ·
  Ingresos · Escenarios · Sensibilidad · Urbanístico). Elimina el scroll horizontal.
- Nuevo **tablero de Inicio** ("Evaluación Financiera de Proyectos") con tarjetas agrupadas
  (Datos · Resultados · Flujo & Financiación · Análisis) + cronograma del portafolio — réplica
  del INICIO de APEX.
- Header + KPIs visibles en todas las secciones.
- Dependencia: `streamlit-option-menu`.

## [1.9.1] — 2026-05-29
### Corregido
- "Unidades totales" en Datos generales ya es un **conteo en vivo** (suma de las unidades por
  etapa) con guía clara. Las unidades se ajustan en la columna *Unidades* de la tabla de etapas.

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
