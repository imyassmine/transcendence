import asyncio
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

from .domains import registrable_domain
from .fetcher import Page, SafeFetcher
from .parsing import extract_links, find_privacy_emails, is_privacy_link, score_link

PROBE_PATHS = ["/account/delete", "/delete-account", "/account/close", "/settings/account",
               "/account", "/privacy", "/privacy-policy", "/legal/privacy",
               "/confidentialite", "/politique-de-confidentialite", "/help"]
SITEMAP_RE = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.IGNORECASE | re.DOTALL)
MAX_SITEMAP_LOCS = 5000
MIN_SITEMAP_SCORE = 5.0
PROBE_BONUS = 1.0


@dataclass
class Candidate:
    url: str
    text: str = ""
    score: float = 0.0
    origins: set[str] = field(default_factory=set)


@dataclass
class CrawlResult:
    candidates: list[Candidate]
    privacy_url: str | None
    emails: list[str]


def same_site(url: str, domain: str) -> bool:
    host = urlsplit(url).hostname or ""
    return bool(host) and registrable_domain(host) == registrable_domain(domain)


def canonical(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/", p.query, ""))


def ok(page: Page | None) -> bool:
    return page is not None and page.status < 400


class Crawler:
    def __init__(self, fetcher: SafeFetcher) -> None:
        self.fetcher = fetcher

    async def crawl(self, domain: str) -> CrawlResult:
        base = f"https://{domain}"
        cands: dict[str, Candidate] = {}

        def add(url: str, text: str, origin: str, bonus: float = 0.0) -> None:
            if url.startswith("mailto:") or not same_site(url, domain):
                return
            key = canonical(url)
            c = cands.setdefault(key, Candidate(url=key))
            if len(text) > len(c.text):
                c.text = text[:120]
            c.origins.add(origin)
            c.score = max(c.score, score_link(key, c.text) + bonus)

        home, sitemap, *probes = await asyncio.gather(
            self.fetcher.get(base + "/"),
            self.fetcher.get(base + "/sitemap.xml"),
            *(self.fetcher.get(base + p) for p in PROBE_PATHS),
        )

        home_links = extract_links(home.text, home.url) if ok(home) else []
        for url, text in home_links:
            add(url, text, "home")

        if ok(sitemap):
            for loc in SITEMAP_RE.findall(sitemap.text)[:MAX_SITEMAP_LOCS]:
                if score_link(loc, "") >= MIN_SITEMAP_SCORE:
                    add(loc, "", "sitemap")

        for path, page in zip(PROBE_PATHS, probes):
            if page is not None and page.status == 200 and same_site(page.url, domain):
                add(page.url, path, "probe", bonus=PROBE_BONUS)

        emails = find_privacy_emails(home.text, home_links) if ok(home) else []
        privacy = next((c for c in sorted(cands.values(), key=lambda c: -c.score)
                        if is_privacy_link(c.url, c.text)), None)
        if privacy:
            page = await self.fetcher.get(privacy.url)
            if ok(page):
                links = extract_links(page.text, page.url)
                for url, text in links:
                    add(url, text, "privacy")
                emails = find_privacy_emails(page.text, links) + emails

        ranked = sorted((c for c in cands.values() if c.score > 0), key=lambda c: -c.score)
        return CrawlResult(
            candidates=ranked,
            privacy_url=privacy.url if privacy else None,
            emails=list(dict.fromkeys(emails)),
        )
