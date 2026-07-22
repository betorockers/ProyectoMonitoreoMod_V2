"""
Argos Guard Enterprise v4.0 - Core Unit Tests.
"""
import pytest
import asyncio
from apps.core.path_resolver import PathResolver
from apps.core.async_runner import NetworkProbeRunner

def test_path_resolver_singleton():
    res1 = PathResolver()
    res2 = PathResolver()
    assert res1 is res2
    assert res1.base_dir.exists()
    assert res1.app_data_dir.exists()

@pytest.mark.asyncio
async def test_network_probe_runner():
    res = await NetworkProbeRunner.ping_host("127.0.0.1", port=80, timeout=0.5)
    assert "host" in res
    assert "status" in res
    assert "latency_ms" in res
