from fastapi import Request

from src.pipeline import TicketPipeline


def get_pipeline(request: Request) -> TicketPipeline:
    """Return the pipeline owned by the current application."""
    return request.app.state.pipeline