from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TicketCategory(str,Enum):
    """Supported categories for ticket classification."""

    TECHNICAL_SUPPORT = "Technical Support"
    BILLING = "Billing"
    GENERAL_INQUIRY  = "General Inquiry"
    PRODUCT_FEEDBACK = "Product Feedback"

class TicketSentiment(str,Enum):
    """Supported sentiment classification."""

    POSITIVE = "Positive"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negative"

class TicketInput(BaseModel):
    """Schema representing incoming raw ticket data."""

    ticket_id:Optional[str] = Field(
        default = None,
        description = "Unique identifier for the ticket (if available)"
    )

    text:str = Field(
        ...,
        min_length=5,
        description="The raw customer support ticket text."
    )


class TicketProcessingResult(BaseModel):
    """Schema representing the structured AI output after ticket processing."""

    is_safe: bool = Field(
        ...,
        description = "Flag indicating if the content is safe and free from prompt injection or toxic text."
    )
    reasoning: Optional[str] = Field(
        default = None,
        description = "Chain of Thought: Step-by-step reasoning behind the decision."
    )
    predicted_category: TicketCategory = Field(
        ...,
        description = "The assigned category based on the ticket content."
    )
    predicted_sentiment: TicketSentiment = Field(
        ...,
        description = "The emotional tone identified in the ticket."
    )
    summary: str = Field(
        ...,
        max_length = 300,
        description = "A concise summary of the core issue or request in English."
    )
    suggested_action: Optional[str] = Field(
        default = None,
        description = "A brief recommended next step for the support agent."
    )
    suggested_reply: Optional[str] = Field(
        default = None,
        description = "An optional preliminary draft response to the customer."
    )


# if __name__ == "__main__":
#     # Quick  check
#     sample_data = {
#         "predicted_category": "Billing",
#         "predicted_sentiment": "Negative",
#         "is_safe": True,
#         "summary": "Customer is complaining about an unexpected charge on their card."
#     }
#     result = TicketProcessingResult(**sample_data)
#     print("Validation Successful:")
#     print(result.model_dump_json(indent=2))
