import httpx
import pytest

from ia.links.crawler import Candidate
from ia.links.ranker import rank
from ia.llm import OllamaClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def llm():
    c = OllamaClient()
    try:
        r = await c.client.get(f"{c.base_url}/api/tags", timeout=2)
        models = [m["name"] for m in r.json().get("models", [])]
    except (httpx.HTTPError, ValueError):
        await c.aclose()
        pytest.skip("Ollama non lancé (docker compose up -d)")
    if c.model not in models:
        await c.aclose()
        pytest.skip(f"modèle {c.model} absent (docker compose up ollama-pull)")
    yield c
    await c.aclose()


CANDS = [Candidate("https://shop.example.com/legal/privacy", "Politique de confidentialité", 2),
         Candidate("https://shop.example.com/login", "Se connecter", 0),
         Candidate("https://shop.example.com/help/delete-my-account", "", 7),
         Candidate("https://shop.example.com/account/settings", "Paramètres du compte", 2)]


async def test_live_rank_picks_deletion_page(llm):
    choice = await rank(llm, "shop.example.com", CANDS, "Shop")
    assert choice is not None
    assert choice.candidate.url.endswith("/help/delete-my-account")


async def test_live_rank_none_when_irrelevant(llm):
    noise = [Candidate("https://shop.example.com/blog", "Blog", 0),
             Candidate("https://shop.example.com/careers", "Recrutement", 0)]
    assert await rank(llm, "shop.example.com", noise, "Shop") is None
