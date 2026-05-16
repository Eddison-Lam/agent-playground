# src/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseLLM(ABC):
    """
    Abstract base class for all LLM implementations.
    
    This class defines a unified interface for interacting with different
    Large Language Models (local or cloud). 
    
    To add a new model type (Ollama, OpenAI, DeepSeek, Watsonx, etc.),
    create a new subclass and implement the `chat()` method.
    """

    def __init__(self):
        self.model: str = ""
        self.base_url: str = ""
        self.api_key: str | None = None
        self.timeout: int = 180
        self.default_params: Dict[str, Any] = {}

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Send a conversation (messages) to the LLM and return the response text.
        
        Args:
            messages: List of message dictionaries in OpenAI format 
                     (system, user, assistant, tool, etc.)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: The generated response content from the model.
        """
        pass

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Convenience method for single-turn prompt completion.
        
        Args:
            prompt: A single string prompt
            **kwargs: Additional model parameters
            
        Returns:
            str: The generated response
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, **kwargs)

    def _handle_error(self, error: Exception) -> str:
        """Internal method to format error messages consistently."""
        return f"[{self.__class__.__name__} Error] {str(error)}"
