# -*- coding: utf-8 -*-
"""Excepciones de dominio del motor.

Hoy el motor degrada de forma controlada (registra un warning y devuelve {} ante datos de
portafolio inválidos), para no romper la app que llama a `calcular()` directamente. En la Fase 2
(capa de servicios) estas excepciones se LANZARÁN desde el kernel y se capturarán en el servicio,
mostrando al usuario un mensaje claro en vez de "sin datos" en silencio.
"""


class ErrorMotor(Exception):
    """Base de los errores de dominio del motor financiero."""


class DatosInvalidos(ErrorMotor):
    """Los datos del proyecto no permiten calcular (fechas mal formadas, estructura faltante…)."""


class HitosFaltantes(ErrorMotor):
    """No se pudieron resolver los hitos del portafolio (secuenciamiento de etapas/sucesoras)."""
