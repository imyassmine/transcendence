import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from .cache import TTLCache
from .letters import Letter, LetterGenerator, LetterRequest
from .links.dataset import DeletionDataset
from .links.domains import _extract, normalize_domain
from .links.fetcher import SafeFetcher
from .links.finder import DeletionLink, LinkFinder
from .links.search import SearxClient
from .llm import OllamaClient
from .ratelimit import RateLimiter

DATASET = Path(__file__).resolve().parent / "links" / "data" / "jdm_sites.json"

LINK_RATE_PER_MIN = int(os.getenv("IA_LINK_RATE_PER_MIN", "60"))
LETTER_RATE_PER_MIN = int(os.getenv("IA_LETTER_RATE_PER_MIN", "10"))
MAX_PARALLEL_FINDS = int(os.getenv("IA_MAX_PARALLEL_FINDS", "3"))
LINK_CACHE_TTL_S = float(os.getenv("IA_LINK_CACHE_TTL_S", str(7 * 24 * 3600)))


@dataclass
class IAServices:
    finder: LinkFinder
    generator: LetterGenerator
    cache: TTLCache[DeletionLink]
    link_limiter: RateLimiter
    letter_limiter: RateLimiter
    semaphore: asyncio.Semaphore


def build_services(finder: LinkFinder, generator: LetterGenerator) -> IAServices:
    return IAServices(
        finder=finder,
        generator=generator,
        cache=TTLCache(LINK_CACHE_TTL_S),
        link_limiter=RateLimiter(LINK_RATE_PER_MIN),
        letter_limiter=RateLimiter(LETTER_RATE_PER_MIN),
        semaphore=asyncio.Semaphore(MAX_PARALLEL_FINDS),
    )


@asynccontextmanager
async def ia_lifespan(app: FastAPI) -> AsyncIterator[None]:
    fetcher, llm, search = SafeFetcher(), OllamaClient(), SearxClient()
    finder = LinkFinder(DeletionDataset.from_file(DATASET), fetcher, llm, search)
    app.state.ia = build_services(finder, LetterGenerator(llm))
    try:
        yield
    finally:
        await fetcher.aclose()
        await llm.aclose()
        await search.aclose()


def get_services(request: Request) -> IAServices:
    return request.app.state.ia


def get_user_key(request: Request) -> str:
    return request.client.host if request.client else "anonymous"


def check_rate(limiter: RateLimiter, key: str) -> None:
    if not limiter.allow(key):
        raise HTTPException(429, "trop de requêtes, réessaie plus tard",
                            headers={"Retry-After": str(limiter.retry_after(key))})


def domain_or_422(account: str) -> str:
    domain = normalize_domain(account)
    ext = _extract(domain)
    if not ext.domain or not ext.suffix:
        raise HTTPException(422, "compte ou domaine invalide")
    return domain


def sse(event: dict[str, Any]) -> str:
    data = json.dumps(event, ensure_ascii=False, default=str)
    return f"event: {event['type']}\ndata: {data}\n\n"


router = APIRouter(prefix="/ia", tags=["ia"])


@router.get("/link")
async def get_link(account: str = Query(min_length=3, max_length=254),
                   service: str | None = Query(None, max_length=100),
                   refresh: bool = False,
                   ia: IAServices = Depends(get_services),
                   user: str = Depends(get_user_key)) -> dict[str, Any]:
    domain = domain_or_422(account)
    if not refresh and (cached := ia.cache.get(domain)) is not None:
        return asdict(cached) | {"cached": True}
    check_rate(ia.link_limiter, user)
    async with ia.semaphore:
        result = await ia.finder.find(domain, service)
    ia.cache.set(domain, result)
    return asdict(result) | {"cached": False}


@router.post("/letter", response_model=None)
async def post_letter(req: LetterRequest, stream: bool = True,
                      ia: IAServices = Depends(get_services),
                      user: str = Depends(get_user_key)) -> Letter | StreamingResponse:
    check_rate(ia.letter_limiter, user)
    if req.recipient_email is None and req.domain:
        cached = ia.cache.get(normalize_domain(req.domain))
        if cached and cached.contact_email:
            req = req.model_copy(update={"recipient_email": cached.contact_email})
    if not stream:
        return await ia.generator.generate(req)

    async def events() -> AsyncIterator[str]:
        async for event in ia.generator.stream(req):
            yield sse(event)

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
