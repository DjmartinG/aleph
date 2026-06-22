# -*- coding: utf-8 -*-
"""Conector SINCO (DATAMART SQL Server) — actuals de obra / valor ganado. Fase 1 · Paso 1.

LEE (solo lectura) la view `ADP_DTM_VFACT.ControlProyecto` del DATAMART de SINCO y la transforma en
registros `actuals` (PV/EV/AC/BAC por proyecto·nivel·periodo) para la tabla `actuals_obra` (migración 0004).

Mismo espíritu config-driven que los conectores macro (M6): **toda** la config va por variables de entorno
(NUNCA en código), la conexión es **inyectable** para pruebas, y el módulo importa sin el driver instalado
(el `import pymssql` es PEREZOSO, solo al conectar en vivo). **Solo lectura, solo agregados.**

ESTADO (Paso 1): el esqueleto está completo y probado con fixture, PERO `MAPEO_CONTROL_PROYECTO` está
VACÍO (placeholders `# TODO`): no inventamos nombres de columnas. Se llena en el Paso 2 con el diccionario
real de `ControlProyecto` (lo descubre el smoke `python -m aleph_api.conectores.sinco`, que imprime las
columnas). Hasta entonces `to_actuals(...)` con el mapeo por defecto falla en voz alta (no en silencio).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime

from .base import parse_fecha_iso

# View de solo lectura del DATAMART (agregados de control de proyecto). Esquema.objeto fijo de SINCO.
VIEW_CONTROL_PROYECTO = "ADP_DTM_VFACT.ControlProyecto"

# Variables de entorno que configuran la conexión (ver .env.example). Jamás hardcodear credenciales.
ENV_SERVER = "SINCO_SERVER"      # p.ej. 'datamart.sincoerp.com,4263'  (host,puerto al estilo SQL Server)
ENV_DB = "SINCO_DB"              # p.ej. 'SincoCGDW'
ENV_USER = "SINCO_USER"
ENV_PASSWORD = "SINCO_PASSWORD"

# Mapeo lógico (ALEPH) -> columna real de la view ControlProyecto.
# VACÍO a propósito: NO inventar nombres. Se llena en el Paso 2 con el diccionario real de la view.
# `proyecto/nivel/periodo/pv/ev/ac` son OBLIGATORIOS; `bac/corte` son opcionales.
MAPEO_CONTROL_PROYECTO: dict[str, str | None] = {
    "proyecto": None,  # TODO [pendiente columnas reales] — slug/código del proyecto
    "nivel": None,     # TODO [pendiente columnas reales] — capítulo / WBS (None por fila => 'TOTAL')
    "periodo": None,   # TODO [pendiente columnas reales] — mes/fecha del dato
    "pv": None,        # TODO [pendiente columnas reales] — valor planeado (Planned Value)
    "ev": None,        # TODO [pendiente columnas reales] — valor ganado (Earned Value)
    "ac": None,        # TODO [pendiente columnas reales] — costo real (Actual Cost)
    "bac": None,       # TODO [pendiente columnas reales] — presupuesto total (opcional)
    "corte": None,     # TODO [pendiente columnas reales] — fecha de corte de la extracción (opcional)
}

_OBLIGATORIOS = ("proyecto", "nivel", "periodo", "pv", "ev", "ac")


@dataclass(frozen=True)
class ActualObra:
    """Un registro de actuals agregado, listo para `actuals_obra` (migración 0004)."""
    proyecto: str
    nivel: str
    periodo: date          # día 1 del mes
    pv: float
    ev: float
    ac: float
    bac: float | None = None
    corte: date | None = None
    source: str = "sinco"

    def as_record(self) -> dict:
        """Dict con las columnas de la tabla `actuals_obra` (para el upsert del Paso 2)."""
        return {
            "proyecto": self.proyecto, "nivel": self.nivel,
            "periodo": self.periodo.isoformat(),
            "pv": self.pv, "ev": self.ev, "ac": self.ac,
            "bac": self.bac,
            "corte": self.corte.isoformat() if self.corte else None,
            "source": self.source,
        }


# --------------------------------------------------------------------------------------------------
# Conexión en vivo (solo se usa en producción; en tests se inyecta una conexión falsa).
# --------------------------------------------------------------------------------------------------
def _config() -> dict:
    """Lee y valida la config desde el entorno. Falla en voz alta si falta alguna variable."""
    cfg = {
        "server": os.environ.get(ENV_SERVER),
        "database": os.environ.get(ENV_DB),
        "user": os.environ.get(ENV_USER),
        "password": os.environ.get(ENV_PASSWORD),
    }
    faltan = [env for env, key in
              ((ENV_SERVER, "server"), (ENV_DB, "database"), (ENV_USER, "user"), (ENV_PASSWORD, "password"))
              if not cfg[key]]
    if faltan:
        raise RuntimeError(
            "Config SINCO incompleta: faltan " + ", ".join(faltan) +
            ". Defínelas por entorno (ver .env.example). Jamás en código.")
    return cfg


def _import_pymssql():  # pragma: no cover - requiere el driver instalado
    """Import PEREZOSO del driver SQL Server. Aislado para no exigir `pymssql` en CI/tests."""
    try:
        import pymssql
    except ImportError as e:
        raise RuntimeError(
            "Falta el driver 'pymssql'. Instálalo con:  pip install 'aleph-api[sinco]'  (o  pip install pymssql).") from e
    return pymssql


def conectar(*, timeout: int = 15):  # pragma: no cover - conexión real, se mockea en tests
    """Abre una conexión de SOLO LECTURA al DATAMART de SINCO. Solo en vivo (en tests se inyecta un fake)."""
    cfg = _config()
    pymssql = _import_pymssql()
    server, port = cfg["server"], None
    if "," in server:                      # 'host,puerto' (estilo SQL Server) -> host + port para pymssql
        server, _, p = server.partition(",")
        port = (p.strip() or None)
    return pymssql.connect(
        server=server.strip(), port=port, user=cfg["user"], password=cfg["password"],
        database=cfg["database"], login_timeout=timeout, timeout=timeout, as_dict=True)


def leer_control_proyecto(conn=None, *, limit: int | None = None) -> list[dict]:
    """Ejecuta un `SELECT [TOP n] * FROM ADP_DTM_VFACT.ControlProyecto` (solo lectura) y devuelve filas
    (lista de dicts). `conn` es INYECTABLE: en tests se pasa una conexión falsa; en vivo (conn=None) se
    abre y cierra una propia. No muta nada: solo SELECT."""
    propia = conn is None
    if propia:
        conn = conectar()
    try:
        top = f"TOP {int(limit)} " if limit else ""
        sql = f"SELECT {top}* FROM {VIEW_CONTROL_PROYECTO}"  # noqa: S608 - sin entrada de usuario; `limit` es int
        cur = conn.cursor(as_dict=True)
        cur.execute(sql)
        return list(cur.fetchall())
    finally:
        if propia:
            conn.close()


# --------------------------------------------------------------------------------------------------
# Transformación SINCO -> actuals (pura, testeable sin red). Es el corazón del Paso 1.
# --------------------------------------------------------------------------------------------------
def _validar_mapeo(mapeo: dict) -> None:
    """El mapeo debe tener columnas REALES en los campos obligatorios. Si siguen en `# TODO` (None),
    falla en voz alta antes de producir datos basura."""
    sin_definir = [k for k in _OBLIGATORIOS if not mapeo.get(k)]
    if sin_definir:
        raise RuntimeError(
            "MAPEO_CONTROL_PROYECTO sin definir para: " + ", ".join(sin_definir) +
            ". Llénalo con las columnas reales de ControlProyecto (Paso 2) antes de usar to_actuals en vivo.")


def _num(v) -> float:
    """Numérico defensivo: None/'' -> 0.0; soporta coma decimal ('1.234,56'-> mejor pasar limpio)."""
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def _fecha(v) -> date | None:
    """date/datetime/'YYYY-MM-DD'... -> date; None si no se puede."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return parse_fecha_iso(v)


def _mes(v) -> date | None:
    """Normaliza al día 1 del mes (clave de periodo). None si no parsea."""
    d = _fecha(v)
    return date(d.year, d.month, 1) if d else None


def _txt(v) -> str:
    return ("" if v is None else str(v)).strip()


def to_actuals(filas, mapeo: dict = MAPEO_CONTROL_PROYECTO, *, source: str = "sinco") -> list[ActualObra]:
    """Transforma filas crudas de ControlProyecto en `ActualObra`, AGREGANDO (roll-up) PV/EV/AC/BAC por
    (proyecto, nivel, periodo). Asume que las filas crudas son sub-ítems que suman al nivel pedido; por eso
    PV/EV/AC **y BAC** se SUMAN dentro de cada clave. `corte` toma la fecha de extracción más reciente del
    grupo. Filas sin proyecto o sin periodo válido se ignoran. No toca la red: opera sobre `filas` ya leídas."""
    _validar_mapeo(mapeo)
    c_bac, c_corte = mapeo.get("bac"), mapeo.get("corte")
    grupos: dict[tuple, dict] = {}
    orden: list[tuple] = []
    for fila in filas:
        proyecto = _txt(fila.get(mapeo["proyecto"]))
        nivel = _txt(fila.get(mapeo["nivel"])) or "TOTAL"
        periodo = _mes(fila.get(mapeo["periodo"]))
        if not proyecto or periodo is None:
            continue  # sin clave mínima -> se descarta
        key = (proyecto, nivel, periodo)
        g = grupos.get(key)
        if g is None:
            g = {"pv": 0.0, "ev": 0.0, "ac": 0.0, "bac": None, "corte": None}
            grupos[key] = g
            orden.append(key)
        g["pv"] += _num(fila.get(mapeo["pv"]))
        g["ev"] += _num(fila.get(mapeo["ev"]))
        g["ac"] += _num(fila.get(mapeo["ac"]))
        if c_bac:
            raw = fila.get(c_bac)
            if raw not in (None, ""):
                g["bac"] = (g["bac"] or 0.0) + _num(raw)
        if c_corte:
            c = _fecha(fila.get(c_corte))
            if c and (g["corte"] is None or c > g["corte"]):
                g["corte"] = c
    return [
        ActualObra(proyecto=p, nivel=n, periodo=per, pv=g["pv"], ev=g["ev"], ac=g["ac"],
                   bac=g["bac"], corte=g["corte"], source=source)
        for (p, n, per) in orden
        for g in (grupos[(p, n, per)],)
    ]


def _smoke():  # pragma: no cover - smoke manual en vivo (NO en CI); requiere credenciales + driver
    """SELECT TOP 5 contra ControlProyecto: verifica firewall/usuario e IMPRIME los nombres de columna
    reales (para llenar MAPEO_CONTROL_PROYECTO en el Paso 2). Lo corre Martín local, no el CI:
        python -m aleph_api.conectores.sinco
    """
    print(f"[sinco] conectando a {os.environ.get(ENV_SERVER)} / {os.environ.get(ENV_DB)} ...")
    try:
        filas = leer_control_proyecto(limit=5)
    except Exception as e:  # noqa: BLE001
        print(f"   error: {type(e).__name__}: {e}")
        return
    print(f"   OK — {len(filas)} filas leídas de {VIEW_CONTROL_PROYECTO}")
    if filas:
        print("   columnas:", list(filas[0].keys()))
        for f in filas:
            print("  ", f)


if __name__ == "__main__":  # pragma: no cover
    _smoke()
