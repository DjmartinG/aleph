# Acta (BORRADOR) — Tributario *after-tax* a nivel de DECISIÓN · Fase C1

> **ESTADO: BORRADOR — NO APROBADA.** Requiere (1) **validación del asesor fiscal de CG** de las reglas/tasas marcadas `[VALIDAR]` y (2) **aprobación explícita de Martín** antes de tocar una sola cifra o mergear código que publique cifras after-tax de decisión. Este documento **no cambia el motor ni el dorado**; es la preparación que exige la Regla #6b de la constitución.
>
> **Fecha:** 2026-06-20 · **Autor:** agente (Claude) · **Curso de referencia:** Camacol M4 (consecuencias tributarias en viabilidad) + M6 (tributación).

---

## 1. Por qué este acta

La Fase C1 del plan Camacol busca **completar el tratamiento tributario** y dar la **opción de evaluar la decisión (TIR/VPN) después de impuestos (Layer B)**. A diferencia de las Fases A y B —aditivas y dorado-seguras—, **C1 introduce cifras de DECISIÓN nuevas** (rentabilidad after-tax) que dependen de supuestos fiscales aún sin confirmar. La constitución (Regla #6b) prohíbe aplicar esto en silencio: primero el acta + el visto bueno del asesor + la aprobación de Martín.

## 2. Estado actual (auditado en el código, no asumido)

- **Las cifras de decisión son PRE-IMPUESTO.** El dorado y todo lo que ve el comité (TIR proyecto **37,60%**, TIR socio **41,72%**, VPN @TIO, flujo, exposición) se calculan **antes del impuesto de renta** sobre el flujo. La única línea fiscal que ya entra al P&G es la **renta → UDI** (utilidad después de renta), vía `tributario.calcular_renta`, con la **exención VIS** ya aplicada (M2).
- **Ya existe un Layer-B DIRECCIONAL, pero solo en el comparador de Vehículos.** `tributario.overlay_after_tax` aplica a las **series mensuales** renta + GMF + dividendos y produce `tir_proyecto_at` / `tir_socio_at` / `vpn_proyecto_at` **after-tax** por vehículo (`tributario.comparar`). Hoy se usa **solo** en la pestaña *Vehículos*, etiquetado explícitamente como **direccional** y con la TIR auditada de la fiducia reportada **aparte** como cifra oficial.
- **Las tasas de ese Layer-B son PLACEHOLDERS `[VALIDAR]`:** `GMF_TASA = 0.4%` (4×1000), `DIVIDENDOS_TASA = 10%`, además del timing (impuesto modelado **contemporáneo** al flujo, sin diferimiento a la declaración del año siguiente). Ver `tributario.py:145-146` y las notas `[VALIDAR]` de cada vehículo en `vehiculos.py`.
- **Faltan tributos del curso:** **devolución de IVA en VIS (4%)**, **ICA** (municipal, por actividad/municipio), **retención en la fuente**, y el **GMF real** con sus exenciones de fiducia. Hoy no se modelan.

**Conclusión del estado:** el andamiaje after-tax existe pero es **direccional y acotado al comparador**; llevarlo a las **cifras de decisión** exige convertir placeholders en tasas/reglas reales.

## 3. Qué propone C1 (alcance)

1. **Tributos faltantes en el motor** (cada uno con su norma y `[VALIDAR]`):
   - **Devolución de IVA VIS 4%** (Ley 1607/2012 y reglamentación; aplicabilidad y *timing* del reintegro).
   - **ICA** por municipio/actividad (tarifa de construcción/venta en Bogotá y demás municipios donde opera CG).
   - **Retención en la fuente** sobre pagos/recaudos relevantes.
   - **GMF real** (4×1000, Art. 871 ET) **con las exenciones de patrimonio autónomo/fiducia** (clave: hoy el placeholder lo aplica sin exención).
2. **Capa de decisión after-tax (Layer B), ADITIVA y etiquetada:** exponer `TIR proyecto (después de imp.)`, `TIR socio (después de imp.)` y `VPN @TIO (después de imp.)` **junto** a las pre-impuesto, **nunca en su reemplazo**. El comité seguiría viendo la cifra pre-impuesto como hoy + la after-tax como lente adicional (igual que A3 hizo con las tasas reales).

## 4. Clasificación de gobernanza (importante)

- **Técnicamente es ADITIVO al `result` del motor:** las cifras pre-impuesto (el dorado) **NO cambian**; se agregan campos nuevos after-tax. Igual que el patrón de A2/A3: regenerar snapshots + `diff_dorado.py` confirma **solo-adiciones** (cero colaterales). Es decir, **el dorado no se mueve**.
- **PERO la gobernanza es de cifra-moving en su efecto:** se publican **cifras de decisión nuevas** que el comité podría usar para decidir, y cuya validez depende de supuestos fiscales. Por eso **no basta** con el patrón aditivo: hace falta la **validación del asesor fiscal** (para no publicar números que engañen, el mismo riesgo que evitamos en A1 con la “utilidad después de intereses”) **y la aprobación de Martín**.
- **Regla operativa:** **no se mergea ni se enciende ninguna cifra after-tax de decisión** hasta cerrar el §5. Mientras tanto, el comparador de Vehículos sigue como está (direccional, etiquetado).

## 5. Preguntas para el ASESOR FISCAL (cerrar los `[VALIDAR]` antes de codear)

1. **Renta VIS:** ¿la exención (ET 235-2 num.4) cubre **solo la utilidad** o también los **honorarios**? Hoy el motor grava los honorarios salvo `vis_exime_honorarios=true`. ¿Vigencia post Ley 2277/2022 y plazos de licencia?
2. **GMF (4×1000):** ¿qué movimientos de la **fiducia/patrimonio autónomo** están **exentos** (Art. 871 ET y exenciones)? El placeholder hoy lo aplica al movimiento bruto **sin** exención → probablemente **sobreestima** la carga.
3. **Dividendos (vehículos opacos SAS/SPV):** tarifa marginal aplicable al socio (Ley 2277/2022) y si la **venta de la SPV >2 años** como ganancia ocasional (15%) es defendible (Art. 869 abuso).
4. **IVA VIS 4%:** ¿procede la **devolución**, sobre qué base y con qué **timing** de reintegro (afecta el flujo, no solo el P&G)?
5. **ICA:** tarifa por **municipio/actividad** para CG (Bogotá y otros) y base gravable.
6. **Retención en la fuente:** conceptos y tarifas relevantes al recaudo/pagos del proyecto.
7. **Timing:** ¿modelar el impuesto **contemporáneo** al flujo (como hoy) o **diferido** a la declaración del año siguiente? Impacta la TIR after-tax.

## 6. Plan de implementación (SOLO tras §5 validado + aprobación)

1. Reemplazar placeholders por tasas/reglas confirmadas en `tributario.py` (+ `vehiculos.py` donde aplique); sumar IVA VIS / ICA / retención como funciones puras.
2. Exponer la capa after-tax de decisión **aditiva y etiquetada** en `apalancamiento`/`build` + `metrics.REGISTRO` (con etiqueta de base “después de imp.”). Greenfield → “— greenfield”.
3. **Verificación dorado:** regenerar snapshots y correr `python engine/execution/diff_dorado.py --permite <campos after-tax nuevos>` → confirmar **cero colaterales** (las cifras pre-impuesto intactas). Si algún pre-impuesto se moviera, **parar**: eso ya sería re-baseline con acta de cifras.
4. UI: lente after-tax junto a la pre-impuesto (Resumen) + comparador de Vehículos con tasas reales. Cada cifra con su etiqueta.

## 7. Decisión solicitada a Martín

- [ ] Llevar el §5 al **asesor fiscal** de CG y traer las respuestas.
- [ ] Con las respuestas, **aprobar** (o ajustar) el alcance del §3 y autorizar la implementación del §6.
- [ ] Confirmar si la capa after-tax se publica **al comité** o queda como vista interna mientras madura.

> Hasta recibir lo anterior, **C1 queda detenido a propósito** (sin código, sin cifras). Es la aplicación correcta de la Regla #6b: preparar y esperar la aprobación explícita.
