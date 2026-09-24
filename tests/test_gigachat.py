import json
import time

import httpx

from intonaciya.llm import GigaChatProvider, Message
from intonaciya.llm.gigachat import API_URL, OAUTH_URL


class FakeGigaChat:
    """Records requests and serves canned OAuth and completion responses."""

    def __init__(self, completion_statuses: list[int] | None = None) -> None:
        self.oauth_calls = 0
        self.completion_requests: list[httpx.Request] = []
        self._completion_statuses = completion_statuses or []

    def handler(self, request: httpx.Request) -> httpx.Response:
        if str(request.url) == OAUTH_URL:
            self.oauth_calls += 1
            expires_at_ms = int((time.time() + 1800) * 1000)
            return httpx.Response(
                200, json={"access_token": f"token-{self.oauth_calls}", "expires_at": expires_at_ms}
            )

        assert str(request.url) == f"{API_URL}/chat/completions"
        self.completion_requests.append(request)
        if self._completion_statuses:
            status = self._completion_statuses.pop(0)
            if status != 200:
                return httpx.Response(status)
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"role": "assistant", "content": "Привет"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 12, "completion_tokens": 3},
            },
        )


def _provider(fake: FakeGigaChat) -> GigaChatProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(fake.handler))
    return GigaChatProvider("auth-key", model="GigaChat-Pro", client=client)


async def test_complete_parses_response_and_sends_model() -> None:
    fake = FakeGigaChat()
    provider = _provider(fake)

    completion = await provider.complete([Message("user", "Привет")])

    assert completion.text == "Привет"
    assert completion.finish_reason == "stop"
    assert (completion.prompt_tokens, completion.completion_tokens) == (12, 3)
    body = json.loads(fake.completion_requests[0].content)
    assert body == {"model": "GigaChat-Pro", "messages": [{"role": "user", "content": "Привет"}]}
    assert fake.completion_requests[0].headers["Authorization"] == "Bearer token-1"


async def test_token_is_reused_between_calls() -> None:
    fake = FakeGigaChat()
    provider = _provider(fake)

    await provider.complete([Message("user", "1")])
    await provider.complete([Message("user", "2")])

    assert fake.oauth_calls == 1


async def test_unauthorized_refreshes_token_once() -> None:
    fake = FakeGigaChat(completion_statuses=[401, 200])
    provider = _provider(fake)

    completion = await provider.complete([Message("user", "Привет")])

    assert completion.text == "Привет"
    assert fake.oauth_calls == 2
    assert fake.completion_requests[1].headers["Authorization"] == "Bearer token-2"
