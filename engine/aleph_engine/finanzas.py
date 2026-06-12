# -*- coding: utf-8 -*-
"""Utilidades financieras del motor — fuente ÚNICA de TIR, VPN y WACC.

Centraliza el cálculo que antes estaba DUPLICADO en `modelo.py` (tir, calcular_wacc) y en
`apalancamiento.py` (_tir, _tir_periodo, _vpn). No importa ningún otro módulo del motor, así
que rompe el ciclo de importación modelo↔apalancamiento.

Misma matemática que antes (verificado por las anclas auditadas y por test_finanzas.py):
  - irr_periodo: escaneo de cambio de signo + brentq (la TIR por periodo, requiere scipy).
  - irr_anual:   anualiza una TIR mensual → (1+TIR_mensual)^12 − 1.
  - irr_biseccion: TIR por bisección robusta (para la serie anual auditada de fiducia).
  - vpn:         valor presente neto a una tasa de periodo.
  - calcular_wacc: build-up CAPM de mercado emergente (Damodaran/CESLA, hoja k.beta).
"""
try:
    from scipy import optimize
    _SCIPY = True
except Exception:
    _SCIPY = False


def vpn(flujos, r):
    """Valor presente neto de una serie a la tasa de periodo `r`."""
    return sum(f / (1 + r) ** t for t, f in enumerate(flujos))


def irr_periodo(flujos):
    """TIR POR PERIODO: escaneo de cambio de signo desde −0.6 + brentq (xtol=1e-10).
    Requiere scipy (si falta → None). Devuelve la tasa por periodo de la serie (mensual si la
    serie es mensual). None si no se encuentra cambio de signo."""
    if not _SCIPY:
        return None
    r = -0.6
    prev = vpn(flujos, r)
    while r < 5.0:
        r2 = r + 0.005
        cur = vpn(flujos, r2)
        if prev * cur < 0:
            try:
                return optimize.brentq(lambda x: vpn(flujos, x), r, r2, xtol=1e-10)
            except Exception:
                pass
        prev = cur
        r = r2
    return None


def irr_anual(flujos):
    """TIR ANUAL a partir de una serie MENSUAL: (1 + TIR_mensual)^12 − 1. None si no converge."""
    m = irr_periodo(flujos)
    return ((1 + m) ** 12 - 1) if m is not None else None


def irr_biseccion(flujos):
    """TIR POR PERIODO por BISECCIÓN robusta. La serie ya viene en su periodicidad (p.ej. anual),
    así que devuelve esa tasa directamente. Se usa para la serie anual auditada de fiducia.
    None si no hay cambio de signo en [−0.95, 5.0]."""
    lo, hi = -0.95, 5.0
    if vpn(flujos, lo) * vpn(flujos, hi) > 0:
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        if vpn(flujos, lo) * vpn(flujos, mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def irr_anual_biseccion(flujos):
    """TIR ANUAL desde una serie MENSUAL por BISECCIÓN robusta + escaneo de cambio de signo:
    `(1 + TIR_mensual)^12 − 1`. None si no encuentra cambio de signo.

    Variante usada por el CONSOLIDADO de portafolio para la TIR equity. Es DISTINTA de `irr_anual`
    (que usa brentq): se conserva tal cual (extraída de la app) porque produce el valor exacto que ya
    mostraba el portafolio, y esa cifra no está cubierta por el snapshot dorado (que es por-proyecto)."""
    def _vpn(r):
        return sum(f / (1 + r) ** t for t, f in enumerate(flujos))
    lo, hi = -0.95, 5.0
    flo, fhi = _vpn(lo), _vpn(hi)
    if flo * fhi > 0:                                  # buscar un sub-intervalo con cambio de signo
        r = lo
        prev = flo
        found = False
        while r < hi:
            r2 = r + 0.01
            cur = _vpn(r2)
            if prev * cur < 0:
                lo, hi, flo = r, r2, prev
                found = True
                break
            prev = cur
            r = r2
        if not found:
            return None
    for _ in range(200):
        mid = (lo + hi) / 2
        fm = _vpn(mid)
        if flo * fm <= 0:
            hi = mid
        else:
            lo = mid
            flo = fm
    m = (lo + hi) / 2
    try:
        return (1 + m) ** 12 - 1
    except Exception:
        return None


def calcular_wacc(p, detalle=False):
    """WACC en COP por el build-up CAPM de mercado emergente (metodología Damodaran/CESLA, auditada CG).

    Cadena: beta de la deuda → desapalancar beta US (CON beta de deuda) → reapalancar a la estructura
    de Colombia → Ke USD → + riesgo país (EMBI) → paridad de inflación a COP → Kd COP (compuesto) →
    WACC = E·Ke$COP + D·Kd·(1−t). Reproduce la hoja k.beta (WACC Navarra = 21,54%).

    `detalle=True` devuelve todos los eslabones intermedios (para la sección Costo de Capital).
    """
    rf = p["rf"]/100; rm = p["rm"]/100; pm = rm - rf                  # prima de mercado = Rm − Rf
    # --- beta de la deuda del comparable US: βd = (kd_us − rf) / (Rm − Rf) ---
    kd_us = p.get("kd_us", 9.335)/100
    beta_d = (kd_us - rf)/pm if pm else 0.0
    # --- desapalancar beta US CON beta de deuda (no Hamada simple) ---
    de_us = p["de_us"]/100; t_us = p["tax_us"]/100
    E_us = 1.0/(1.0+de_us); D_us = 1.0 - E_us                         # de_us = D/E
    den_u = E_us + D_us*(1-t_us)
    beta_u = (E_us/den_u)*p["beta_us"] + (D_us*(1-t_us)/den_u)*beta_d
    # --- reapalancar a la estructura de Colombia CON beta de deuda ---
    de_col = p["de_col"]/100; t_col = p["tax_col"]/100
    beta_l = beta_u + (beta_u - beta_d)*(1-t_col)*de_col
    # --- costo de recursos propios en USD + riesgo país (EMBI) ---
    ke_usd = rf + beta_l*pm
    ke_usd_rp = ke_usd + p["rp"]/100
    # --- pasar a COP por paridad de inflación de largo plazo (RPLP/DPLP) ---
    rplp = (1+p["inf_col"]/100)/(1+p["inf_us"]/100) - 1
    ke_cop = (1+ke_usd_rp)*(1+rplp) - 1
    # --- costo de la deuda en Colombia (COMPUESTO, no aditivo) ---
    kd_cop = (1+p["tasa_d"]/100)*(1+p["spread"]/100) - 1
    # --- WACC ---
    we = p["eq_w"]/100; wd = 1.0 - we
    wacc = we*ke_cop + wd*kd_cop*(1-t_col)
    if detalle:
        return {"pm":pm, "beta_d":beta_d, "beta_u":beta_u, "beta_l":beta_l,
                "ke_usd":ke_usd, "rp":p["rp"]/100, "ke_usd_rp":ke_usd_rp, "rplp":rplp,
                "ke_cop":ke_cop, "kd_cop":kd_cop, "we":we, "wd":wd, "t_col":t_col, "wacc":wacc,
                "E_us":E_us, "D_us":D_us}
    return wacc
