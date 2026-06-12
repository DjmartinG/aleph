# Directiva — Aplicativo de Prefactibilidad / Factibilidad CG

> SOP (instrucción para personas y agente). Documento vivo, versionado junto al código.
> **Versión:** 1.0.0 · **Fecha:** 2026-05-28 · **Responsable:** Gerencia / Estrategia CG

## 1. Objetivo
Aplicativo web que calcula la prefactibilidad/factibilidad financiera de proyectos
inmobiliarios de CG Constructora, reemplazando el proceso manual en Excel. Multi-proyecto,
versionado y con estándares internacionales de modelación financiera.

## 2. Principio rector (NO negociable)
**Fuente única de verdad.** Toda la lógica financiera vive en `app_factibilidad/engine/`
(Python). La interfaz (Streamlit) solo presenta; NO recalcula ni duplica fórmulas.

## 3. Arquitectura (3 capas)
- **Directiva (esta):** qué hace, entradas/salidas, estándares.
- **Ejecución:** `engine/curvas.py` (motor de distribución PERT/Normal/Triangular) y
  `engine/modelo.py` (P&G, reparto, flujo, escenarios, sensibilidades).
- **Presentación:** `app.py` (Streamlit) — formularios, KPIs, gráficos, export.

## 4. Entradas (por proyecto, en `proyectos/<nombre>.json`)
- Meta: nombre, ubicación, unidades, moneda.
- Áreas: vendible, construida, lote bruta/útil.
- Etapas: nombre, unidades, ventas (miles COP).
- Costos (% sobre ventas): directos, indirectos, honorarios, utilidad lote; lote bruto.
- Financiero: renta, reparto CG/socio, tasa crédito, WACC, TIR apalancada de referencia.
- Cronograma: duración obra, moda PERT por etapa.

## 5. Salidas
P&G, reparto CG/socio, distribución de costos (curva PERT), flujo de caja del proyecto,
necesidad de crédito, escenarios (base/optimista/pesimista), sensibilidades (tornado),
economía unitaria ($/m²) e índices urbanísticos. Export a Excel.

## 6. Estándares
- **Modelación:** separación inputs/cálculo/salida; supuestos explícitos; trazabilidad;
  validación de datos (FAST/SMART standard).
- **Enfoque híbrido (decisión 2026-05-28):** el modelo propio posee P&G, costos, crédito;
  la **TIR apalancada de decisión** se toma del modelo aprobado (referencia, editable).
- **Versionado:** Git + versionado semántico (MAJOR.MINOR.PATCH) + `CHANGELOG.md`.
  Cada proyecto guarda versiones fechadas de sus parámetros.
- **Docs-as-code:** esta directiva se versiona con el código.

## 7. Cómo correr
```
cd app_factibilidad
pip install -r requirements.txt
streamlit run app.py
```

## 8. Despliegue
Streamlit Community Cloud (repo Git). Ver `README.md`.

## 9. Aprendizajes
<!-- registrar gotchas, decisiones, límites aquí -->
- 2026-05-28 — v1.0.0: motor validado al 99,87% vs prefactibilidad Dominica. Crédito máx
  propio calibrado = $29.601M (exacto). TIR apalancada de referencia: 21,83% (modelo aprobado).
