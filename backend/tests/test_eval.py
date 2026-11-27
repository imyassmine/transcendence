import csv
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest

from ia.letters import LetterGenerator, LetterRequest
from ia.letters.generator import effective_grounds, validate_letter
from ia.letters.gdpr import select_refs
from ia.links.dataset import DeletionDataset
from ia.links.domains import normalize_domain
from ia.links.fetcher import SafeFetcher
from ia.links.finder import LinkFinder
from ia.links.search import SearxClient
from ia.llm import OllamaClient

pytestmark = pytest.mark.anyio

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "ia" / "links" / "data" / "jdm_sites.json"
TESTSET = Path(__file__).parent / "data" / "testset.csv"
SEARCH_CACHE = Path(__file__).parent / "data" / "search_cache.json"

MIN_CONFIRMED = 17
MIN_ACTION_RATE = 0.95


@pytest.fixture
def anyio_backend():
    return "asyncio"


def same_page(a: str, b: str) -> bool:
    if not a or not b:
        return False
    pa, pb = urlsplit(a), urlsplit(b)
    return (normalize_domain(pa.hostname or "") == normalize_domain(pb.hostname or "")
            and pa.path.lower().rstrip("/") == pb.path.lower().rstrip("/"))


def valid_urls(row: dict) -> list[str]:
    return [u.strip() for u in row.get("valid_urls", "").split("|") if u.strip()]


async def services_up(llm: OllamaClient, search: SearxClient) -> str | None:
    try:
        r = await llm.client.get(f"{llm.base_url}/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
    except (httpx.HTTPError, ValueError):
        return "Ollama non lancé : docker compose up -d"
    if llm.model not in models:
        return f"modèle {llm.model} absent : docker compose up ollama-pull"
    try:
        r = await search.client.get(f"{search.base_url}/search",
                                    params={"q": "test", "format": "json"}, timeout=5)
        r.raise_for_status()
    except httpx.HTTPError:
        return "SearxNG non lancé ou format json refusé : docker compose up -d searxng"
    return None


async def search_works(search: SearxClient) -> bool:
    if search._cache:
        return True
    try:
        r = await search.client.get(f"{search.base_url}/search",
                                    params={"q": "site:wikipedia.org rgpd", "format": "json"},
                                    timeout=15)
        return bool(r.json().get("results"))
    except (httpx.HTTPError, ValueError):
        return False


async def test_eval_20_sites():
    rows = list(csv.DictReader(open(TESTSET, encoding="utf-8")))
    fetcher, llm, search = SafeFetcher(), OllamaClient(), SearxClient(cache_file=SEARCH_CACHE)
    try:
        if reason := await services_up(llm, search):
            pytest.skip(reason)
        if not await search_works(search):
            pytest.fail("SearxNG ne renvoie aucun résultat : moteurs bloqués (captcha). "
                        "Attends ~10 min ou regarde docker compose logs searxng")
        finder = LinkFinder(DeletionDataset.from_file(DATASET), fetcher, llm, search)
        letters = LetterGenerator(llm)
        counts = {"lien_ok": 0, "lien_a_verifier": 0, "lettre": 0}
        letter_errors: list[str] = []
        by = {"llm": 0, "template": 0}
        dpo = 0
        contact = 0
        lines = []
        t0 = time.perf_counter()

        for row in rows:
            t = time.perf_counter()
            res = await finder.find(row["domain"], row["service"])
            if res.url and res.confident:
                cat = "lien_ok" if any(same_page(u, res.url) for u in valid_urls(row)) \
                    else "lien_a_verifier"
            else:
                cat = "lettre"
            counts[cat] += 1
            t_link = time.perf_counter() - t

            t = time.perf_counter()
            recipient, page = (res.contact_email, None) if res.contact_email \
                else await finder.find_contact(row["domain"], row["service"])
            req = LetterRequest(full_name="Jean Dupont", account_email="jean.dupont@gmail.com",
                                service_name=res.service or row["service"],
                                domain=row["domain"], recipient_email=recipient,
                                contact_url=page, breached=True)
            letter = await letters.generate(req)
            t_letter = time.perf_counter() - t
            keys = select_refs(effective_grounds(req), req.data_public)
            if problems := validate_letter(letter.body, req, keys):
                letter_errors.append(f"{row['domain']} : {problems}")
            by[letter.generated_by] += 1
            dpo += bool(recipient)
            contact += bool(recipient or page)
            lines.append(f"{cat:<16} {row['domain']:<18} {res.kind:<9} p={res.probability:<5} "
                         f"lien {t_link:5.1f}s  lettre[{letter.generated_by}] {t_letter:4.1f}s  "
                         f"{res.url or '-'}"
                         + (f"\n{'':<17}DPO={recipient}" if recipient
                            else f"\n{'':<17}envoyer via : {page}" if page
                            else f"\n{'':<17}destinataire non trouvé")
                         + "".join(f"\n{'':<17}rejet IA : {w}" for w in letter.warnings))
    finally:
        await fetcher.aclose()
        await llm.aclose()
        await search.aclose()

    total = len(rows)
    links = counts["lien_ok"] + counts["lien_a_verifier"]
    actions = links + counts["lettre"]
    print("\n" + "\n".join(lines))
    print(f"\n{total} sites en {time.perf_counter() - t0:.0f}s")
    print(f"Lien confirmé           : {counts['lien_ok']}/{total}")
    print(f"Lien à vérifier         : {counts['lien_a_verifier']}/{total}")
    print(f"Lettre RGPD             : {counts['lettre']}/{total}")
    print(f"Action utile            : {actions}/{total} ({100 * actions / total:.0f} %)")
    print(f"Lettres générées        : {total - len(letter_errors)}/{total} valides "
          f"(paragraphe IA : {by['llm']}, modèle fixe : {by['template']})")
    print(f"E-mail DPO trouvé       : {dpo}/{total}")
    print(f"Où envoyer (e-mail/page): {contact}/{total}")
    for e in letter_errors:
        print(f"  lettre invalide -> {e}")

    assert total == 20
    assert not letter_errors
    assert by["llm"] + by["template"] == total
    assert counts["lien_ok"] >= MIN_CONFIRMED
    assert actions / total >= MIN_ACTION_RATE
