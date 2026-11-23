import asyncio
import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

Message = dict[str, str]

RETRY_STATUS = {429, 500, 502, 503, 504}
NUM_CTX = 4096


class LLMError(Exception):
    pass


def _env_bool(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    return value.strip().lower() in ("1", "true", "yes", "on")


class OllamaClient:
    def __init__(self, base_url: str | None = None, model: str | None = None,
                 client: httpx.AsyncClient | None = None,
                 timeout: float = 300.0, retries: int = 2, backoff: float = 0.5,
                 think: bool | None = None) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.think = think if think is not None else _env_bool("OLLAMA_THINK")
        self.retries = retries
        self.backoff = backoff
        self.client = client or httpx.AsyncClient(timeout=timeout)

    def _payload(self, messages: list[Message], stream: bool, temperature: float,
                 schema: dict[str, Any] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature, "num_ctx": NUM_CTX},
        }
        if schema is not None:
            body["format"] = schema
        if self.think is not None:
            body["think"] = self.think
        return body

    async def chat(self, messages: list[Message], schema: dict[str, Any] | None = None,
                   temperature: float = 0.0) -> str:
        payload = self._payload(messages, False, temperature, schema)
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                r = await self.client.post(f"{self.base_url}/api/chat", json=payload)
                if r.status_code in RETRY_STATUS:
                    last = LLMError(f"HTTP {r.status_code}")
                else:
                    r.raise_for_status()
                    return r.json()["message"]["content"]
            except (httpx.TransportError, httpx.TimeoutException) as e:
                last = e
            except (httpx.HTTPStatusError, KeyError, TypeError, ValueError) as e:
                raise LLMError(f"réponse invalide : {e}") from e
            if attempt < self.retries:
                await asyncio.sleep(self.backoff * 2 ** attempt)
        raise LLMError(f"LLM injoignable : {last}")

    async def chat_json(self, messages: list[Message], schema: dict[str, Any],
                        temperature: float = 0.0) -> dict[str, Any]:
        raw = await self.chat(messages, schema=schema, temperature=temperature)
        try:
            data = json.loads(raw)
        except ValueError as e:
            raise LLMError(f"JSON invalide : {raw[:200]!r}") from e
        if not isinstance(data, dict):
            raise LLMError("le JSON n'est pas un objet")
        return data

    async def stream(self, messages: list[Message], temperature: float = 0.4) -> AsyncIterator[str]:
        payload = self._payload(messages, True, temperature)
        try:
            async with self.client.stream("POST", f"{self.base_url}/api/chat", json=payload) as r:
                if r.status_code != 200:
                    raise LLMError(f"HTTP {r.status_code}")
                async for line in r.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except ValueError:
                        continue
                    if text := chunk.get("message", {}).get("content"):
                        yield text
                    if chunk.get("done"):
                        break
        except (httpx.TransportError, httpx.TimeoutException) as e:
            raise LLMError(f"stream interrompu : {e}") from e

    async def aclose(self) -> None:
        await self.client.aclose()
