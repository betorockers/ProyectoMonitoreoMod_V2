"""
Argos Guard Enterprise v4.0 - Security Unit Tests.
"""
import pytest
from django.contrib.auth.hashers import make_password, check_password
from apps.security.services import generate_jwt_pair

def test_django_native_hashing():
    raw_pass = "ArgosSecurity2026!"
    hashed = make_password(raw_pass)
    assert hashed != raw_pass
    assert check_password(raw_pass, hashed) is True
    assert check_password("WrongPassword", hashed) is False

def test_jwt_generation():
    tokens = generate_jwt_pair("betorock", "super_admin")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
