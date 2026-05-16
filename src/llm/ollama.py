import os
import ollama
from typing import List, Dict
from .base import BaseLLM


class OllamaModel(BaseLLM):
    """
    Local Ollama implementation.
    """

    def __init__(self):
        super().__init__()
        self.model = os.getenv("OLLAMA_MODEL", "llama3.1")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        print(f"Ollama local model initialized: {self.model}")

    def chat(self, messages: List[Dict], **kwargs) -> str:
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response['message']['content']
        except Exception as e:
            return self._handle_error(e)
