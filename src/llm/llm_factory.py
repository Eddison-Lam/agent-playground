import os
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from .base import BaseLLM
from logger_utils import get_logger

logger = get_logger("LLM", subdir="llm")


def get_llm() -> BaseLLM:
    """
    Factory function to get LLM instance based on LLM_PROVIDER.
    
    Supported providers:
    - ollama: Local Ollama instance
    - openai_compatible: OpenAI-compatible APIs (DeepSeek, custom APIs, etc.)
    
    Environment variables:
    - LLM_PROVIDER: Provider type (default: ollama)
    - LLM_BASE_URL: API base URL (required)
    - LLM_MODEL: Model name (required)
    - LLM_API_KEY: API key (required for openai_compatible, optional for ollama)
    - LLM_TIMEOUT: Request timeout in seconds (default: 180)
    - LLM_TEMPERATURE: Model temperature (default: 0.7)
    
    Returns:
        BaseLLM: LLM instance
        
    Raises:
        ValueError: If provider is unknown or required env vars are missing
    """
    load_dotenv(override=False)
    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()
    
    logger.info(f"Loading LLM provider: {provider}")
    
    match provider:
        case "ollama":
            from .ollama import OllamaModel
            return OllamaModel()
        
        case "openai_compatible":
            from .openai_like import OpenAILikeModel
            return OpenAILikeModel()
        
        case _:
            error_msg = (
                f"Unknown LLM_PROVIDER: '{provider}'\n"
                f"Supported providers: 'ollama', 'openai_compatible'"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)


def get_langchain_llm() -> BaseChatModel:
    """
    Factory function for LangGraph-compatible LLM.
    
    Returns:
        BaseChatModel: LangChain chat model ready for LangGraph
        
    Example:
        >>> from llm import get_langchain_llm
        >>> llm = get_langchain_llm()
        >>> # Use in LangGraph nodes
    """
    llm_wrapper = get_llm()
    return llm_wrapper.get_langchain_model()


__all__ = ["get_llm", "get_langchain_llm", "BaseLLM"]