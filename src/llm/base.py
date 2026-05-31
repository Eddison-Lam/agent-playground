# src/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel


class BaseLLM(ABC):
    """
    Abstract base class for all LLM implementations.
    Supports both direct API calls and LangGraph integration.
    """

    def __init__(self):
        self.model: str = ""
        self.base_url: str = ""
        self.api_key: str | None = None
        self.timeout: int = 180
        self.default_params: Dict[str, Any] = {}
        self._langchain_model: Optional[BaseChatModel] = None

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send messages to LLM and return response."""
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        """Convenience method for single-turn completion."""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    @abstractmethod
    def get_langchain_model(self) -> BaseChatModel:
        """
        Return a LangChain-compatible chat model for use with LangGraph.
        
        Returns:
            BaseChatModel: LangChain chat model instance
        """
        pass

    def _handle_error(self, error: Exception) -> str:
        return f"[{self.__class__.__name__} Error] {str(error)}"