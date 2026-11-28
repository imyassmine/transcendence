from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core import create_access_token, set_auth_cookie
from db import get_db
from models import Users
from schemas import LoginRequest, RegisterRequest, User
from services import authenticate_user, get_current_user, register_user

auth_router = APIRouter(prefix="/api/v1/auth")


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> User:
    user = await register_user(session, data)
    try:
        await session.commit()
    except (
        IntegrityError
    ):  # violation de contraintes SQL (email déjà pris etc)
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already exists",
        )
    return User.model_validate(user)


@auth_router.post("/login")
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> User:
    user = await authenticate_user(session, data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(user.id)
    set_auth_cookie(response, token)
    return User.model_validate(user)


@auth_router.get("/me")
async def me(user: Users = Depends(get_current_user)) -> User:
    return User.model_validate(user)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        path="/api",
    )
