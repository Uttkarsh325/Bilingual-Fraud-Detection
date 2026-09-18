"""
Qdrant vector store — setup, upsert helpers, and retrieval.
"""
from functools import lru_cache
from typing import Optional

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PayloadSchemaType,
)

from core.config import settings
from core.logging import logger
from rag.embeddings import get_embeddings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    kwargs: dict = {"url": settings.qdrant_url}
    if settings.qdrant_api_key:
        kwargs["api_key"] = settings.qdrant_api_key
    client = QdrantClient(**kwargs)
    logger.info("qdrant.connected", url=settings.qdrant_url)
    return client


def ensure_collection(client: Optional[QdrantClient] = None) -> None:
    """
    Create the advisory collection if it does not exist.
    Called once at app startup.
    """
    if client is None:
        client = get_qdrant_client()

    existing = {c.name for c in client.get_collections().collections}
    if settings.qdrant_collection_name in existing:
        logger.info("qdrant.collection_exists", name=settings.qdrant_collection_name)
        return

    client.create_collection(
        collection_name=settings.qdrant_collection_name,
        vectors_config=VectorParams(
            size=settings.embedding_dim,
            distance=Distance.COSINE,
        ),
    )

    # Create payload index for fast filtering by source_type
    client.create_payload_index(
        collection_name=settings.qdrant_collection_name,
        field_name="metadata.source_type",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=settings.qdrant_collection_name,
        field_name="metadata.scam_category",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    logger.info("qdrant.collection_created", name=settings.qdrant_collection_name)


@lru_cache(maxsize=1)
def get_vector_store() -> QdrantVectorStore:
    """Returns a LangChain-compatible QdrantVectorStore (cached)."""
    client = get_qdrant_client()
    ensure_collection(client)
    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection_name,
        embedding=get_embeddings(),
    )
