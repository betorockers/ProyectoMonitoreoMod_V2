import sys
import os
import django
import pytest

# Configurar Django para pytest
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend_v4'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.osint.services import (
    scrape_rut, scrape_ppu, resolve_dns_records,
    query_geografia, query_fugas, query_reputacion, query_infra,
    query_whois, query_ipgeo, query_web, query_puertos,
    query_subdominios, query_email, query_traceroute
)
from apps.core.models import ApiKeyConfig

@pytest.mark.django_db
def test_scrape_rut():
    rut_test = "16.691.169-9"
    result = scrape_rut(rut_test)
    assert isinstance(result, dict)
    assert "error" not in result or "timeout" in result.get("error", "").lower()

@pytest.mark.django_db
def test_scrape_ppu():
    ppu_test = "TYCC70"
    result = scrape_ppu(ppu_test)
    assert isinstance(result, dict)
    assert "error" not in result or "timeout" in result.get("error", "").lower()

def test_resolve_dns_records():
    domain_test = "betograf.cl"
    result = resolve_dns_records(domain_test)
    assert isinstance(result, dict)
    assert "A" in result

def test_query_geografia():
    city = "Santiago"
    result = query_geografia(city)
    assert isinstance(result, dict)
    assert "Coordenadas" in result

@pytest.mark.django_db
def test_query_fugas():
    # Requiere API key, testeamos manejo de falta de llave
    email = "contacto@betograf.cl"
    result = query_fugas(email)
    assert isinstance(result, dict)

@pytest.mark.django_db
def test_query_reputacion():
    ip = "8.8.8.8"
    result = query_reputacion(ip)
    assert isinstance(result, dict)

@pytest.mark.django_db
def test_query_infra():
    target = "betograf.cl"
    result = query_infra(target)
    assert isinstance(result, dict)

def test_query_whois():
    domain = "app.meipass.com"
    result = query_whois(domain)
    assert isinstance(result, dict)

def test_query_ipgeo():
    ip = "1.1.1.1"
    result = query_ipgeo(ip)
    assert isinstance(result, dict)

def test_query_web():
    url = "betograf.cl"
    result = query_web(url)
    assert isinstance(result, dict)
    assert "URL" in result

def test_query_puertos():
    target = "betograf.cl"
    result = query_puertos(target)
    assert isinstance(result, dict)

def test_query_subdominios():
    domain = "betograf.cl"
    result = query_subdominios(domain)
    assert isinstance(result, dict)

def test_query_email():
    email = "controlaccesos@anvic.cl"
    result = query_email(email)
    assert isinstance(result, dict)

def test_query_traceroute():
    target = "8.8.8.8"
    result = query_traceroute(target)
    assert isinstance(result, dict)
