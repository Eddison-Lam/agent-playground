import os
import requests
from typing import List, Dict
from .base import BaseLLM


class OpenAILikeModel(BaseLLM):
    """
    OpenAI-compatible API implementation.
    Supports OpenAI, DeepSeek, Groq, Together.ai, etc.
    """

    def __init__(self):
        super().__init__() 
        self.api_key = os.getenv("CLOUD_API_KEY")
        self.base_url = os.getenv("CLOUD_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.model = os.getenv("CLOUD_MODEL", "gpt-4o-mini")

        if not self.api_key:
            raise ValueError(
                "CLOUD_API_KEY is required for cloud mode but not found in environment variables."
            )

        print(f"Cloud LLM initialized: {self.model} @ {self.base_url}")

    def chat(self, messages: List[Dict], **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            **self.default_params,
            **kwargs
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return self._handle_error(e)

