"""Nightly archive export to S3.

Each archive manifest is signed with a KMS key so auditors can check it
without us handing out key material.
"""

import base64
import json
import os
from datetime import datetime, timezone

import boto3

from .config import get_settings


def _kms():
    return boto3.client("kms", region_name=os.environ.get("AWS_REGION", "eu-west-1"))


def sign_manifest(manifest: dict) -> dict:
    body = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    resp = _kms().sign(
        KeyId=os.environ["ARCHIVE_KMS_KEY_ID"],
        Message=body,
        MessageType="RAW",
        SigningAlgorithm=get_settings().archive_signing_alg,
    )
    return {
        "manifest": manifest,
        "key_id": resp["KeyId"],
        "algorithm": resp["SigningAlgorithm"],
        "signature": base64.b64encode(resp["Signature"]).decode(),
    }


def export_archive(documents: list[dict]) -> str:
    s = get_settings()
    if not s.archive_bucket:
        raise RuntimeError("ARCHIVE_BUCKET is not configured")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    signed = sign_manifest({"created": stamp, "documents": documents})
    key = f"archives/{stamp}/manifest.json"
    boto3.client("s3").put_object(
        Bucket=s.archive_bucket, Key=key, Body=json.dumps(signed).encode()
    )
    return key
