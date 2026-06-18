# Ontología canónica de ALEPH — nota de mapeo

Esta nota acompaña a `engine/aleph_engine/ontologia.py`: una **fachada de solo lectura** que consolida
el vocabulario del motor en una fuente única **por referencia** (cero valores duplicados que puedan
derivar) + un **registro de invariantes** de cuadre. Es **100% aditiva**: no toca `calcular()`, no mueve
cifras, no reescribe lógica. **Dependencia de una sola dirección:** `ontologia.py` importa de los demás
módulos; los demás **no** se reconectan a ella (eso sería un paso futuro, deliberado).

> **Glosario v0.1:** el borrador `Ontologia_Canonica_CG_borrador.md` vive en la carpeta de ALEPH
> (OneDrive de gerencia), no en el repo. Conviene **copiarlo aquí** (`docs/ontologia_canonica_glosario.md`)
> para versionarlo; esta nota mapea cada elemento del módulo al concepto del glosario.

## Mapeo elemento ↔ fuente real (auditado, no asumido)

| Elemento del módulo | Concepto (glosario) | Fuente real en el código | Cómo se referencia |
|---|---|---|---|
| `FASES` / `FASE_DEFAULT` / `FASE_LABEL` | Fases del ciclo de vida | `config.ESTADOS` / `ESTADO_DEFAULT` / `ESTADO_LABEL` | import directo (identidad) |
| `TIPOS_PROYECTO` | Tipos de proyecto (VIS/VIP/No VIS) | `schema.Meta.tipo` es `Optional[str]` (comentario, **no** Literal) | **constante canónica** (no hay fuente tipada hoy) |
| `CATEGORIAS_COSTO` | Categorías de costo (top-down, % de ventas) | `schema.CostosPct` (directos, indirectos, honorarios, util_lote) | `tuple(CostosPct.model_fields)` |
| `HITOS` / `HITOS_POR_CODIGO` | Hitos del cronograma | códigos `IV/PE/FV/IC/FC` que produce `modelo._hitos` → `portafolio.calcular_portafolio` | **constantes nuevas** (nombran lo implícito; el cálculo no se toca) |
| `CONCEPTOS_RECAUDO` | Esquema de recaudo colombiano | implícito en `modelo._recaudo` / `ingresos.recaudo_portafolio` | **constantes nuevas** (documentales) |
| `INDICADORES` / `indicador()` | Diccionario de indicadores | `metrics.REGISTRO` (22 entradas, dataclass `Metric`) | referencia al mismo dict + accesor `metrics.metric` |
| `VEHICULOS` | Vehículos jurídico-financieros | `vehiculos.claves()` (catálogo `_CATALOGO`, 7 vehículos) | `tuple(vehiculos.claves())` |
| `INVARIANTES` | Invariantes de cuadre (topología) | `checks.correr(R)` (5 checks) + `checks.check_spi(evm)` | cada `referencia` apunta a la **función existente** |

### Invariantes registrados (todos referencian funciones reutilizables, ninguno se extrajo)

| id | Nombre | Descripción | Lo calcula |
|---|---|---|---|
| `pyg_ingresos` | P&G cierra | `total_ingresos == ventas + reconocimientos` | `checks.correr` |
| `recaudo_ventas` | Recaudo = ingresos del P&G | `sum(ingresos del flujo apalancado) == total_ingresos` | `checks.correr` |
| `flujo_utilidad` | Flujo ≈ utilidad | `acumulado_operativo[-1] == utilidad operativa` | `checks.correr` |
| `reparto` | Reparto cuadra | `CG + socio == resultados` | `checks.correr` |
| `credito` | Crédito cuadra | `0 ≤ cupo ≤ financiable` y `credito_max ≥ 0` | `checks.correr` |
| `spi_plausible` | SPI plausible | `SPI ∈ [0.4, 2.0]` | `checks.check_spi` |

> Los 5 checks de `checks.correr` ya eran una **función reutilizable** (no se calculaban inline), así que
> el registro los referencia sin extraer ni reescribir nada. Si en el futuro algún check naciera inline,
> la regla es **documentar su ubicación** en `referencia` (string), no extraerlo en este paso.

## TODO `[por validar]` — NO encodeado (no se hornean suposiciones)

Quedan como comentarios en el módulo, **sin valor**, hasta que el comité / asesor los confirme:

- **Capítulos del WBS** (presupuesto bottom-up): hoy el costo es top-down (`CostosPct`, % de ventas). El
  desglose por capítulo llegará con el "Auditor de presupuestos" / SINCO; no se inventa la lista.
- **% del crédito constructor:** `config.COBERTURA_CC = 0.80` es un *default*; el real por proyecto se
  confirma con el banco.
- **Uso de VIP:** hoy el motor trata VIS y VIP igual para la exención de renta; confirmar si hay
  diferencia operativa/normativa que amerite separarlos.
- **Yield on cost:** aún no existe como indicador en `metrics.REGISTRO`; definir fórmula + etiqueta de
  base antes de encodearlo.

## Verificación

`engine/tests/test_ontologia.py` (11 tests): importa limpio · consistencia sin drift (`FASES is
config.ESTADOS`, vehículos/indicadores/categorías = la fuente) · los `id` de los invariantes coinciden
**exactamente** con las claves que emiten los checks (probado con un `R` sintético, data-independiente) ·
los códigos de hito existen en el cronograma real · **dorado INTACTO** (importar la fachada no mueve
ninguna ancla de `calcular()`). El gate completo del motor (incl. `test_golden_harness`) queda verde.

## Próximo paso (futuro, NO este)

Cuando el vocabulario esté estable y validado, se podría **re-cablear** algún módulo para que consuma de
`ontologia` (p.ej. `schema` validando `Meta.tipo` contra `TIPOS_PROYECTO`). Eso **acopla comportamiento**
→ exige su propio golden + acta. Por ahora la fachada es solo lectura, una sola dirección.
