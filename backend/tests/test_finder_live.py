import csv
import os
import time
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from ia.links.dataset import DeletionDataset
from ia.links.domains import normalize_domain
from ia.links.fetcher import SafeFetcher
from ia.links.finder import LINK_KINDS, LinkFinder
from ia.links.search import SearxClient
from ia.llm import OllamaClient

pytestmark = [pytest.mark.anyio,
              pytest.mark.skipif(os.getenv("RUN_LIVE_EVAL") != "1",
                                 reason="éval réelle : RUN_LIVE_EVAL=1 uv run pytest tests/test_finder_live.py -s")]

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "ia" / "links" / "data" / "jdm_sites.json"
TESTSET = Path(__file__).parent / "data" / "testset.csv"


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


def category(row: dict, res) -> str:
    if res.url and res.confident:
        if any(same_page(u, res.url) for u in valid_urls(row)):
            return "lien_ok"
        return "lien_a_verifier"
    if res.contact_email:
        return "lettre"
    if res.url:
        return "lien_faible"
    return "rien"


async def test_finder_live_eval():
    rows = list(csv.DictReader(open(TESTSET, encoding="utf-8")))
    fetcher, llm, search = SafeFetcher(), OllamaClient(), SearxClient()
    finder = LinkFinder(DeletionDataset.from_file(DATASET), fetcher, llm, search)
    counts: dict[str, int] = {}
    lines = []
    t0 = time.perf_counter()
    try:
        for row in rows:
            t = time.perf_counter()
            res = await finder.find(row["domain"], row["service"])
            cat = category(row, res)
            counts[cat] = counts.get(cat, 0) + 1
            lines.append(f"{cat:<16} {row['domain']:<18} {res.kind:<9} p={res.probability:<5} "
                         f"{time.perf_counter() - t:5.1f}s  {res.url or '-'}"
                         + "".join(f"\n{'':<17}alt={a}" for a in res.alternatives)
                         + (f"\n{'':<17}DPO={res.contact_email}" if res.contact_email else "")
                         + (f"\n{'':<17}{res.reason}" if res.reason else ""))
    finally:
        await fetcher.aclose()
        await llm.aclose()
        await search.aclose()

    total = len(rows)
    links = counts.get("lien_ok", 0) + counts.get("lien_a_verifier", 0)
    actions = links + counts.get("lettre", 0)
    print("\n" + "\n".join(lines))
    print(f"\nTotal {total} sites en {time.perf_counter() - t0:.0f}s")
    print(f"Lien de suppression trouvé : {links}/{total} ({100 * links / total:.0f} %)")
    print(f"  dont confirmé par testset : {counts.get('lien_ok', 0)}")
    print(f"Action utile (lien ou lettre) : {actions}/{total} ({100 * actions / total:.0f} %)")
    for k in ("lien_ok", "lien_a_verifier", "lettre", "lien_faible", "rien"):
        print(f"  {k:<16}: {counts.get(k, 0)}")
    assert total >= 20
