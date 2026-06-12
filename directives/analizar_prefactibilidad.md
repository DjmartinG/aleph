# Directiva — Analizar prefactibilidad (Excel) y cargar números reales

## Objetivo
Tomar la prefactibilidad anterior de un proyecto (Excel) y volcar sus **números reales** al
modelo del aplicativo (`app_factibilidad`), mejorándola con el motor propio (P&G, ritmos de
venta/entrega, costos por curva, flujo, apalancamiento, indicadores).

## Entradas
- Excel de prefactibilidad en `insumos_prefactibilidad/` (1 archivo por proyecto).
  - Carpeta **fuera del repo público** → datos confidenciales no se publican.
  - Si el archivo está en OneDrive "solo en la nube": clic derecho → *Mantener siempre en este
    dispositivo* antes de leer (si no, falla la copia/lectura).

## Herramientas (Capa 3)
- `execution/extraer_prefactibilidad.py` — volcado determinista a dossier:
  - `python execution/extraer_prefactibilidad.py` → procesa toda la carpeta de insumos.
  - `python execution/extraer_prefactibilidad.py "ruta\archivo.xlsx"` → un archivo.
  - Salidas en `.tmp/`: `dossier_<archivo>.json` (completo) + `dossier_<archivo>.md` (resumen).
  - Lee **valores calculados** (data_only) y **fórmulas**; copia primero a `.tmp/_work/`.
  - Python del equipo: `C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe`.

## Proceso (Capa 2 — orquestación)
1. Confirmar que el/los Excel están en `insumos_prefactibilidad/`.
2. Correr el extractor → leer el `dossier_*.md` para mapear la estructura (hojas, etiquetas).
3. Leer del `dossier_*.json` los valores reales y mapearlos al esquema de proyecto del modelo:
   - `meta`: nombre, ubicación, zona, tipo (VIS/No VIS), unidades.
   - `areas`: m² vendibles/construidos, lote bruta/útil.
   - `etapas[]`: und, precio (+ método $/m² o $/und), área/und, **vmes/frec** (ritmo ventas),
     **emes/efrec** (ritmo entregas), pe_pct, sucesora, desfase, dur_obra, escrituración.
   - `costos_pct`, `lote_bruto_miles`, `cronograma` (curva, escaladores), `financiero`
     (pct_ci, separación, tasa crédito, cobertura, WACC, tir_apalancada_ref).
4. Cargar los números reales en archivo de proyecto **privado** (ver Salidas), validar con el
   motor (`engine/modelo.calcular`) y reconciliar contra los totales de la prefactibilidad
   (ventas, utilidad, reparto) — registrar % de coincidencia.
5. Reportar diferencias relevantes vs. la versión anterior (mejoras del nuevo modelo).

## Salidas (CONFIDENCIALIDAD)
- Números reales → **NO** en `app_factibilidad/proyectos/` (repo público).
- Guardar en `app_factibilidad/proyectos_privados/<proyecto>.json` (carpeta en `.gitignore`,
  no se publica) **o** en el repo privado `cg-factibilidad`. Patrón existente:
  `Dominica_v_nueva/dominica_REAL_privado.json`.
- El repo público conserva solo cifras ilustrativas (`proyectos/1_navarra.json`, etc.).

## Casos extremos / gotchas
- `.xlsx` bloqueado por Excel abierto o placeholder de OneDrive → el extractor copia primero;
  si aún falla, cerrar Excel / forzar descarga local.
- `data_only=True` lee el **último valor calculado y guardado** por Excel; si una celda nunca se
  recalculó/guardó, puede venir vacía → abrir y guardar el Excel una vez, reintentar.
- Hojas con miles de celdas se truncan a 6000 (tope de seguridad); subir el tope si hace falta.
- Rangos con nombre suelen marcar inputs/outputs clave — revisarlos primero.

## Aprendizajes
- **Estructura común (APEX):** los 3 Excel comparten hojas — `DATOS GENERALES` (proyecto, socios,
  lote), `DATOS DE ENTRADA` (inputs), `PROYECCION ING`/`VENTAS`/`ventas` (precios y ritmo),
  `PRESUPUESTO`/`PREFACTIBILIDAD.` (costos y P&G), `INDICADORES`/`Resumen Factibilidad`,
  `Distribución Gauss` (curva obra), `Cronograma Proyecto`.
- **Magnitud:** casi todo en **MILES COP** (encabezado "Valores en Miles ($COP)"). PERO algunas
  hojas (p.ej. Navarra `PREFACT X ETAPA`) están en **pesos completos** → verificar por magnitud.
- **Las prefactibilidades NO calculan TIR/VPN/WACC** (las etiquetas existen con celdas vacías). Su
  métrica de decisión es **utilidad operativa / reintegros**. La TIR apalancada de decisión viene
  del modelo aprobado externo (Dominica 21,83%). No inventar TIR desde estos libros.
- **Etapas con doble granularidad:** comercial (base del flujo de ventas) vs constructiva (por
  torre). Mapear la **comercial**. Navarra 3 oper. (158/476/317) ó 4 por torre; Torres 4 comercial
  (237/169/169/338) ó 5 torres.
- **Socios ≠ reparto:** la tabla de socios de `DATOS GENERALES` suele estar desactualizada; el
  reparto real está en `Disti Utili`/`PREFACT X ETAPA`/`PREFACTIBILIDAD.`. Distinguir % de aportes
  de capital vs % de reparto de resultados.
- **Para reconciliar la UO en el motor:** `costos_pct = abs/ventas_viviendas` y `recon_codensa`
  absorbe OTROS INGRESOS (comercio+parqueaderos+devol. IVA+recuperaciones) = (UO+costos)−ventas.
- **Gotcha extractor:** celdas tipo `time`/`bytes` rompen JSON → el extractor ya las castea. Celdas
  `#REF!/#DIV/0!` (fórmulas rotas) aparecen en Torres; no afectan los anclas.
- **Crédito constructor (hoja `CALCULO COSTOS FINANCIEROS`):** mecánica CG = desembolsa el costo de
  obra (directos+indirectos) hasta un **cupo = cobertura% × (D+I)** ("COBERTURA CREDITO 80%"), se
  amortiza con subrogaciones; el **máx del saldo insoluto** = "Vr. Max Credito Constructor". Anclas
  Navarra: cupo $130.760M, crédito máx $56.827M, prom $20.983M, intereses+fiduciarios $12.681M
  (`FINANCIEROS!H28`). Validado al peso en el motor (v2.8.0).
- **Proyectos en ejecución (Navarra):** modelar con fechas reales por etapa (`fecha_inicio`,
  `escrituracion`, `ic_offset`); la preventa puede anteceder la obra años. El "Cronograma Proyecto"
  trae por etapa: COMERCIALIZACION (ritmo ventas), PUNTO DE EQUILIBRIO (%), CONSTRUCCION (IC..FC),
  ESCRITURACION y ENTREGA con sus meses exactos.
