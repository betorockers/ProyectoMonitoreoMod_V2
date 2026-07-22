"""
Argos Guard Enterprise v4.0 - Licensing Unit Tests.
"""
import pytest
from apps.licensing.services import get_system_hwid

def test_get_system_hwid():
    hwid = get_system_hwid()
    assert isinstance(hwid, str)
    assert len(hwid) > 0
