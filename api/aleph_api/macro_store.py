# -*- coding: utf-8 -*-
"""Persistencia de supuestos macro en la tabla `supuestos_macro` con COMPUERTA DE REVISIÓN (M6).

Flujo: los conectores (Socrata/Banrep/Damodaran) producen `ValorMacro`; `refrescar()` los PROPONE
(estado 'por_validar', vigente=False) — NO los aplica. Un admin los APRUEBA (`aprobar`) y solo ahí
pasan a vigentes (un vigente por clave, garantizado por el índice único de la migración 0003).

Mismo patrón que `write.py`: exige Supabase configurado. NO toca el motor ni mueve cifras: solo
guarda datos de referencia que la UI/análisis pueden consultar y que M1 (cuando se cablee) usaría
como insumo del WACC. `sb` y `recolectar` son inyectables para pruebas (sin red ni Supabase).
"""
from __future__ import annotations

from fastapi import HTTPException

from . import repo
from .conectores import banrep, damodaran, socrata

TABLE = "supuestos_macro"


def _sb():
    if not repo._usa_supabase():
        raise HTTPException(status_code=503, detail="supuestos_macro requiere Supabase configurado")
    return repo._cliente()


def _fila(v):
    """`ValorMacro` → fila de la tabla, SIEMPRE como propuesta (vigente=False, por_validar)."""
    return {
        "clave": v.clave, "nombre": v.nombre, "valor": float(v.valor), "unidad": v.unidad,
        "fuente": v.fuente, "metodo": v.metodo, "descripcion": "",
        "fecha": v.fecha.isoformat() if v.fecha else None,
        "estado_validacion": "por_validar", "fuente_normativa": v.fuente_normativa, "vigente": False,
    }


def proponer(valores, *, sb=None):
    """Inserta cada `ValorMacro` como PROPUESTA (no vigente). Devuelve cuántas se propusieron."""
    sb = sb or _sb()
    n = 0
    for v in valores:
        sb.table(TABLE).insert(_fila(v)).execute()
        n += 1
    return {"propuestos": n}


def listar_vigentes(*, sb=None):
    sb = sb or _sb()
    return sb.table(TABLE).select("*").eq("vigente", True).execute().data or []


def pendientes(*, sb=None):
    sb = sb or _sb()
    return sb.table(TABLE).select("*").eq("estado_validacion", "por_validar").execute().data or []


def aprobar(claves, *, sb=None):
    """Admin: por cada clave, baja el vigente anterior y sube la propuesta más reciente a vigente.
    Garantiza un solo vigente por clave (coherente con el índice único de 0003)."""
    sb = sb or _sb()
    aprobadas = []
    for clave in claves:
        (sb.table(TABLE).update({"vigente": False, "estado_validacion": "reemplazado"})
         .eq("clave", clave).eq("vigente", True).execute())
        prop = (sb.table(TABLE).select("id").eq("clave", clave).eq("estado_validacion", "por_validar")
                .order("created_at", desc=True).limit(1).execute().data or [])
        if prop:
            (sb.table(TABLE).update({"vigente": True, "estado_validacion": "vigente"})
             .eq("id", prop[0]["id"]).execute())
            aprobadas.append(clave)
    return {"aprobadas": aprobadas}


def _recolectar_default():
    """Corre todos los conectores en vivo y junta los `ValorMacro`. Tolerante a fallos por fuente."""
    out = []
    try:
        out += socrata.fetch_tasas_vivienda()
    except Exception:  # noqa: BLE001
        pass
    for serie in ("trm", "ibr"):
        try:
            v = banrep.fetch_serie(serie)
            if v:
                out.append(v)
        except Exception:  # noqa: BLE001
            pass
    try:
        out += damodaran.fetch_damodaran("Colombia")
    except Exception:  # noqa: BLE001
        pass
    return out


def refrescar(*, sb=None, recolectar=_recolectar_default):
    """Corre los conectores y PROPONE sus valores (compuerta de revisión). No aplica nada."""
    valores = recolectar()
    res = proponer(valores, sb=sb)
    res["recolectados"] = len(valores)
    return res
