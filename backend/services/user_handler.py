import asyncio
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import decode_access_token, hash_password, verify_password
from db import get_db
from models import Users
from schemas import LoginRequest, RegisterRequest

_DUMMY_HASH = hash_password("dummy-password")
# Mécanisme de sécurité contre une attaque appelée user enumeration
# Le hash factice sert à ce que « email inconnu » prenne le même temps
# que « mauvais mot de passe », sinon on peut deviner quels emails existent
# car la vérification prend un certain temps
# Argon2 étant volontairement coûteux en calcul et en mémoire


async def get_current_user(
    session: AsyncSession = Depends(get_db),
    access_token: Annotated[str | None, Cookie()] = None,
) -> Users:
    if access_token:
        user_id = decode_access_token(access_token)
        if user_id is not None:
            user = await session.get(Users, user_id)
            if user is not None:
                return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing access token",
    )


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def register_user(session: AsyncSession, data: RegisterRequest) -> Users:
    email = normalize_email(data.email)
    hashed = await asyncio.to_thread(hash_password, data.password)
    user = Users(name=data.name, email=email, hashed_pwd=hashed)
    session.add(user)
    return user


async def authenticate_user(
    session: AsyncSession, data: LoginRequest
) -> Users | None:
    user = await session.scalar(
        select(Users).where(Users.email == normalize_email(data.email))
    )
    if user is None or user.hashed_pwd is None:
        await asyncio.to_thread(verify_password, _DUMMY_HASH, data.password)
        return None
    if await asyncio.to_thread(
        verify_password, user.hashed_pwd, data.password
    ):
        return user
    return None
