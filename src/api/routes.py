from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_pipeline
from src.api.schemas import ErrorResponse, HealthResponse, TriageRequest
from src.pipeline import TicketPipeline
from src.schemas import ProcessedTicket


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
)

def health() -> HealthResponse:
    """Report process liveness without contacting the model provider"""
    return HealthResponse()

@router.post(
    "/triage",
    response_model=ProcessedTicket,
    tags=["Triage"],
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Invalid input.",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal processing failure",
        },
        502: {
            "model": ErrorResponse,
            "description": "Unsuccessful or invalid model response",
        },
        503: {
            "model": ErrorResponse,
            "description": "Model provider unavailable",
        },
        504: {
            "model": ErrorResponse,
            "description": "Model provider timeout.",
        },
    }   
)
def tirage(
    payload: TriageRequest,
    pipeline: Annotated[TicketPipeline, Depends(get_pipeline)],
) -> ProcessedTicket:
    """Process one customer ticket through the existing pipeline."""
    return pipeline.process(payload.ticket_text)