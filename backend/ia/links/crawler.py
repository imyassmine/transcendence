import asyncio
import json
import re
import secrets
from dataclasses import dataclass, field
from urllib.parse import quote, urlsplit, urlunsplit

from .domains import registrable_domain
from .fetcher import Page, SafeFetcher
from .parsing import extract_links, find_privacy_emails, fold, is_privacy_link, score_link

PROBE_PATHS = ["/account/delete", "/delete-account", "/account/close", "/settings/account",
               "/account", "/privacy", "/privacy-policy", "/legal/privacy",
               "/confidentialite", "/politique-de-confidentialite", "/help"]
HELP_SUBDOMAINS = ["help", "support", "aide", "assistance", "faq"]
ZENDESK_QUERIES = ["supprimer compte", "delete account"]
SITEMAP_HINTS = ["help", "support", "faq", "aide", "article", "page", "account", "compte", "fr"]

LOC_RE = re.compile(r"<loc>\s*(.*?)\s*</loc>", re.IGNORECASE | re.DOTALL)
ROBOTS_SITEMAP_RE = re.compile(r"^\s*sitemap:\s*(\S+)", re.IGNORECASE | re.MULTILINE)

MAX_SITEMAP_LOCS = 5000
MAX_CHILD_SITEMAPS = 8
MIN_SITEMAP_SCORE = 5.0
PROBE_BONUS = 1.0


@dataclass
class Candidate:
    url: str
    text: str = ""
    score: float = 0.0
    origins: set[str] = field(default_factory=set)
    excerpt: str = ""


@dataclass
class CrawlResult:
    candidates: list[Candidate]
    privacy_url: str | None
    emails: list[str]


def same_site(url: str, domain: str) -> bool:
    host = urlsplit(url).hostname or ""
    return bool(host) and registrable_domain(host) == registrable_domain(domain)


def same_brand(url: str, domain: str) -> bool:
    host = urlsplit(url).hostname or ""
    return bool(host) and registrable_domain(host).split(".")[0] == \
        registrable_domain(domain).split(".")[0]


def help_hosts_for(domain: str) -> list[str]:
    root = registrable_domain(domain)
    roots = [root]
    brand_com = root.split(".")[0] + ".com"
    if brand_com != root:
        roots.append(brand_com)
    return [f"{sub}.{r}" for r in roots for sub in HELP_SUBDOMAINS if f"{sub}.{r}" != domain]


def canonical(url: str) -> str:
    p = urlsplit(url)
    return urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/", p.query, ""))


def landed_on(final_url: str, path: str) -> bool:
    return urlsplit(final_url).path.rstrip("/").lower().endswith(path.rstrip("/").lower())


def is_catch_all(page: Page | None, random_path: str) -> bool:
    return page is not None and page.status == 200 and landed_on(page.url, random_path)


def ok(page: Page | None) -> bool:
    return page is not None and page.status < 400


def is_sitemap_index(xml: str) -> bool:
    return "<sitemapindex" in xml.lower()


def pick_child_sitemaps(locs: list[str], limit: int = MAX_CHILD_SITEMAPS) -> list[str]:
    def priority(url: str) -> int:
        hay = fold(urlsplit(url).path)
        return -sum(h in hay for h in SITEMAP_HINTS)
    return sorted(locs, key=priority)[:limit]


def zendesk_results(text: str) -> list[tuple[str, str]]:
    try:
        data = json.loads(text)
    except ValueError:
        return []
    if not isinstance(data, dict):
        return []
    out = []
    for item in data.get("results", []) or []:
        if isinstance(item, dict) and item.get("html_url"):
            out.append((str(item["html_url"]), str(item.get("title") or "")))
    return out


class Crawler:
    def __init__(self, fetcher: SafeFetcher) -> None:
        self.fetcher = fetcher

    async def _sitemap_locs(self, base: str, robots: Page | None) -> list[str]:
        roots = [base + "/sitemap.xml"]
        if ok(robots):
            roots += ROBOTS_SITEMAP_RE.findall(robots.text)
        roots = list(dict.fromkeys(roots))[:4]
        pages = await asyncio.gather(*(self.fetcher.get(u) for u in roots))
        locs: list[str] = []
        children: list[str] = []
        for page in pages:
            if not ok(page):
                continue
            found = LOC_RE.findall(page.text)
            if is_sitemap_index(page.text):
                children += found
            else:
                locs += found
        if children:
            child_pages = await asyncio.gather(
                *(self.fetcher.get(u) for u in pick_child_sitemaps(children)))
            for page in child_pages:
                if ok(page) and not is_sitemap_index(page.text):
                    locs += LOC_RE.findall(page.text)
        return locs[:MAX_SITEMAP_LOCS]

    async def _zendesk(self, host: str) -> list[tuple[str, str]]:
        urls = [f"https://{host}/api/v2/help_center/articles/search.json?query={quote(q)}"
                for q in ZENDESK_QUERIES]
        pages = await asyncio.gather(*(self.fetcher.get(u) for u in urls))
        out: list[tuple[str, str]] = []
        for page in pages:
            if page is not None and page.status == 200:
                out += zendesk_results(page.text)
        return out

    async def crawl(self, domain: str) -> CrawlResult:
        base = f"https://{domain}"
        help_hosts = help_hosts_for(domain)
        cands: dict[str, Candidate] = {}

        def add(url: str, text: str, origin: str, bonus: float = 0.0) -> None:
            if url.startswith("mailto:") or not same_brand(url, domain):
                return
            key = canonical(url)
            c = cands.setdefault(key, Candidate(url=key))
            if len(text) > len(c.text):
                c.text = text[:120]
            c.origins.add(origin)
            c.score = max(c.score, score_link(key, c.text) + bonus)

        random_path = f"/{secrets.token_hex(8)}-page-inexistante"
        home, robots, random_page, *rest = await asyncio.gather(
            self.fetcher.get(base + "/"),
            self.fetcher.get(base + "/robots.txt"),
            self.fetcher.get(base + random_path),
            *(self.fetcher.get(base + p) for p in PROBE_PATHS),
            *(self.fetcher.get(f"https://{h}/") for h in help_hosts),
        )
        probes, help_homes = rest[:len(PROBE_PATHS)], rest[len(PROBE_PATHS):]

        home_links = extract_links(home.text, home.url) if ok(home) else []
        for url, text in home_links:
            add(url, text, "home")

        catch_all = is_catch_all(random_page, random_path)
        for path, page in zip(PROBE_PATHS, probes):
            if (not catch_all and page is not None and page.status == 200
                    and same_site(page.url, domain) and landed_on(page.url, path)):
                add(page.url, "", "probe", bonus=PROBE_BONUS)

        live_help_hosts = []
        for host, page in zip(help_hosts, help_homes):
            if ok(page) and same_brand(page.url, domain):
                live_help_hosts.append(urlsplit(page.url).hostname or host)
                for url, text in extract_links(page.text, page.url):
                    add(url, text, "help")

        sitemap_task = self._sitemap_locs(base, robots)
        zendesk_tasks = [self._zendesk(h) for h in dict.fromkeys(live_help_hosts)]
        locs, *zendesk = await asyncio.gather(sitemap_task, *zendesk_tasks)

        for loc in locs:
            if score_link(loc, "") >= MIN_SITEMAP_SCORE:
                add(loc, "", "sitemap")
        for results in zendesk:
            for url, title in results:
                add(url, title, "zendesk")

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
