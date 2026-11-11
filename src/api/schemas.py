from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TriageRequest(BaseModel):
    """Input contract for single-ticket processing"""

    model_config = ConfigDict(extra="forbid")

    ticket_text: str = Field(
        ...,
        strict=True,
        min_length=1,
        max_length=12000,
        description="Customer ticket text to process."
    )

    @field_validator("ticket_text")
    @classmethod
    def validate_ticket_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("ticket_text must not be empty or whitespace.")

        return value

class HealthResponse(BaseModel):
    """Liveness response without a model provider check."""
    status: Literal["ok"] = "ok"

class ErrorResponse(BaseModel):
    """Public error response without internal diagnostic details."""
    
    detail: str