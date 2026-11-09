from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class TicketCategory(str, Enum):
    ACCOUNT = "account"
    CANCEL = "cancel"
    CONTACT = "contact"
    DELIVERY = "delivery"
    FEEDBACK = "feedback"
    INVOICE = "invoice"
    ORDER = "order"
    PAYMENT = "payment"
    REFUND = "refund"
    SHIPPING = "shipping"
    SUBSCRIPTION = "subscription"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TicketSentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class ProcessedTicket(BaseModel):
    category: TicketCategory = Field(
        ..., 
        description="Ticket category mapped directly to the supported taxonomy."
    )
    priority: TicketPriority = Field(..., description="Inferred ticket priority.")
    sentiment: TicketSentiment = Field(..., description="Customer sentiment.")
    intent: Optional[str] = Field(
        default=None, 
        description="Specific intent action inferred from the ticket (if recognizable)."
    )
    summary: str = Field(..., description="Brief one-line summary of customer problem.")
