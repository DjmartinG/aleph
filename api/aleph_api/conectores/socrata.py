# -*- coding: utf-8 -*-
"""Conector datos.gov.co (Socrata SODA) — tasas de colocación por entidad (origen: SFC, Formato 414).

Datasets: reciente `qzsc-9esp` (últimas semanas) e histórico `w9zh-vetq` (CC BY-SA, gratis, semanal).
Entrega `ValorMacro` por banco para CRÉDITO DE VIVIENDA (VIS / No-VIS) = la tasa a la que cada banco
desembolsó. **Preview / solo lectura:** no escribe nada, no toca el motor.

OJO conceptual: el crédito CONSTRUCTOR (spread negociado con cada banco) NO se publica por entidad →
va en una tabla MANUAL (otro incremento). Esto cubre la tasa al COMPRADOR (afecta subrogaciones/demanda).

GOTCHA Socrata (resuelto): los nombres de columna del API se autogeneran del título y la tilde de
"Crédito" cambia el campo (p.ej. `tipo_de_cr_dito`). Por eso NO filtramos por nombre de columna en el
servidor: leemos una página ordenada por :id DESC y descubrimos los campos reales de la fila, filtrando
en Python. El dataset trae varias filas por banco (plazos/semanas) → se CONSOLIDA a una por banco
(la del corte más reciente).
"""
from __future__ import annotations

from .base import ValorMacro, get_json, parse_fecha_iso, slug

URL_RECIENTE = "https://www.datos.gov.co/resource/qzsc-9esp.json"
URL_HISTORICO = "https://www.datos.gov.co/resource/w9zh-vetq.json"

BANCOS_CG = (
    "Bancolombia", "Davivienda", "Banco de Bogota", "BBVA", "Scotiabank Colpatria",
    "Banco Caja Social", "Itau", "AV Villas", "Fondo Nacional del Ahorro",
)

_F_ENTIDAD = ("nombre_entidad", "entidad", "nombre_de_la_entidad")
_F_TASA = ("tasa_efectiva_promedio", "tasa_efectiva", "tasa")
_F_PRODUCTO = ("producto_de_credito", "producto_de_cr_dito", "producto")
_F_TIPO = ("tipo_de_credito", "tipo_de_cr_dito", "tipo")
_F_FECHA = ("fecha_corte", "fecha_de_corte", "fecha", "corte")


def _find_campo(keys, candidatos, hints):
    for c in candidatos:
        if c in keys:
            return c
    for k in keys:
        kl = k.lower()
        if any(h in kl for h in hints):
            return k
    return None


def _resolver_campos(keys):
    return {
        "tipo": _find_campo(keys, _F_TIPO, ("tipo",)),
        "tasa": _find_campo(keys, _F_TASA, ("tasa",)),
        "entidad": _find_campo(keys, _F_ENTIDAD, ("entidad",)),
        "producto": _find_campo(keys, _F_PRODUCTO, ("producto",)),
        "fecha": _find_campo(keys, _F_FECHA, ("fecha", "corte")),
    }


def _norm(s):
    return (s or "").strip().lower()


def _es_vis(producto) -> bool:
    p = _norm(producto)
    return "vis" in p and "no vis" not in p and "no-vis" not in p


def parse_tasas_vivienda(rows, bancos=BANCOS_CG):
    """Filas Socrata → `ValorMacro` por banco y tipo (VIS/No-VIS), CRUDAS (puede haber varias por
    banco). Descubre los nombres de campo de la propia fila (defensivo). Ignora filas que no sean
    'Vivienda', sin entidad o sin tasa numérica."""
    if not rows:
        return []
    campos = _resolver_campos(list(rows[0].keys()))
    if not (campos["tipo"] and campos["entidad"] and campos["tasa"]):
        return []
    bset = tuple(slug(b) for b in bancos) if bancos else None
    out = []
    for row in rows:
        if _norm(row.get(campos["tipo"])) != "vivienda":
            continue
        ent = row.get(campos["entidad"])
        tasa = row.get(campos["tasa"])
        if not ent or tasa in (None, ""):
            continue
        ent_slug = slug(ent)
        if bset and not any(b in ent_slug for b in bset):
            continue
        try:
            val = float(str(tasa).replace(",", "."))
        except (TypeError, ValueError):
            continue
        prod = row.get(campos["producto"]) if campos["producto"] else None
        vis = _es_vis(prod)
        out.append(ValorMacro(
            clave=f"tasa_vivienda:{ent_slug}:{'vis' if vis else 'no_vis'}",
            nombre=f"Tasa vivienda {'VIS' if vis else 'No-VIS'} - {ent}",
            valor=val, unidad="pct_ea", fuente="SFC vía datos.gov.co (Socrata)",
            metodo="api", fecha=parse_fecha_iso(row.get(campos["fecha"])) if campos["fecha"] else None,
            fuente_normativa="SFC Formato 414",
            detalle={"entidad": ent, "producto": prod, "vis": vis},
        ))
    return out


def consolidar_por_clave(vals):
    """Una tasa por `clave` (banco × VIS/No-VIS): la del corte MÁS RECIENTE. Desempata por el primero
    visto (las filas vienen ordenadas :id DESC = recientes primero)."""
    from datetime import date
    best = {}
    for v in vals:
        cur = best.get(v.clave)
        f_v = v.fecha or date.min
        if cur is None or f_v > (cur.fecha or date.min):
            best[v.clave] = v
    return list(best.values())


def fetch_tasas_vivienda(bancos=BANCOS_CG, *, get=get_json, historico=False, limite=5000, consolidado=True):
    """Lee una página del dataset (sin filtrar por nombre de columna, para evitar el 400 de Socrata) y
    filtra en Python. :id DESC trae lo más reciente. Por defecto CONSOLIDA a una tasa por banco.
    Errores de red se PROPAGAN. `get` inyectable para pruebas."""
    url = URL_HISTORICO if historico else URL_RECIENTE
    rows = get(url, params={"$limit": limite, "$order": ":id DESC"})
    vals = parse_tasas_vivienda(rows, bancos=bancos)
    return consolidar_por_clave(vals) if consolidado else vals


def _preview():  # pragma: no cover
    for hist in (False, True):
        etiqueta = "historico" if hist else "reciente"
        try:
            vals = fetch_tasas_vivienda(historico=hist)
        except Exception as e:  # noqa: BLE001
            print(f"[socrata] {etiqueta}: no se pudo leer en vivo: {e}")
            continue
        if vals:
            print(f"[socrata] {etiqueta}: {len(vals)} tasas por banco (consolidadas)")
            for v in sorted(vals, key=lambda x: x.clave):
                f = v.fecha.isoformat() if v.fecha else "s/f"
                print(f"  {v.nombre:<52} {v.valor:>7.2f}% EA   corte {f}")
            return
        print(f"[socrata] {etiqueta}: sin filas de vivienda para los bancos CG.")
    print("[socrata] no se obtuvieron tasas (revisa conexion o el dataset).")


if __name__ == "__main__":  # pragma: no cover
    _preview()
