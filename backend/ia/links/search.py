import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
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
                 timeout: float = 15.0, language: str = "fr",
                 cache_file: str | Path | None = None) -> None:
        self.base_url = (base_url or os.getenv("SEARXNG_URL", "http://localhost:8080")).rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=timeout)
        self.language = language
        path = cache_file or os.getenv("SEARCH_CACHE_FILE")
        self.cache_file = Path(path) if path else None
        self._cache: dict[str, list[SearchResult]] = self._load()

    def _load(self) -> dict[str, list[SearchResult]]:
        if not self.cache_file or not self.cache_file.exists():
            return {}
        try:
            raw = json.loads(self.cache_file.read_text(encoding="utf-8"))
            return {q: [SearchResult(**r) for r in rs] for q, rs in raw.items()}
        except (ValueError, TypeError):
            return {}

    def _save(self) -> None:
        if not self.cache_file:
            return
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {q: [asdict(r) for r in rs] for q, rs in self._cache.items()}
        self.cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

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
        if results:
            self._cache[query] = results
            self._save()
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
