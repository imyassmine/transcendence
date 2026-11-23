import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

Resolver = Callable[[str], Awaitable[list[str]]]

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_PORTS = (None, 80, 443)
TEXT_TYPES = ("html", "xml", "text", "json")


class UnsafeURL(Exception):
    pass


@dataclass
class Page:
    url: str
    status: int
    text: str


async def system_resolver(host: str) -> list[str]:
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    return [info[4][0] for info in infos]


class SafeFetcher:
    def __init__(self, client: httpx.AsyncClient | None = None,
                 resolver: Resolver = system_resolver,
                 timeout: float = 8.0, max_bytes: int = 2_000_000,
                 max_redirects: int = 4,
                 user_agent: str = "TranscendenceBot/0.1") -> None:
        self.resolver = resolver
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects
        self.client = client or httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers={"User-Agent": user_agent, "Accept-Language": "fr,en;q=0.8"},
        )

    async def check_url(self, url: str) -> None:
        parts = urlsplit(url)
        if parts.scheme not in ALLOWED_SCHEMES:
            raise UnsafeURL(f"scheme refusé : {parts.scheme!r}")
        try:
            port = parts.port
        except ValueError as e:
            raise UnsafeURL("port invalide") from e
        if port not in ALLOWED_PORTS:
            raise UnsafeURL(f"port refusé : {port}")
        host = parts.hostname
        if not host:
            raise UnsafeURL("pas de host")
        try:
            ips = await self.resolver(host)
        except OSError as e:
            raise UnsafeURL(f"DNS en échec pour {host}") from e
        if not ips:
            raise UnsafeURL(f"aucune IP pour {host}")
        for ip in ips:
            if not ipaddress.ip_address(ip.split("%")[0]).is_global:
                raise UnsafeURL(f"{host} -> IP non publique {ip}")

    async def get(self, url: str) -> Page | None:
        try:
            for _ in range(self.max_redirects + 1):
                await self.check_url(url)
                async with self.client.stream("GET", url) as r:
                    if r.is_redirect and "location" in r.headers:
                        url = urljoin(url, r.headers["location"])
                        continue
                    ctype = r.headers.get("content-type", "")
                    if not any(t in ctype for t in TEXT_TYPES):
                        return Page(str(r.url), r.status_code, "")
                    body = bytearray()
                    async for chunk in r.aiter_bytes():
                        body += chunk
                        if len(body) > self.max_bytes:
                            del body[self.max_bytes:]
                            break
                    text = bytes(body).decode(r.encoding or "utf-8", errors="replace")
                    return Page(str(r.url), r.status_code, text)
        except (UnsafeURL, httpx.HTTPError):
            return None
        return None

    async def aclose(self) -> None:
        await self.client.aclose()
