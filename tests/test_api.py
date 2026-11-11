import json

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APITimeoutError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from src.api.app import create_app
from src.api.settings import APISettings
from src.pipeline import TicketPipeline


VALID_RESULT = {
    "category": "payment",
    "priority": "medium",
    "sentiment": "negative",
    "intent": None,
    "summary": "Customer reports a duplicate charge.",
}


class FakeEngine:
    """Return deterministic output without network access."""

    def __init__(self, response=None, error=None):
        self.response = (
            json.dumps(VALID_RESULT)
            if response is None
            else response
        )
        self.error = error
        self.calls = []

    def generate(
        self,
        prompt,
        system_prompt=None,
        temperature=0.0,
        **kwargs,
    ):
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
            }
        )

        if self.error is not None:
            raise self.error

        return self.response


def make_app(engine, max_retries=0):
    pipeline = TicketPipeline(
        llm_engine=engine,
        max_retries=max_retries,
    )
    return create_app(pipeline=pipeline)


def test_health_does_not_call_model():
    engine = FakeEngine()

    with TestClient(make_app(engine)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert engine.calls == []


def test_triage_returns_validated_result():
    engine = FakeEngine()

    with TestClient(make_app(engine)) as client:
        response = client.post(
            "/triage",
            json={"ticket_text": "I was charged twice."},
        )

    assert response.status_code == 200
    assert response.json() == VALID_RESULT
    assert len(engine.calls) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"ticket_text": None},
        {"ticket_text": 123},
        {"ticket_text": []},
        {"ticket_text": ""},
        {"ticket_text": "   "},
        {"ticket_text": "x" * 12001},
        {"ticket_text": "Hello", "unexpected": True},
    ],
)
def test_invalid_input_never_calls_model(payload):
    engine = FakeEngine()

    with TestClient(make_app(engine)) as client:
        response = client.post("/triage", json=payload)

    assert response.status_code == 422
    assert engine.calls == []


def test_invalid_output_returns_502_after_retry():
    engine = FakeEngine(response="not valid json")

    with TestClient(make_app(engine, max_retries=1)) as client:
        response = client.post(
            "/triage",
            json={"ticket_text": "I need a refund."},
        )

    assert response.status_code == 502
    assert len(engine.calls) == 2


def test_timeout_returns_504():
    error = APITimeoutError(
        request=httpx.Request("POST", "https://provider.invalid"),
    )
    engine = FakeEngine(error=error)

    with TestClient(make_app(engine)) as client:
        response = client.post(
            "/triage",
            json={"ticket_text": "I need help."},
        )

    assert response.status_code == 504
    assert len(engine.calls) == 1


@pytest.mark.parametrize(
    ("error_type", "provider_status"),
    [
        (RateLimitError, 429),
        (AuthenticationError, 401),
    ],
)
def test_provider_access_errors_are_safe(error_type, provider_status):
    request = httpx.Request("POST", "https://provider.invalid")
    provider_response = httpx.Response(
        provider_status,
        request=request,
    )

    error = error_type(
        "private-provider-message",
        response=provider_response,
        body={"message": "private-provider-message"},
    )
    engine = FakeEngine(error=error)

    with TestClient(make_app(engine)) as client:
        response = client.post(
            "/triage",
            json={"ticket_text": "I need help."},
        )

    assert response.status_code == 503
    assert "private-provider-message" not in response.text
    assert len(engine.calls) == 1


def test_unexpected_error_returns_safe_500():
    engine = FakeEngine(
        error=ValueError("private-internal-message"),
    )

    with TestClient(
        make_app(engine),
        raise_server_exceptions=False,
    ) as client:
        response = client.post(
            "/triage",
            json={"ticket_text": "I need help."},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal processing error."}
    assert "private-internal-message" not in response.text


def test_sequential_requests_are_processed_separately():
    engine = FakeEngine()

    with TestClient(make_app(engine)) as client:
        first = client.post(
            "/triage",
            json={"ticket_text": "FIRST_UNIQUE_TICKET"},
        )
        second = client.post(
            "/triage",
            json={"ticket_text": "SECOND_UNIQUE_TICKET"},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(engine.calls) == 2
    assert "FIRST_UNIQUE_TICKET" in engine.calls[0]["prompt"]
    assert "FIRST_UNIQUE_TICKET" not in engine.calls[1]["prompt"]
    assert "SECOND_UNIQUE_TICKET" in engine.calls[1]["prompt"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"api_key": ""},
        {"model_name": ""},
        {"model_timeout_seconds": 0},
        {"output_retries": -1},
        {"base_url": "not-a-url"},
        {"provider": "unsupported"},
    ],
)
def test_invalid_settings_are_rejected(overrides):
    values = {
        "api_key": "fake-test-key",
        "model_name": "fake-test-model",
    }
    values.update(overrides)

    with pytest.raises(ValidationError):
        APISettings.model_validate(values)


def test_owned_engine_is_closed_on_shutdown(monkeypatch):
    from src.api import app as app_module

    class ClosableFakeEngine(FakeEngine):
        def __init__(self):
            super().__init__()
            self.closed = False

        def close(self):
            self.closed = True

    engine = ClosableFakeEngine()

    settings = APISettings(
        api_key="fake-test-key",
        model_name="fake-test-model",
    )

    monkeypatch.setattr(
        APISettings,
        "from_environment",
        classmethod(lambda cls: settings),
    )
    monkeypatch.setattr(
        app_module,
        "OpenAIEngine",
        lambda **kwargs: engine,
    )

    with TestClient(app_module.create_app()) as client:
        assert client.get("/health").status_code == 200
        assert engine.closed is False

    assert engine.closed is True
    assert engine.calls == []
