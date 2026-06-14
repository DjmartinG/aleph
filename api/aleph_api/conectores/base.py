# -*- coding: utf-8 -*-
"""Framework mínimo de conectores de datos macro (M6 · spec_pyg_dinamico.md).

`ValorMacro` = un dato leído de una fuente, listo para revisar y (luego) sembrar en `supuestos_macro`.
HTTP por `urllib` de la stdlib → SIN dependencias nuevas. Solo lectura: ningún conector escribe.
Con reintentos ante errores transitorios 5xx/red (los endpoints oficiales son ocasionalmente flaky).
"""
from __future__ import annotations

import json
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class ValorMacro:
    """Dato macro normalizado (preview). `valor` es el número leído; `detalle` lleva el contexto."""
    clave: str
    nombre: str
    valor: float
    unidad: str                  # pct_ea | ratio | indice | COP | pbs | ...
    fuente: str                  # "Banrep" | "SFC vía datos.gov.co" | "Damodaran" | "DANE" ...
    metodo: str = "api"          # api | manual | benchmark
    fecha: date | None = None    # corte del dato
    estado_validacion: str = "vigente"
    fuente_normativa: str = ""
    detalle: dict = field(default_factory=dict)


def _abrir(url, params, accept, timeout, retries=2, backoff=1.5):
    """GET → bytes, con reintentos ante 5xx/URLError (transitorios). Propaga el último error."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "ALEPH/1.0 (CG)"})
    ultimo = None
    for intento in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            ultimo = e
            if e.code >= 500 and intento < retries:
                time.sleep(backoff)
                continue
            raise
        except urllib.error.URLError as e:
            ultimo = e
            if intento < retries:
                time.sleep(backoff)
                continue
            raise
    raise ultimo


def get_json(url: str, params: dict | None = None, timeout: int = 20, accept: str = "application/json"):
    """GET → JSON con stdlib (reintentos ante 5xx). `accept` negocia el media-type."""
    return json.loads(_abrir(url, params, accept, timeout).decode("utf-8"))


def get_text(url: str, params: dict | None = None, timeout: int = 25, accept: str = "application/xml"):
    """GET → texto crudo (p.ej. SDMX-ML de Banrep), con reintentos ante 5xx."""
    return _abrir(url, params, accept, timeout).decode("utf-8", "replace")


def parse_fecha_iso(s) -> date | None:
    """'2025-04-25T00:00:00.000' o '2025-04-25' → date; None si no se puede parsear."""
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def slug(texto: str) -> str:
    """'Banco Davivienda S.A.' → 'banco_davivienda_s_a' (ascii, sin acentos; claves estables)."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode("ascii").lower()
    return "_".join("".join(c if c.isalnum() else " " for c in t).split())
