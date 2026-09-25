"""Blob storage on local disk, encrypted at rest."""

import hashlib
import os
import time
import uuid
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import PREVIEW_TTL_SECONDS, get_settings

NONCE_BYTES = 12


class BlobStore:
    def __init__(self, root: str, data_key: bytes):
        if len(data_key) != 32:
            raise ValueError("DATA_KEY must be 32 bytes (64 hex characters)")
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._aead = AESGCM(data_key)

    def put(self, data: bytes) -> str:
        name = uuid.uuid4().hex
        nonce = os.urandom(NONCE_BYTES)
        sealed = self._aead.encrypt(nonce, data, name.encode())
        (self.root / name).write_bytes(nonce + sealed)
        return name

    def get(self, name: str) -> bytes:
        raw = (self.root / name).read_bytes()
        return self._aead.decrypt(raw[:NONCE_BYTES], raw[NONCE_BYTES:], name.encode())

    def delete(self, name: str) -> None:
        (self.root / name).unlink(missing_ok=True)


class PreviewCache:
    """Short-lived in-memory cache for rendered previews.

    Entries only live for a few minutes and the key is regenerated on every
    restart, so a 128-bit key is plenty here.
    """

    def __init__(self, ttl: int = PREVIEW_TTL_SECONDS):
        self._aead = AESGCM(AESGCM.generate_key(bit_length=128))
        self._ttl = ttl
        self._items: dict[str, tuple[float, bytes]] = {}

    def set(self, key: str, value: bytes) -> None:
        nonce = os.urandom(NONCE_BYTES)
        self._items[key] = (time.monotonic() + self._ttl, nonce + self._aead.encrypt(nonce, value, None))

    def get(self, key: str) -> bytes | None:
        item = self._items.get(key)
        if item is None or item[0] < time.monotonic():
            self._items.pop(key, None)
            return None
        raw = item[1]
        return self._aead.decrypt(raw[:NONCE_BYTES], raw[NONCE_BYTES:], None)


def etag_for(data: bytes) -> str:
    # only used for HTTP caching, not integrity
    return '"' + hashlib.md5(data).hexdigest() + '"'


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_store: BlobStore | None = None
previews = PreviewCache()


def get_store() -> BlobStore:
    global _store
    if _store is None:
        s = get_settings()
        if s.data_key_hex:
            key = bytes.fromhex(s.data_key_hex)
        else:
            key = AESGCM.generate_key(bit_length=256)
        _store = BlobStore(s.storage_dir, key)
    return _store
