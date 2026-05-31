import os
from typing import List, Dict
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel
from .base import BaseLLM


class OllamaModel(BaseLLM):
    """Local Ollama model."""
    
    def __init__(self):
        super().__init__()
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "llama3.2")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "180"))
        self.default_params = {
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            "frequency_penalty": float(os.getenv("LLM_FREQUENCY_PENALTY", "0.4")),
            "presence_penalty": float(os.getenv("LLM_PRESENCE_PENALTY", "0.3")),
        }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Direct API call."""
        try:
            import ollama
            response = ollama.chat(
                model=self.model,
                messages=messages,
                **{**self.default_params, **kwargs}
            )
            return response['message']['content']
        except Exception as e:
            return self._handle_error(e)

    def get_langchain_model(self) -> BaseChatModel:
        """Return LangChain Ollama model."""
        if self._langchain_model is None:
            self._langchain_model = ChatOllama(
                model=self.model,
                base_url=self.base_url,
                timeout=self.timeout,
                **self.default_params
            )
        return self._langchain_model