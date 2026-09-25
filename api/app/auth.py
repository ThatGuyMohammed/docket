import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_session
from .models import User

ALLOWED_JWT_ALGS = ("RS256", "ES256", "EdDSA")

_bearer = HTTPBearer(auto_error=False)
_keys: tuple[object, object] | None = None


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"{salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    salt_hex, _ = stored.split("$", 1)
    return hmac.compare_digest(hash_password(password, bytes.fromhex(salt_hex)), stored)


def _dev_key(alg: str):
    if alg == "RS256":
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)
    if alg == "ES256":
        return ec.generate_private_key(ec.SECP256R1())
    return ed25519.Ed25519PrivateKey.generate()


def _token_keys():
    global _keys
    if _keys is None:
        s = get_settings()
        if s.jwt_alg not in ALLOWED_JWT_ALGS:
            raise RuntimeError(f"JWT_ALG must be one of {ALLOWED_JWT_ALGS}")
        if s.jwt_private_key_path:
            with open(s.jwt_private_key_path, "rb") as fh:
                private = serialization.load_pem_private_key(fh.read(), password=None)
        else:
            private = _dev_key(s.jwt_alg)
        _keys = (private, private.public_key())
    return _keys


def issue_token(user: User) -> str:
    s = get_settings()
    private, _ = _token_keys()
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "iat": now,
        "exp": now + timedelta(minutes=s.jwt_ttl_minutes),
    }
    return jwt.encode(claims, private, algorithm=s.jwt_alg)


def decode_token(token: str) -> dict:
    _, public = _token_keys()
    return jwt.decode(token, public, algorithms=[get_settings().jwt_alg])


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_session),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing token")
    try:
        claims = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
    user = db.get(User, int(claims["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown user")
    return user
