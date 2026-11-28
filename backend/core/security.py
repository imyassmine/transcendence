from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    VerificationError,
    VerifyMismatchError,
)
from fastapi import Response

from core.config import get_config

_hasher = PasswordHasher()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_access_token(user_id: UUID) -> str:
    config = get_config()
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + timedelta(minutes=config.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "jti": str(uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(
            token,
            get_config().JWT_SECRET,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        return UUID(payload["sub"])
    except jwt.PyJWTError:
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=get_config().JWT_EXPIRE_MINUTES * 60,
        path="/api",
    )
