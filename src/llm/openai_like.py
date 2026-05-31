import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from .base import BaseLLM


class OpenAILikeModel(BaseLLM):
    """OpenAI-compatible API (DeepSeek, custom APIs, etc.)."""
    
    def __init__(self):
        super().__init__()
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")
        self.api_key = os.getenv("LLM_API_KEY")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "180"))
        
        # Validate required environment variables
        if not all([self.base_url, self.model, self.api_key]):
            raise ValueError(
                "Missing required environment variables for OpenAI-compatible API:\n"
                "  - LLM_BASE_URL\n"
                "  - LLM_MODEL\n"
                "  - LLM_API_KEY"
            )
        
        self.default_params = {
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        }

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Direct API call using OpenAI client."""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout
            )
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                **{**self.default_params, **kwargs}
            )
            return response.choices[0].message.content
        except Exception as e:
            return self._handle_error(e)

    def get_langchain_model(self) -> BaseChatModel:
        """Return ChatOpenAI for LangGraph."""
        if self._langchain_model is None:
            self._langchain_model = ChatOpenAI(
                model=self.model,
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout,
                **self.default_params
            )
        return self._langchain_model