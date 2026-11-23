import os
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from .domains import registrable_domain

LINK_QUERIES = ["site:{root} supprimer compte", "site:{root} delete account"]
EMAIL_QUERY = "site:{root} dpo données personnelles rgpd"


@dataclass
class SearchResult:
    url: str
    title: str
    content: str


def parse_results(data: object) -> list[SearchResult]:
    if not isinstance(data, dict):
        return []
    out = []
    for item in data.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "")
        if urlsplit(url).scheme not in ("http", "https"):
            continue
        out.append(SearchResult(url, str(item.get("title") or ""), str(item.get("content") or "")))
    return out


class SearxClient:
    def __init__(self, base_url: str | None = None, client: httpx.AsyncClient | None = None,
                 timeout: float = 15.0, language: str = "fr") -> None:
        self.base_url = (base_url or os.getenv("SEARXNG_URL", "http://localhost:8080")).rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=timeout)
        self.language = language
        self._cache: dict[str, list[SearchResult]] = {}

    async def search(self, query: str) -> list[SearchResult]:
        if query in self._cache:
            return self._cache[query]
        try:
            r = await self.client.get(f"{self.base_url}/search",
                                      params={"q": query, "format": "json",
                                              "language": self.language})
            r.raise_for_status()
            results = parse_results(r.json())
        except (httpx.HTTPError, ValueError):
            return []
        self._cache[query] = results
        return results

    async def for_domain(self, domain: str) -> tuple[list[SearchResult], list[SearchResult]]:
        root = registrable_domain(domain)
        links: list[SearchResult] = []
        for q in LINK_QUERIES:
            links += await self.search(q.format(root=root))
        emails = await self.search(EMAIL_QUERY.format(root=root))
        return links, emails

    async def aclose(self) -> None:
        await self.client.aclose()
