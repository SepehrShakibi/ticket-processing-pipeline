import json

import streamlit as st

from ui.api_client import APIClientError, check_health
from ui.config import UISettings


def display_label(value: object) -> str:
    """Convert machine-readable labels into readable UI text."""
    if value is None or value == "":
        return "Not provided"

    return str(value).replace("_", " ").replace("-", " ").title()


def render_header() -> None:
    st.title("Ticket Triage")
    st.caption(
        "Analyze a customer support ticket and review its structured result."
    )


def render_sidebar(settings: UISettings) -> None:
    with st.sidebar:
        st.header("Service")
        st.caption("Backend endpoint")
        st.code(settings.api_base_url, language=None)

        if st.button(
            "Check API connection",
            use_container_width=True,
        ):
            with st.spinner("Checking API connection..."):
                try:
                    check_health(settings)
                except APIClientError as exc:
                    st.error(str(exc))
                else:
                    st.success("API is reachable.")

        st.caption(
            "This check confirms API liveness only. "
            "It does not verify model access or account balance."
        )

        st.divider()

        st.subheader("How to use")
        st.markdown(
            "1. Enter one customer ticket.\n"
            "2. Select **Analyze ticket**.\n"
            "3. Review the result and download the JSON if needed."
        )

        st.info(
            "Avoid submitting passwords, API keys, payment card details, "
            "or unnecessary personal information."
        )


def render_result(
    result: dict,
    completed_at: str,
) -> None:
    st.subheader("Analysis result")
    st.caption(f"Latest successful submission · {completed_at}")

    category_column, priority_column, sentiment_column = st.columns(3)

    category_column.metric(
        "Category",
        display_label(result["category"]),
    )
    priority_column.metric(
        "Priority",
        display_label(result["priority"]),
    )
    sentiment_column.metric(
        "Sentiment",
        display_label(result["sentiment"]),
    )

    st.divider()

    st.markdown("**Summary**")

    st.text(result["summary"])

    st.markdown("**Intent**")
    st.text(display_label(result.get("intent")))

    st.caption(
        "AI-generated output may be inaccurate. "
        "Review the result before taking action."
    )

    with st.expander("View structured JSON"):
        st.json(result)

    export = json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    )

    st.download_button(
        label="Download result as JSON",
        data=export,
        file_name="ticket-triage-result.json",
        mime="application/json",
        use_container_width=True,
    )
