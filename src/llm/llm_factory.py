import os
from dotenv import load_dotenv
from .base import BaseLLM


def get_llm() -> BaseLLM:
    """
    Factory to return LLM instance based on configuration.
    """
    load_dotenv(override=False)

    provider = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

    match provider:
        case "ollama":
            from .ollama import OllamaModel
            return OllamaModel()

        case "openai" | "deepseek" | "groq" | "together" | "fireworks":
            from .openai_like import OpenAILikeModel
            return OpenAILikeModel()

        case _:
            # I support Provider 
            print(f"Unknown LLM_PROVIDER: '{provider}'. Falling back to ollama model.")
            from .ollama import OllamaModel
            return OllamaModel()
