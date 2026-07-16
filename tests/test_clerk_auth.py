"""Clerk JWT doğrulama testleri (P0 — billing ön koşulu).

Pytest gerektirmez — `python tests/test_clerk_auth.py`.
Gerçek ağ çağrısı yok: JWKS istemcisi sahte bir imza-anahtarı döndürecek şekilde
monkeypatch'lenir; RSA anahtar çifti test içinde üretilir.
"""
from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("GEMINI_API_KEY", "fake-key-for-tests")

import jwt  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import rsa  # noqa: E402

from app.config import settings  # noqa: E402
from app.services import clerk_auth  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")
    if not cond:
        _failures.append(msg)


# --- Test yardımcıları --------------------------------------------------------

_ISSUER = "https://clerk.test.example.com"
_PRIV = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUB = _PRIV.public_key()


class _FakeSigningKey:
    key = _PUB


class _FakeJWKSClient:
    """PyJWKClient yerine — kid'e bakmadan sabit public key döndürür."""

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:  # noqa: ARG002
        return _FakeSigningKey()


def _make_token(**overrides) -> str:
    now = _dt.datetime.now(_dt.timezone.utc)
    payload = {
        "sub": "user_123",
        "iss": _ISSUER,
        "iat": now,
        "exp": now + _dt.timedelta(hours=1),
    }
    payload.update(overrides)
    return jwt.encode(payload, _PRIV, algorithm="RS256")


def _enable_auth() -> None:
    settings.clerk_issuer = _ISSUER
    settings.clerk_jwks_url = ""  # issuer'dan türetilsin
    # Gerçek ağ çağrısını engelle: JWKS istemcisini sahtele.
    clerk_auth._jwks_client = _FakeJWKSClient()
    clerk_auth._jwks_client_url = settings.clerk_jwks_url_resolved


def _disable_auth() -> None:
    settings.clerk_issuer = ""
    settings.clerk_jwks_url = ""
    clerk_auth._jwks_client = None
    clerk_auth._jwks_client_url = ""


# --- 1. Config property'leri --------------------------------------------------

def test_config_props() -> None:
    print("test_config_props")
    _disable_auth()
    check(settings.clerk_auth_enabled is False, "issuer boşken auth kapalı")
    check(settings.clerk_jwks_url_resolved == "", "issuer boşken jwks url boş")

    settings.clerk_issuer = "https://clerk.foo.dev/"  # sondaki / temizlenmeli
    check(settings.clerk_auth_enabled is True, "issuer set → auth açık")
    check(
        settings.clerk_jwks_url_resolved
        == "https://clerk.foo.dev/.well-known/jwks.json",
        "jwks url issuer'dan türetildi (trailing slash temizlendi)",
    )

    settings.clerk_jwks_url = "https://custom/jwks"
    check(
        settings.clerk_jwks_url_resolved == "https://custom/jwks",
        "açık jwks override issuer'ı geçersiz kılar",
    )
    _disable_auth()


# --- 2. Bearer ayıklama -------------------------------------------------------

def test_extract_bearer() -> None:
    print("test_extract_bearer")
    check(clerk_auth._extract_bearer(None) is None, "None → None")
    check(clerk_auth._extract_bearer("") is None, "boş → None")
    check(clerk_auth._extract_bearer("Bearer abc") == "abc", "Bearer abc → abc")
    check(clerk_auth._extract_bearer("bearer abc") == "abc", "küçük harf bearer")
    check(clerk_auth._extract_bearer("Bearer ") is None, "boş token → None")
    check(clerk_auth._extract_bearer("Token abc") is None, "yanlış şema → None")
    check(clerk_auth._extract_bearer("abc") is None, "şemasız → None")


# --- 3. verify_token roundtrip + red senaryoları ------------------------------

def test_verify_token_valid() -> None:
    print("test_verify_token_valid")
    _enable_auth()
    claims = clerk_auth.verify_token(_make_token(sub="user_abc"))
    check(claims.get("sub") == "user_abc", "geçerli token → sub çözüldü")
    _disable_auth()


def test_verify_token_expired() -> None:
    print("test_verify_token_expired")
    _enable_auth()
    past = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=2)
    token = _make_token(exp=past, iat=past)
    try:
        clerk_auth.verify_token(token)
        check(False, "expired token reddedilmeli")
    except jwt.ExpiredSignatureError:
        check(True, "expired token → ExpiredSignatureError")
    except jwt.InvalidTokenError:
        check(True, "expired token → InvalidTokenError")
    _disable_auth()


def test_verify_token_wrong_issuer() -> None:
    print("test_verify_token_wrong_issuer")
    _enable_auth()
    token = _make_token(iss="https://evil.example.com")
    try:
        clerk_auth.verify_token(token)
        check(False, "yanlış issuer reddedilmeli")
    except jwt.InvalidIssuerError:
        check(True, "yanlış issuer → InvalidIssuerError")
    except jwt.InvalidTokenError:
        check(True, "yanlış issuer → InvalidTokenError")
    _disable_auth()


def test_verify_token_bad_signature() -> None:
    print("test_verify_token_bad_signature")
    _enable_auth()
    # Farklı bir anahtarla imzalanmış token — sahte JWKS bizim _PUB'ı döner → uyuşmaz.
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = _dt.datetime.now(_dt.timezone.utc)
    token = jwt.encode(
        {"sub": "x", "iss": _ISSUER, "exp": now + _dt.timedelta(hours=1)},
        other,
        algorithm="RS256",
    )
    try:
        clerk_auth.verify_token(token)
        check(False, "geçersiz imza reddedilmeli")
    except jwt.InvalidTokenError:
        check(True, "geçersiz imza → InvalidTokenError")
    _disable_auth()


def test_verify_token_missing_sub() -> None:
    print("test_verify_token_missing_sub")
    _enable_auth()
    now = _dt.datetime.now(_dt.timezone.utc)
    # sub olmadan imzala (require=['sub'] devreye girmeli)
    token = jwt.encode(
        {"iss": _ISSUER, "exp": now + _dt.timedelta(hours=1)}, _PRIV, algorithm="RS256"
    )
    try:
        clerk_auth.verify_token(token)
        check(False, "sub'suz token reddedilmeli")
    except jwt.MissingRequiredClaimError:
        check(True, "sub yok → MissingRequiredClaimError")
    except jwt.InvalidTokenError:
        check(True, "sub yok → InvalidTokenError")
    _disable_auth()


# --- 4. _verified_sub_or_none (lenient çekirdek) ------------------------------

def test_verified_sub_or_none() -> None:
    print("test_verified_sub_or_none")
    _disable_auth()
    check(
        clerk_auth._verified_sub_or_none("Bearer x") is None,
        "auth kapalı → None",
    )
    _enable_auth()
    check(clerk_auth._verified_sub_or_none(None) is None, "token yok → None")
    check(
        clerk_auth._verified_sub_or_none("Bearer garbage.token.here") is None,
        "geçersiz token → None (fırlatmaz)",
    )
    good = "Bearer " + _make_token(sub="user_ok")
    check(
        clerk_auth._verified_sub_or_none(good) == "user_ok",
        "geçerli token → sub",
    )
    _disable_auth()


# --- 5. require_verified_tenant_id (strict dependency) ------------------------

def test_require_strict() -> None:
    print("test_require_strict")
    from fastapi import HTTPException

    _disable_auth()
    try:
        clerk_auth.require_verified_tenant_id("Bearer x")
        check(False, "auth kapalıyken strict 503 vermeli")
    except HTTPException as e:
        check(e.status_code == 503, "auth kapalı → 503")

    _enable_auth()
    try:
        clerk_auth.require_verified_tenant_id(None)
        check(False, "token yokken strict 401 vermeli")
    except HTTPException as e:
        check(e.status_code == 401, "token yok → 401")

    tid = clerk_auth.require_verified_tenant_id("Bearer " + _make_token(sub="u9"))
    check(tid == "u9", "geçerli token → doğrulanmış tenant döner")
    _disable_auth()


# --- 6. resolve_tenant_id (spoof koruması) -----------------------------------

def test_resolve_tenant_id() -> None:
    print("test_resolve_tenant_id")
    # Auth kapalı → supplied'a düş (bugünkü davranış)
    _disable_auth()
    check(
        clerk_auth.resolve_tenant_id(None, "client_supplied") == "client_supplied",
        "auth kapalı + verified yok → supplied",
    )
    # Auth açık
    _enable_auth()
    check(
        clerk_auth.resolve_tenant_id("verified_u", "spoofed") == "verified_u",
        "verified varsa supplied'ı yok say (spoof koruması)",
    )
    check(
        clerk_auth.resolve_tenant_id(None, "spoofed") is None,
        "auth açık + verified yok → None (supplied'a güvenme)",
    )
    _disable_auth()


def _run() -> int:
    test_config_props()
    test_extract_bearer()
    test_verify_token_valid()
    test_verify_token_expired()
    test_verify_token_wrong_issuer()
    test_verify_token_bad_signature()
    test_verify_token_missing_sub()
    test_verified_sub_or_none()
    test_require_strict()
    test_resolve_tenant_id()
    print()
    if _failures:
        print(f"❌ {len(_failures)} test BAŞARISIZ:")
        for f in _failures:
            print(f"   - {f}")
        return 1
    print("✅ Tüm clerk_auth testleri geçti.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
