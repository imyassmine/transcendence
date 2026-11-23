import httpx
import pytest

from ia.links.search import SearxClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_live_searxng_returns_results():
    client = SearxClient()
    try:
        r = await client.client.get(f"{client.base_url}/search",
                                    params={"q": "test", "format": "json"}, timeout=5)
    except httpx.HTTPError:
        await client.aclose()
        pytest.skip("SearxNG non lancé (docker compose up -d searxng)")
    if r.status_code == 403:
        await client.aclose()
        pytest.fail("format json refusé : vérifier searxng/settings.yml (search.formats)")
    results = await client.search("site:funbooker.com supprimer compte")
    await client.aclose()
    print("\n" + "\n".join(f"  {x.url} | {x.title}" for x in results[:10]))
    assert results, "aucun résultat : moteurs bloqués ou réseau du conteneur"
