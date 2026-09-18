"""
Document chunking — splits PDF / text files into overlapping chunks
suitable for embedding and retrieval.
"""
import re
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNK_SIZE = 512          # characters
CHUNK_OVERLAP = 80        # characters


def _clean(text: str) -> str:
    """Strip excessive whitespace and normalize unicode spaces."""
    text = re.sub(r"\s+", " ", text)
    text = text.replace("\u00a0", " ")
    return text.strip()


def load_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return _clean(" ".join(pages))
    except Exception as exc:
        raise RuntimeError(f"Failed to read PDF {path}: {exc}") from exc


def load_text(path: Path) -> str:
    """Read a plain text file."""
    return _clean(path.read_text(encoding="utf-8", errors="ignore"))


def load_document(path: Path) -> str:
    """Auto-detect and load a document."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in {".txt", ".md"}:
        return load_text(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_document(
    text: str,
    metadata: dict,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[Document]:
    """
    Split `text` into overlapping chunks.
    Each chunk gets the provided metadata dict attached.

    Metadata keys expected:
        title       : str   — document title
        source_type : str   — "rbi_advisory" | "npci_advisory" | etc.
        source_url  : str   — (optional) canonical URL
        scam_category: str  — (optional) associated scam taxonomy category
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    raw_chunks = splitter.split_text(text)

    docs = []
    for i, chunk in enumerate(raw_chunks):
        chunk = _clean(chunk)
        if len(chunk) < 40:           # Skip near-empty chunks
            continue
        chunk_meta = {**metadata, "chunk_index": i, "chunk_total": len(raw_chunks)}
        docs.append(Document(page_content=chunk, metadata=chunk_meta))

    return docs
