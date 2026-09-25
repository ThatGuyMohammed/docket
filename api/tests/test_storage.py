import pytest

from app.storage import BlobStore, PreviewCache, etag_for

from .utils import sample_bytes


def test_roundtrip(tmp_path):
    store = BlobStore(str(tmp_path), b"k" * 32)
    name = store.put(b"hello")
    assert store.get(name) == b"hello"
    assert (tmp_path / name).read_bytes() != b"hello"


def test_short_key_rejected(tmp_path):
    with pytest.raises(ValueError):
        BlobStore(str(tmp_path), b"k" * 16)


def test_preview_cache_expires():
    cache = PreviewCache(ttl=-1)
    cache.set("a", b"x")
    assert cache.get("a") is None


def test_etag_stable():
    assert etag_for(sample_bytes()) == etag_for(sample_bytes())
