from datetime import datetime, timezone

import streamlit as st


def initialize_state() -> None:
    """Initialize state without overwriting existing session values."""
    defaults = {
        "triage_result": None,
        "triage_error": None,
        "triage_completed_at": None,
        "ticket_input": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_result() -> None:
    """Remove previous output before a new processing attempt."""
    st.session_state["triage_result"] = None
    st.session_state["triage_error"] = None
    st.session_state["triage_completed_at"] = None


def save_result(result: dict) -> None:
    """Store the latest successful result in the current session."""
    st.session_state["triage_result"] = result
    st.session_state["triage_error"] = None
    st.session_state["triage_completed_at"] = datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def save_error(message: str) -> None:
    """Store a safe error message without keeping stale output."""
    clear_result()
    st.session_state["triage_error"] = message


def clear_workspace() -> None:
    """Clear ticket input and result through a widget callback."""
    clear_result()
    st.session_state["ticket_input"] = ""
