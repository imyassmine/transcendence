import httpx
import pytest

from ia.links.crawler import Candidate
from ia.links.evidence import describe, enrich, excerpt, is_login_url, page_text
from ia.links.fetcher import SafeFetcher

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_page_text_skips_scripts_and_reads_title():
    html = ("<html><head><title> Aide  Shop </title><style>.a{}</style></head>"
            "<body><script>var x = 'delete';</script><h1>Supprimer\n votre compte</h1></body></html>")
    assert page_text(html) == ("Aide Shop", "Supprimer votre compte")


def test_page_text_malformed():
    assert page_text("<div><p>ok<<<</span>")[1].startswith("ok")


def test_excerpt_centers_on_deletion_keyword():
    text = "x" * 1000 + " Pour supprimer votre compte, allez dans Paramètres. " + "y" * 1000
    ex = excerpt(text, 300)
    assert "supprimer votre compte" in ex and len(ex) == 300


def test_excerpt_without_keyword_takes_start():
    assert excerpt("Bienvenue sur notre site " * 50, 50) == ("Bienvenue sur notre site " * 50)[:50]


def test_is_login_url():
    assert is_login_url("https://x.com/fr/login?next=/account")
    assert is_login_url("https://x.com/connexion")
    assert not is_login_url("https://x.com/account/settings")


def test_describe_redirect_to_login():
    d = describe("https://x.com/dashboard/profile", "https://x.com/login",
                 200, "<title>Connexion</title><p>Se connecter</p>")
    assert d.startswith("[redirige vers la page de connexion")
    assert "titre : Connexion" in d


def test_describe_error_and_empty():
    assert describe("https://x.com/a", "https://x.com/a", 404, "") == "[erreur HTTP 404]"
    assert describe("https://x.com/a", "https://x.com/a", 200,
                    "<div id='root'></div>") == "[page vide ou générée en JavaScript]"


SITE = {
    "/help/delete": "<title>Supprimer mon compte</title><p>Pour supprimer votre compte, cliquez ici.</p>",
    "/dashboard/profile": None,
    "/login": "<title>Connexion</title><p>Se connecter</p>",
}


def handler(r: httpx.Request) -> httpx.Response:
    if r.url.path == "/dashboard/profile":
        return httpx.Response(302, headers={"location": "/login"})
    body = SITE.get(r.url.path)
    if body is None:
        return httpx.Response(404, text="", headers={"content-type": "text/html"})
    return httpx.Response(200, text=body, headers={"content-type": "text/html"})


async def public(host):
    return ["93.184.216.34"]


async def test_enrich_sets_excerpts_on_top_candidates_only():
    f = SafeFetcher(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)), resolver=public)
    cands = [Candidate("https://x.com/help/delete", "", 7),
             Candidate("https://x.com/dashboard/profile", "", 2),
             Candidate("https://x.com/missing", "", 2),
             Candidate("https://x.com/never", "", 1)]
    await enrich(f, cands, limit=3)
    assert "supprimer votre compte" in cands[0].excerpt.lower()
    assert cands[1].excerpt.startswith("[redirige vers la page de connexion")
    assert cands[2].excerpt == "[erreur HTTP 404]"
    assert cands[3].excerpt == ""
