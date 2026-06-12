# -*- coding: utf-8 -*-
"""Auth de la API: validación de JWT de Microsoft Entra ID (Fase 4c).

Sigue la guía oficial (learn.microsoft.com/entra/identity-platform/access-tokens#validate-tokens):
valida **firma** (RS256, clave por `kid` desde el JWKS del tenant), **issuer**, **audience**, **tid**
(tenant, defensa cross-tenant) y **exp/nbf**, usando **PyJWT** (librería establecida; no se hace la
cripto a mano). El JWKS se descarga y cachea vía `PyJWKClient`.

**Config-driven con fail-closed:** la auth se ACTIVA si hay `ENTRA_TENANT_ID` + `API_AUDIENCE`. Sin
ellas la API quedaría abierta — útil en dev/CI — PERO si `ALEPH_AUTH_REQUIRED=true` (lo que debe
ponerse en PRODUCCIÓN) y la auth NO está configurada, las rutas protegidas devuelven **503** en vez de
abrirse (fail-closed): un despliegue mal configurado falla ruidoso, no silenciosamente abierto.

Variables de entorno:
  ENTRA_TENANT_ID     GUID del tenant de Entra (el mismo del App Service actual).
  API_AUDIENCE        audiencia del token = App ID URI o client-id del registro de app de la API.
  ALEPH_AUTH_REQUIRED "true" en PRODUCCIÓN → exige que la auth esté configurada (fail-closed).
  ENTRA_ISSUER        (opcional) override del issuer; por defecto v2: …/{tenant}/v2.0.
  ALEPH_ADMINS        (opcional) correos admin separados por coma.
  ALEPH_ALLOWED_AZP   (opcional) client-ids autorizados a llamar la API (claim azp/appid).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

log = logging.getLogger("aleph_api.auth")


@dataclass
class Principal:
    sub: str | None = None
    oid: str | None = None          # Azure AD object id (auditoría/correlación de logs)
    email: str | None = None
    name: str | None = None
    roles: list[str] = field(default_factory=list)
    is_admin: bool = False
    autenticado: bool = True


# ---------- configuración (se lee del entorno en cada llamada → fácil de testear) ----------

def _tenant() -> str:
    return os.environ.get("ENTRA_TENANT_ID", "").strip()


def _audience() -> str:
    return os.environ.get("API_AUDIENCE", "").strip()


def auth_enabled() -> bool:
    """True solo si el tenant y la audiencia están configurados."""
    return bool(_tenant() and _audience())


def auth_required() -> bool:
    """True si se EXIGE auth (producción): un despliegue sin auth configurada debe fallar, no abrirse."""
    return os.environ.get("ALEPH_AUTH_REQUIRED", "").strip().lower() in ("1", "true", "yes", "si", "sí")


def _issuer() -> str:
    t = _tenant()
    if not t:
        raise RuntimeError("ENTRA_TENANT_ID requerido para construir el issuer")
    return os.environ.get("ENTRA_ISSUER", "").strip() or f"https://login.microsoftonline.com/{t}/v2.0"


def _jwks_uri() -> str:
    t = _tenant()
    if not t:
        raise RuntimeError("ENTRA_TENANT_ID requerido para el JWKS")
    return f"https://login.microsoftonline.com/{t}/discovery/v2.0/keys"


def _admins() -> set[str]:
    return {e.strip().lower() for e in os.environ.get("ALEPH_ADMINS", "").split(",") if e.strip()}


def _allowed_azp() -> set[str]:
    return {a.strip() for a in os.environ.get("ALEPH_ALLOWED_AZP", "").split(",") if a.strip()}


# ---------- validación del token ----------

_jwk_client = None


def _signing_key(token: str):
    """Clave pública de firma para el token (por `kid`), desde el JWKS del tenant (cacheado).
    Aislada en una función para poder inyectar una clave de prueba en los tests."""
    global _jwk_client
    import jwt
    if _jwk_client is None:
        _jwk_client = jwt.PyJWKClient(_jwks_uri())
    return _jwk_client.get_signing_key_from_jwt(token).key


def validate_token(token: str) -> dict:
    """Valida un JWT de Entra ID y devuelve sus claims. Lanza `jwt.PyJWTError` si no es válido.

    Seguridad: SOLO RS256 (no se toma el `alg` del header → evita alg-confusion/none); exige `aud`,
    `iss`, `exp`; valida `tid == tenant` (defensa cross-tenant); valida `azp`/`appid` contra la lista
    permitida si está configurada; tolerancia de reloj acotada (30 s)."""
    import jwt
    key = _signing_key(token)
    claims = jwt.decode(
        token, key,
        algorithms=["RS256"],
        audience=_audience(),
        issuer=_issuer(),
        leeway=30,
        options={"require": ["exp", "iss", "aud"], "verify_signature": True},
    )
    # Defensa en profundidad: el tenant del token debe ser EXACTAMENTE el nuestro.
    if claims.get("tid") != _tenant():
        raise jwt.InvalidIssuerError("tid (tenant) del token no coincide con ENTRA_TENANT_ID")
    # Opcional: solo apps cliente autorizadas (si se configura ALEPH_ALLOWED_AZP).
    permitidos = _allowed_azp()
    if permitidos:
        azp = claims.get("azp") or claims.get("appid")
        if azp not in permitidos:
            raise jwt.InvalidTokenError("azp/appid no autorizado para llamar esta API")
    return claims


def principal_de_claims(claims: dict) -> Principal:
    """Construye el Principal desde los claims. admin si trae rol 'admin' o si el correo está en ALEPH_ADMINS."""
    email = (claims.get("preferred_username") or claims.get("email") or claims.get("upn") or "").lower() or None
    roles = list(claims.get("roles") or [])
    is_admin = any(r.lower() == "admin" for r in roles) or (email is not None and email in _admins())
    return Principal(sub=claims.get("sub"), oid=claims.get("oid"), email=email,
                     name=claims.get("name"), roles=roles, is_admin=is_admin)


# ---------- dependencias FastAPI ----------

_bearer = HTTPBearer(auto_error=False)


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    """Usuario autenticado. Fail-closed: si se exige auth (`ALEPH_AUTH_REQUIRED`) y NO está configurada,
    devuelve 503 en vez de abrir. En dev/CI (sin exigir auth) devuelve un principal de desarrollo."""
    if not auth_enabled():
        if auth_required():
            log.error("ALEPH_AUTH_REQUIRED=true pero falta ENTRA_TENANT_ID/API_AUDIENCE → 503 (fail-closed)")
            raise HTTPException(status_code=503, detail="Auth requerida pero no configurada en el servidor")
        log.warning("AUTH DESHABILITADA (sin ENTRA_TENANT_ID/API_AUDIENCE): API abierta — solo dev/CI")
        return Principal(sub="dev", name="dev", roles=["admin"], is_admin=True, autenticado=False)
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=401, detail="Falta el token Bearer de Entra ID")
    import jwt
    try:
        claims = validate_token(cred.credentials)
    except jwt.PyJWTError as e:
        log.info("Rechazo de token: %s", e.__class__.__name__)        # detalle solo en logs, no al cliente
        raise HTTPException(status_code=401, detail="Token de autenticación inválido o mal formado") from e
    return principal_de_claims(claims)


def require_admin(user: Principal = Depends(current_user)) -> Principal:
    """Exige rol admin (para endpoints de escritura, que llegan en fases posteriores).
    En producción la protección real la da `ALEPH_AUTH_REQUIRED` (current_user ya hace fail-closed)."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Requiere rol admin")
    return user
