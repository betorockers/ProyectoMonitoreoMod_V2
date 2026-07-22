"""
Argos Guard Enterprise v4.0 - OSINT Unit Tests.
"""
import pytest
from apps.osint.services import format_rut_with_dots, resolve_dns_records

def test_format_rut_with_dots():
    assert format_rut_with_dots("166911699") == "16.691.169-9"
    assert format_rut_with_dots("173763875") == "17.376.387-5"
    assert format_rut_with_dots("16.691.169-9") == "16.691.169-9"

def test_dns_resolution_local():
    dns_res = resolve_dns_records("localhost")
    assert isinstance(dns_res, dict)
    assert 'A' in dns_res
