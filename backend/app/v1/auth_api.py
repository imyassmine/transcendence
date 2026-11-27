from db import get_db
from fastapi import APIRouter, Depends, HTTPException, status, Response
from core import get_config, create_access_token
from models import Users
from schemas import RegisterRequest, User, LoginRequest
from services import register_user, authenticate_user, get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

auth_router = APIRouter(prefix="/api/v1/auth")


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> User:
    user = await register_user(session, data)
    try:
        await session.commit()
    except IntegrityError:  # violation de contraintes SQL (email déjà pris etc)
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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(user.id)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # le JavaScript du navigateur ne peut pas lire le cookie pour limiter le vol de token par attaque XSS
        secure=True,  # le cookie ne part qu'en HTTPS
        max_age=get_config().JWT_EXPIRE_MINUTES * 60,
        path="/api",
    )
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
