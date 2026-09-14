from abc import ABC, abstractmethod
from typing import Optional, Any
from openai import OpenAI
from src.config import Config

class BaseLLMEngine(ABC):
    """Abstract base class for all LLM providers (Model-Agnostic Interface)."""
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        **kwargs: Any
    ) -> str:
        """
        Genrate text response from the underlying LLM.

        :param prompt: User prompt or main input text.
        :param system_prompt: Optional system instructions.
        :param temperature: Sampling temprature (0..0 for deterministic ouput).
        :return: Raw string response from the model.
        """
        pass

class OpenAIEngine(BaseLLMEngine):
    """LLM Engine implementaion for OpenAI / OpenAI-compatible APIs."""

    def __init__(self, model_name: str, api_key: str, base_url: Optional[str] = None):
        self.model_name = model_name

        self.client = OpenAI(api_key = api_key, base_url = base_url)

    def generate(self, prompt: str, 
                  system_prompt: Optional[str] = None, 
                  temperature: float = 0.0, 
                  **kwargs: Any) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            **kwargs
        )
        return response.choices[0].message.content or ""


def get_llm_engine() -> BaseLLMEngine:
    """
    Factory function to instantiate the configured LLM engine.
    Selection is driven by settings in src/config.py
    """
    provider = getattr(Config, "LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        return OpenAIEngine(
            api_key=Config.OPENAI_API_KEY,
            model_name=getattr(Config, "OPENAI_MODEL", "gpt-5.6-sol"),
            base_url=getattr(Config, "OPENAI_BASE_URL", None)
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")