import math 
import os 
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class UISettings:
    """Connection settings owned by the Streamlit application."""

    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_seconds: float = 90.0
    health_timeout_seconds: float = 3.0

    def __post_init__(self) -> None:
        parsed = urlsplit(self.api_base_url)

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("API base URL must be a valid HTTP or HTTPS URL.")

        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Credentials must not be embedded in the API URL.")

        if parsed.query or parsed.fragment:
            raise ValueError("API base URL must not contain a query or fragment.")

        for value in (
            self.request_timeout_seconds,
            self.health_timeout_seconds,
        ):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Timeout must be a positive finite number.")
    @classmethod
    def from_environment(cls) -> "UISettings":
        """Load UI settings without importing backend configuration"""
        return cls(
            api_base_url=os.getenv(
                "TICKET_API_BASE_URL",
                "http://127.0.0.1:8000",
            ).strip().rstrip("/"),
            request_timeout_seconds=float(os.getenv("TICKET_UI_TIMEOUT_SECONDS","90")),
            health_timeout_seconds=float(os.getenv("TICKET_UI_HEALTH_TIMEOUT_SECONDS","3"))
        )
