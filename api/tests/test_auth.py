from types import SimpleNamespace

from app import auth


def test_password_hash_roundtrip():
    stored = auth.hash_password("correct horse battery")
    assert auth.check_password("correct horse battery", stored)
    assert not auth.check_password("wrong", stored)


def test_token_roundtrip():
    user = SimpleNamespace(id=7, email="a@example.com")
    token = auth.issue_token(user)
    claims = auth.decode_token(token)
    assert claims["sub"] == "7"
