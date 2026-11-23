import json

import httpx
import pytest

from ia.links.dataset import DeletionDataset
from ia.links.fetcher import SafeFetcher
from ia.links.finder import LinkFinder
from ia.links.search import SearxClient, parse_results

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def searx(results_by_query, calls=None):
    def handler(r: httpx.Request) -> httpx.Response:
        q = r.url.params["q"]
        if calls is not None:
            calls.append(q)
        assert r.url.params["format"] == "json"
        return httpx.Response(200, json={"results": results_by_query.get(q, [])})
    return SearxClient(base_url="http://searx:8080",
                       client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def test_parse_results():
    data = {"results": [{"url": "https://x.com/a", "title": "A", "content": "c"},
                        {"url": "javascript:alert(1)", "title": "bad"},
                        {"title": "sans url"}, "pas un dict"]}
    res = parse_results(data)
    assert [(r.url, r.title, r.content) for r in res] == [("https://x.com/a", "A", "c")]
    assert parse_results([1, 2]) == []


async def test_search_caches_queries():
    calls = []
    client = searx({"q1": [{"url": "https://x.com/a", "title": "A"}]}, calls)
    assert len(await client.search("q1")) == 1
    assert len(await client.search("q1")) == 1
    assert calls == ["q1"]


async def test_search_errors_give_empty():
    client = SearxClient(base_url="http://searx:8080", client=httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(403))))
    assert await client.search("q") == []


async def test_for_domain_uses_registrable_domain():
    calls = []
    await searx({}, calls).for_domain("mail.shopfr.fr")
    assert calls == ["site:shopfr.fr supprimer compte", "site:shopfr.fr delete account",
                     "site:shopfr.fr dpo données personnelles rgpd"]


def html(body, status=200):
    return httpx.Response(status, text=body, headers={"content-type": "text/html"})


async def public(host):
    return ["93.184.216.34"]


def finder_with(routes, search, entries=()):
    def handler(r):
        resp = routes.get((r.url.host, r.url.path))
        return resp if resp is not None else html("", 404)
    fetcher = SafeFetcher(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
                          resolver=public)
    return LinkFinder(DeletionDataset(list(entries)), fetcher, None, search)


SEARCH = {
    "site:shopfr.fr supprimer compte": [
        {"url": "https://www.shopfr.fr/page/suppression-compte", "title": "Supprimer mon compte | Shop"},
        {"url": "https://autre-site.com/supprimer-compte-shop", "title": "Comment supprimer Shop"},
        {"url": "https://www.shopfr.fr/page/dead-delete-account", "title": "Delete account"},
    ],
    "site:shopfr.fr dpo données personnelles rgpd": [
        {"url": "https://www.shopfr.fr/cgu", "title": "CGU", "content": "Contactez dpo@shopfr.fr pour vos données."},
    ],
}


async def test_finder_uses_search_when_crawl_finds_nothing():
    routes = {
        ("shopfr.fr", "/"): html("<a href='/blog'>Blog</a>"),
        ("www.shopfr.fr", "/page/suppression-compte"):
            html("<title>Supprimer mon compte</title><p>Pour supprimer votre compte, écrivez-nous.</p>"),
    }
    res = await finder_with(routes, searx(SEARCH)).find("shopfr.fr")
    assert res.url == "https://www.shopfr.fr/page/suppression-compte"
    assert res.source == "search" and res.confident
    assert res.contact_email == "dpo@shopfr.fr"
    assert all("autre-site.com" not in a for a in res.alternatives)
    assert all("dead-delete" not in a for a in res.alternatives)


async def test_finder_skips_search_when_dataset_is_confident():
    calls = []
    entry = {"name": "Shop", "url": "https://shopfr.fr/account/delete", "domains": ["shopfr.fr"]}
    routes = {("shopfr.fr", "/account/delete"): html("<title>Supprimer mon compte</title>")}
    res = await finder_with(routes, searx(SEARCH, calls), [entry]).find("shopfr.fr")
    assert res.source == "dataset" and calls == []


async def test_finder_without_search_client_still_works():
    routes = {("shopfr.fr", "/"): html("<a href='/blog'>Blog</a>")}
    res = await finder_with(routes, None).find("shopfr.fr")
    assert res.kind == "none"



async def test_search_emails_from_other_brands_ignored():
    search = searx({
        "site:shopfr.fr dpo données personnelles rgpd": [
            {"url": "https://www.shopfr.fr/jouets/playmobil", "title": "Playmobil",
             "content": "Contact DPO : dpo.f@playmobil.fr"},
            {"url": "https://www.shopfr.fr/legal", "title": "Mentions",
             "content": "Écrire à rgpd@shopfr.fr"},
        ]})
    routes = {("shopfr.fr", "/"): html("<a href='/blog'>Blog</a>")}
    res = await finder_with(routes, search).find("shopfr.fr")
    assert res.contact_email == "rgpd@shopfr.fr"
