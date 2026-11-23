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


from ia.links.crawler import (help_hosts_for, is_catch_all, is_sitemap_index, pick_child_sitemaps, same_brand,
                              zendesk_results)


def test_same_brand_and_help_hosts():
    assert same_brand("https://help.backmarket.com/hc/fr", "backmarket.fr")
    assert not same_brand("https://autre.com/x", "backmarket.fr")
    hosts = help_hosts_for("backmarket.fr")
    assert "help.backmarket.fr" in hosts and "help.backmarket.com" in hosts
    assert help_hosts_for("x.com").count("help.x.com") == 1


def test_sitemap_helpers():
    assert is_sitemap_index("<?xml?><sitemapindex><sitemap><loc>a</loc></sitemap></sitemapindex>")
    assert not is_sitemap_index("<urlset><url><loc>a</loc></url></urlset>")
    picked = pick_child_sitemaps(["https://x.com/sitemap-products-1.xml",
                                  "https://x.com/sitemap-help-fr.xml",
                                  "https://x.com/sitemap-blog.xml"], limit=1)
    assert picked == ["https://x.com/sitemap-help-fr.xml"]


def test_zendesk_results():
    data = '{"results": [{"html_url": "https://help.x.com/hc/fr/articles/1-Supprimer", "title": "Supprimer mon compte"}, {"title": "sans url"}]}'
    assert zendesk_results(data) == [("https://help.x.com/hc/fr/articles/1-Supprimer", "Supprimer mon compte")]
    assert zendesk_results("pas du json") == []
    assert zendesk_results("[1]") == []


DEEP = {
    ("bigshop.fr", "/"): ("<a href='/fr'>Accueil</a>", "text/html"),
    ("bigshop.fr", "/robots.txt"): ("User-agent: *\nSitemap: https://bigshop.fr/sm-index.xml\n", "text/plain"),
    ("bigshop.fr", "/sm-index.xml"): ("<sitemapindex><sitemap><loc>https://bigshop.fr/sm-help.xml</loc></sitemap></sitemapindex>", "application/xml"),
    ("bigshop.fr", "/sm-help.xml"): ("<urlset><url><loc>https://bigshop.fr/fr/help/close-account</loc></url></urlset>", "application/xml"),
    ("help.bigshop.com", "/"): ("<a href='/hc/fr/categories/1'>Mon compte</a>", "text/html"),
    ("help.bigshop.com", "/api/v2/help_center/articles/search.json"): (
        '{"results": [{"html_url": "https://help.bigshop.com/hc/fr/articles/42-Supprimer-mon-compte", "title": "Supprimer mon compte"}]}',
        "application/json"),
}


def deep_handler(r: httpx.Request) -> httpx.Response:
    hit = DEEP.get((r.url.host, r.url.path))
    if hit is None:
        return httpx.Response(404, text="", headers={"content-type": "text/html"})
    body, ctype = hit
    return httpx.Response(200, text=body, headers={"content-type": ctype})


async def test_crawl_follows_robots_sitemap_index():
    urls = [c.url for c in (await crawler(deep_handler).crawl("bigshop.fr")).candidates]
    assert "https://bigshop.fr/fr/help/close-account" in urls


async def test_crawl_help_subdomain_and_zendesk_search():
    res = await crawler(deep_handler).crawl("bigshop.fr")
    z = [c for c in res.candidates if "zendesk" in c.origins]
    assert z and z[0].url == "https://help.bigshop.com/hc/fr/articles/42-Supprimer-mon-compte"
    assert z[0].text == "Supprimer mon compte"
    assert any("help" in c.origins for c in res.candidates)



def test_is_catch_all():
    from ia.links.fetcher import Page
    assert is_catch_all(Page("https://x.com/abc-page-inexistante", 200, ""), "/abc-page-inexistante")
    assert not is_catch_all(Page("https://x.com/abc", 404, ""), "/abc")
    assert not is_catch_all(Page("https://x.com/", 200, ""), "/abc")
    assert not is_catch_all(None, "/abc")


async def test_catch_all_site_ignores_probes():
    def everything_200(r):
        return httpx.Response(200, text="<div id='app'></div>", headers={"content-type": "text/html"})
    res = await crawler(everything_200).crawl("spa.example.com")
    assert not any("probe" in c.origins for c in res.candidates)
