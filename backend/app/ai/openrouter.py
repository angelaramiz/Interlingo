import json
import logging
import re
import time

import httpx

from ..config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

log = logging.getLogger("interlingo.ai")

_RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("openrouter: no JSON object in response")
    return json.loads(cleaned[start : end + 1])


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        fallback_models: list[str] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        backoff_base: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.model = model or settings.openrouter_model
        if fallback_models is None:
            raw = settings.openrouter_fallback_models.strip()
            fallback_models = [m.strip() for m in raw.split(",") if m.strip()]
        self.fallback_models = list(fallback_models)
        self.timeout = settings.openrouter_timeout if timeout is None else timeout
        self.max_retries = (
            settings.openrouter_max_retries if max_retries is None else max_retries
        )
        self.backoff_base = backoff_base
        self._transport = transport
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            kwargs: dict = {"timeout": self.timeout}
            if self._transport is not None:
                kwargs["transport"] = self._transport
            self._client = httpx.Client(**kwargs)
        return self._client

    def _request(self, model: str, messages: list[dict]) -> dict:
        resp = self._get_client().post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return _extract_json(content)

    def chat_json(self, messages: list[dict]) -> dict:
        last_exc: Exception | None = None
        for model in [self.model, *self.fallback_models]:
            for attempt in range(1, self.max_retries + 1):
                try:
                    return self._request(model, messages)
                except httpx.HTTPStatusError as e:
                    last_exc = e
                    status = e.response.status_code
                    if status == 404:
                        log.warning("openrouter model %s not found, trying fallback", model)
                        break
                    if status not in _RETRYABLE_STATUS:
                        raise
                except (httpx.TimeoutException, httpx.TransportError, ValueError) as e:
                    last_exc = e
                if attempt < self.max_retries:
                    delay = self.backoff_base * (2 ** (attempt - 1))
                    log.warning(
                        "openrouter %s attempt %d failed (%s), retry in %.1fs",
                        model, attempt, last_exc, delay,
                    )
                    if delay > 0:
                        time.sleep(delay)
        assert last_exc is not None
        raise last_exc


openrouter = OpenRouterClient()
