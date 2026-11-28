from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import OAuthAccounts, Users

from .user_handler import normalize_email


class OAuthEmailConflict(Exception):
    """An account already exists with this email"""


async def get_or_create_oauth_user(
    session: AsyncSession,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str | None,
) -> Users:
    account = await session.scalar(
        select(OAuthAccounts).where(
            OAuthAccounts.provider == provider,
            OAuthAccounts.provider_user_id == provider_user_id,
        )
    )
    if account:
        user = await session.get(Users, account.user_id)
        if user is not None:
            return user

    email = normalize_email(email)
    existing = await session.scalar(select(Users).where(Users.email == email))
    if existing:
        raise OAuthEmailConflict

    display_name = (name or "").strip() or email.split("@")[0]
    user = Users(name=display_name[:50], email=email, hashed_pwd=None)
    session.add(user)
    await session.flush()  # génère user.id
    session.add(
        OAuthAccounts(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
        )
    )
    await session.flush()
    return user
