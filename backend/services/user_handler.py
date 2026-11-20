from models import Users
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

#TODO: Finished in authentication

async def check_pwd(plain_pwd, hashed_pwd):
    pass


async def get_current_user(
    name: str, session: AsyncSession, password: str
) -> Users:
    user = await session.scalar(select(Users).where(Users.name == name))

    if not user or not check_pwd(password, user.hashed_pwd):
        raise ValueError("Invalid username or passwor")
    return user
