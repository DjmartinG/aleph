# Acta — Corrección VIS en el P&G (M2 · Layer A) · 14-jun-2026

**Decisión:** reconocer la EXENCIÓN de renta de la utilidad VIS en la línea UDI del P&G. Aprobada por
Martín (Dirección Financiera). Es la corrección de exhibición (las decisiones siguen pre-impuestos —
ver "Pendiente Layer B"). Hallazgo de la auditoría M2: la renta del 35% hoy NO entra en la TIR/VPN
(que son antes de impuestos); vive solo en la línea UDI del P&G.

## Regla aplicada (`engine/aleph_engine/modelo.py::pyg`)

- **VIS/VIP:** la utilidad de la primera venta es **renta EXENTA** (ET Art. 235-2 num. 4)
  `[VALIDAR vigencia Ley 2277/2022]`. Los **honorarios** (ingreso por servicios) siguen **GRAVADOS**
  por defecto. Si el asesor confirma exención total, `financiero.vis_exime_honorarios=true` → renta 0.
- **No-VIS:** renta 35% sobre el reintegro completo (sin cambio).

## Impacto (millones COP)

| Proyecto | Tipo | renta antes | renta después | UDI antes | UDI después |
|---|---|---|---|---|---|
| Navarra | VIS | 12.126 | **8.149** | 22.520 | **26.497** (+3.977) |
| Torres de Campiñas | VIS | 9.372 | **7.213** | 17.405 | **19.564** (+2.159) |
| Dominica | No-VIS | — | — | — | sin cambio |

Cota superior (si el asesor exime también honorarios, flag `vis_exime_honorarios`): UDI Navarra 34.646.

## Alcance (verificado por diff estricto)

Solo cambian `result.pyg.renta` y `result.pyg.udi` de los proyectos **VIS**. Dominica (No-VIS): 0
cambios. **Intactos:** TIR proyecto, TIR socio, VPN @TIO, flujo, crédito, reparto CG/socio — las
decisiones son antes de impuestos y no dependen de la renta.

## Verificación

Engine 41 (incl. dorado re-baselizado) · API 62 · ruff. Test nuevo `engine/tests/test_tributario_vis.py`
(sintético, CI-safe): VIS exime utilidad/grava honorarios, No-VIS grava todo, flag de exención total.

## Archivos

`engine/aleph_engine/modelo.py` (pyg), `engine/tests/test_tributario_vis.py`, 6 snapshots regenerados
(solo los VIS cambian). Reversión: quitar la rama `_es_vis` y regenerar.

## Pendiente — Layer B (decisión de comité)

Llevar las cifras de DECISIÓN (TIR/VPN) a **después de impuestos** cambia el criterio de evaluación:
VIS quedaría más atractivo que No-VIS (la TIR de No-VIS bajaría al entrar el 35%). Es la palanca grande
del motor tributario por vehículo; se recomienda ratificarla con el Comité antes de implementarla.
