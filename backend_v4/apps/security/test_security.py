"""
Argos Guard Enterprise v4.0 - Security Unit Tests.
"""
import pytest
from apps.security.services import hash_password, verify_password, generate_jwt_pair

def test_argon2id_hashing():
    raw_pass = "ArgosSecurity2026!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(hashed, raw_pass) is True
    assert verify_password(hashed, "WrongPassword") is False

def test_jwt_generation():
    tokens = generate_jwt_pair("betorock", "super_admin")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
