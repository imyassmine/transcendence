import json

import httpx
import pytest

from ia.links.crawler import Candidate
from ia.links.dataset import DeletionDataset
from ia.links.fetcher import Page, SafeFetcher
from ia.links.finder import (Check, LinkFinder, classify, clean_reason, domain_penalty, is_forum,
                             is_search_page, is_soft_404, is_user_content_host, localized,
                             path_has_words, score, to_check)
from ia.llm import OllamaClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def html(body, status=200, **headers):
    return httpx.Response(status, text=body, headers={"content-type": "text/html", **headers})


async def public(host):
    return ["93.184.216.34"]


def make_finder(routes, entries=(), llm=None, log=None):
    def handler(r: httpx.Request) -> httpx.Response:
        if log is not None:
            log.append(f"{r.url.host}{r.url.path}")
        resp = routes.get((r.url.host, r.url.path))
        if resp is None:
            return html("", 404)
        return resp() if callable(resp) else resp
    fetcher = SafeFetcher(client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
                          resolver=public)
    return LinkFinder(DeletionDataset(list(entries)), fetcher, llm)


def fake_llm(index, confidence=0.9):
    content = json.dumps({"index": index, "confidence": confidence, "reason": "test"})
    resp = httpx.Response(200, json={"message": {"content": content}, "done": True})
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: resp))
    return OllamaClient(base_url="http://ollama:11434", model="t", client=http, backoff=0)


DELETE_PAGE = html("<title>Supprimer mon compte</title><p>Pour supprimer votre compte cliquez ici</p>")


# ------------------------------------------------------------------ fonctions pures

def chk(url, final=None, status=200, title="", text="", login=False, blocked=False, reachable=True):
    return Check(url, final or url, status, reachable, blocked, login, title, text)


def test_is_soft_404():
    assert is_soft_404("Page introuvable | Shop", "x" * 1000)
    assert is_soft_404("Shop", "Oups, cette page n'existe pas.")
    assert not is_soft_404("Supprimer mon compte", "Pour supprimer votre compte " + "x" * 1000)


def test_to_check_detects_login_404_blocked():
    assert to_check("https://x.com/a", None).reachable is False
    assert to_check("https://x.com/a", Page("https://x.com/a", 404, "")).reachable is False
    c = to_check("https://x.com/account", Page("https://x.com/login", 200, "<title>Connexion</title>"))
    assert c.login and c.reachable
    assert to_check("https://x.com/a", Page("https://x.com/a", 401, "")).login
    b = to_check("https://x.com/a", Page("https://x.com/a", 403, ""))
    assert b.blocked and not b.reachable
    s = to_check("https://x.com/a", Page("https://x.com/a", 200, "<title>Erreur 404</title>"))
    assert not s.reachable


def test_classify_kinds():
    c = Candidate("u")
    assert classify(c, chk("https://x.com/account/delete"))[0] == "direct"
    assert classify(c, chk("https://x.com/hc/fr/articles/1-supprimer-mon-compte"))[0] == "help"
    assert classify(c, chk("https://x.com/settings", text="Supprimer le compte"))[0] == "settings"
    assert classify(c, chk("https://x.com/settings")) == ("settings", 0.5)
    assert classify(c, chk("https://x.com/Account", "https://x.com/login", login=True))[0] == "settings"
    assert classify(c, chk("https://x.com/privacy/data-deletion", "https://x.com/signin", login=True))[0] == "direct"
    assert classify(c, chk("https://x.com/legal/privacy"))[0] == "privacy"
    assert classify(c, chk("https://x.com/blog"))[0] is None
    assert classify(c, chk("https://x.com/account/delete", status=404, reachable=False))[0] is None


def test_domain_penalty():
    assert domain_penalty("https://help.x.fr/a", "x.fr") == (0.0, None)
    assert domain_penalty("https://www.amazon.com/a", "amazon.fr")[0] == 0.10
    assert domain_penalty("https://www.doctolib.de/a", "doctolib.fr")[0] == 0.40
    assert domain_penalty("https://autre.com/a", "x.fr")[0] == 1.0


def test_score_ordering():
    direct = score(Candidate("u", score=7), chk("https://x.fr/account/delete"), "x.fr")
    settings = score(Candidate("u", score=2), chk("https://x.fr/account", "https://x.fr/login", login=True), "x.fr")
    privacy = score(Candidate("u", score=2), chk("https://x.fr/legal/privacy"), "x.fr")
    blocked = score(Candidate("u", score=7), chk("https://x.fr/account/delete", status=403,
                                                 blocked=True, reachable=False), "x.fr")
    assert direct.probability > settings.probability > privacy.probability
    assert blocked.probability < direct.probability
    assert score(Candidate("u"), chk("https://autre.com/account/delete"), "x.fr") is None


# ------------------------------------------------------------------ finder complet

ENTRY = {"name": "Shop", "url": "https://shopfr.fr/account/delete", "domains": ["shopfr.fr"],
         "email": "dpo@shopfr.fr"}


async def test_dataset_link_verified_returns_without_crawl():
    log = []
    f = make_finder({("shopfr.fr", "/account/delete"): DELETE_PAGE}, [ENTRY], log=log)
    res = await f.find("noreply@mail.shopfr.fr")
    assert res.url == "https://shopfr.fr/account/delete"
    assert res.kind == "direct" and res.source == "dataset" and res.verified
    assert res.contact_email == "dpo@shopfr.fr" and res.service == "Shop"
    assert "shopfr.fr/robots.txt" not in log


async def test_dataset_404_falls_back_to_crawl():
    routes = {
        ("shopfr.fr", "/"): html("<a href='/aide/fermer-mon-compte'>Fermer mon compte</a>"),
        ("shopfr.fr", "/aide/fermer-mon-compte"): html("<title>Fermer mon compte</title>" + "<p>x</p>" * 200),
    }
    res = await make_finder(routes, [ENTRY]).find("shopfr.fr")
    assert res.url == "https://shopfr.fr/aide/fermer-mon-compte"
    assert res.kind == "help" and res.source == "crawl"


async def test_soft_404_rejected():
    routes = {("shopfr.fr", "/account/delete"): html("<title>Page introuvable</title><p>Oups</p>")}
    res = await make_finder(routes, [ENTRY]).find("shopfr.fr")
    assert res.url is None and res.kind == "none"
    assert res.contact_email == "dpo@shopfr.fr"


async def test_account_page_behind_login_is_settings():
    routes = {
        ("shopfr.fr", "/"): html("<a href='https://secure.shopfr.fr/Account'>Mon compte</a>"),
        ("secure.shopfr.fr", "/Account"): httpx.Response(302, headers={"location": "/login"}),
        ("secure.shopfr.fr", "/login"): html("<title>Connexion</title><p>Se connecter</p>"),
    }
    res = await make_finder(routes).find("shopfr.fr")
    assert res.kind == "settings"
    assert res.url == "https://secure.shopfr.fr/Account"
    assert "connectés" in res.reason


async def test_other_country_dataset_loses_to_local_page():
    entry = dict(ENTRY, url="https://www.shopfr.de/account/edit")
    routes = {
        ("www.shopfr.de", "/account/edit"): html("<p>Konto</p>"),
        ("shopfr.fr", "/"): html("<a href='/compte/supprimer'>Supprimer mon compte</a>"),
        ("shopfr.fr", "/compte/supprimer"): DELETE_PAGE,
    }
    res = await make_finder(routes, [entry]).find("shopfr.fr")
    assert res.url == "https://shopfr.fr/compte/supprimer"


async def test_nothing_found_gives_none_with_email():
    routes = {
        ("shopfr.fr", "/"): html("<a href='/blog'>Blog</a><a href='mailto:rgpd@shopfr.fr'>RGPD</a>"),
    }
    res = await make_finder(routes).find("shopfr.fr")
    assert res.kind == "none" and res.url is None
    assert res.contact_email == "rgpd@shopfr.fr"


async def test_llm_choice_breaks_tie():
    page = html("<title>Aide</title>" + "<p>x</p>" * 200)
    routes = {
        ("shopfr.fr", "/"): html("<a href='/aide/supprimer-compte-a'>Supprimer mon compte</a>"
                                 "<a href='/aide/supprimer-compte-b'>Supprimer mon compte</a>"),
        ("shopfr.fr", "/aide/supprimer-compte-a"): page,
        ("shopfr.fr", "/aide/supprimer-compte-b"): page,
    }
    res_a = await make_finder(routes, llm=fake_llm(0)).find("shopfr.fr")
    res_b = await make_finder(routes, llm=fake_llm(1)).find("shopfr.fr")
    assert {res_a.url, res_b.url} == {"https://shopfr.fr/aide/supprimer-compte-a",
                                      "https://shopfr.fr/aide/supprimer-compte-b"}
    assert res_a.source == "crawl+llm" and "choisi par l'IA" in res_a.reason


async def test_alternatives_listed():
    routes = {
        ("shopfr.fr", "/"): html("<a href='/compte/supprimer'>Supprimer mon compte</a>"
                                 "<a href='/aide/fermer-mon-compte'>Fermer mon compte</a>"),
        ("shopfr.fr", "/compte/supprimer"): DELETE_PAGE,
        ("shopfr.fr", "/aide/fermer-mon-compte"): html("<title>Aide</title>" + "<p>x</p>" * 200),
    }
    res = await make_finder(routes).find("shopfr.fr")
    assert res.url == "https://shopfr.fr/compte/supprimer"
    assert "https://shopfr.fr/aide/fermer-mon-compte" in res.alternatives



def test_regressions_from_live_eval():
    c = Candidate("u")
    bitwarden = chk("https://bitwarden.com/resources/old-delete-monitor-bitwarden-events-using-sentinel/")
    todoist = chk("https://www.todoist.com/fr/help/todoist/deletion-of-todoist-activity-history-HsK")
    turo = chk("https://help.turo.com/en_us/closing-your-account-SJQn4EeEq")
    carvertical = chk("https://www.carvertical.com/help/account/how-can-i-delete-my-carvertical-account")
    amazon = chk("https://www.amazon.com/privacy/data-deletion",
                 "https://www.amazon.com/ax/claim?arb=1", login=True)
    assert classify(c, bitwarden)[0] is None
    assert classify(c, todoist)[0] is None
    assert classify(c, turo)[0] == "help"
    assert classify(c, carvertical)[0] == "help"
    assert classify(c, amazon)[0] == "direct"


def test_to_check_register_page_is_login():
    page = Page("https://www.vinted.com/member/register/select_type?ref_url=x", 200, "<title>Inscription</title>")
    assert to_check("https://www.vinted.com/member/general/delete_account", page).login


async def test_returns_original_url_not_login_redirect():
    entry = {"name": "Amz", "url": "https://amz.fr/privacy/data-deletion", "domains": ["amz.fr"]}
    routes = {
        ("amz.fr", "/privacy/data-deletion"): httpx.Response(302, headers={"location": "/ax/claim?arb=1"}),
        ("amz.fr", "/ax/claim"): html("<title>Amz Connexion</title>"),
    }
    res = await make_finder(routes, [entry]).find("amz.fr")
    assert res.url == "https://amz.fr/privacy/data-deletion"
    assert res.kind == "direct" and res.confident


async def test_weak_settings_not_confident():
    routes = {
        ("shopfr.fr", "/"): html("<a href='/myaccount'>Mon espace</a>"),
        ("shopfr.fr", "/myaccount"): html("<title>Shop</title>" + "<p>x</p>" * 200),
    }
    res = await make_finder(routes).find("shopfr.fr")
    assert res.kind == "settings" and not res.confident



def test_localized():
    assert localized("https://www.amazon.com/privacy/data-deletion", "amazon.fr") == \
        "https://www.amazon.fr/privacy/data-deletion"
    assert localized("https://www.doctolib.de/account/edit", "doctolib.fr") == \
        "https://www.doctolib.fr/account/edit"
    assert localized("https://x.fr/a", "x.fr") is None
    assert localized("https://autre.com/a", "x.fr") is None


async def test_dataset_other_tld_tries_local_domain_first():
    entry = dict(ENTRY, url="https://www.shopfr.com/account/delete")
    routes = {("www.shopfr.fr", "/account/delete"): DELETE_PAGE,
              ("www.shopfr.com", "/account/delete"): DELETE_PAGE}
    res = await make_finder(routes, [entry]).find("shopfr.fr")
    assert res.url == "https://www.shopfr.fr/account/delete"



def test_dataset_weak_settings_boost_but_not_help():
    ds = Candidate("u", score=7, origins={"dataset"})
    todoist = score(ds, chk("https://todoist.com/app/settings/account"), "todoist.com")
    sncf = score(ds, chk("https://www.sncf-connect.com/en-en/help/your-customer-account"), "sncf-connect.com")
    crawled = score(Candidate("u", score=2), chk("https://todoist.com/app/settings/account"), "todoist.com")
    assert todoist.probability >= 0.6
    assert sncf.probability < 0.6
    assert crawled.probability < 0.6



def test_search_pages_rejected():
    assert is_search_page("https://www.cdiscount.com/informatique/r-supprimer+compte.html")
    assert is_search_page("https://clients.cdiscount.com/faq.html?userinput=Compte+Client")
    assert is_search_page("https://x.com/search?q=delete")
    assert not is_search_page("https://x.com/help/delete-account")
    c = Candidate("u")
    assert classify(c, chk("https://www.cdiscount.com/informatique/r-supprimer+compte.html"))[0] is None


def test_forum_penalised_below_official_help():
    forum = score(Candidate("u", score=7), chk("https://www.jotform.com/fr/answers/43491401-supprimer-compte"), "jotform.com")
    official = score(Candidate("u", score=7), chk("https://www.jotform.com/fr/help/comment-supprimer-mon-compte"), "jotform.com")
    assert is_forum("https://www.jotform.com/answers/1-x")
    assert official.probability > forum.probability
    assert "forum" in " ".join(forum.reasons)


def test_clean_reason():
    assert clean_reason("Le lien mène à la suppression") == "Le lien mène à la suppression"
    assert clean_reason("Le lien指向直接的账户删除页面") == "raison fournie dans une autre langue"



def test_user_content_hosts_rejected():
    assert is_user_content_host("https://form.jotform.com/80184016110340", "jotform.com")
    assert is_user_content_host("https://blog.funbooker.com/x", "funbooker.com")
    assert not is_user_content_host("https://help.jotform.com/x", "jotform.com")
    assert not is_user_content_host("https://www.jotform.com/x", "jotform.com")
    form = Candidate("u", text="Delete my account", score=7)
    assert score(form, chk("https://form.jotform.com/80184016110340", title="Delete account"), "jotform.com") is None


def test_title_only_intent_penalised():
    assert not path_has_words("https://x.com/80184016110340")
    assert not path_has_words("https://x.com/p/3f2a9c1e-77aa-4b2c")
    assert path_has_words("https://x.com/fr/help/comment-supprimer-mon-compte")
    numeric = score(Candidate("u", text="Supprimer mon compte", score=7),
                    chk("https://x.com/80184016110340", title="Supprimer mon compte"), "x.com")
    words = score(Candidate("u", text="Supprimer mon compte", score=7),
                  chk("https://x.com/compte/supprimer", title="Supprimer mon compte"), "x.com")
    assert words.probability - numeric.probability >= 0.25
