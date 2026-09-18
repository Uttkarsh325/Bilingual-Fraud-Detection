"""
Embedder — converts document chunks into vectors and upserts them into Qdrant.
"""
import uuid
from typing import Optional

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
    PayloadSchemaType,
)
from tqdm import tqdm


EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384
BATCH_SIZE = 64


def get_embeddings(model_name: str = EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def ensure_collection(
    client: QdrantClient,
    collection_name: str,
    dim: int = EMBEDDING_DIM,
) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if collection_name in existing:
        print(f"[qdrant] Collection '{collection_name}' already exists — skipping create.")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )
    # Payload indexes for fast filtered search
    for field, schema in [
        ("metadata.source_type", PayloadSchemaType.KEYWORD),
        ("metadata.scam_category", PayloadSchemaType.KEYWORD),
        ("metadata.title", PayloadSchemaType.KEYWORD),
    ]:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=schema,
        )
    print(f"[qdrant] Created collection '{collection_name}'.")


def upsert_documents(
    documents: list[Document],
    client: QdrantClient,
    collection_name: str,
    embeddings: Optional[HuggingFaceEmbeddings] = None,
) -> int:
    """
    Embed and upsert documents into Qdrant.
    Returns the number of points upserted.
    """
    if embeddings is None:
        embeddings = get_embeddings()

    total = 0
    for i in tqdm(range(0, len(documents), BATCH_SIZE), desc="Upserting"):
        batch = documents[i : i + BATCH_SIZE]
        texts = [doc.page_content for doc in batch]
        vectors = embeddings.embed_documents(texts)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                },
            )
            for doc, vec in zip(batch, vectors)
        ]
        client.upsert(collection_name=collection_name, points=points)
        total += len(points)

    return total
