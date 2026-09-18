"""
Uploads raw advisory documents to AWS S3 for long-term storage and backup.
"""
import os
from pathlib import Path

import boto3


def upload_advisories(
    source_dir: Path,
    bucket_name: str,
    prefix: str = "advisories/",
    region: str = "ap-south-1",
) -> list[str]:
    """
    Upload all PDFs and text files from `source_dir` to S3.
    Returns list of uploaded S3 keys.
    """
    client = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=region,
    )

    uploaded: list[str] = []
    for path in sorted(source_dir.rglob("*")):
        if path.suffix.lower() not in {".pdf", ".txt", ".md"}:
            continue

        key = prefix + path.name
        try:
            client.upload_file(
                Filename=str(path),
                Bucket=bucket_name,
                Key=key,
            )
            uploaded.append(key)
            print(f"[s3] Uploaded {path.name} → s3://{bucket_name}/{key}")
        except Exception as exc:  # noqa: BLE001
            print(f"[s3] Failed to upload {path.name}: {exc}")

    return uploaded
