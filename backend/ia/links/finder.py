import asyncio
import re
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import parse_qs, urlsplit, urlunsplit

from ..llm import OllamaClient
from .crawler import Candidate, Crawler, canonical, same_brand, same_site
from .dataset import DeletionDataset
from .domains import normalize_domain, registrable_domain
from .evidence import describe, is_login_url, page_text
from .fetcher import Page, SafeFetcher
from .parsing import (ACCOUNT, PRIVACY, STRONG, find_privacy_emails, fold, is_privacy_link,
                      score_link)
from .ranker import rank
from .search import SearxClient

Kind = Literal["direct", "settings", "help", "privacy", "none"]

KIND_BASE = {"direct": 0.90, "settings": 0.75, "help": 0.65, "privacy": 0.35}
WEAK_SETTINGS_BASE = 0.50
LINK_KINDS = ("direct", "settings", "help")

HELP_HINTS = ["help", "aide", "support", "faq", "hc/", "article", "assistance", "centre-d-aide",
              "kb/", "knowledge"]
SOFT_404_HINTS = ["404", "page introuvable", "page non trouvee", "not found", "page not found",
                  "n'existe pas", "n'existe plus", "doesn't exist", "does not exist",
                  "page inexistante", "erreur 404", "oops", "oups"]
AUTH_STATUS = {401}
BLOCKED_STATUS = {403, 429, 503}
GENERIC_TLDS = {"com", "net", "org", "io", "co", "app", "eu"}
DATA_DELETION = ["data-deletion", "data deletion", "data/deletion", "account-deletion",
                 "account deletion", "deleteaccount", "delete-account", "delete account"]
MIN_CONFIDENT = 0.60
SEARCH_PATH_HINTS = ["/search", "/recherche", "/r-", "/results", "/resultats"]
SEARCH_QUERY_KEYS = {"q", "query", "s", "search", "k", "keyword", "keywords", "userinput",
                     "recherche", "term"}
FORUM_HINTS = ["/answers/", "/forum", "/community", "/communaute", "/questions/", "/topic",
               "/t/", "/discussions/"]
FORUM_PENALTY = 0.30
UGC_SUBDOMAINS = {"form", "forms", "survey", "surveys", "community", "forum", "forums",
                  "answers", "blog", "blogs", "status", "careers", "jobs", "shop", "store"}
TITLE_ONLY_PENALTY = 0.30

VERIFY_LIMIT = 12
LLM_BONUS = 0.10
DATASET_BONUS = 0.05
BLOCKED_PENALTY = 0.25
OTHER_GENERIC_TLD_PENALTY = 0.10
OTHER_COUNTRY_PENALTY = 0.40
STOP_IF_DATASET_ABOVE = 0.80


@dataclass
class Check:
    url: str
    final_url: str
    status: int
    reachable: bool
    blocked: bool
    login: bool
    title: str
    text: str


@dataclass
class Scored:
    candidate: Candidate
    check: Check
    kind: Kind
    probability: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class DeletionLink:
    domain: str
    service: str | None
    url: str | None
    kind: Kind
    probability: float
    verified: bool
    source: str
    contact_email: str | None
    reason: str
    confident: bool = False
    alternatives: list[str] = field(default_factory=list)


def has_any(hay: str, words: list[str]) -> bool:
    return any(w in hay for w in words)


def url_hay(url: str) -> str:
    p = urlsplit(url)
    return fold(f"{p.hostname or ''}/{p.path} {p.query}").replace("_", "-")


def is_soft_404(title: str, text: str) -> bool:
    head = fold(f"{title} {text[:300]}")
    return has_any(fold(title), SOFT_404_HINTS) or (len(text) < 400 and has_any(head, SOFT_404_HINTS))


def brand(host: str) -> str:
    return registrable_domain(host).split(".")[0]


def tld(host: str) -> str:
    return registrable_domain(host).rsplit(".", 1)[-1]


def to_check(url: str, page: Page | None) -> Check:
    if page is None:
        return Check(url, url, 0, False, False, False, "", "")
    title, text = page_text(page.text) if page.text else ("", "")
    login = page.status in AUTH_STATUS or (is_login_url(page.url) and not is_login_url(url))
    blocked = page.status in BLOCKED_STATUS
    reachable = (page.status < 400 or login) and not is_soft_404(title, text)
    return Check(url, page.url, page.status, reachable, blocked, login, title, text)


def is_search_page(url: str) -> bool:
    p = urlsplit(url)
    path = p.path.lower()
    if any(h in path for h in SEARCH_PATH_HINTS):
        return True
    return bool(SEARCH_QUERY_KEYS & {k.lower() for k in parse_qs(p.query)})


def is_user_content_host(url: str, domain: str) -> bool:
    host = urlsplit(url).hostname or ""
    root = registrable_domain(host)
    labels = host[: -len(root)].rstrip(".").split(".") if host != root else []
    return any(label in UGC_SUBDOMAINS for label in labels) and host != domain


def path_has_words(url: str) -> bool:
    segments = [seg for seg in urlsplit(url).path.split("/") if seg]
    return any(re.search(r"[a-zA-Z]{3,}", seg) and not re.fullmatch(r"[0-9a-fA-F-]{8,}", seg)
               for seg in segments)


def is_forum(url: str) -> bool:
    return any(h in urlsplit(url).path.lower() for h in FORUM_HINTS)


def clean_reason(reason: str) -> str:
    if any(ord(ch) > 0x2FFF for ch in reason):
        return "raison fournie dans une autre langue"
    return reason


def deletion_intent(hay: str) -> bool:
    spaced = hay.replace("-", " ").replace("/", " ")
    both = f"{hay} {spaced}"
    if has_any(both, DATA_DELETION):
        return True
    return has_any(both, STRONG) and has_any(both, ACCOUNT)


def classify(c: Candidate, chk: Check) -> tuple[Kind | None, float]:
    if not chk.reachable and not chk.blocked:
        return None, 0.0
    if is_search_page(chk.url) or is_search_page(chk.final_url):
        return None, 0.0
    path = url_hay(chk.url) + " " + url_hay(chk.final_url)
    title = fold(chk.title)
    page = fold(f"{chk.title} {chk.text[:3000]}")
    intent = deletion_intent(f"{path} {fold(c.text)}") or deletion_intent(title)
    account_path = has_any(path, ACCOUNT)
    help_url = has_any(path, HELP_HINTS)

    if chk.login:
        if intent:
            return "direct", KIND_BASE["direct"]
        if account_path:
            return "settings", KIND_BASE["settings"]
        return None, 0.0
    if intent and help_url:
        return "help", KIND_BASE["help"]
    if intent:
        return "direct", KIND_BASE["direct"]
    if account_path:
        if deletion_intent(page) or has_any(page, STRONG):
            return "settings", KIND_BASE["settings"]
        return "settings", WEAK_SETTINGS_BASE
    if is_privacy_link(chk.final_url, c.text) or has_any(title, PRIVACY):
        return "privacy", KIND_BASE["privacy"]
    return None, 0.0


def localized(url: str, domain: str) -> str | None:
    p = urlsplit(url)
    host = p.hostname or ""
    if not host or same_site(url, domain) or brand(host) != brand(domain):
        return None
    sub = host[: -len(registrable_domain(host))]
    return urlunsplit((p.scheme or "https", sub + registrable_domain(domain), p.path, p.query, ""))


def domain_penalty(url: str, domain: str) -> tuple[float, str | None]:
    if same_site(url, domain):
        return 0.0, None
    host = urlsplit(url).hostname or ""
    if brand(host) != brand(domain):
        return 1.0, "autre site"
    if tld(host) in GENERIC_TLDS or tld(domain) in GENERIC_TLDS:
        return OTHER_GENERIC_TLD_PENALTY, f"domaine {registrable_domain(host)}"
    return OTHER_COUNTRY_PENALTY, f"autre pays ({registrable_domain(host)})"


def score(c: Candidate, chk: Check, domain: str) -> Scored | None:
    kind, base = classify(c, chk)
    if kind is None:
        return None
    if is_user_content_host(chk.url, domain) or is_user_content_host(chk.final_url, domain):
        return None
    reasons = [kind]
    if kind in ("direct", "help") and not path_has_words(chk.url) \
            and not deletion_intent(url_hay(chk.url)):
        base -= TITLE_ONLY_PENALTY
        reasons.append("intention déduite du titre seulement")
    if (kind == "settings" and base == WEAK_SETTINGS_BASE and "dataset" in c.origins
            and not has_any(url_hay(chk.url), HELP_HINTS)):
        base = KIND_BASE["settings"]
        reasons.append("page de compte référencée par le dataset")
    p = base + 0.05 * min(c.score, 10.0) / 10.0
    if "dataset" in c.origins:
        p += DATASET_BONUS
        reasons.append("dataset")
    if is_forum(chk.final_url):
        p -= FORUM_PENALTY
        reasons.append("forum / réponse communautaire")
    if chk.blocked:
        p -= BLOCKED_PENALTY
        reasons.append(f"non vérifiable (HTTP {chk.status})")
    elif chk.login:
        reasons.append("réservée aux comptes connectés")
    penalty, why = domain_penalty(chk.final_url, domain)
    if penalty >= 1.0:
        return None
    if why:
        p -= penalty
        reasons.append(why)
    return Scored(c, chk, kind, max(0.0, min(p, 0.99)), reasons)


def has_confident_link(scored: list[Scored]) -> bool:
    return any(s.kind in LINK_KINDS and s.probability >= MIN_CONFIDENT for s in scored)


class LinkFinder:
    def __init__(self, dataset: DeletionDataset, fetcher: SafeFetcher,
                 llm: OllamaClient | None = None, search: SearxClient | None = None) -> None:
        self.dataset = dataset
        self.fetcher = fetcher
        self.crawler = Crawler(fetcher)
        self.llm = llm
        self.search = search

    async def _search(self, domain: str, known: set[str]) -> tuple[list[Candidate], list[str]]:
        if self.search is None:
            return [], []
        links, email_hits = await self.search.for_domain(domain)
        cands: dict[str, Candidate] = {}
        for r in links:
            if not same_brand(r.url, domain):
                continue
            key = canonical(r.url)
            if key in known or key in cands:
                continue
            cands[key] = Candidate(url=key, text=r.title[:120],
                                   score=score_link(key, r.title), origins={"search"})
        emails = [e for r in email_hits + links if same_brand(r.url, domain)
                  for e in find_privacy_emails(f"{r.title} {r.content}", [])
                  if same_brand("https://" + e.split("@")[-1], domain)]
        ranked = sorted(cands.values(), key=lambda c: -c.score)[:VERIFY_LIMIT]
        return ranked, emails

    async def _verify(self, cands: list[Candidate], domain: str) -> list[Scored]:
        pages = await asyncio.gather(*(self.fetcher.get(c.url) for c in cands))
        out = []
        for c, page in zip(cands, pages):
            chk = to_check(c.url, page)
            if page is not None:
                c.excerpt = describe(c.url, page.url, page.status, page.text)
            if s := score(c, chk, domain):
                out.append(s)
        return out

    async def find(self, domain_or_email: str, service: str | None = None,
                   lang: str = "fr") -> DeletionLink:
        domain = normalize_domain(domain_or_email)
        hit = self.dataset.lookup(domain, service, lang)
        service = service or (hit["service"] if hit else None)
        emails: list[str] = [hit["email"]] if hit and hit.get("email") else []
        scored: list[Scored] = []

        if hit:
            ds = [Candidate(url=hit["url"], text="", score=7.0, origins={"dataset"})]
            local = localized(hit["url"], domain)
            if local:
                ds.insert(0, Candidate(url=local, text="", score=7.0, origins={"dataset", "localized"}))
            scored += await self._verify(ds, domain)
            scored.sort(key=lambda s: -s.probability)
            if scored and scored[0].kind in ("direct", "settings") \
                    and scored[0].probability >= STOP_IF_DATASET_ABOVE:
                return self._result(domain, service, scored, emails, llm_used=False)

        crawl = await self.crawler.crawl(domain)
        emails += crawl.emails
        known = {s.candidate.url for s in scored}
        to_check_list = [c for c in crawl.candidates if c.url not in known][:VERIFY_LIMIT]
        scored += await self._verify(to_check_list, domain)

        if not has_confident_link(scored):
            known = {canonical(s.candidate.url) for s in scored}
            found, search_emails = await self._search(domain, known)
            emails += search_emails
            scored += await self._verify(found, domain)

        llm_used = False
        links = [s for s in scored if s.kind in LINK_KINDS]
        if self.llm is not None and len(links) > 1:
            links.sort(key=lambda s: -s.probability)
            choice = await rank(self.llm, domain, [s.candidate for s in links], service)
            llm_used = True
            if choice:
                for s in links:
                    if s.candidate is choice.candidate:
                        s.probability = min(0.99, s.probability + LLM_BONUS * choice.confidence)
                        s.reasons.append(f"choisi par l'IA : {clean_reason(choice.reason)}")
        return self._result(domain, service, scored, emails, llm_used)

    def _result(self, domain: str, service: str | None, scored: list[Scored],
                emails: list[str], llm_used: bool) -> DeletionLink:
        email = next(iter(dict.fromkeys(e for e in emails if e)), None)
        if not scored:
            return DeletionLink(domain, service, None, "none", 0.0, False, "none", email,
                                "aucun lien fiable trouvé : utiliser la lettre RGPD")
        scored.sort(key=lambda s: -s.probability)
        best = scored[0]
        origins = best.candidate.origins
        if "dataset" in origins:
            source = "dataset"
        elif "search" in origins:
            source = "search+llm" if llm_used else "search"
        else:
            source = "crawl+llm" if llm_used else "crawl"
        alternatives = [s.candidate.url for s in scored[1:4] if s.kind in LINK_KINDS]
        return DeletionLink(
            domain=domain,
            service=service,
            url=best.candidate.url,
            kind=best.kind,
            probability=round(best.probability, 2),
            verified=best.check.reachable and not best.check.blocked,
            source=source,
            contact_email=email,
            reason=" ; ".join(best.reasons),
            confident=best.kind in LINK_KINDS and best.probability >= MIN_CONFIDENT,
            alternatives=alternatives,
        )
