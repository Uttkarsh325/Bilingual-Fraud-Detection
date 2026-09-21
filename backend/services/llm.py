"""
LLM factory — returns a LangChain ChatModel based on the configured provider.
Supports Groq (cloud) and Ollama (local).
"""
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from core.config import settings
from core.logging import logger


@lru_cache(maxsize=8)
def get_llm(max_tokens: int = 1024) -> BaseChatModel:
    """
    Returns a cached LangChain ChatModel instance.
    Provider is chosen from settings.llm_provider.
    A cache hit is returned for identical (provider, max_tokens) combos —
    so callers that need longer outputs (e.g. translation) pass a bigger cap.
    """
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq

        logger.info(
            "llm.provider",
            provider="groq",
            model=settings.groq_model,
            max_tokens=max_tokens,
        )
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.1,
            max_tokens=max_tokens,
        )

    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama

        logger.info("llm.provider", provider="ollama", model=settings.ollama_model)
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.1,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider!r}. "
        "Choose 'groq' or 'ollama' in your .env file."
    )
