import json
import logging
from pydantic import ValidationError
from src.schemas import TicketProcessingResult
from src.prompt import SYSTEM_PROMPT, build_prompt


class TicketPipeline:
    def __init__(self, llm_engine):
        self.engine = llm_engine
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _clean_json_response(raw_response: str) -> str:
        lines = raw_response.strip().splitlines()
        if lines and lines[0].strip().startswith("`"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("`"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    def process(self, ticket_text: str, max_retries: int = 2) -> TicketProcessingResult:
        prompt = build_prompt(ticket_text)

        for attempt in range(max_retries + 1):
            try:
                raw_response = self.engine.generate(SYSTEM_PROMPT, prompt)
                cleaned = self._clean_json_response(raw_response)
                data = json.loads(cleaned)
                return TicketProcessingResult.model_validate(data)

            except (json.JSONDecodeError, ValidationError) as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    raise RuntimeError("Max retries reached. Pipeline failed.")
