from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui.api_client import APIClientError


APP_PATH = Path(__file__).resolve().parents[1] / "ui" / "app.py"

VALID_RESULT = {
    "category": "payment",
    "priority": "medium",
    "sentiment": "negative",
    "intent": None,
    "summary": "Customer reports a duplicate charge.",
}


@pytest.fixture(autouse=True)
def clean_ui_environment(monkeypatch):
    for name in (
        "TICKET_API_BASE_URL",
        "TICKET_UI_TIMEOUT_SECONDS",
        "TICKET_UI_HEALTH_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def make_app():
    return AppTest.from_file(
        str(APP_PATH),
        default_timeout=10,
    ).run()


def click_button(app, label):
    button = next(
        item for item in app.button
        if item.label == label
    )
    button.click().run()


def test_initial_page_does_not_call_api(monkeypatch):
    calls = []

    def fake_triage(settings, ticket_text):
        calls.append(ticket_text)
        return VALID_RESULT

    monkeypatch.setattr(
        "ui.api_client.triage_ticket",
        fake_triage,
    )

    app = make_app()

    assert len(app.exception) == 0
    assert app.title[0].value == "Ticket Triage"
    assert calls == []


def test_successful_submission(monkeypatch):
    calls = []

    def fake_triage(settings, ticket_text):
        calls.append(ticket_text)
        return VALID_RESULT

    monkeypatch.setattr(
        "ui.api_client.triage_ticket",
        fake_triage,
    )

    app = make_app()
    app.text_area[0].input("I was charged twice.")
    click_button(app, "Analyze ticket")

    assert len(app.exception) == 0
    assert calls == ["I was charged twice."]
    assert app.session_state["triage_result"] == VALID_RESULT
    assert len(app.metric) == 3

    app.run()
    assert len(calls) == 1


def test_failed_submission_removes_previous_result(monkeypatch):
    responses = [
        VALID_RESULT,
        APIClientError("The API did not respond in time."),
    ]

    def fake_triage(settings, ticket_text):
        response = responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response

    monkeypatch.setattr(
        "ui.api_client.triage_ticket",
        fake_triage,
    )

    app = make_app()
    app.text_area[0].input("First ticket")
    click_button(app, "Analyze ticket")

    assert app.session_state["triage_result"] is not None

    app.text_area[0].input("Second ticket")
    click_button(app, "Analyze ticket")

    assert len(app.exception) == 0
    assert app.session_state["triage_result"] is None
    assert len(app.metric) == 0
    assert "did not respond" in app.error[0].value


def test_clear_workspace(monkeypatch):
    monkeypatch.setattr(
        "ui.api_client.triage_ticket",
        lambda settings, ticket_text: VALID_RESULT,
    )

    app = make_app()
    app.text_area[0].input("I need help.")
    click_button(app, "Analyze ticket")
    click_button(app, "Clear workspace")

    assert len(app.exception) == 0
    assert app.text_area[0].value == ""
    assert app.session_state["triage_result"] is None
    assert app.session_state["triage_error"] is None
