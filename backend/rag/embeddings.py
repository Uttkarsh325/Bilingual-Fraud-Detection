"""
Embedding model wrapper.
Uses a multilingual sentence-transformer that handles Hindi + Indic scripts.
"""
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from core.config import settings
from core.logging import logger


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Returns a cached HuggingFaceEmbeddings instance.

    Model: paraphrase-multilingual-MiniLM-L12-v2
    - 384-dim vectors
    - Supports 50+ languages including Hindi, Bengali, Tamil, etc.
    - Runs on CPU comfortably; ~120 MB
    """
    logger.info("embeddings.loading", model=settings.embedding_model)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
