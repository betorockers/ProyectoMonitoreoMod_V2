"""
Argos Guard Enterprise v4.0 - Monitoring & Telemetry Views.
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import TargetNode, CameraStream, MonitoringEvent
from django.utils import timezone

from django.contrib.auth.decorators import login_required

@login_required(login_url='/security/login/')
def dashboard(request):
    """Renderiza la Consola Táctica Cyberpunk Principal."""
    nodes = TargetNode.objects.all()
    cameras = CameraStream.objects.all()
    context = {
        'nodes': nodes,
        'cameras': cameras,
        'system_version': 'v4.0.0 Enterprise'
    }
    return render(request, 'monitoring/dashboard.html', context)

def telemetry_nodes_partial(request):
    """Fragmento parcial HTMX para actualizar las cards de nodos sin recarga."""
    from apps.monitoring.daemon import toast_queue
    import queue
    
    nodes = list(TargetNode.objects.all())
    
    context = {'nodes': nodes}
    
    # Extraer el último mensaje Toast de la cola si existe
    toast_message = None
    toast_status = None
    
    try:
        # Vaciamos la cola y nos quedamos con el último mensaje (o procesamos el último)
        while True:
            msg = toast_queue.get_nowait()
            toast_message = msg['message']
            toast_status = msg['status']
    except queue.Empty:
        pass
        
    if toast_message:
        context['toast_message'] = toast_message
        context['toast_status'] = toast_status
        
    return render(request, 'monitoring/partials/node_grid.html', context)

def add_node(request):
    """Agrega un nuevo nodo a la base de datos."""
    import requests
    if request.method == 'POST':
        host = request.POST.get('host', '').strip()
        label = request.POST.get('label', '').strip()
        mac_address = request.POST.get('mac_address', '').strip()
        location = request.POST.get('location', '').strip()
        if host and label:
            if location:
                label = f"{label} - {location}"
            
            # Geolocalizar
            lat, lon, isp, asn = None, None, None, None
            try:
                res = requests.get(f"http://ip-api.com/json/{host}", timeout=5).json()
                if res.get("status") == "success":
                    lat = res.get("lat")
                    lon = res.get("lon")
                    isp = res.get("isp")
                    asn = res.get("as")
            except Exception:
                pass
                
            # Fallback coordinates if ip-api fails or returns private IP
            if lat is None or lon is None:
                import random
                lat = -33.4489 + random.uniform(-0.01, 0.01)
                lon = -70.6693 + random.uniform(-0.01, 0.01)
                isp = isp or "Red Interna / Privada"

            TargetNode.objects.create(
                host=host, 
                label=label,
                mac_address=mac_address,
                latitude=lat,
                longitude=lon,
                isp=isp,
                asn=asn
            )
            return render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'✅ Nodo "{label}" agregado exitosamente.',
                'toast_status': 'success'
            })
    return HttpResponse(status=400)

def remove_node(request):
    """Elimina un nodo de la base de datos por IP o Dominio."""
    if request.method == 'POST':
        host = request.POST.get('host', '').strip()
        if host:
            TargetNode.objects.filter(host=host).delete()
            return render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'❌ Nodo "{host}" eliminado de la red.',
                'toast_status': 'offline'
            })
    return HttpResponse(status=400)

def tactical_map_partial(request):
    """Fragmento parcial HTMX para el Mapa Táctico Leaflet."""
    nodes = TargetNode.objects.all()
    return render(request, 'monitoring/partials/tactical_map.html', {'nodes': nodes})

def event_history_partial(request):
    """Fragmento parcial HTMX para el Historial de Eventos y Latencia Global."""
    from .models import MonitoringEvent, TargetNode
    from django.utils import timezone
    import datetime

    nodes = TargetNode.objects.all()
    events = MonitoringEvent.objects.all()[:50]

    # Calcular Uptime REAL de las últimas 24 horas para cada equipo
    now = timezone.now()
    since = now - datetime.timedelta(hours=24)
    total_seconds = 24.0 * 3600.0

    nodes_with_uptime = []
    for node in nodes:
        node_events = list(MonitoringEvent.objects.filter(
            node=node,
            created_at__gte=since
        ).order_by('created_at'))

        if not node_events:
            # Sin eventos registrados: depende de su estado actual
            uptime = 100.0 if node.status == 'online' else 0.0
        else:
            offline_seconds = 0.0
            last_down = None

            for ev in node_events:
                if ev.event_type == 'node_down':
                    last_down = ev.created_at
                elif ev.event_type == 'node_up' and last_down:
                    offline_seconds += (ev.created_at - last_down).total_seconds()
                    last_down = None

            # Si sigue caído al final del día
            if last_down:
                offline_seconds += (now - last_down).total_seconds()

            offline_seconds = min(offline_seconds, total_seconds)
            uptime = 100.0 * (1.0 - (offline_seconds / total_seconds))
            uptime = round(max(0.0, min(100.0, uptime)), 1)

        node.real_uptime = uptime
        nodes_with_uptime.append(node)

    return render(request, 'monitoring/partials/event_history.html', {'nodes': nodes_with_uptime, 'events': events})

def pdf_report_panel_partial(request):
    """Fragmento parcial HTMX para descarga de plantilla JSON y Reporte PDF."""
    return render(request, 'monitoring/partials/pdf_report_panel.html')

def video_surveillance_partial(request):
    """Fragmento parcial HTMX para la pestaña Video Vigilancia."""
    cameras = CameraStream.objects.all()
    return render(request, 'monitoring/partials/video_surveillance.html', {'cameras': cameras})

def add_camera(request):
    """Agrega una nueva cámara RTSP/HTTP/MJPEG/HLS/WebRTC."""
    if request.method == 'POST':
        # El modelo CameraStream usa 'label' y 'endpoint'
        label = request.POST.get('name', '').strip() or request.POST.get('label', '').strip()
        protocol = request.POST.get('protocol', 'RTSP').strip().upper()
        endpoint = request.POST.get('endpoint_url', '').strip() or request.POST.get('endpoint', '').strip()
        if label and endpoint:
            CameraStream.objects.create(label=label, protocol=protocol, endpoint=endpoint)
            cameras = CameraStream.objects.all()
            return render(request, 'monitoring/partials/video_surveillance.html', {
                'cameras': cameras,
                'toast_message': f'✅ Cámara "{label}" agregada exitosamente.',
                'toast_status': 'success'
            })
    return HttpResponse(status=400)

def remove_camera(request):
    """Elimina una cámara por label o id."""
    if request.method == 'POST':
        label = request.POST.get('name', '').strip() or request.POST.get('label', '').strip()
        if label:
            CameraStream.objects.filter(label=label).delete()
            cameras = CameraStream.objects.all()
            return render(request, 'monitoring/partials/video_surveillance.html', {
                'cameras': cameras,
                'toast_message': f'❌ Cámara "{label}" eliminada del sistema.',
                'toast_status': 'offline'
            })
    return HttpResponse(status=400)

def export_nodes_json(request):
    """Genera plantilla de nodos JSON para descarga."""
    sample_data = [
        {"ip": "10.88.22.54", "alias": "Servidor Core Santiago", "mac": "00:1A:2B:3C:4D:5E", "ping_interval": 5},
        {"ip": "192.168.1.1", "alias": "Gateway Valparaíso", "mac": "00:1A:2B:3C:4D:5F", "ping_interval": 5}
    ]
    response = JsonResponse(sample_data, safe=False, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="plantilla_equipos.json"'
    return response

def import_nodes_json(request):
    """Importa masivamente nodos desde un archivo JSON."""
    import json
    import requests
    import random
    
    if request.method == 'POST' and request.FILES.get('json_file'):
        try:
            json_file = request.FILES['json_file']
            data = json.load(json_file)
            
            imported_count = 0
            for item in data:
                ip = item.get('ip')
                alias = item.get('alias')
                mac = item.get('mac', '')
                
                if ip and alias:
                    # Geolocalizar o Fallback
                    lat, lon, isp, asn = None, None, None, None
                    try:
                        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=3).json()
                        if res.get("status") == "success":
                            lat = res.get("lat")
                            lon = res.get("lon")
                            isp = res.get("isp")
                            asn = res.get("as")
                    except:
                        pass
                        
                    if lat is None or lon is None:
                        lat = -33.4489 + random.uniform(-0.01, 0.01)
                        lon = -70.6693 + random.uniform(-0.01, 0.01)
                        isp = isp or "Red Interna / Privada"
                        
                    TargetNode.objects.create(
                        host=ip,
                        label=alias,
                        mac_address=mac,
                        latitude=lat,
                        longitude=lon,
                        isp=isp,
                        asn=asn
                    )
                    imported_count += 1
                    
            return render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'✅ {imported_count} Nodos importados exitosamente.',
                'toast_status': 'success'
            })
            
        except Exception as e:
            return render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'❌ Error al procesar JSON: {str(e)}',
                'toast_status': 'offline'
            })
            
    return HttpResponse(status=400)

def backup_sqlite(request):
    """Descarga copia de respaldo de la base de datos SQLite/SQLCipher."""
    import os
    from django.conf import settings
    db_path = settings.DATABASES['default'].get('NAME', 'db.sqlite3')
    if os.path.exists(db_path):
        with open(db_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/x-sqlite3')
            response['Content-Disposition'] = f'attachment; filename="argos_guard_backup.db"'
            return response
    return HttpResponse('Base de datos no encontrada.', status=404)

def generate_pdf_report(request):
    """Genera informe gerencial PDF usando fpdf2."""
    from django.utils import timezone as tz
    try:
        from fpdf import FPDF
        nodes = TargetNode.objects.all()
        events = MonitoringEvent.objects.all()[:50]

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'Argos Guard Enterprise v4.0 - Reporte Gerencial', ln=True, align='C')
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 8, f'Generado: {tz.now().strftime("%Y-%m-%d %H:%M:%S")} (America/Santiago)', ln=True, align='C')
        pdf.ln(6)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, f'Resumen de Nodos Monitoreados ({nodes.count()} total)', ln=True)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(70, 7, 'Label', border=1)
        pdf.cell(50, 7, 'Host', border=1)
        pdf.cell(25, 7, 'Estado', border=1)
        pdf.cell(30, 7, 'Latencia (ms)', border=1, ln=True)
        pdf.set_font('Helvetica', '', 9)
        for node in nodes:
            pdf.cell(70, 7, node.label[:35], border=1)
            pdf.cell(50, 7, node.host[:25], border=1)
            pdf.cell(25, 7, node.status.upper(), border=1)
            pdf.cell(30, 7, str(round(node.latency_ms, 2)), border=1, ln=True)
        pdf.ln(6)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, f'Últimos Eventos ({events.count()} mostrados)', ln=True)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(40, 7, 'Fecha', border=1)
        pdf.cell(30, 7, 'Severidad', border=1)
        pdf.cell(105, 7, 'Mensaje', border=1, ln=True)
        pdf.set_font('Helvetica', '', 8)
        for event in events:
            pdf.cell(40, 6, event.created_at.strftime('%Y-%m-%d %H:%M'), border=1)
            pdf.cell(30, 6, event.severity.upper(), border=1)
            pdf.cell(105, 6, event.message[:55], border=1, ln=True)

        pdf_bytes = bytes(pdf.output())
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Reporte_Gerencial_ArgosGuard.pdf"'
        return response
    except ImportError:
        return HttpResponse(
            'Error: La librería fpdf2 no está instalada. Ejecute: pip install fpdf2',
            status=500,
            content_type='text/plain'
        )


def check_monitoring_updates(request):
    """
    Endpoint ultraligero que verifica actualizaciones en toast_queue.
    Si hay cambios, extrae los elementos y retorna individualmente las tarjetas de nodos 
    y notificaciones toast modificadas mediante HTMX Out-of-Band (OOB) swapping.
    """
    import queue
    from apps.monitoring.daemon import toast_queue
    from django.template.loader import render_to_string
    
    if toast_queue.empty():
        return HttpResponse(status=204)
        
    html_payload = []
    processed_node_ids = set()
    
    try:
        while True:
            msg_data = toast_queue.get_nowait()
            node_id = msg_data.get('node_id')
            msg_text = msg_data.get('message')
            status = msg_data.get('status')
            
            # 1. Renderizar la tarjeta del nodo afectada de forma OOB (si se indica)
            if node_id and node_id not in processed_node_ids:
                try:
                    node = TargetNode.objects.get(id=node_id)
                    node_html = render_to_string(
                        'monitoring/partials/node_card.html', 
                        {'node': node, 'oob': True}
                    )
                    html_payload.append(node_html)
                    processed_node_ids.add(node_id)
                except TargetNode.DoesNotExist:
                    pass
            
            # 2. Renderizar el toast OOB para que aparezca en el contenedor general
            if msg_text:
                toast_html = render_to_string(
                    'security/partials/_config_toast.html',
                    {'message': msg_text, 'status': status}
                )
                # Envolver en un div con hx-swap-oob="beforeend:#toast-container"
                wrapped_toast = f'<div hx-swap-oob="beforeend:#toast-container">{toast_html}</div>'
                html_payload.append(wrapped_toast)
                
    except queue.Empty:
        pass
        
    if html_payload:
        return HttpResponse("\n".join(html_payload), content_type="text/html")
    return HttpResponse(status=204)


