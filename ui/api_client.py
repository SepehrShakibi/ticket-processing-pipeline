import httpx
from pydantic import ValidationError

from src.schemas import ProcessedTicket
from ui.config import UISettings


MAX_TICKET_LENGTH = 12000


class APIClientError(RuntimeError):
    """A safe, user-facing API communication error."""


STATUS_MESSAGES = {
    401: "The API requires authentication.",
    403: "You do not have permission to use this API.",
    404: "The API endpoint was not found. Check the server configuration.",
    413: "The submitted request is too large.",
    422: "The API rejected the ticket. Check the input and try again.",
    429: "Too many requests. Please wait before submitting another ticket.",
    500: "The backend encountered an internal error.",
    502: "The model provider returned an unsuccessful or invalid response.",
    503: (
        "The model provider is unavailable. "
        "Check provider access, quota, or service availability."
    ),
    504: (
        "The model provider timed out. "
        "The request may already have consumed provider resources."
    ),
}


def _send_request(
    settings: UISettings,
    method: str,
    path: str,
    *,
    timeout_seconds: float,
    payload: dict | None = None,
) -> httpx.Response:
    """Send one HTTP request without automatic retries."""
    url = f"{settings.api_base_url.rstrip('/')}{path}"

    timeout = httpx.Timeout(
        timeout_seconds,
        connect=min(5.0, timeout_seconds),
    )

    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
        ) as client:
            response = client.request(
                method,
                url,
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise APIClientError(
            "The API did not respond in time. Processing may still be running. "
            "Submitting again may create a duplicate request."
        ) from exc
    except httpx.RequestError as exc:
        raise APIClientError(
            "Could not reach the API. Verify that the backend is running "
            "and the connection settings are correct."
        ) from exc

    if response.status_code != 200:
        message = STATUS_MESSAGES.get(
            response.status_code,
            "The API returned an unexpected HTTP response.",
        )
        raise APIClientError(message)

    return response


def check_health(settings: UISettings) -> None:
    """Check backend liveness without checking the model provider."""
    response = _send_request(
        settings,
        "GET",
        "/health",
        timeout_seconds=settings.health_timeout_seconds,
    )

    try:
        payload = response.json()
    except ValueError as exc:
        raise APIClientError(
            "The API returned an invalid health response."
        ) from exc

    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise APIClientError("The API returned an invalid health response.")


def triage_ticket(
    settings: UISettings,
    ticket_text: str,
) -> dict:
    """Submit one ticket and validate the successful response."""
    if not isinstance(ticket_text, str):
        raise APIClientError("Ticket text must be a string.")

    if len(ticket_text) > MAX_TICKET_LENGTH:
        raise APIClientError(
            f"Ticket text must not exceed {MAX_TICKET_LENGTH:,} characters."
        )

    ticket_text = ticket_text.strip()

    if not ticket_text:
        raise APIClientError("Enter a ticket before submitting.")

    response = _send_request(
        settings,
        "POST",
        "/triage",
        timeout_seconds=settings.request_timeout_seconds,
        payload={"ticket_text": ticket_text},
    )

    try:
        result = ProcessedTicket.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise APIClientError(
            "The API returned an invalid ticket result."
        ) from exc

    return result.model_dump(mode="json")
