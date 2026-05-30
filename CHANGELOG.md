# Changelog — App Factibilidad CG

Versionado semántico (MAJOR.MINOR.PATCH).

## [2.8.0] — 2026-05-30
### Cambiado (waterfall de crédito — mecánica corregida, calibración EN CURSO)
- **Crédito constructor reespecificado** según la hoja `CALCULO COSTOS FINANCIEROS` de CG: el
  crédito **desembolsa el costo de obra (directos+indirectos)** hasta un **cupo = cobertura% ×
  (D+I)** y se **amortiza con las subrogaciones**; el interés corre sobre el saldo insoluto.
  (Antes desembolsaba solo 80% de los directos → subestimaba/desfasaba el saldo.)
- **Estado de la calibración (Navarra) — NO validada todavía:** la mecánica es ahora la correcta,
  pero las cifras aún sobreestiman: crédito máx **$81.995 M (1.44×** del real $56.827 M; venía de
  2.02×), crédito prom 1.32×, **intereses 2.10×**, **TIR equity −26 %** (debería ser ~+42 %). Falta
  iterar: base financiable real ($163.449 M, no D+I=$177.727 M), inclusión de otros ingresos en el
  flujo, y timing de subrogaciones/lote.
### Corregido (cableado de KPIs)
- La app mostraba el **`flujo_caja` legacy** (crédito crudo, sin calendario real) en vez del
  **waterfall**. Ahora el crédito máx, VPN, intereses y TIR de los KPIs y del consolidado salen de
  `apalancamiento`. (El VPN del portafolio sigue saliendo negativo → parte de la calibración
  pendiente, NO usar para decisión aún.)
- **Consolidado alineado por calendario absoluto** (epoch ene-2022): el pico de crédito del
  portafolio ya no suma picos de meses distintos.
### Motor v1.11.0
- `flujo_apalancado` expone `credito_prom`, `tir_apalancada_ref`; cupo = cobertura×(D+I).
### Nota
- La versión anterior de esta entrada afirmaba una validación exacta que era **incorrecta**; se
  corrigió con las cifras reales medidas. Hasta cerrar la calibración, crédito/VPN/TIR son
  **preliminares**.

## [2.7.0] — 2026-05-30
### Añadido (motor — calendario real por etapa)
- `engine/portafolio.py`: nueva opción **`ic_offset`** por etapa (meses desde el Inicio de Ventas
  hasta el Inicio de Obra). Permite fijar la **fecha real de inicio de construcción** en proyectos
  en ejecución donde la pre-venta antecede a la obra por años (p. ej. Navarra: Etapa 1 vendida
  2022-23, construida 2025-26). Por defecto (sin `ic_offset`) se mantiene la lógica anterior
  (obra arranca tras el Punto de Equilibrio). Combinable con `fecha_inicio` y `escrituracion`
  por etapa para modelar el calendario fiel de un proyecto en curso.

## [2.6.0] — 2026-05-30
### Añadido (consolidado del portafolio)
- En **🏢 Proyectos activos**, el encabezado muestra los **KPIs consolidados** del portafolio
  (suma de los proyectos listados): **Ventas totales · Utilidad operativa · UDI** (sumas,
  reconciliadas con lo real), **TIR apalancada** (referencia ponderada por ventas), **VPN @WACC**
  (suma) y **Crédito máx** (pico de la curva de crédito *sumada*, no la suma de picos).
- **Tabla financiera del portafolio** con ventas/utilidad/margen/crédito por proyecto + fila TOTAL.
- Consolidación correcta por tipo de métrica (aditivas se suman; el crédito usa el pico del saldo
  consolidado; la TIR no se promedia ingenuamente).
### Nota (honestidad de cifras)
- **Ventas/UO/UDI** están reconciliadas con las prefactibilidades reales (verde). **VPN y crédito
  máx** provienen del módulo de flujo/apalancamiento **en calibración** → se marcan **preliminar**
  (el crédito tiende a sobreestimarse porque la subrogación llega tarde). Próximo paso sugerido:
  calibrar el waterfall de crédito antes de usar esas cifras para decisión.

## [2.5.0] — 2026-05-30
### Añadido (datos reales privados)
- La app puede cargar **proyectos privados** desde `proyectos_privados/` (en `.gitignore`, no se
  publica). Tienen prioridad sobre los ilustrativos del mismo proyecto (que se ocultan localmente);
  el deploy público —sin esa carpeta— sigue mostrando solo cifras ilustrativas.
- Sello en el encabezado: **🔒 datos reales** vs *cifras ilustrativas*.
### Datos
- Cargadas las prefactibilidades **reales** de Navarra, Dominica y Torres de Campiñas (extraídas de
  los Excel con `execution/extraer_prefactibilidad.py` + `cargar_reales.py`). El motor **reconcilia
  exacto la utilidad operativa real** de los tres (otros ingresos —comercio/parqueaderos/IVA/
  recuperaciones— absorbidos para cerrar el P&G). Los datos reales NO están en el repo público.

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
