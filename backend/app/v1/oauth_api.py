import httpx
import secrets
from core import get_config
from core.security import create_access_token, set_auth_cookie
from db import get_db
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from services import OAuthEmailConflict, get_or_create_oauth_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from urllib.parse import urlencode


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
STATE_COOKIE = "oauth_state"
STATE_COOKIE_PATH = "/api/v1/auth/oauth/google"


oauth_router = APIRouter(prefix="/api/v1/auth/oauth", tags=["oauth"])


def _clear_state_cookie(response: Response) -> None:
    response.delete_cookie(
        key=STATE_COOKIE,
        path=STATE_COOKIE_PATH,
        httponly=True,
        secure=True,
        samesite="lax",
    )


@oauth_router.get("/google/login")
async def google_login() -> RedirectResponse:
    config = get_config()
    if not all(
        [
            config.GOOGLE_CLIENT_ID,
            config.GOOGLE_CLIENT_SECRET,
            config.GOOGLE_REDIRECT_URI,
        ]
    ):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth not configured"
        )
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    response = RedirectResponse(
        f"{GOOGLE_AUTH_URL}?{urlencode(params)}", status_code=302
    )
    response.set_cookie(
        key=STATE_COOKIE,
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=600,
        path=STATE_COOKIE_PATH,
    )
    return response


@oauth_router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    oauth_state: Annotated[str | None, Cookie()] = None,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google authentication failed",
        )
    if (
        not code
        or not state
        or not oauth_state
        or not secrets.compare_digest(state.encode(), oauth_state.encode())
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth request"
        )

    config = get_config()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": config.GOOGLE_CLIENT_ID,
                    "client_secret": config.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": config.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise HTTPException(
                    status.HTTP_502_BAD_GATEWAY, detail="Google token exchange failed"
                )
            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise HTTPException(
                    status.HTTP_502_BAD_GATEWAY, detail="Google token exchange failed"
                )
            profile_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if profile_resp.status_code != 200:
                raise HTTPException(
                    status.HTTP_502_BAD_GATEWAY, detail="Google profile fetch failed"
                )
            profile = profile_resp.json()
    except httpx.HTTPError:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail="Google unreachable")

    if not (
        profile.get("email_verified") and profile.get("sub") and profile.get("email")
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Google account email not verified"
        )

    try:
        user = await get_or_create_oauth_user(
            session, "google", profile["sub"], profile["email"], profile.get("name")
        )
        await session.commit()
    except (OAuthEmailConflict, IntegrityError):
        await session.rollback()
        redirect = RedirectResponse("/login?error=oauth_email_exists", status_code=302)
        _clear_state_cookie(redirect)
        return redirect

    redirect = RedirectResponse("/", status_code=302)
    set_auth_cookie(redirect, create_access_token(user.id))
    _clear_state_cookie(redirect)
    return redirect
