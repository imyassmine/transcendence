import httpx
import pytest
from fastapi import FastAPI

from ia.api import build_services, get_user_key, router
from ia.letters import LetterGenerator
from ia.links.finder import DeletionLink

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeFinder:
    def __init__(self):
        self.calls = []

    async def find(self, domain, service=None, lang="fr"):
        self.calls.append(domain)
        return DeletionLink(domain=domain, service=service or "Shop",
                            url=f"https://{domain}/account/delete", kind="direct",
                            probability=0.95, verified=True, source="dataset",
                            contact_email=f"dpo@{domain}", reason="test", confident=True)


def make_app(link_rate=60, letter_rate=10):
    app = FastAPI()
    app.include_router(router)
    finder = FakeFinder()
    ia = build_services(finder, LetterGenerator(None))
    ia.link_limiter.max_calls = link_rate
    ia.letter_limiter.max_calls = letter_rate
    app.state.ia = ia
    return app, finder


def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


LETTER = {"full_name": "Jean Dupont", "account_email": "jean@gmail.com",
          "service_name": "Shop", "domain": "shop.fr"}


async def test_link_returns_result_and_caches():
    app, finder = make_app()
    async with client(app) as c:
        r1 = await c.get("/ia/link", params={"account": "noreply@mail.shop.fr"})
        r2 = await c.get("/ia/link", params={"account": "mail.shop.fr"})
        r3 = await c.get("/ia/link", params={"account": "mail.shop.fr", "refresh": "true"})
    assert r1.status_code == 200
    body = r1.json()
    assert body["url"] == "https://mail.shop.fr/account/delete"
    assert body["confident"] is True and body["cached"] is False
    assert r2.json()["cached"] is True
    assert r3.json()["cached"] is False
    assert finder.calls == ["mail.shop.fr", "mail.shop.fr"]


@pytest.mark.parametrize("account", ["localhost", "127.0.0.1", "co.uk", "pas un domaine", "ab"])
async def test_link_rejects_invalid_accounts(account):
    app, _ = make_app()
    async with client(app) as c:
        r = await c.get("/ia/link", params={"account": account})
    assert r.status_code == 422


async def test_link_rate_limited():
    app, _ = make_app(link_rate=2)
    async with client(app) as c:
        codes = [(await c.get("/ia/link", params={"account": f"site{i}.fr"})).status_code
                 for i in range(3)]
        cached = await c.get("/ia/link", params={"account": "site0.fr"})
        r = await c.get("/ia/link", params={"account": "site9.fr"})
    assert codes == [200, 200, 429]
    assert cached.status_code == 200
    assert r.status_code == 429 and int(r.headers["retry-after"]) >= 1


async def test_rate_limit_is_per_user():
    app, _ = make_app(link_rate=1)
    users = iter(["alice", "bob"])
    app.dependency_overrides[get_user_key] = lambda: next(users)
    async with client(app) as c:
        a = await c.get("/ia/link", params={"account": "a.fr"})
        b = await c.get("/ia/link", params={"account": "b.fr"})
    assert a.status_code == 200 and b.status_code == 200


async def test_letter_non_stream():
    app, _ = make_app()
    async with client(app) as c:
        r = await c.post("/ia/letter", params={"stream": "false"}, json=LETTER)
    assert r.status_code == 200
    body = r.json()
    assert "Jean Dupont" in body["body"] and body["generated_by"] == "template"


async def test_letter_stream_sse():
    app, _ = make_app()
    async with client(app) as c:
        r = await c.post("/ia/letter", json=LETTER)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    assert "event: meta" in r.text and "event: done" in r.text


async def test_letter_uses_cached_dpo_email():
    app, _ = make_app()
    async with client(app) as c:
        await c.get("/ia/link", params={"account": "shop.fr"})
        r = await c.post("/ia/letter", params={"stream": "false"}, json=LETTER)
    assert r.json()["recipient_email"] == "dpo@shop.fr"


async def test_letter_validation_error():
    app, _ = make_app()
    async with client(app) as c:
        r = await c.post("/ia/letter", json=LETTER | {"account_email": "nope"})
    assert r.status_code == 422


async def test_letter_rate_limited():
    app, _ = make_app(letter_rate=1)
    async with client(app) as c:
        ok = await c.post("/ia/letter", params={"stream": "false"}, json=LETTER)
        ko = await c.post("/ia/letter", params={"stream": "false"}, json=LETTER)
    assert ok.status_code == 200 and ko.status_code == 429
