from src.core.security import hash_password, verify_password

def test_hash_and_verify_password_roundtrip():
    pw = "MyStrongPass123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("wrong", hashed) is False
