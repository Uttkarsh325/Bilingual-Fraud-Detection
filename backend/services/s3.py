"""
AWS S3 helper — upload/download advisory documents, audio artifacts,
and embedding backups.
"""
import io
import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from core.config import settings
from core.logging import logger


class S3Service:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self._bucket = settings.s3_bucket_name

    # ── Upload ────────────────────────────────────────────────────────────────

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to S3. Returns the S3 key."""
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info("s3.upload", key=key, size=len(data))
        return key

    def upload_audio(self, audio_bytes: bytes, session_id: str) -> str:
        """Upload voice query / TTS audio, returns S3 key."""
        key = f"audio/{session_id}/{uuid.uuid4()}.wav"
        return self.upload_bytes(audio_bytes, key, content_type="audio/wav")

    def upload_document(self, file_bytes: bytes, filename: str) -> str:
        """Upload an advisory PDF or text document."""
        key = f"advisories/{filename}"
        return self.upload_bytes(file_bytes, key, content_type="application/pdf")

    # ── Presigned URL ─────────────────────────────────────────────────────────

    def presign_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed GET URL valid for `expires_in` seconds."""
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    # ── Download ──────────────────────────────────────────────────────────────

    def download_bytes(self, key: str) -> bytes:
        """Download an object and return its bytes."""
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        return obj["Body"].read()

    # ── Bucket bootstrap ──────────────────────────────────────────────────────

    def ensure_bucket(self) -> None:
        """Create the bucket if it does not exist (idempotent)."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "404":
                if settings.aws_region == "us-east-1":
                    self._client.create_bucket(Bucket=self._bucket)
                else:
                    self._client.create_bucket(
                        Bucket=self._bucket,
                        CreateBucketConfiguration={
                            "LocationConstraint": settings.aws_region
                        },
                    )
                logger.info("s3.bucket_created", bucket=self._bucket)
            else:
                raise


# Singleton — lazily initialized so missing keys don't crash at import time
_s3: Optional[S3Service] = None


def get_s3() -> S3Service:
    global _s3
    if _s3 is None:
        _s3 = S3Service()
    return _s3
