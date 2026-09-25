"""Receipt signing for the accounting export.

Accounting's import tool only accepts RSA / PKCS#1 v1.5 signatures, so this
stays separate from the document signer in the API.
"""

import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def load_or_create_key(path: str) -> rsa.RSAPrivateKey:
    p = Path(path)
    if p.exists():
        return serialization.load_pem_private_key(p.read_bytes(), password=None)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    os.chmod(p, 0o600)
    return key


def build_payload(document_id: int, filename: str, sha256: str, signed_at: str) -> str:
    return json.dumps(
        {"document_id": document_id, "filename": filename, "sha256": sha256, "signed_at": signed_at},
        sort_keys=True,
        separators=(",", ":"),
    )


def sign_receipt(key: rsa.RSAPrivateKey, payload: str) -> str:
    sig = key.sign(payload.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(sig).decode()


def verify_receipt(public_key: rsa.RSAPublicKey, payload: str, signature_b64: str) -> None:
    public_key.verify(base64.b64decode(signature_b64), payload.encode(), padding.PKCS1v15(), hashes.SHA256())
