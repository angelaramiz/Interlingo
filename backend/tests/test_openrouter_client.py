import httpx
import pytest

from app.ai.openrouter import OpenRouterClient

MSGS = [{"role": "user", "content": "hola"}]


def _ok_response(content: str) -> httpx.Response:
    return httpx.Response(
        200, json={"choices": [{"message": {"content": content}}]}
    )


def _sequence_client(responses: list, **kwargs) -> tuple:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    transport = httpx.MockTransport(handler)
    client = OpenRouterClient(
        api_key="key", model="m-primary", backoff_base=0.0, transport=transport, **kwargs
    )
    return client, calls


class TestRetries:
    def test_retries_on_500_then_succeeds(self):
        client, calls = _sequence_client(
            [
                httpx.Response(500, json={"error": "x"}),
                httpx.Response(500, json={"error": "x"}),
                _ok_response('{"a": 1}'),
            ],
            max_retries=3,
        )
        assert client.chat_json(MSGS) == {"a": 1}
        assert len(calls) == 3

    def test_raises_after_exhausting_retries(self):
        client, calls = _sequence_client(
            [httpx.Response(500, json={"error": "x"})] * 5, max_retries=2
        )
        with pytest.raises(httpx.HTTPStatusError):
            client.chat_json(MSGS)
        assert len(calls) == 2

    def test_retries_on_transport_error(self):
        client, calls = _sequence_client(
            [httpx.ConnectError("down"), _ok_response('{"a": 1}')], max_retries=2
        )
        assert client.chat_json(MSGS) == {"a": 1}
        assert len(calls) == 2


class TestFallback:
    def test_falls_back_on_unknown_model(self):
        def handler(request: httpx.Request) -> httpx.Response:
            import json as jsonlib

            model = jsonlib.loads(request.content.decode())["model"]
            if model == "m-primary":
                return httpx.Response(404, json={"error": "not found"})
            return _ok_response('{"a": 2}')

        transport = httpx.MockTransport(handler)
        client = OpenRouterClient(
            api_key="key",
            model="m-primary",
            fallback_models=["m-fallback"],
            backoff_base=0.0,
            transport=transport,
        )
        assert client.chat_json(MSGS) == {"a": 2}


class TestJsonRepair:
    def test_parses_fenced_json(self):
        client, _ = _sequence_client(
            [_ok_response('Aquí tienes:\n```json\n{"a": 3}\n```')]
        )
        assert client.chat_json(MSGS) == {"a": 3}


class TestClientReuse:
    def test_reuses_single_http_client(self):
        created = []
        real_client = httpx.Client

        class RecordingClient(real_client):
            def __init__(self, *args, **kwargs):
                created.append(kwargs)
                super().__init__(*args, **kwargs)

        import app.ai.openrouter as or_module

        old = or_module.httpx.Client
        or_module.httpx.Client = RecordingClient
        try:
            transport = httpx.MockTransport(
                lambda request: _ok_response('{"a": 1}')
            )
            client = OpenRouterClient(
                api_key="key", model="m", backoff_base=0.0, transport=transport
            )
            client.chat_json(MSGS)
            client.chat_json(MSGS)
        finally:
            or_module.httpx.Client = old
        assert len(created) == 1
        assert created[0].get("timeout") == 60.0
