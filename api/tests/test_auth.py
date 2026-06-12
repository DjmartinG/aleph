# -*- coding: utf-8 -*-
"""Tests de la validación de JWT de Entra ID (`aleph_api.auth`).

Se firma con una clave RSA de PRUEBA (no se contacta a Entra) y se inyecta la clave pública vía
`_signing_key`. Cubre los pilares de seguridad: firma, audiencia, issuer, expiración, y rechazo de
alg-confusion (HS256). Más la extracción de roles y la dependencia `current_user`.
"""
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from aleph_api import auth

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUB = _KEY.public_key()
ISS = "https://test-issuer/v2.0"
AUD = "api://aleph-test"


TENANT = "test-tenant"


def _token(claims=None, alg="RS256", key=None, **over):
    base = {"sub": "u1", "aud": AUD, "iss": ISS, "tid": TENANT, "exp": int(time.time()) + 3600,
            "name": "Tester", "preferred_username": "tester@cg.com"}
    base.update(over)
    if claims:
        base.update(claims)
    return jwt.encode(base, key or _KEY, algorithm=alg)


@pytest.fixture
def cfg(monkeypatch):
    """Activa la auth con valores de prueba + inyecta la clave pública (sin tocar Entra)."""
    monkeypatch.setenv("ENTRA_TENANT_ID", TENANT)
    monkeypatch.setenv("API_AUDIENCE", AUD)
    monkeypatch.setenv("ENTRA_ISSUER", ISS)
    monkeypatch.setattr(auth, "_signing_key", lambda token: _PUB)
    assert auth.auth_enabled()


def test_token_valido(cfg):
    claims = auth.validate_token(_token())
    assert claims["sub"] == "u1" and claims["aud"] == AUD


def test_expirado(cfg):
    # Expirado MÁS allá de la tolerancia de reloj (leeway 60 s).
    with pytest.raises(jwt.ExpiredSignatureError):
        auth.validate_token(_token(exp=int(time.time()) - 120))


def test_audiencia_incorrecta(cfg):
    with pytest.raises(jwt.InvalidAudienceError):
        auth.validate_token(_token(aud="api://otra"))


def test_issuer_incorrecto(cfg):
    with pytest.raises(jwt.InvalidIssuerError):
        auth.validate_token(_token(iss="https://malicioso/v2.0"))


def test_tid_de_otro_tenant_rechazado(cfg):
    # Firma/aud/iss correctos pero tenant distinto → rechazado (defensa cross-tenant).
    with pytest.raises(jwt.InvalidIssuerError):
        auth.validate_token(_token(tid="otro-tenant-9999"))


def test_azp_no_autorizado(cfg, monkeypatch):
    monkeypatch.setenv("ALEPH_ALLOWED_AZP", "cliente-bueno")
    auth.validate_token(_token(azp="cliente-bueno"))                       # autorizado pasa
    with pytest.raises(jwt.InvalidTokenError):
        auth.validate_token(_token(azp="cliente-malo"))                    # no autorizado falla


def test_rechaza_alg_confusion_hs256(cfg):
    # Token firmado con HS256 (secreto) debe ser RECHAZADO: solo se acepta RS256.
    hs = jwt.encode({"sub": "u1", "aud": AUD, "iss": ISS, "exp": int(time.time()) + 3600}, "secreto", algorithm="HS256")
    with pytest.raises(jwt.InvalidAlgorithmError):
        auth.validate_token(hs)


def test_firma_invalida_otra_llave(cfg):
    otra = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(jwt.InvalidSignatureError):
        auth.validate_token(_token(key=otra))


def test_principal_roles_y_admins(monkeypatch):
    monkeypatch.setenv("ALEPH_ADMINS", "jefe@cg.com, otro@cg.com")
    # admin por claim de rol
    p = auth.principal_de_claims({"sub": "x", "roles": ["Admin"], "preferred_username": "a@cg.com"})
    assert p.is_admin and "Admin" in p.roles
    # admin por correo en la lista
    p2 = auth.principal_de_claims({"sub": "y", "preferred_username": "JEFE@cg.com"})
    assert p2.is_admin and p2.email == "jefe@cg.com"
    # usuario normal (gerencia)
    p3 = auth.principal_de_claims({"sub": "z", "preferred_username": "nadie@cg.com"})
    assert not p3.is_admin


def test_current_user_abierto_en_dev():
    # Sin ENTRA_TENANT_ID/API_AUDIENCE la auth está deshabilitada → principal de desarrollo.
    assert not auth.auth_enabled()
    u = auth.current_user(cred=None)
    assert u.is_admin and u.autenticado is False


def test_fail_closed_si_se_exige_auth(monkeypatch):
    # PRODUCCIÓN: ALEPH_AUTH_REQUIRED=true pero falta la config → 503, NO se abre.
    monkeypatch.delenv("ENTRA_TENANT_ID", raising=False)
    monkeypatch.delenv("API_AUDIENCE", raising=False)
    monkeypatch.setenv("ALEPH_AUTH_REQUIRED", "true")
    assert not auth.auth_enabled() and auth.auth_required()
    with pytest.raises(HTTPException) as e:
        auth.current_user(cred=None)
    assert e.value.status_code == 503


def test_current_user_exige_token(cfg):
    with pytest.raises(HTTPException) as e:
        auth.current_user(cred=None)
    assert e.value.status_code == 401


def test_current_user_valido(cfg):
    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials=_token())
    u = auth.current_user(cred=cred)
    assert u.sub == "u1" and u.autenticado is True
