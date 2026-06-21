# -*- coding: utf-8 -*-
"""C2 (edición de tipologías) · validación de la tabla de tipologías — compuerta de ESCRITURA.

`normalizar_tipologias` (modelo.py) deriva und/ventas de la tabla `tipologias` SIN avisar de datos
malformados (etapa inexistente → grupo huérfano que no suma; clase omitida → default 'apartamento';
precio en MILES en vez de PESOS → ventas 10x abajo). Este módulo VALIDA esa tabla antes de persistir,
con mensajes legibles. Es PURO y NO se llama desde `calcular()` (dorado intacto); lo invoca el API en
el camino de escritura (crear/editar/aprobar). Espeja las reglas del motor, no las duplica en cifra.
"""
from __future__ import annotations

METODOS_VALIDOS = ("$/und", "$/m²")
PRECIO_MIN = 1_000_000   # el precio va en PESOS COP; < 1.000.000 casi siempre es el gotcha "miles" (10x)


def _clases_validas() -> set[str]:
    # Fuente única: las clases del motor (HOUSING + ADICIONAL). Import lazy → cero acoplamiento de carga.
    from . import modelo
    return set(modelo.HOUSING) | set(modelo.ADICIONAL)


def validar_tipologias(par: dict) -> list[str]:
    """Devuelve una lista de errores legibles (vacía = válida). No lanza; el API decide el 422."""
    tip = par.get("tipologias")
    if not tip:
        return []
    if not isinstance(tip, list):
        return ["'tipologias' debe ser una lista."]

    clases = _clases_validas()
    cods = {e.get("cod") for e in (par.get("etapas") or [])}
    cods_legibles = sorted(c for c in cods if c is not None)
    errores: list[str] = []

    for i, t in enumerate(tip, 1):
        if not isinstance(t, dict):
            errores.append(f"tipología {i}: cada tipología debe ser un objeto.")
            continue
        nom = t.get("nombre") or f"tipología {i}"

        if t.get("etapa") not in cods:
            errores.append(f"{nom}: la etapa {t.get('etapa')!r} no existe en el proyecto (etapas: {cods_legibles}).")

        clase = t.get("clase")
        if clase not in clases:
            errores.append(f"{nom}: clase {clase!r} inválida (use una de {sorted(clases)}).")

        metodo = t.get("metodo", "$/und")
        if metodo not in METODOS_VALIDOS:
            errores.append(f"{nom}: método {metodo!r} inválido (use '$/und' o '$/m²').")

        und = t.get("und")
        if isinstance(und, bool) or not isinstance(und, int) or und < 0:
            errores.append(f"{nom}: 'und' debe ser un entero ≥ 0 (recibido {und!r}).")

        precio = t.get("precio")
        if isinstance(precio, bool) or not isinstance(precio, (int, float)) or precio <= 0:
            errores.append(f"{nom}: 'precio' debe ser un número > 0 (recibido {precio!r}).")
        elif precio < PRECIO_MIN:
            errores.append(
                f"{nom}: 'precio' {precio:,.0f} parece estar en MILES; debe ir en PESOS COP "
                f"(≥ {PRECIO_MIN:,.0f}). Revisa la escala para no dividir las ventas por 1.000 (error 10x).")

        if metodo == "$/m²":
            area = t.get("area_und")
            if isinstance(area, bool) or not isinstance(area, (int, float)) or area <= 0:
                errores.append(f"{nom}: con método '$/m²', 'area_und' debe ser un número > 0 (recibido {area!r}).")

    return errores
