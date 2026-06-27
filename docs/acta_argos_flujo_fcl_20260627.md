# Acta — Argos-CVP: corrección del flujo de caja auditado (fila 20 "FCL") + carga v4

**Fecha:** 2026-06-27
**Proyecto:** Argos (CVP/RenoBo) · slug `4_argos_cvp_REAL` · VIS · prefactibilidad
**Alcance:** mueve cifras de **UN** proyecto (Argos). **NO toca el dorado** de Navarra/Dominica/Torres (verificado).
**Estado de gobernanza:** ⚠️ **NO APROBADA.** Requiere el OK explícito de Martín ANTES de `--apply` a prod.

---

## Qué cambia y por qué

El flujo de caja del proyecto (override `fiducia.fcl_proyecto`) en prod (v3) se extrajo de una fila
**equivocada** del Excel. Se corrige a la fila autoritativa:

- **Fuente:** `…/PREFACTIBILIDADES/24062026 PREFACTIBILIDAD PREDIO ARGOS 20 pisos1420_Conaltura.xlsx`, hoja **`FC INVERSION `** (con espacio final).
- **Correcto:** fila **20 "FCL"**, bloque **"FC PROYECTO"** → es el Flujo de Caja Libre del proyecto.
- **Incorrecto (lo que había):** la serie previa daba TIR 30.44% (sobreestimada). La fila **82 "Comprobacion"** es una fila de **chequeo**, no el FCL (su XIRR mensual = **19.70%**).
- Verificación de la fila correcta: **XIRR mensual fila 20 = 29.85%** = la TIR que el propio Excel reporta (celda r93). La serie anualizada reproduce EXACTAMENTE la serie de referencia (suma +84.11 mil M).

El P&G **no cambia** (ya estaba calibrado a los % del Excel); solo se corrige el flujo + se documenta el desglose fino.

## Antes (v3, prod) → Después (v4)

| Métrica | v3 (serie vieja) | **v4 (fila 20 "FCL")** | Nota |
|---|---:|---:|---|
| Suma del FCL | +80.87 mil M | **+84.11 mil M** | = serie de referencia |
| TIR proyecto | 30.44% | **29.81%** | = XIRR Excel 29.85% (fiel) |
| VPN@TIO 15% | +20.40 mil M | **+16.48 mil M** | |
| VPN@WACC 17.66% | +15.16 mil M | **+11.71 mil M** | GENERA VALOR (TIR > WACC) |

> La corrección **baja** el titular (30.44 → 29.81) porque la serie vieja estaba sobreestimada. 29.81% es la cifra **fiel al Excel** (XIRR 29.85%). La diferencia 29.81 (anual ALEPH) vs 29.85 (XIRR mensual) es la convención anual vs mensual.

## Verificación (gate local — verde)

P&G (% sobre ventas 459.5 mil M), todos calzan con el Excel:

| Concepto | ALEPH | Excel |
|---|---:|---:|
| Total ingresos | 103.80% | 103.80% |
| Reconocimiento (IVA 3.50 + Codensa 0.30) | 3.80% | 3.80% |
| Costo directo | 60.57% | 60.57% |
| Indirectos | 17.60% | 17.60% |
| Honorarios | 10.00% | 10.00% |
| Lote | 11.00% | 11.00% |
| **Utilidad operativa** | **4.63%** | **4.63%** |
| Renta (VIS exento) | 0 | 0 |

- **TIR socio CG = None** (por diseño: CG no aporta capital → retorno por honorarios → IRR indefinida).
- **After-tax = titular** (VIS exento de renta + `iva_en_operativo` → sin impacto tributario neto adicional).
- **Checks de cuadre: 5/5 verdes.**
- **`crea_valor = True`** → **GENERA VALOR**.
- **Dorado de Navarra/Dominica/Torres: INTACTO** (35 tests golden/anclas/finanzas verdes; el par de Argos es gitignored y no está en el dorado).
- **DRY-RUN `push_proyecto.py`:** crearía `scenarios v4 approved` (idempotente por hash; no escribió nada).

## Acción para Martín (tras aprobar las cifras de arriba)

```
python db/push_proyecto.py --check-only   # re-verifica el gate (opcional)
python db/push_proyecto.py                 # DRY-RUN (muestra que crearía v4)
python db/push_proyecto.py --apply         # ESCRIBE v4 approved en Supabase (prod)
```

El API recalcula en vivo; `/web → Portafolio → Argos` mostrará TIR 29.81% / GENERA VALOR. Rollback: el v3 queda inmutable; basta no leer el v4 (o cargar un v5 corrector).

## Pendientes (no bloquean la carga, sí el carácter definitivo)

- **Validación fiscal VIS** con asesor (renta exenta renovación urbana literal c, IVA 4% vs 3.8%, GMF ET 879).
- **TdR oficial de Argos** (vigilar SECOP II) — hoy plantilla "Lomas Pijaos II".
- **Costos bottom-up reales** de CG para firmar el veredicto de valor.

Disclaimer del proyecto = **PROVISIONAL** (visible en la ficha).
