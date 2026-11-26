import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any

from core.config import get_config
from db import get_db
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from models import Users
from services import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession

from . import repository
from .letters import Letter, LetterGenerator, LetterRequest
from .links.dataset import DeletionDataset
from .links.domains import _extract, normalize_domain
from .links.fetcher import SafeFetcher
from .links.finder import LinkFinder
from .links.search import SearxClient
from .llm import OllamaClient
from .ratelimit import RateLimiter

DATASET = Path(__file__).resolve().parent / "links" / "data" / "jdm_sites.json"

LINK_RATE_PER_MIN = int(os.getenv("IA_LINK_RATE_PER_MIN", "60"))
LETTER_RATE_PER_MIN = int(os.getenv("IA_LETTER_RATE_PER_MIN", "10"))
MAX_PARALLEL_FINDS = int(os.getenv("IA_MAX_PARALLEL_FINDS", "3"))
LINK_CACHE_MAX_AGE = timedelta(days=get_config().IA_LINK_CACHE_TTL_DAYS)


class KeyedLocks:
    def __init__(self) -> None:
        self._locks: dict[str, tuple[asyncio.Lock, int]] = {}

    @asynccontextmanager
    async def hold(self, key: str) -> AsyncIterator[None]:
        lock, users = self._locks.get(key, (asyncio.Lock(), 0))
        self._locks[key] = (lock, users + 1)
        try:
            async with lock:
                yield
        finally:
            lock, users = self._locks[key]
            if users == 1:
                del self._locks[key]
            else:
                self._locks[key] = (lock, users - 1)


@dataclass
class IAServices:
    finder: LinkFinder
    generator: LetterGenerator
    locks: KeyedLocks
    link_limiter: RateLimiter
    letter_limiter: RateLimiter
    semaphore: asyncio.Semaphore


def build_services(
    finder: LinkFinder, generator: LetterGenerator
) -> IAServices:
    return IAServices(
        finder=finder,
        generator=generator,
        locks=KeyedLocks(),
        link_limiter=RateLimiter(LINK_RATE_PER_MIN),
        letter_limiter=RateLimiter(LETTER_RATE_PER_MIN),
        semaphore=asyncio.Semaphore(MAX_PARALLEL_FINDS),
    )


@asynccontextmanager
async def ia_lifespan(app: FastAPI) -> AsyncIterator[None]:
    fetcher, llm, search = SafeFetcher(), OllamaClient(), SearxClient()
    finder = LinkFinder(
        DeletionDataset.from_file(DATASET), fetcher, llm, search
    )
    app.state.ia = build_services(finder, LetterGenerator(llm))
    try:
        yield
    finally:
        await fetcher.aclose()
        await llm.aclose()
        await search.aclose()


def get_services(request: Request) -> IAServices:
    return request.app.state.ia


def get_user_key(user: Users = Depends(get_current_user)) -> str:
    return str(user.id)


def check_rate(limiter: RateLimiter, key: str) -> None:
    if not limiter.allow(key):
        raise HTTPException(
            429,
            "trop de requêtes, réessaie plus tard",
            headers={"Retry-After": str(limiter.retry_after(key))},
        )


def domain_or_422(account: str) -> str:
    domain = normalize_domain(account)
    ext = _extract(domain)
    if not ext.domain or not ext.suffix:
        raise HTTPException(422, "compte ou domaine invalide")
    return domain


def sse(event: dict[str, Any]) -> str:
    data = json.dumps(event, ensure_ascii=False, default=str)
    return f"event: {event['type']}\ndata: {data}\n\n"


async def find_recipient(
    ia: IAServices, session: AsyncSession, domain: str, service: str | None
) -> tuple[str | None, str | None]:
    contact = await repository.get_contact(session, domain, LINK_CACHE_MAX_AGE)
    if contact is not None:
        return contact
    await session.rollback()
    async with ia.locks.hold(f"contact:{domain}"):
        contact = await repository.get_contact(
            session, domain, LINK_CACHE_MAX_AGE
        )
        if contact is not None:
            return contact
        await session.rollback()
        async with ia.semaphore:
            contact = await ia.finder.find_contact(domain, service)
        await repository.save_contact(session, domain, *contact)
        await session.commit()
    return contact


router = APIRouter(prefix="/api/v1/ia", tags=["ia"])


@router.get("/link")
async def get_link(
    account: str = Query(min_length=3, max_length=254),
    service: str | None = Query(None, max_length=100),
    refresh: bool = False,
    ia: IAServices = Depends(get_services),
    session: AsyncSession = Depends(get_db),
    user: str = Depends(get_user_key),
) -> dict[str, Any]:
    domain = domain_or_422(account)
    if (
        not refresh
        and (
            cached := await repository.get_link(
                session, domain, LINK_CACHE_MAX_AGE
            )
        )
        is not None
    ):
        return asdict(cached) | {"cached": True}
    check_rate(ia.link_limiter, user)
    await session.rollback()
    async with ia.locks.hold(f"link:{domain}"):
        if (
            not refresh
            and (
                cached := await repository.get_link(
                    session, domain, LINK_CACHE_MAX_AGE
                )
            )
            is not None
        ):
            return asdict(cached) | {"cached": True}
        await session.rollback()
        async with ia.semaphore:
            result = await ia.finder.find(domain, service)
        await repository.save_link(session, result)
        await session.commit()
    return asdict(result) | {"cached": False}


@router.post("/letter", response_model=None)
async def post_letter(
    req: LetterRequest,
    stream: bool = True,
    ia: IAServices = Depends(get_services),
    session: AsyncSession = Depends(get_db),
    user: str = Depends(get_user_key),
) -> Letter | StreamingResponse:
    check_rate(ia.letter_limiter, user)
    if req.recipient_email is None and req.domain:
        email, page = await find_recipient(
            ia, session, normalize_domain(req.domain), req.service_name
        )
        req = req.model_copy(
            update={
                "recipient_email": email,
                "contact_url": req.contact_url or page,
            }
        )
    if not stream:
        return await ia.generator.generate(req)

    async def events() -> AsyncIterator[str]:
        async for event in ia.generator.stream(req):
            yield sse(event)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
