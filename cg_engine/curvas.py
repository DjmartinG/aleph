# -*- coding: utf-8 -*-
"""Motor de curvas de distribución (PERT/Normal/Triangular/Lineal). Fuente única de verdad."""
import math

def _norm(ws):
    s = sum(ws)
    return [w/s for w in ws] if s else ws

def pert(n, moda=None, lam=4.0):
    a, b = 0.0, float(n)
    m = moda if moda else n*0.55
    m = min(max(m, a+1e-6), b-1e-6)
    alpha = 1 + lam*(m-a)/(b-a)
    beta  = 1 + lam*(b-m)/(b-a)
    return _norm([((i+0.5)/n)**(alpha-1) * (1-(i+0.5)/n)**(beta-1) for i in range(n)])

def normal(n, media=None, sigma=None):
    mu = media if media else n/2.0
    sg = sigma if sigma else n/4.0
    return _norm([math.exp(-0.5*((i+0.5-mu)/sg)**2) for i in range(n)])

def triangular(n, moda=None):
    m = moda if moda else n*0.5
    out=[]
    for i in range(n):
        x=i+0.5
        out.append(x/m if x<=m else ((n-x)/(n-m) if n>m else 0))
    return _norm([max(w,0) for w in out])

def lineal(n):
    return [1.0/n]*n

def gauss(n, moda=None):
    """Curva de avance de obra (k.Directo): Normal centrada en el punto medio
    de la duración, con desviación = STDEV de 1..n y residuo normalizador (suma = 1)."""
    if n <= 1:
        return [1.0] * max(1, n)
    mu = (n + 1) / 2.0
    var = sum((i - mu) ** 2 for i in range(1, n + 1)) / (n - 1)
    sg = math.sqrt(var) or 1.0
    pdf = [math.exp(-0.5 * ((i - mu) / sg) ** 2) / (sg * math.sqrt(2 * math.pi)) for i in range(1, n + 1)]
    resid = (1 - sum(pdf)) / n
    return _norm([p + resid for p in pdf])

CURVAS = {"PERT":pert, "Normal":normal, "Triangular":triangular, "Lineal":lineal, "Gauss":gauss}

def distribuir(total, n, tipo="PERT", moda=None):
    fn = CURVAS.get(tipo, pert)
    pesos = fn(n, moda) if tipo in ("PERT","Triangular") and moda else fn(n)
    return [total*w for w in pesos]

def escalar_mat_mo(serie, rel_mat=0.8, ea_mat=0.06, ea_mo=0.12, ppa=12):
    out=[]
    for t,base in enumerate(serie):
        out.append(base*rel_mat*(1+ea_mat)**(t/ppa) + base*(1-rel_mat)*(1+ea_mo)**(t/ppa))
    return out
