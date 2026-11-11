import logging

import streamlit as st

from ui.api_client import (
    APIClientError,
    MAX_TICKET_LENGTH,
    triage_ticket,
)
from ui.components import (
    render_header,
    render_result,
    render_sidebar,
)
from ui.config import UISettings
from ui.state import (
    clear_result,
    clear_workspace,
    initialize_state,
    save_error,
    save_result,
)


logger = logging.getLogger(__name__)


def main() -> None:
    st.set_page_config(
        page_title="Ticket Triage",
        page_icon="🎫",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    initialize_state()

    try:
        settings = UISettings.from_environment()
    except (ValueError, TypeError):
        st.error(
            "The interface configuration is invalid. "
            "Check the API URL and timeout settings."
        )
        st.stop()

    render_header()
    render_sidebar(settings)

    input_column, result_column = st.columns(
        [1, 1],
        gap="large",
    )

    with input_column:
        with st.container(border=True):
            st.subheader("Customer ticket")

            with st.form("ticket_form", clear_on_submit=False):
                ticket_text = st.text_area(
                    "Ticket text",
                    key="ticket_input",
                    height=280,
                    max_chars=MAX_TICKET_LENGTH,
                    placeholder=(
                        "Example: I was charged twice for my subscription. "
                        "Please help me resolve this."
                    ),
                    help=(
                        "Submit one customer ticket at a time. "
                        "Maximum length: 12,000 characters."
                    ),
                )

                st.caption(
                    "The request is sent only when you select Analyze ticket."
                )

                submitted = st.form_submit_button(
                    "Analyze ticket",
                    type="primary",
                    use_container_width=True,
                )

            st.button(
                "Clear workspace",
                on_click=clear_workspace,
                use_container_width=True,
            )

            st.caption(
                "Results describe the latest successful submission, "
                "not any unsubmitted edits."
            )

    if submitted:
        clear_result()

        with result_column:
            with st.spinner("Analyzing ticket..."):
                try:
                    result = triage_ticket(settings, ticket_text)
                except APIClientError as exc:
                    save_error(str(exc))
                except Exception as exc:

                    logger.error(
                        "Unexpected UI failure: type=%s",
                        type(exc).__name__,
                    )
                    save_error(
                        "An unexpected interface error occurred. "
                        "Contact the application maintainer."
                    )
                else:
                    save_result(result)

    with result_column:
        with st.container(border=True):
            error = st.session_state["triage_error"]
            result = st.session_state["triage_result"]

            if error:
                st.error(error)
            elif result is not None:
                render_result(
                    result,
                    st.session_state["triage_completed_at"],
                )
            else:
                st.subheader("Analysis result")
                st.info(
                    "Your ticket analysis will appear here after submission."
                )


if __name__ == "__main__":
    main()
