import httpx
import pytest

from ia.letters import LetterGenerator, LetterRequest
from ia.llm import OllamaClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_live_letter_is_written_by_llm():
    llm = OllamaClient()
    try:
        r = await llm.client.get(f"{llm.base_url}/api/tags", timeout=2)
        r.raise_for_status()
    except httpx.HTTPError:
        await llm.aclose()
        pytest.skip("Ollama non lancé")
    req = LetterRequest(full_name="Jean Dupont", account_email="jean.dupont@gmail.com",
                        service_name="Funbooker", domain="funbooker.com", breached=True)
    letter = await LetterGenerator(llm).generate(req)
    await llm.aclose()
    print(f"\n[{letter.generated_by}] {letter.warnings}\nObjet : {letter.subject}\n\n{letter.body}")
    assert "Jean Dupont" in letter.body and "article 17" in letter.body.lower()
    assert "je retire mon consentement" in letter.body
    assert "CNIL" in letter.body and "d'un mois" in letter.body
    assert letter.generated_by == "llm", f"paragraphe IA rejeté : {letter.warnings}"
