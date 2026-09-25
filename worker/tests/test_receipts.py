from exporter.receipts import build_payload, load_or_create_key, sign_receipt, verify_receipt


def test_receipt_signature_roundtrip(tmp_path):
    key = load_or_create_key(str(tmp_path / "receipts.pem"))
    payload = build_payload(1, "contract.pdf", "ab" * 32, "2024-01-01T00:00:00+00:00")
    sig = sign_receipt(key, payload)
    verify_receipt(key.public_key(), payload, sig)


def test_key_is_reused(tmp_path):
    path = str(tmp_path / "receipts.pem")
    a = load_or_create_key(path)
    b = load_or_create_key(path)
    assert a.private_numbers() == b.private_numbers()
