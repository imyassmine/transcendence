import httpx
import pytest

from ia.links.crawler import Crawler, canonical, landed_on, same_site
from ia.links.fetcher import SafeFetcher

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


SITE = {
    "/": '<a href="/login">Se connecter</a><a href="/blog">Blog</a>'
         '<a href="https://autre-site.com/delete-account">pub</a>'
         '<a href="/legal/privacy">Politique de confidentialité</a>',
    "/sitemap.xml": "<urlset><url><loc>https://shop.example.com/help/delete-my-account</loc></url>"
                    "<url><loc>https://shop.example.com/about</loc></url></urlset>",
    "/legal/privacy": '<p>Contact DPO : <a href="mailto:dpo@shop.example.com">ici</a></p>'
                      '<a href="/account/settings">Paramètres du compte</a>',
    "/account": "<h1>Mon compte</h1>",
}


def handler(request: httpx.Request) -> httpx.Response:
    if request.url.host != "shop.example.com":
        return httpx.Response(404)
    body = SITE.get(request.url.path)
    if body is None:
        return httpx.Response(404, text="nope", headers={"content-type": "text/html"})
    ctype = "application/xml" if request.url.path.endswith(".xml") else "text/html"
    return httpx.Response(200, text=body, headers={"content-type": ctype})


async def public(host):
    return ["93.184.216.34"]


def crawler(h=handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(h))
    return Crawler(SafeFetcher(client=client, resolver=public))


def test_same_site():
    assert same_site("https://help.shop.example.com/x", "shop.example.com")
    assert same_site("https://www.netflix.com/x", "mail.netflix.com")
    assert not same_site("https://autre-site.com/x", "shop.example.com")
    assert not same_site("mailto:a@b.com", "b.com")


def test_canonical():
    assert canonical("https://X.com/a/#frag") == "https://x.com/a"
    assert canonical("https://x.com") == "https://x.com/"
    assert canonical("https://x.com/a?b=1") == "https://x.com/a?b=1"


async def test_crawl_finds_sitemap_deletion_page_first():
    res = await crawler().crawl("shop.example.com")
    assert res.candidates[0].url == "https://shop.example.com/help/delete-my-account"
    assert "sitemap" in res.candidates[0].origins


async def test_crawl_ignores_other_sites_and_noise():
    urls = [c.url for c in (await crawler().crawl("shop.example.com")).candidates]
    assert not any("autre-site.com" in u for u in urls)
    assert "https://shop.example.com/login" not in urls
    assert "https://shop.example.com/blog" not in urls


async def test_crawl_privacy_page_and_email():
    res = await crawler().crawl("shop.example.com")
    assert res.privacy_url == "https://shop.example.com/legal/privacy"
    assert res.emails == ["dpo@shop.example.com"]
    assert "https://shop.example.com/account/settings" in [c.url for c in res.candidates]


async def test_crawl_probe_only_counts_existing_pages():
    res = await crawler().crawl("shop.example.com")
    probe = {c.url for c in res.candidates if "probe" in c.origins}
    assert "https://shop.example.com/account" in probe
    assert "https://shop.example.com/account/delete" not in probe


async def test_crawl_candidates_sorted_and_positive():
    scores = [c.score for c in (await crawler().crawl("shop.example.com")).candidates]
    assert scores == sorted(scores, reverse=True)
    assert all(s > 0 for s in scores)


async def test_crawl_dead_site_returns_empty():
    def down(r):
        raise httpx.ConnectError("down")
    res = await crawler(down).crawl("dead.example.com")
    assert res.candidates == [] and res.privacy_url is None and res.emails == []


def test_landed_on():
    assert landed_on("https://x.com/account", "/account")
    assert landed_on("https://x.com/fr-fr/account/", "/account")
    assert not landed_on("https://x.com/shop?showCountrySelector=true", "/account/delete")


async def test_probe_redirected_elsewhere_is_ignored():
    def redirecting(r):
        if r.url.path == "/account/delete":
            return httpx.Response(302, headers={"location": "/shop?showCountrySelector=true"})
        if r.url.path == "/shop":
            return httpx.Response(200, text="<p>Boutique</p>", headers={"content-type": "text/html"})
        return httpx.Response(404, text="", headers={"content-type": "text/html"})
    res = await crawler(redirecting).crawl("shop.example.com")
    assert not any("showCountrySelector" in c.url for c in res.candidates)
