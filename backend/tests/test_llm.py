import json

import httpx
import pytest

from ia.links.crawler import Candidate
from ia.links.ranker import build_prompt, rank
from ia.llm import LLMError, OllamaClient

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def client(handler, **kw):
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OllamaClient(base_url="http://ollama:11434", model="test", client=http,
                        backoff=0, **kw)


def answer(content):
    return httpx.Response(200, json={"message": {"role": "assistant", "content": content},
                                     "done": True})


# ------------------------------------------------------------------ OllamaClient

async def test_chat_sends_model_schema_temperature():
    seen = {}

    def handler(r):
        seen.update(json.loads(r.content))
        seen["path"] = r.url.path
        return answer("ok")
    out = await client(handler).chat([{"role": "user", "content": "hi"}],
                                     schema={"type": "object"}, temperature=0.0)
    assert out == "ok"
    assert seen["path"] == "/api/chat"
    assert seen["model"] == "test" and seen["stream"] is False
    assert seen["format"] == {"type": "object"}
    assert seen["options"]["temperature"] == 0.0


async def test_chat_retries_then_succeeds():
    calls = {"n": 0}

    def handler(r):
        calls["n"] += 1
        return httpx.Response(503) if calls["n"] < 3 else answer("ok")
    assert await client(handler, retries=2).chat([]) == "ok"
    assert calls["n"] == 3


async def test_chat_gives_up_after_retries():
    calls = {"n": 0}

    def handler(r):
        calls["n"] += 1
        return httpx.Response(503)
    with pytest.raises(LLMError):
        await client(handler, retries=1).chat([])
    assert calls["n"] == 2


async def test_chat_network_error():
    def handler(r):
        raise httpx.ConnectError("down")
    with pytest.raises(LLMError):
        await client(handler, retries=0).chat([])


async def test_chat_bad_response():
    with pytest.raises(LLMError):
        await client(lambda r: httpx.Response(200, json={"oops": 1})).chat([])


async def test_chat_json():
    assert await client(lambda r: answer('{"index": 2}')).chat_json([], {}) == {"index": 2}
    with pytest.raises(LLMError):
        await client(lambda r: answer("pas du json")).chat_json([], {})
    with pytest.raises(LLMError):
        await client(lambda r: answer("[1, 2]")).chat_json([], {})


async def test_stream():
    lines = "\n".join(json.dumps(x) for x in [
        {"message": {"content": "Bon"}, "done": False},
        {"message": {"content": "jour"}, "done": False},
        {"message": {"content": ""}, "done": True},
    ])
    out = [t async for t in client(lambda r: httpx.Response(200, text=lines)).stream([])]
    assert "".join(out) == "Bonjour"


async def test_stream_error():
    with pytest.raises(LLMError):
        _ = [t async for t in client(lambda r: httpx.Response(500)).stream([])]


# ------------------------------------------------------------------ ranker

CANDS = [Candidate("https://x.com/legal/privacy", "Confidentialité", 2.0),
         Candidate("https://x.com/help/delete-my-account", "", 7.0),
         Candidate("https://x.com/account/settings", "Paramètres", 2.0)]


def test_build_prompt_numbers_candidates():
    p = build_prompt("x.com", CANDS, "X")
    assert "Site : X (x.com)" in p
    assert "1. https://x.com/help/delete-my-account | texte : -" in p


async def test_rank_picks_by_index():
    llm = client(lambda r: answer('{"index": 1, "confidence": 0.9, "reason": "aide suppression"}'))
    choice = await rank(llm, "x.com", CANDS)
    assert choice and choice.candidate.url == "https://x.com/help/delete-my-account"
    assert choice.confidence == 0.9 and choice.reason == "aide suppression"


@pytest.mark.parametrize("content", [
    '{"index": -1, "confidence": 0.8, "reason": "rien"}',
    '{"index": 99, "confidence": 0.8, "reason": "hors liste"}',
    '{"index": "abc", "confidence": 0.8, "reason": "x"}',
    '{"confidence": 0.8}',
    "pas du json",
])
async def test_rank_invalid_answers_give_none(content):
    assert await rank(client(lambda r: answer(content)), "x.com", CANDS) is None


async def test_rank_llm_down_gives_none():
    def down(r):
        raise httpx.ConnectError("down")
    assert await rank(client(down, retries=0), "x.com", CANDS) is None


async def test_rank_clamps_confidence():
    llm = client(lambda r: answer('{"index": 0, "confidence": 7, "reason": "x"}'))
    assert (await rank(llm, "x.com", CANDS)).confidence == 1.0


async def test_rank_no_candidates_no_call():
    def fail(r):
        raise AssertionError("ne doit pas appeler le LLM")
    assert await rank(client(fail), "x.com", []) is None
