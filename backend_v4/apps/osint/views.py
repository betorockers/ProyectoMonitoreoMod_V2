"""
Argos Guard Enterprise v4.0 - OSINT Views (HTMX Enabled).
"""
from django.shortcuts import render
from django.http import JsonResponse
from .services import (
    scrape_rut, scrape_ppu, resolve_dns_records,
    query_geografia, query_fugas, query_reputacion, query_infra,
    query_whois, query_ipgeo, query_web, query_puertos,
    query_subdominios, query_email, query_traceroute,
    scan_lan_security,
)
from .models import OsintQueryLog

def osint_tab_view(request):
    """Página principal del panel OSINT por pestañas."""
    return render(request, 'osint/intel_panel.html')

def query_rut_partial(request):
    rut = request.GET.get('rut', '').strip()
    if not rut: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un RUT válido.'})
    try:
        result = scrape_rut(rut)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="RUT", query_term=rut, result_json=str(result))
        
        # Visualmente mostrar únicamente Nombre y RUT
        filtered_result = {
            "Nombre": result.get("Nombre", ""),
            "RUT": result.get("RUT", "")
        }
        return render(request, 'osint/partials/result_card.html', {'result': filtered_result, 'title': f'RUT: {rut}'})
    except Exception as e:
        return render(request, 'osint/partials/result_card.html', {'error': f'Error en módulo OSINT RUT: {str(e)}'})

def query_ppu_partial(request):
    ppu = request.GET.get('ppu', '').strip()
    if not ppu: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese una PPU válida.'})
    try:
        result = scrape_ppu(ppu)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="PPU", query_term=ppu, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'PPU: {ppu.upper()}'})
    except Exception as e:
        return render(request, 'osint/partials/result_card.html', {'error': f'Error en módulo OSINT PPU: {str(e)}'})

def query_dns_partial(request):
    domain = request.GET.get('domain', '').strip()
    if not domain: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un dominio válido.'})
    try:
        result = resolve_dns_records(domain)
        OsintQueryLog.objects.create(module_type="DNS", query_term=domain, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'DNS: {domain}'})
    except Exception as e:
        return render(request, 'osint/partials/result_card.html', {'error': f'Error en módulo DNS: {str(e)}'})

def query_geografia_partial(request):
    city = request.GET.get('city', '').strip()
    if not city: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese una ciudad válida.'})
    try:
        result = query_geografia(city)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="GEOGRAFIA", query_term=city, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Geografía y Clima: {city}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_fugas_partial(request):
    email = request.GET.get('email', '').strip()
    if not email: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un email válido.'})
    try:
        result = query_fugas(email)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="FUGAS", query_term=email, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Fugas: {email}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_reputacion_partial(request):
    ip = request.GET.get('ip', '').strip()
    if not ip: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese una IP válida.'})
    try:
        result = query_reputacion(ip)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="REPUTACION", query_term=ip, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Reputación: {ip}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_infra_partial(request):
    target = request.GET.get('target', '').strip()
    if not target: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un target válido.'})
    try:
        result = query_infra(target)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="INFRAESTRUCTURA", query_term=target, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Infraestructura: {target}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_whois_partial(request):
    domain = request.GET.get('domain', '').strip()
    if not domain: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un dominio válido.'})
    try:
        result = query_whois(domain)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="WHOIS", query_term=domain, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'WHOIS: {domain}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_ipgeo_partial(request):
    ip = request.GET.get('ip', '').strip()
    if not ip: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese una IP válida.'})
    try:
        result = query_ipgeo(ip)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="IPGEO", query_term=ip, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'IP Geo: {ip}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_web_partial(request):
    url = request.GET.get('url', '').strip()
    if not url: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese una URL válida.'})
    try:
        result = query_web(url)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="WEB", query_term=url, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Análisis Web: {url}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_puertos_partial(request):
    target = request.GET.get('target', '').strip()
    if not target: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un target válido.'})
    try:
        result = query_puertos(target)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="PUERTOS", query_term=target, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Puertos: {target}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_subdominios_partial(request):
    domain = request.GET.get('domain', '').strip()
    if not domain: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un dominio válido.'})
    try:
        result = query_subdominios(domain)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="SUBDOMINIOS", query_term=domain, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Subdominios: {domain}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_email_partial(request):
    email = request.GET.get('email', '').strip()
    if not email: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un email válido.'})
    try:
        result = query_email(email)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="EMAIL", query_term=email, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Email: {email}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})

def query_traceroute_partial(request):
    target = request.GET.get('target', '').strip()
    if not target: return render(request, 'osint/partials/result_card.html', {'error': 'Por favor ingrese un target válido.'})
    try:
        result = query_traceroute(target)
        if isinstance(result, dict) and "error" in result: return render(request, 'osint/partials/result_card.html', {'error': result["error"]})
        OsintQueryLog.objects.create(module_type="TRACEROUTE", query_term=target, result_json=str(result))
        return render(request, 'osint/partials/result_card.html', {'result': result, 'title': f'Traceroute: {target}'})
    except Exception as e: return render(request, 'osint/partials/result_card.html', {'error': str(e)})


def query_lan_scan_partial(request):
    """
    Escanea la subred LAN local en busca de hosts activos y servicios inseguros.
    """
    subnet = request.GET.get('subnet', '').strip()
    max_hosts = int(request.GET.get('max_hosts', 60))
    import re as _re
    if subnet and not _re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}$', subnet):
        return render(request, 'osint/partials/lan_scan_result.html',
                      {'error': 'Formato de subred inválido. Use formato: 192.168.1'})
    try:
        result = scan_lan_security(subnet=subnet, max_hosts=max_hosts)
        OsintQueryLog.objects.create(
            module_type="LAN_SCAN",
            query_term=result.get('subnet', subnet or 'auto'),
            result_json=str({
                'activos': result['hosts_activos'],
                'criticos': result['hosts_criticos'],
                'altos': result['hosts_altos'],
            })
        )
        return render(request, 'osint/partials/lan_scan_result.html', {'result': result})
    except Exception as e:
        return render(request, 'osint/partials/lan_scan_result.html',
                      {'error': f'Error en escáner LAN: {str(e)}'})


