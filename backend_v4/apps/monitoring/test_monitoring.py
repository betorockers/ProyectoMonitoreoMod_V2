"""
Argos Guard Enterprise v4.0 - Monitoring Unit Tests.
"""
import pytest
from django.urls import reverse
from apps.monitoring.models import TargetNode, CameraStream

@pytest.mark.django_db
def test_target_node_creation():
    node = TargetNode.objects.create(
        label="Router Principal",
        host="192.168.1.1",
        port=80,
        protocol="HTTP",
        status="online"
    )
    assert node.id is not None
    assert str(node) == "Router Principal (192.168.1.1:80)"

@pytest.mark.django_db
def test_dashboard_view(client):
    url = reverse('dashboard')
    response = client.get(url)
    assert response.status_code == 200
    assert "ARGOS GUARD" in response.content.decode().upper()

@pytest.mark.django_db
def test_telemetry_nodes_partial(client):
    TargetNode.objects.create(label="Server Alpha", host="10.0.0.1", port=443)
    url = reverse('telemetry_nodes_partial')
    response = client.get(url)
    assert response.status_code == 200
    assert "Server Alpha" in response.content.decode()
