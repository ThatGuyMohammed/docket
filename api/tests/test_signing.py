import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.signing import SIGNERS, DocumentSigner

from .utils import md5_of, sample_bytes


@pytest.mark.parametrize("alg", sorted(SIGNERS))
def test_sign_and_verify(alg):
    signer = DocumentSigner(alg)
    data = sample_bytes()
    sig = signer.sign(data)
    assert signer.verify(data, sig), md5_of(data)
    assert not signer.verify(data + b"x", sig)


def test_unknown_alg_rejected():
    with pytest.raises(ValueError):
        DocumentSigner("sha1-rsa")


def test_key_type_mismatch(tmp_path):
    # small key keeps the test fast; only the type check matters here
    key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    from cryptography.hazmat.primitives import serialization

    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    path = tmp_path / "k.pem"
    path.write_bytes(pem)
    with pytest.raises(ValueError):
        DocumentSigner("ed25519", str(path))
    # sanity: the key itself still works
    sig = key.sign(b"abc", padding.PKCS1v15(), hashes.SHA256())
    key.public_key().verify(sig, b"abc", padding.PKCS1v15(), hashes.SHA256())
