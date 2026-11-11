import json
from unittest.mock import patch

import httpx
import pytest

from ui.api_client import (
    APIClientError,
    check_health,
    triage_ticket,
)
from ui.config import UISettings


VALID_RESULT = {
    "category": "payment",
    "priority": "medium",
    "sentiment": "negative",
    "intent": None,
    "summary": "Customer reports a duplicate charge.",
}


@pytest.fixture
def settings():
    return UISettings()


@pytest.fixture
def mock_http():
    with patch("ui.api_client.httpx.Client") as client_class:
        client = client_class.return_value.__enter__.return_value
        yield client


def test_successful_triage(settings, mock_http):
    mock_http.request.return_value = httpx.Response(
        200,
        json=VALID_RESULT,
    )

    result = triage_ticket(settings, "  I was charged twice.  ")

    assert result == VALID_RESULT
    mock_http.request.assert_called_once_with(
        "POST",
        "http://127.0.0.1:8000/triage",
        json={"ticket_text": "I was charged twice."},
    )


@pytest.mark.parametrize(
    "ticket_text",
    ["", "   ", "x" * 12001, None, 123],
)
def test_invalid_input_does_not_send_request(
    settings,
    mock_http,
    ticket_text,
):
    with pytest.raises(APIClientError):
        triage_ticket(settings, ticket_text)

    mock_http.request.assert_not_called()


@pytest.mark.parametrize(
    "status_code",
    [401, 403, 422, 429, 500, 502, 503, 504],
)
def test_http_errors_do_not_expose_response_body(
    settings,
    mock_http,
    status_code,
):
    mock_http.request.return_value = httpx.Response(
        status_code,
        json={"detail": "private-provider-message"},
    )

    with pytest.raises(APIClientError) as error:
        triage_ticket(settings, "I need help.")

    assert "private-provider-message" not in str(error.value)
    assert mock_http.request.call_count == 1


def test_timeout_is_not_retried(settings, mock_http):
    mock_http.request.side_effect = httpx.ReadTimeout(
        "private-timeout-details"
    )

    with pytest.raises(APIClientError, match="may still be running"):
        triage_ticket(settings, "I need help.")

    assert mock_http.request.call_count == 1


def test_connection_failure(settings, mock_http):
    mock_http.request.side_effect = httpx.ConnectError(
        "private-connection-details"
    )

    with pytest.raises(APIClientError, match="Could not reach the API"):
        triage_ticket(settings, "I need help.")


@pytest.mark.parametrize(
    "body",
    [
        "not-json",
        json.dumps({"unexpected": True}),
    ],
)
def test_invalid_success_response(settings, mock_http, body):
    mock_http.request.return_value = httpx.Response(
        200,
        text=body,
    )

    with pytest.raises(APIClientError, match="invalid ticket result"):
        triage_ticket(settings, "I need help.")


def test_health(settings, mock_http):
    mock_http.request.return_value = httpx.Response(
        200,
        json={"status": "ok"},
    )

    check_health(settings)

    mock_http.request.assert_called_once_with(
        "GET",
        "http://127.0.0.1:8000/health",
        json=None,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"api_base_url": "not-a-url"},
        {"api_base_url": "ftp://example.com"},
        {"api_base_url": "https://user:password@example.com"},
        {"request_timeout_seconds": 0},
        {"request_timeout_seconds": float("nan")},
        {"health_timeout_seconds": -1},
    ],
)
def test_invalid_settings(overrides):
    with pytest.raises(ValueError):
        UISettings(**overrides)
