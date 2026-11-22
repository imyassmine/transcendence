"""Évaluation du dataset JustDeleteMe sur le jeu de test réel.

Rapport :  uv run pytest tests/test_coverage.py -q
"""

import csv
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from ia.links.dataset import DeletionDataset
from ia.links.domains import normalize_domain

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "ia" / "links" / "data" / "jdm_sites.json"
TESTSET = Path(__file__).parent / "data" / "testset.csv"
CATEGORIES = ("hit_ok", "hit_diff", "miss", "miss_ok")

# garde-fous anti-régression : à remonter quand ça s'améliore
MIN_COVERAGE = 0.60   # trouvé / total
MIN_PRECISION = 0.65  # hit_ok / trouvé


# ------------------------------------------------------------------ helpers d'éval

def same_page(a: str, b: str) -> bool:
    if not a or not b:
        return False
    pa, pb = urlsplit(a), urlsplit(b)
    return (normalize_domain(pa.hostname or "") == normalize_domain(pb.hostname or "")
            and pa.path.lower().rstrip("/") == pb.path.lower().rstrip("/"))


def valid_urls(row: dict) -> list[str]:
    return [u.strip() for u in row.get("valid_urls", "").split("|") if u.strip()]


def classify(row: dict, hit: dict | None) -> str:
    if hit is None:
        return "miss_ok" if row["type"] in ("none", "email_only") else "miss"
    ok = any(same_page(u, hit["url"]) for u in valid_urls(row))
    return "hit_ok" if ok else "hit_diff"


def evaluate(csv_path: Path, ds: DeletionDataset) -> dict[str, list[dict]]:
    res: dict[str, list[dict]] = {c: [] for c in CATEGORIES}
    with open(csv_path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            hit = ds.lookup(row["domain"], row["service"])
            if hit:
                row["dataset_url"] = hit["url"]
            res[classify(row, hit)].append(row)
    return res


def metrics(res: dict[str, list[dict]]) -> tuple[int, float, float]:
    total = sum(len(v) for v in res.values())
    found = len(res["hit_ok"]) + len(res["hit_diff"])
    coverage = found / total if total else 0.0
    precision = len(res["hit_ok"]) / found if found else 0.0
    return total, coverage, precision


def report(res: dict[str, list[dict]]) -> str:
    total, coverage, precision = metrics(res)
    found = len(res["hit_ok"]) + len(res["hit_diff"])
    lines = ["", f"Total : {total}",
             f"Couverture : {found}/{total} ({100 * coverage:.1f} %)",
             f"Précision  : {len(res['hit_ok'])}/{found} ({100 * precision:.1f} %)"]
    lines += [f"  {c:<9}: {len(res[c])}" for c in CATEGORIES]
    if res["hit_diff"]:
        lines.append("\nÀ vérifier (hit_diff) :")
        for r in res["hit_diff"]:
            lines.append(f"  {r['domain']:<20} valides={r['valid_urls'] or '-'}")
            lines.append(f"  {'':<20} dataset={r['dataset_url']}")
    if res["miss"]:
        lines.append("\nNon couverts (miss) -> travail du crawler :")
        lines += [f"  {r['domain']}" for r in res["miss"]]
    return "\n".join(lines)


# ------------------------------------------------------------------ tests unitaires des helpers

def test_same_page():
    assert same_page("https://www.netflix.com/account/", "http://netflix.com/account")
    assert same_page("https://x.com/Delete#top", "https://x.com/delete")
    assert not same_page("https://x.com/account", "https://x.com/account/delete")
    assert not same_page("https://a.com/x", "https://b.com/x")
    assert not same_page("", "https://x.com/")


def test_valid_urls():
    expected = ["https://a.com/x", "https://b.com/y"]
    assert valid_urls({"valid_urls": "https://a.com/x | https://b.com/y"}) == expected
    assert valid_urls({"valid_urls": ""}) == []


HIT = {"service": "X", "url": "https://x.com/delete"}


def row(urls="", type_="direct"):
    return {"domain": "x.com", "service": "X", "valid_urls": urls, "type": type_}


def test_classify():
    assert classify(row("https://www.x.com/delete/"), HIT) == "hit_ok"
    assert classify(row("https://x.com/help|https://x.com/delete"), HIT) == "hit_ok"
    assert classify(row("https://x.com/settings"), HIT) == "hit_diff"
    assert classify(row("https://x.com/delete"), None) == "miss"
    assert classify(row("", "none"), None) == "miss_ok"
    assert classify(row("", "email_only"), None) == "miss_ok"


def test_evaluate_fake(tmp_path: Path):
    f = tmp_path / "t.csv"
    f.write_text("domain,service,valid_urls,type\n"
                 "x.com,X,https://x.com/delete,direct\n"
                 "y.com,Y,https://y.com/new,help\n"
                 "z.com,Z,https://z.com/delete,direct\n"
                 "w.com,W,,none\n", encoding="utf-8")
    ds = DeletionDataset([{"name": "X", "url": "https://x.com/delete", "domains": ["x.com"]},
                          {"name": "Y", "url": "https://y.com/old", "domains": ["y.com"]}])
    res = evaluate(f, ds)
    got = {c: [r["domain"] for r in v] for c, v in res.items()}
    assert got == {"hit_ok": ["x.com"], "hit_diff": ["y.com"],
                   "miss": ["z.com"], "miss_ok": ["w.com"]}
    assert metrics(res) == (4, 0.5, 0.5)


# ------------------------------------------------------------------ éval sur le vrai jeu de test

def test_dataset_coverage_report(capsys):
    if not TESTSET.exists():
        pytest.skip(f"{TESTSET} absent")
    res = evaluate(TESTSET, DeletionDataset.from_file(DATASET))
    with capsys.disabled():
        print(report(res))
    total, coverage, precision = metrics(res)
    assert total >= 20
    assert coverage >= MIN_COVERAGE
    assert precision >= MIN_PRECISION