import json
import logging
from pydantic import ValidationError
from src.schemas import ProcessedTicket
from src.prompt import SYSTEM_PROMPT, build_prompt


class TicketPipeline:
    def __init__(self, llm_engine, max_retries: int = 2):
        if (
        isinstance(max_retries, bool)
        or not isinstance(max_retries, int)
        or max_retries < 0
        ):
            raise ValueError("max_retries must be a non-negative integer.")
        self.engine = llm_engine
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _clean_json_response(raw_response: str) -> str:
        """
        Extracts valid JSON substring between the first '{' and the last '}'.
        """
        content = raw_response.strip()

        start = content.find("{")
        end = content.rfind("}")

        if start != -1 and end != -1 and end > start:
            return content[start:end + 1]

        return content

    def process(self, ticket_text: str) -> ProcessedTicket:
        """
        Processes a ticket text through the LLM and validates
        against ProcessedTicket schema.
        """
        if not isinstance(ticket_text, str):
            raise TypeError("ticket_text must be a string.")

        ticket_text = ticket_text.strip()

        if not ticket_text:
            raise ValueError("ticket_text must not be empty.")

        prompt = build_prompt(ticket_text)

        for attempt in range(self.max_retries + 1):
            try:
                raw_response = self.engine.generate(prompt=prompt, system_prompt=SYSTEM_PROMPT)
                cleaned = self._clean_json_response(raw_response)
                data = json.loads(cleaned)
                return ProcessedTicket.model_validate(data)

            except (json.JSONDecodeError, ValidationError) as e:
                self.logger.warning(f"Attempt {attempt + 1}/{self.max_retries + 1} failed: {e}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"Max retries reached ({self.max_retries}). Last error: {e}")
