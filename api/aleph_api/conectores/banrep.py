# -*- coding: utf-8 -*-
"""Conector Banco de la República (SDMX REST) — IBR, DTF, TRM, EMBI (riesgo país).

Servicio: https://totoro.banrep.gov.co/nsi-jax-ws/rest (NSI). Responde **SDMX-ML 2.1 (XML)** —no JSON
(da 406)—, así que pedimos `application/xml` y parseamos con `ElementTree` (stdlib). Estos datos
alimentan el WACC (M1): EMBI = riesgo país; IBR/DTF = base del Kd. **Preview / solo lectura.**

Los IDs de dataflow de IBR/DTF/EMBI se FIJAN con `descubrir_dataflows()` (TRM ya conocido).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

from .base import ValorMacro, get_text, parse_fecha_iso

URL_BASE = "https://totoro.banrep.gov.co/nsi-jax-ws/rest"

# IDs de dataflow: TRM conocido; el resto POR CONFIRMAR vía descubrir_dataflows().
SERIES = {
    "trm": {"dataflow": "ESTAT,DF_TRM_DAILY_LATEST,1.0", "nombre": "TRM (COP/USD)", "unidad": "COP"},
    "ibr": {"dataflow": "ESTAT,DF_IBR_DAILY_LATEST,1.0", "nombre": "IBR overnight", "unidad": "pct_ea"},
    "dtf": {"dataflow": None, "nombre": "DTF", "unidad": "pct_ea"},
    "embi": {"dataflow": None, "nombre": "EMBI Colombia (riesgo pais)", "unidad": "pbs"},
}


def _lname(tag):
    return tag.rsplit("}", 1)[-1]


def _root(xml_text):
    # ET no acepta str con declaración de encoding → pasar bytes.
    data = xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        return None


def parse_sdmx_xml_ultimo(xml_text):
    """SDMX-ML 2.1 GenericData → {valor, periodo} de la observación MÁS RECIENTE. Por nombre local de
    etiqueta (robusto ante namespaces). Cada `Obs` trae `ObsDimension value=periodo` + `ObsValue value`."""
    root = _root(xml_text)
    if root is None:
        return None
    obs = []
    for el in root.iter():
        if _lname(el.tag) != "Obs":
            continue
        periodo = valor = None
        for ch in el:
            ln = _lname(ch.tag)
            if ln == "ObsDimension":
                periodo = ch.get("value")
            elif ln == "ObsValue":
                valor = ch.get("value")
        if valor is not None:
            obs.append((periodo or "", valor))
    if not obs:
        return None
    periodo, valor = max(obs, key=lambda o: o[0])
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return None
    return {"valor": valor, "periodo": periodo or None}


def parse_dataflows_xml(xml_text, filtro=("ibr", "dtf", "embi", "trm")):
    """SDMX-ML Structure → lista (id, nombre, ref) de dataflows; `ref` = 'AGENCIA,ID,VERSION' para la
    URL de datos. Filtra por subcadena de id/nombre (None = todos)."""
    root = _root(xml_text)
    if root is None:
        return []
    flows = []
    for el in root.iter():
        if _lname(el.tag) != "Dataflow":
            continue
        did = el.get("id") or ""
        agency = el.get("agencyID") or ""
        version = el.get("version") or ""
        nombre = ""
        for ch in el:
            if _lname(ch.tag) == "Name":
                nombre = (ch.text or "").strip()
                break
        ref = ",".join(x for x in (agency, did, version) if x) if agency else did
        texto = f"{did} {nombre}".lower()
        if not filtro or any(f in texto for f in filtro):
            flows.append((did, nombre, ref))
    return flows


def fetch_serie(clave, *, get=get_text, desde="2024"):
    """ValorMacro de la observación más reciente de una serie de `SERIES`. None si el dataflow aún no
    está confirmado o no hay dato. Errores de red se PROPAGAN."""
    cfg = SERIES.get(clave)
    if not cfg or not cfg.get("dataflow"):
        return None
    url = f"{URL_BASE}/data/{cfg['dataflow']}/all/"
    xml = get(url, params={"startPeriod": desde, "lastNObservations": 1}, accept="application/xml")
    p = parse_sdmx_xml_ultimo(xml)
    if not p:
        return None
    return ValorMacro(
        clave=f"banrep:{clave}", nombre=cfg["nombre"], valor=p["valor"], unidad=cfg["unidad"],
        fuente="Banco de la República (SDMX)", metodo="api",
        fecha=parse_fecha_iso(p["periodo"]), fuente_normativa="Banrep series estadísticas",
        detalle={"periodo": p["periodo"], "dataflow": cfg["dataflow"]},
    )


def descubrir_dataflows(filtro=("ibr", "dtf", "embi", "trm"), *, get=get_text):
    """Lista (id, nombre, ref) de dataflows del catálogo que casen con `filtro`. Fija los IDs reales."""
    xml = get(f"{URL_BASE}/dataflow/all/all/latest", accept="application/xml")
    return parse_dataflows_xml(xml, filtro=filtro)


def _preview():  # pragma: no cover
    for clave in ("trm", "ibr"):
        try:
            v = fetch_serie(clave)
            print(f"[banrep] {clave.upper():4} -> "
                  + (f"{v.valor} {v.unidad}  ({v.detalle.get('periodo')})" if v else "sin dato / parse vacío"))
        except Exception as e:  # noqa: BLE001
            print(f"[banrep] {clave.upper():4} -> error {type(e).__name__}: {e}")
    print("[banrep] buscando DTF/EMBI y afines en el catálogo...")
    amplio = ("dtf", "embi", "deposito", "cdt", "riesgo", "spread", "tes", "captacion", "interes")
    try:
        flows = descubrir_dataflows(filtro=amplio)
        if flows:
            for did, nombre, ref in flows[:60]:
                print(f"   ref={ref:<34} {nombre}")
        else:
            print("   sin coincidencias para DTF/EMBI (probablemente no están en este servicio).")
    except Exception as e:  # noqa: BLE001
        print(f"   error catálogo: {type(e).__name__}: {e}")


if __name__ == "__main__":  # pragma: no cover
    _preview()
