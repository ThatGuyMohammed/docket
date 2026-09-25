"""Document signatures.

The algorithm is picked with DOC_SIGNING_ALG. Each entry in SIGNERS knows how
to create a key, check that a loaded key is the right type, and sign/verify.
"""

import base64
import logging
from dataclasses import dataclass
from typing import Any, Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, mldsa, padding, rsa

from .config import get_settings

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Signer:
    name: str
    key_type: type
    generate: Callable[[], Any]
    sign: Callable[[Any, bytes], bytes]
    verify: Callable[[Any, bytes, bytes], None]


_PSS = padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)

SIGNERS: dict[str, Signer] = {
    "ed25519": Signer(
        name="ed25519",
        key_type=ed25519.Ed25519PrivateKey,
        generate=ed25519.Ed25519PrivateKey.generate,
        sign=lambda k, data: k.sign(data),
        verify=lambda pub, sig, data: pub.verify(sig, data),
    ),
    "ml-dsa-65": Signer(
        name="ml-dsa-65",
        key_type=mldsa.MLDSA65PrivateKey,
        generate=mldsa.MLDSA65PrivateKey.generate,
        sign=lambda k, data: k.sign(data),
        verify=lambda pub, sig, data: pub.verify(sig, data),
    ),
    "rsa-pss-3072": Signer(
        name="rsa-pss-3072",
        key_type=rsa.RSAPrivateKey,
        generate=lambda: rsa.generate_private_key(public_exponent=65537, key_size=3072),
        sign=lambda k, data: k.sign(data, _PSS, hashes.SHA256()),
        verify=lambda pub, sig, data: pub.verify(sig, data, _PSS, hashes.SHA256()),
    ),
}


class DocumentSigner:
    def __init__(self, alg: str, key_path: str | None = None):
        if alg not in SIGNERS:
            raise ValueError(f"unsupported DOC_SIGNING_ALG {alg!r}, expected one of {sorted(SIGNERS)}")
        self.signer = SIGNERS[alg]
        self.key = self._load(key_path)

    def _load(self, key_path: str | None):
        if not key_path:
            log.warning("DOC_SIGNING_KEY_PATH not set, using a throwaway %s key", self.signer.name)
            return self.signer.generate()
        with open(key_path, "rb") as fh:
            key = serialization.load_pem_private_key(fh.read(), password=None)
        if not isinstance(key, self.signer.key_type):
            raise ValueError(f"key at {key_path} is not a {self.signer.name} key")
        return key

    @property
    def alg(self) -> str:
        return self.signer.name

    def public_key_pem(self) -> str:
        return self.key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def sign(self, data: bytes) -> str:
        return base64.b64encode(self.signer.sign(self.key, data)).decode()

    def verify(self, data: bytes, signature_b64: str) -> bool:
        try:
            self.signer.verify(self.key.public_key(), base64.b64decode(signature_b64), data)
            return True
        except (InvalidSignature, ValueError):
            return False


_signer: DocumentSigner | None = None


def get_signer() -> DocumentSigner:
    global _signer
    if _signer is None:
        s = get_settings()
        _signer = DocumentSigner(s.doc_signing_alg, s.doc_signing_key_path)
    return _signer
