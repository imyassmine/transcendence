from typing import Annotated

from core.security import decode_access_token
from db import get_db
from fastapi import Cookie, Depends, HTTPException, status
from models import Users
from sqlalchemy.ext.asyncio import AsyncSession


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
