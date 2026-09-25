import hashlib
import hmac

from app.webhooks import sign_payload


def test_signature_matches_docs_example():
    body = b'{"event":"document.signed"}'
    expected = hmac.new(b"s3cret", b"1700000000." + body, hashlib.sha256).hexdigest()
    assert sign_payload("s3cret", 1700000000, body) == expected
