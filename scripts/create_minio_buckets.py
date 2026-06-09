"""
Run AFTER docker compose up (infrastructure services must be running):
    pip install minio
    python scripts/create_minio_buckets.py

Creates the required MinIO buckets and sets the merchant-media bucket to
public-read so the admin panel and Mini App can display product images by URL.
Idempotent — safe to re-run.
"""
import json
import os

from minio import Minio

client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "saleos_minio_admin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "saleos_minio_dev_secret"),
    secure=os.getenv("MINIO_USE_SSL", "false").lower() == "true",
)

OCR_BUCKET = os.getenv("MINIO_BUCKET_OCR", "ocr-receipts")
MEDIA_BUCKET = os.getenv("MINIO_BUCKET_MEDIA", "merchant-media")
RECEIPTS_BUCKET = os.getenv("MINIO_BUCKET_RECEIPTS", "payment-receipts")


def ensure_bucket(name: str) -> None:
    if not client.bucket_exists(name):
        client.make_bucket(name)
        print(f"Created bucket: {name}")
    else:
        print(f"Bucket already exists: {name}")


def set_public_read(bucket: str) -> None:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    client.set_bucket_policy(bucket, json.dumps(policy))
    print(f"Set public-read policy on bucket: {bucket}")


ensure_bucket(OCR_BUCKET)  # private (receipts are sensitive)
ensure_bucket(MEDIA_BUCKET)
set_public_read(MEDIA_BUCKET)
ensure_bucket(RECEIPTS_BUCKET)  # private — payment receipts contain bank/account info

print("Done.")
