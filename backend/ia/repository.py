from datetime import UTC, datetime, timedelta

from models import DeletionLinkCache
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .links.finder import DeletionLink


def to_link(row: DeletionLinkCache) -> DeletionLink:
    return DeletionLink(
        domain=row.domain,
        service=row.service,
        url=row.url,
        kind=row.kind,  # type: ignore[arg-type]
        probability=row.probability,
        verified=row.verified,
        source=row.source,
        contact_email=row.contact_email,
        reason=row.reason,
        confident=row.confident,
        alternatives=list(row.alternatives),
    )


async def get_link(
    session: AsyncSession, domain: str, max_age: timedelta
) -> DeletionLink | None:
    row = await session.scalar(
        select(DeletionLinkCache).where(
            DeletionLinkCache.domain == domain,
            DeletionLinkCache.checked_at >= func.now() - max_age,
        )
    )
    return to_link(row) if row else None


async def save_link(session: AsyncSession, link: DeletionLink) -> None:
    values = {
        "service": link.service,
        "url": link.url,
        "kind": link.kind,
        "probability": link.probability,
        "confident": link.confident,
        "verified": link.verified,
        "source": link.source,
        "reason": link.reason,
        "alternatives": link.alternatives,
    }
    stmt = pg_insert(DeletionLinkCache).values(
        domain=link.domain, contact_email=link.contact_email, **values
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[DeletionLinkCache.domain],
            set_={
                **values,
                "contact_email": func.coalesce(
                    stmt.excluded.contact_email,
                    DeletionLinkCache.contact_email,
                ),
                "checked_at": func.now(),
                "updated_at": func.now(),
            },
        )
    )


async def get_contact(
    session: AsyncSession, domain: str, max_age: timedelta
) -> tuple[str | None, str | None] | None:
    row = await session.scalar(
        select(DeletionLinkCache).where(DeletionLinkCache.domain == domain)
    )
    if row is None:
        return None
    limit = datetime.now(UTC) - max_age
    if row.contact_checked_at is not None:
        return (
            (row.contact_email, row.contact_url)
            if row.contact_checked_at >= limit
            else None
        )
    if row.contact_email and row.checked_at >= limit:
        return row.contact_email, None
    return None


async def save_contact(
    session: AsyncSession,
    domain: str,
    email: str | None,
    url: str | None,
) -> None:
    now = func.now()
    values = {
        "contact_email": email,
        "contact_url": url,
        "contact_checked_at": now,
        "updated_at": now,
    }
    await session.execute(
        pg_insert(DeletionLinkCache)
        .values(
            domain=domain,
            kind="none",
            probability=0.0,
            confident=False,
            verified=False,
            source="contact",
            reason="",
            alternatives=[],
            checked_at=datetime.fromtimestamp(0, UTC),
            **values,
        )
        .on_conflict_do_update(
            index_elements=[DeletionLinkCache.domain], set_=values
        )
    )
