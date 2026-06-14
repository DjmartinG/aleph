# -*- coding: utf-8 -*-
"""M6.5 (spec_pyg_dinamico.md) — persistencia de supuestos macro con compuerta de revisión.

Cliente Supabase FALSO en memoria: prueba que refrescar PROPONE (no aplica) y que aprobar sube a
vigente garantizando uno por clave. Sin red ni Supabase real.
"""
from datetime import date

from aleph_api import macro_store
from aleph_api.conectores.base import ValorMacro


class _Res:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, sb):
        self.sb = sb
        self._op = self._payload = self._order = self._limit = None
        self._filters = []

    def insert(self, d):
        self._op, self._payload = "insert", d
        return self

    def select(self, *a):
        self._op = "select"
        return self

    def update(self, d):
        self._op, self._payload = "update", d
        return self

    def eq(self, k, v):
        self._filters.append((k, v))
        return self

    def order(self, k, desc=False):
        self._order = (k, desc)
        return self

    def limit(self, n):
        self._limit = n
        return self

    def execute(self):
        rows = [r for r in self.sb.rows if all(r.get(k) == v for k, v in self._filters)]
        if self._op == "insert":
            self.sb._id += 1
            row = dict(self._payload, id=self.sb._id, created_at=self.sb._id)
            self.sb.rows.append(row)
            return _Res([row])
        if self._op == "update":
            for r in rows:
                r.update(self._payload)
            return _Res(rows)
        if self._order:
            k, desc = self._order
            rows = sorted(rows, key=lambda r: r.get(k, 0), reverse=desc)
        if self._limit:
            rows = rows[: self._limit]
        return _Res(rows)


class FakeSB:
    def __init__(self):
        self.rows = []
        self._id = 0

    def table(self, name):
        return _Table(self)


VALS = [
    ValorMacro("damodaran:crp:colombia", "CRP Colombia", 0.0285, "ratio", "Damodaran"),
    ValorMacro("banrep:trm", "TRM", 4125.0, "COP", "Banrep", fecha=date(2026, 5, 22)),
]


def test_refrescar_propone_pero_no_aplica():
    sb = FakeSB()
    res = macro_store.refrescar(sb=sb, recolectar=lambda: VALS)
    assert res["propuestos"] == 2 and res["recolectados"] == 2
    # nada vigente todavía (compuerta cerrada)
    assert macro_store.listar_vigentes(sb=sb) == []
    assert len(macro_store.pendientes(sb=sb)) == 2


def test_aprobar_sube_a_vigente():
    sb = FakeSB()
    macro_store.refrescar(sb=sb, recolectar=lambda: VALS)
    out = macro_store.aprobar(["banrep:trm"], sb=sb)
    assert out["aprobadas"] == ["banrep:trm"]
    vig = macro_store.listar_vigentes(sb=sb)
    assert len(vig) == 1 and vig[0]["clave"] == "banrep:trm" and vig[0]["valor"] == 4125.0
    # la otra sigue pendiente
    assert any(r["clave"] == "damodaran:crp:colombia" for r in macro_store.pendientes(sb=sb))


def test_aprobar_reemplaza_vigente_anterior():
    sb = FakeSB()
    # vigente viejo
    macro_store.refrescar(sb=sb, recolectar=lambda: [ValorMacro("banrep:trm", "TRM", 4000.0, "COP", "Banrep")])
    macro_store.aprobar(["banrep:trm"], sb=sb)
    # nueva propuesta + aprobar
    macro_store.refrescar(sb=sb, recolectar=lambda: [ValorMacro("banrep:trm", "TRM", 4200.0, "COP", "Banrep")])
    macro_store.aprobar(["banrep:trm"], sb=sb)
    vig = macro_store.listar_vigentes(sb=sb)
    assert len(vig) == 1 and vig[0]["valor"] == 4200.0  # un solo vigente, el nuevo


def test_proponer_marca_por_validar_y_no_vigente():
    sb = FakeSB()
    macro_store.proponer(VALS, sb=sb)
    for r in sb.rows:
        assert r["vigente"] is False and r["estado_validacion"] == "por_validar"
