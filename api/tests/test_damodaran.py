# -*- coding: utf-8 -*-
"""M6.4 (spec_pyg_dinamico.md) — parser HTML de Damodaran (CRP/ERP por país): defensivo, sin red.

Incluye la FILA REAL de Colombia observada en vivo, para bloquear el mapeo posicional.
"""
from aleph_api.conectores import damodaran

# Réplica de la estructura real: una fila basura (link al paper) + la fila real de Colombia (8 celdas).
HTML_REAL = """<html><body><table>
<tr><td>My paper on equity risk premiums:</td><td></td><td></td><td>https://papers.ssrn.com/x</td></tr>
<tr><td>Colombia</td><td>Baa3</td><td>1.87%</td><td>2.85%</td><td>7.08%</td><td>35.00%</td><td>3.20%</td><td>9.09%</td></tr>
</table></body></html>"""

# Con cabecera limpia (mapeo por nombre).
HTML_HDR = """<html><body><table>
<tr><th>Country</th><th>Moody's rating</th><th>Adj. Default Spread</th><th>Country Risk Premium</th><th>Total Equity Risk Premium</th><th>Tax</th></tr>
<tr><td>Colombia</td><td>Baa3</td><td>1.87%</td><td>2.85%</td><td>7.08%</td><td>35.00%</td></tr>
</table></body></html>"""


def test_parse_fila_real_posicional():
    d = damodaran.parse_html(HTML_REAL, "Colombia")
    assert d is not None
    assert abs(d["crp"] - 0.0285) < 1e-9       # 2.85% = CRP
    assert abs(d["erp_total"] - 0.0708) < 1e-9  # 7.08% = Total ERP


def test_parse_por_cabecera():
    d = damodaran.parse_html(HTML_HDR, "Colombia")
    assert abs(d["crp"] - 0.0285) < 1e-9 and abs(d["erp_total"] - 0.0708) < 1e-9


def test_parse_pais_inexistente_es_none():
    assert damodaran.parse_html(HTML_REAL, "Narnia") is None


def test_fetch_damodaran_con_get_inyectado():
    vals = {v.clave: v for v in damodaran.fetch_damodaran("Colombia", get=lambda url, **k: HTML_REAL)}
    assert abs(vals["damodaran:crp:colombia"].valor - 0.0285) < 1e-9
    assert abs(vals["damodaran:erp_total:colombia"].valor - 0.0708) < 1e-9
    assert vals["damodaran:crp:colombia"].unidad == "ratio"


def test_pct_helper():
    assert abs(damodaran._pct("3,14 %") - 0.0314) < 1e-9
    assert damodaran._pct("sin pct") is None
