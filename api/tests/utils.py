import hashlib


def md5_of(data: bytes) -> str:
    """Short, stable id for test blobs in assertion messages."""
    return hashlib.md5(data).hexdigest()


def sample_bytes(n: int = 1024) -> bytes:
    return bytes(i % 251 for i in range(n))
