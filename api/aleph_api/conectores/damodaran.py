# -*- coding: utf-8 -*-
"""Conector Damodaran (NYU Stern) — riesgo país (CRP) y ERP por país.

Fuente ESTÁTICA (se actualiza ~anual, enero): la tabla de "Country Risk Premiums". Es justo el insumo
que el WACC del motor usa (metodología Damodaran): el CRP de Colombia es el riesgo país (`rp`/EMBI) y
el Total ERP es la prima de mercado del país. Mucho más estable que un endpoint en vivo.

Página de datos (HTML): se parsea con `html.parser` de la stdlib → SIN dependencias nuevas. Parser
DEFENSIVO: localiza la fila del país y mapea CRP/ERP por la cabecera. **Preview / solo lectura.**
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

from .base import ValorMacro, get_text

URL = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html"


class _Tabla(HTMLParser):
    """Extrae filas de celdas de todas las tablas del HTML (lista de listas de texto)."""

    def __init__(self):
        super().__init__()
        self.filas = []
        self._fila = None
        self._cel = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._fila = []
        elif tag in ("td", "th") and self._fila is not None:
            self._cel = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cel is not None:
            self._fila.append(" ".join("".join(self._cel).split()))
            self._cel = None
        elif tag == "tr" and self._fila is not None:
            self.filas.append(self._fila)
            self._fila = None

    def handle_data(self, data):
        if self._cel is not None:
            self._cel.append(data)


def _pct(texto):
    """'3.14%' / '3,14 %' → 0.0314; None si no hay porcentaje."""
    m = re.search(r"(-?\d+(?:[.,]\d+)?)\s*%", texto or "")
    return float(m.group(1).replace(",", ".")) / 100 if m else None


def parse_html(html, pais="Colombia"):
    """HTML de Damodaran → {crp, erp_total, fila, header} para `pais`. Intenta por CABECERA y, si esta
    no se detecta limpia (la página tiene filas basura), cae a mapeo POSICIONAL del layout estándar de
    Damodaran: [Country, Rating, Adj.Default Spread, CRP, Total ERP, Tax, ...] → CRP=2ª %, ERP=3ª %."""
    p = _Tabla()
    p.feed(html or "")
    filas = p.filas
    fila = None
    for f in filas:
        if f and f[0].strip().lower() == pais.lower():
            fila = f
            break
    if not fila:
        return None
    header = []
    for f in filas:
        if any("country risk premium" in c.lower() for c in f):
            header = f
            break
    crp = erp = None
    if header:
        def col(keys):
            for k, h in enumerate(header):
                if any(x in h.lower() for x in keys):
                    return k
            return None
        j_crp = col(("country risk premium",))
        j_erp = col(("total equity risk premium", "total erp"))
        if j_crp is not None and j_crp < len(fila):
            crp = _pct(fila[j_crp])
        if j_erp is not None and j_erp < len(fila):
            erp = _pct(fila[j_erp])
    if crp is None or erp is None:
        pcts = [x for x in (_pct(c) for c in fila) if x is not None]
        if len(pcts) >= 3:
            crp = crp if crp is not None else pcts[1]
            erp = erp if erp is not None else pcts[2]
    return {"crp": crp, "erp_total": erp, "fila": fila, "header": header}


def fetch_damodaran(pais="Colombia", *, get=get_text):
    """ValorMacro del CRP y el Total ERP del país (lista). Errores de red se PROPAGAN. `get` inyectable."""
    d = parse_html(get(URL, accept="text/html"), pais)
    if not d:
        return []
    out = []
    if d["crp"] is not None:
        out.append(ValorMacro(
            clave=f"damodaran:crp:{pais.lower()}", nombre=f"Riesgo país (CRP) — {pais}",
            valor=d["crp"], unidad="ratio", fuente="Damodaran (NYU Stern)", metodo="api",
            fuente_normativa="Country Risk Premiums (anual)", detalle={"fila": d["fila"]}))
    if d["erp_total"] is not None:
        out.append(ValorMacro(
            clave=f"damodaran:erp_total:{pais.lower()}", nombre=f"ERP total — {pais}",
            valor=d["erp_total"], unidad="ratio", fuente="Damodaran (NYU Stern)", metodo="api",
            fuente_normativa="Country Risk Premiums (anual)", detalle={"fila": d["fila"]}))
    return out


def _preview():  # pragma: no cover
    print(f"[damodaran] leyendo {URL} ...")
    try:
        html = get_text(URL, accept="text/html")
    except Exception as e:  # noqa: BLE001
        print(f"   error de red: {type(e).__name__}: {e}")
        return
    d = parse_html(html, "Colombia")
    if not d:
        print("   no se encontró la fila de Colombia (pega un trozo del HTML para ajustar el parser).")
        print(f"   (HTML recibido: {len(html)} chars)")
        return
    print(f"   CRP Colombia      : {d['crp']}")
    print(f"   ERP total Colombia: {d['erp_total']}")
    print(f"   header detectado  : {d['header']}")
    print(f"   fila Colombia     : {d['fila']}")


if __name__ == "__main__":  # pragma: no cover
    _preview()
