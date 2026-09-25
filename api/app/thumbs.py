"""Fast bulk signing of thumbnails.

Thumbnails are regenerated in large batches, so we call libsodium directly
instead of going through the full document signer. Requires the system
libsodium package (libsodium23 on Debian).
"""

import ctypes
import ctypes.util

_lib = None


def _sodium():
    global _lib
    if _lib is None:
        path = ctypes.util.find_library("sodium")
        if path is None:
            raise RuntimeError("libsodium not found")
        _lib = ctypes.CDLL(path)
        if _lib.sodium_init() < 0:
            raise RuntimeError("sodium_init failed")
    return _lib


class ThumbnailSigner:
    def __init__(self):
        lib = _sodium()
        self._pk = ctypes.create_string_buffer(lib.crypto_sign_publickeybytes())
        self._sk = ctypes.create_string_buffer(lib.crypto_sign_secretkeybytes())
        lib.crypto_sign_keypair(self._pk, self._sk)

    @property
    def public_key(self) -> bytes:
        return self._pk.raw

    def sign(self, thumb: bytes) -> bytes:
        lib = _sodium()
        sig = ctypes.create_string_buffer(lib.crypto_sign_bytes())
        siglen = ctypes.c_ulonglong(0)
        lib.crypto_sign_detached(
            sig, ctypes.byref(siglen), thumb, ctypes.c_ulonglong(len(thumb)), self._sk
        )
        return sig.raw[: siglen.value]

    def sign_many(self, thumbs: list[bytes]) -> list[bytes]:
        return [self.sign(t) for t in thumbs]
