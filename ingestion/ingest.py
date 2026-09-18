"""
Main ingestion script.

Usage:
    python ingest.py --source ../docs/advisories [--upload-s3] [--dry-run]

What it does:
  1. Discovers all PDF/TXT/MD files in the source directory.
  2. Loads and chunks each document.
  3. Embeds and upserts chunks into Qdrant.
  4. (Optional) Uploads raw files to AWS S3.
"""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from qdrant_client import QdrantClient

from chunker import chunk_document, load_document
from embedder import ensure_collection, get_embeddings, upsert_documents
from s3_uploader import upload_advisories


# ── Document metadata catalogue ───────────────────────────────────────────────
# For known advisory files, we provide rich metadata.
# Unknown files get generic metadata derived from their filename.

KNOWN_METADATA: dict[str, dict] = {
    # Add known advisory filenames here, e.g.:
    # "rbi-upi-safety-2024.pdf": {
    #     "title": "RBI UPI Safety Guidelines 2024",
    #     "source_type": "rbi_advisory",
    #     "source_url": "https://rbi.org.in/...",
    #     "scam_category": "upi_collect_scam",
    # },
}


def derive_metadata(path: Path) -> dict:
    """Derive basic metadata from a filename for unknown documents."""
    name_lower = path.stem.lower()
    if "rbi" in name_lower:
        source_type = "rbi_advisory"
    elif "npci" in name_lower:
        source_type = "npci_advisory"
    elif "cybercrime" in name_lower or "faq" in name_lower:
        source_type = "cybercrime_faq"
    else:
        source_type = "scam_pattern"

    return {
        "title": path.stem.replace("-", " ").replace("_", " ").title(),
        "source_type": source_type,
        "source_url": None,
        "scam_category": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest advisory documents into Qdrant")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).parent.parent / "docs" / "advisories",
        help="Directory containing advisory PDFs/text files",
    )
    parser.add_argument(
        "--qdrant-url",
        default=os.environ.get("QDRANT_URL", "http://localhost:6333"),
    )
    parser.add_argument(
        "--collection",
        default=os.environ.get("QDRANT_COLLECTION_NAME", "fraud_advisories"),
    )
    parser.add_argument("--upload-s3", action="store_true", help="Also upload raw files to S3")
    parser.add_argument("--dry-run", action="store_true", help="Parse + chunk only, no upsert")
    args = parser.parse_args()

    source_dir: Path = args.source
    if not source_dir.exists():
        print(f"[ingest] Source directory not found: {source_dir}")
        print("[ingest] Create it and place your advisory PDFs inside.")
        sys.exit(1)

    files = sorted(
        p for p in source_dir.rglob("*")
        if p.suffix.lower() in {".pdf", ".txt", ".md"}
    )
    if not files:
        print(f"[ingest] No PDF/TXT/MD files found in {source_dir}")
        sys.exit(0)

    print(f"[ingest] Found {len(files)} file(s) in {source_dir}")

    # Optional S3 upload
    if args.upload_s3 and not args.dry_run:
        bucket = os.environ.get("S3_BUCKET_NAME", "fraud-advisory-store")
        region = os.environ.get("AWS_REGION", "ap-south-1")
        upload_advisories(source_dir, bucket, region=region)

    # Qdrant client + collection setup
    qdrant_kwargs: dict = {"url": args.qdrant_url}
    if (api_key := os.environ.get("QDRANT_API_KEY")):
        qdrant_kwargs["api_key"] = api_key

    if not args.dry_run:
        client = QdrantClient(**qdrant_kwargs)
        ensure_collection(client, args.collection)
        embeddings = get_embeddings()

    total_chunks = 0
    total_upserted = 0

    for file_path in files:
        print(f"\n[ingest] Processing: {file_path.name}")
        try:
            text = load_document(file_path)
            if not text:
                print(f"  [skip] Empty text extracted from {file_path.name}")
                continue

            meta = KNOWN_METADATA.get(file_path.name, derive_metadata(file_path))
            chunks = chunk_document(text, metadata=meta)
            total_chunks += len(chunks)
            print(f"  Chunks: {len(chunks)} | Source type: {meta['source_type']}")

            if not args.dry_run:
                n = upsert_documents(chunks, client, args.collection, embeddings)
                total_upserted += n
                print(f"  Upserted: {n} points")

        except Exception as exc:  # noqa: BLE001
            print(f"  [error] {exc}")

    print(f"\n[ingest] Done. Total chunks: {total_chunks}, Upserted: {total_upserted}")


if __name__ == "__main__":
    main()
