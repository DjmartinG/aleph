# Cobertura ALEPH ↔ Curso Camacol (Evaluación financiera de proyectos inmobiliarios)

> **Qué es:** matriz de referencia que mapea el currículo del curso de Camacol contra lo que ALEPH ya
> hace, y ancla el plan de acción para volver ALEPH una **plataforma integral del prefacto**.
> Auditado contra el código real (engine/web/data) el 2026-06-20.
>
> **Alcance decidido con Martín:** plataforma integral (crecer a mercado/legal/ambiental como módulos
> integrados al veredicto de viabilidad) · **solo desarrollo-venta** (Cap Rate / NOI / yield-on-cost /
> renta-BTR quedan FUERA salvo fase futura).
>
> Leyenda: ✅ cubierto · 🟡 parcial · ❌ ausente. La columna **Acción** referencia las fases del plan
> (A = completar financiero · B = módulos cualitativos · C = mueve cifras/datos externos).

## Módulo 1 — Introducción / generalidades / ciclo de vida
| Concepto | Estado | Dónde / nota | Acción |
|---|---|---|---|
| Definición y ciclo de vida del proyecto | ✅ | `config.ESTADOS`, `ontologia.FASES` (prefactibilidad→aprobado→construcción→entregado) | — |
| Por qué/viabilidad económico-financiera | ✅ | umbrales de aprobación (`config.UMBRAL_*`), checks de cuadre (`checks.py`) | — |
| Gestión de suelo / ordenamiento territorial (POT) | ❌ | no se valida contra normativa de suelo | **B2** |

## Módulo 2 — Etapas, pre-inversión, localización, operación (ruta crítica)
| Concepto | Estado | Dónde / nota | Acción |
|---|---|---|---|
| Etapas e hitos del cronograma (IV/PE/FV/IC/FC) | ✅ | `modelo._hitos`, `ontologia.HITOS`, web Cronograma (Gantt) | — |
| Pre-inversión / estudio de factibilidad | 🟡 | marco de decisión (ir/no-ir por umbrales); falta el estudio formal | B |
| Localización (impacto financiero) | 🟡 | se captura ubicación/zona; no se modela impacto en precio/costo | **B2/B3** |
| Operación / ruta crítica / plan vs real (EVM) | 🟡 | `evm.py` existe pero `actuals_*` vacías (sin SINCO/CRM) | **C3** |

## Módulo 3 — Estudios sectoriales, mercado y entorno (visión financiera)
| Concepto | Estado | Dónde / nota | Acción |
|---|---|---|---|
| Estudio de mercado (producto, demanda, oferta, precios, competencia, canales) | ❌ | el precio y el ritmo (`vmes`) son INPUTS manuales, no se estiman ni contrastan | **B3** |
| Absorción / ritmo de ventas | ✅ | `modelo`/`ingresos` (ritmo, recaudo, curva de absorción en web) | — |
| Variables macroeconómicas y su impacto | ✅ | `supuestos_macro.py` + conectores (Damodaran/Banrep) + vista `/fuentes` | — |

## Módulo 4 — Estudio legal: sociedad, contratos y viabilidad
| Concepto | Estado | Dónde / nota | Acción |
|---|---|---|---|
| Formas jurídicas / vehículos | ✅ | `vehiculos.py` (7: fiducia, encargo, consorcio, UT, cuentas en participación, SAS/SPV, FCP) | — |
| Tratamiento fiscal por vehículo | 🟡 | `tributario.py` (exención renta VIS + overlay GMF/dividendos como **placeholders `[VALIDAR]`**) | **C1** |
| Marco normativo (tributario) | 🟡 | citado en `vehiculos`/`tributario` con norma; falta IVA VIS 4%, ICA, GMF real, retención | **C1** |
| Estudio de títulos y saneamiento jurídico | ❌ | el lote es un input sin validación de dominio | **B1** |
| Contratos típicos | 🟡 | se modelan efectos (separación, cuota inicial, subrogación); no el documento/cláusulas | **B1** |
| Riesgos legales + mitigación + integración a viabilidad | ❌ | no hay registro de riesgos legales | **B1** |

## Módulo 5 — Aspectos técnicos: tamaño, localización, ingeniería, ambiental
| Concepto | Estado | Dónde / nota | Acción |
|---|---|---|---|
| Urbanístico (índice construcción, aprovechamiento, densidad, $/m²) | 🟡 | `build.urbanistico`/`modelo` lo calcula; no valida contra POT | **B2** |
| Estructura de costos | 🟡 | top-down % de ventas (`schema.CostosPct`); bottom-up por capítulos abierto pero sin taxonomía | **C4** |
| Ingeniería / costos emergentes / contingencias | ❌ | costo es output; sin WBS estandarizado | **C4** |
| Estudio administrativo (organigrama/roles) | 🟡 | gastos fijos lump-sum; sin estructura organizacional | — (baja prioridad) |
| Estudio ambiental / sostenibilidad / ESG | ❌ | no existe módulo (el curso lo enfatiza) | **B1** |

## Módulo 6 — Evaluación financiera (el corazón del curso)
| Concepto | Estado | Dónde / nota | Acción |
|---|---|---|---|
| VPN/VAN (@TIO) y VPN @WACC | ✅ | `apalancamiento`/`valor.py`; `metrics` (`vpn_proyecto`, `valor_creado`) | — |
| TIR proyecto (desapalancada) y TIR socio (apalancada) | ✅ | `finanzas.irr_anual`, `apalancamiento` | — |
| PRI / Payback | 🟡 | `payback_mes` del PROYECTO; falta payback del SOCIO | **A2** |
| Máxima exposición de caja + mes | ✅ | `apalancamiento.max_necesidad_caja` | — |
| Flujo proyecto vs inversionista; fondos propios y acumulados | ✅ | doble flujo en `apalancamiento` | — |
| Evaluación a precios corrientes y **constantes** | 🟡 | modelo 100% corrientes; **falta rama de precios constantes/reales** | **A3** |
| Tasa de descuento / tasa de corte / TIO; costo de oportunidad | 🟡 | TIO 15% (hurdle); falta exponer costo de oportunidad explícito | **A2** |
| CAPM build-up (Damodaran) | ✅ | `finanzas.calcular_wacc` (beta des/reapalancada, EMBI, paridad inflación, Kd, escudo, WACC) | — |
| Cierre financiero (fuentes/usos) | 🟡 | piezas existen (equity/crédito/subrogaciones/lote/costos/intereses); **falta tabla Fuentes=Usos** | **A1** |
| Análisis de sensibilidad (escenarios, tornado, heatmap) | ✅ | `modelo.escenarios`/`heatmap_sensibilidad`; web | — |
| Monte Carlo (distribuciones, percentiles, certeza, tornado de varianza) | ✅ | `simulacion.py` + web **Crystal Ball** (tooltip, banda de certeza, acumulada, certeza interactiva) | — |
| Múltiplo de equity · incidencia del lote · punto de equilibrio operacional % | ❌ | no están en `metrics.REGISTRO` | **A2** |
| Cap Rate · NOI · yield-on-cost · valor de salida | ❌ | **FUERA de alcance** (ALEPH es desarrollo-venta, no renta) | — (fase futura si hay renta) |

## Competencias del curso → estado
- Valoración (VPN/TIR/PRI): ✅ (PRI del socio → A2).
- Identificación y gestión de riesgos: ✅ financieros (Monte Carlo, sensibilidad, estrés de tesorería); 🟡 riesgos legal/ambiental → **B1**.
- Decisiones estratégicas (modelos + estudios de mercado): 🟡 (modelos ✅; estudios de mercado → **B3**).
- Proyectos sostenibles (ESG, impacto ambiental, normativa): ❌ → **B1**.

## Plan de acción
Detalle, secuencia y gobernanza en el plan: ver el documento de planeación de la sesión
(`mejoremos-el-cap-tulo-de-snazzy-yeti.md` en los planes), resumido: **Fase A** (completar M6:
A1 cierre financiero, A2 métricas faltantes, A3 precios constantes) → **Fase B** (B1 due diligence
legal/ambiental/urbanístico al gate de viabilidad, B2 POT, B3 estudio de mercado) → **Fase C** (C1
tributario after-tax con acta, C2 ingreso en /web, C3 EVM/actuals con SINCO/CRM, C4 WBS bottom-up).

> Este documento es **referencia viva**: se actualiza a medida que cada ítem se implementa (mover su
> estado de ❌/🟡 a ✅ con el PR correspondiente).
