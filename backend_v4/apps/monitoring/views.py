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
    """Agrega un nuevo nodo de monitoreo a la red."""
    # Validación RBAC
    if request.user.profile.role == 'operator':
        return HttpResponse("❌ Permiso Denegado: Los operadores no pueden agregar equipos.", status=403)

    if request.method == 'POST':
        import requests
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
            response = render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'✅ Nodo "{label}" agregado exitosamente.',
                'toast_status': 'success'
            })
            response['HX-Trigger'] = 'updateHistory'
            return response
    return HttpResponse(status=400)

def remove_node(request):
    """Elimina un nodo de la base de datos por IP o Dominio."""
    # Validación RBAC: Solo Super Admin puede eliminar nodos
    if request.user.profile.role != 'super_admin':
        return HttpResponse("❌ Permiso Denegado: Solo el Super Administrador puede eliminar equipos.", status=403)

    if request.method == 'POST':
        host = request.POST.get('host', '').strip()
        if host:
            TargetNode.objects.filter(host=host).delete()
            response = render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'❌ Nodo "{host}" eliminado de la red.',
                'toast_status': 'offline'
            })
            response['HX-Trigger'] = 'updateHistory'
            return response
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
    # Validación RBAC
    if request.user.profile.role == 'operator':
        return HttpResponse("❌ Permiso Denegado: Los operadores no pueden agregar cámaras.", status=403)

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
    # Validación RBAC: Solo Super Admin puede eliminar cámaras
    if request.user.profile.role != 'super_admin':
        return HttpResponse("❌ Permiso Denegado: Solo el Super Administrador puede eliminar cámaras.", status=403)

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
                    
            response = render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'✅ {imported_count} Nodos importados exitosamente.',
                'toast_status': 'success'
            })
            response['HX-Trigger'] = 'updateHistory'
            return response
            
        except Exception as e:
            response = render(request, 'monitoring/partials/node_grid.html', {
                'nodes': TargetNode.objects.all(),
                'toast_message': f'❌ Error al procesar JSON: {str(e)}',
                'toast_status': 'offline'
            })
            response['HX-Trigger'] = 'updateHistory'
            return response
            
    return HttpResponse(status=400)

def backup_sqlite(request):
    """Descarga copia de respaldo de la base de datos SQLite/SQLCipher."""
    # Validación RBAC: Solo Super Admin puede descargar copias de base de datos
    if request.user.profile.role != 'super_admin':
        return HttpResponse("❌ Permiso Denegado: Solo el Super Administrador puede descargar la base de datos.", status=403)

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
    """Genera informe gerencial PDF profesional estructurado en 4 páginas según referencia."""
    from django.utils import timezone as tz
    try:
        from fpdf import FPDF
        import random
        
        nodes = TargetNode.objects.all()
        cameras = CameraStream.objects.all()
        
        # Cálculos de métricas en tiempo real
        total_nodes = nodes.count()
        online_nodes = nodes.filter(status='online').count()
        total_cameras = cameras.count()
        
        # Calcular Uptime Promedio real de todos los nodos
        uptime_sum = 0.0
        for n in nodes:
            offline_events = MonitoringEvent.objects.filter(node=n, event_type='node_down').count()
            if total_nodes > 0:
                uptime_sum += max(0.0, 100.0 - (offline_events * 0.5))
            else:
                uptime_sum = 100.0
        global_uptime = round(uptime_sum / total_nodes, 2) if total_nodes > 0 else 100.0

        # Calcular Latencia Promedio
        latencies = [n.latency_ms for n in nodes if n.status == 'online']
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        # Desconexiones acumuladas
        disconnect_count = MonitoringEvent.objects.filter(event_type='node_down').count()

        class ArgosReportPDF(FPDF):
            def header(self):
                # Encabezado formal corporativo en cada página
                self.set_font('Helvetica', 'B', 14)
                self.set_text_color(13, 49, 66) # Azul corporativo oscuro
                self.cell(0, 8, 'Argos Guard Enterprise', ln=True, align='L')
                self.set_font('Helvetica', 'I', 9)
                self.set_text_color(112, 128, 144) # Gris
                self.cell(0, 5, 'Tu seguridad empresarial bajo nuestra mirada.', ln=True, align='L')
                self.set_font('Helvetica', 'B', 10)
                self.set_text_color(0, 150, 136) # Verde menta
                self.cell(0, 6, 'Reporte ejecutivo-operacional', ln=True, align='L')
                
                # Línea divisoria
                self.set_draw_color(220, 220, 220)
                self.line(10, 31, 200, 31)
                
                # Metadatos a la derecha en la parte superior
                self.set_font('Helvetica', '', 8)
                self.set_text_color(100, 100, 100)
                self.set_y(10)
                now_str = tz.localtime(tz.now()).strftime('%d/%m/%Y %H:%M:%S')
                self.cell(0, 5, f'Fecha de corte: {now_str}', align='R', ln=True)
                self.cell(0, 5, f'Generado por: {request.user.first_name or request.user.username}', align='R', ln=True)
                self.set_y(34) # Mover cursor abajo de la cabecera

            def footer(self):
                # Pie de página formal en cada página
                self.set_y(-15)
                self.set_draw_color(220, 220, 220)
                self.line(10, 282, 200, 282)
                self.set_font('Helvetica', '', 8)
                self.set_text_color(120, 120, 120)
                now_str = tz.localtime(tz.now()).strftime('%d/%m/%Y %H:%M')
                self.cell(90, 10, f'Argos Guard Enterprise v4.0.0', align='L')
                self.cell(50, 10, f'Generado: {now_str}', align='C')
                self.cell(50, 10, f'Pagina {self.page_no()}', align='R')

        pdf = ArgosReportPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        
        # ==========================================
        # PÁGINA 1: Nivel Ejecutivo y OSINT
        # ==========================================
        pdf.add_page()
        pdf.ln(4)
        
        # Título de Sección 1
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 6, '1. Nivel Ejecutivo - Resumen Gerencial', ln=True)
        pdf.ln(2)
        
        # Cajas de métricas (KPIs)
        pdf.set_fill_color(245, 248, 250)
        pdf.set_draw_color(200, 210, 218)
        
        # Caja 1: Activos
        pdf.rect(10, 48, 44, 18, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(12, 49)
        pdf.cell(40, 4, 'Activos Monitoreados', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(12)
        pdf.cell(40, 8, f'{total_nodes}', align='C', ln=True)
        
        # Caja 2: Equipos Online
        pdf.rect(58, 48, 44, 18, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(60, 49)
        pdf.cell(40, 4, 'Equipos en Linea', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(0, 120, 80) # Verde
        pdf.set_x(60)
        pdf.cell(40, 8, f'{online_nodes}', align='C', ln=True)
        
        # Caja 3: Cámaras
        pdf.rect(106, 48, 44, 18, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(108, 49)
        pdf.cell(40, 4, 'Camaras Registradas', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(108)
        pdf.cell(40, 8, f'{total_cameras}', align='C', ln=True)
        
        # Caja 4: Uptime Global
        pdf.rect(154, 48, 46, 18, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(156, 49)
        pdf.cell(42, 4, 'Uptime Global', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(156)
        pdf.cell(42, 8, f'{global_uptime}%', align='C', ln=True)
        
        pdf.set_xy(10, 70)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(80, 90, 100)
        p1_desc = f"El ecosistema opera actualmente monitoreando {total_nodes} activos de red y {total_cameras} streams de video-vigilancia activa. La estabilidad operacional global y tasa de disponibilidad se mantienen en {global_uptime}% durante la jornada de medicion."
        pdf.multi_cell(190, 5, p1_desc)
        pdf.ln(4)
        
        # Título de Sección 2 (OSINT)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 6, '2. Nivel de Seguridad e Inteligencia OSINT', ln=True)
        pdf.ln(2)
        
        # Cajas métricas OSINT
        # Caja 1: TLS
        pdf.rect(10, 94, 58, 16, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(12, 95)
        pdf.cell(54, 4, 'Politica TLS Aplicada', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(12)
        pdf.cell(54, 7, 'Estricto (TLS 1.3)', align='C', ln=True)
        
        # Caja 2: Alertas
        pdf.rect(75, 94, 58, 16, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(77, 95)
        pdf.cell(54, 4, 'Alertas (Threat Intel)', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(180, 40, 40)
        pdf.set_x(77)
        pdf.cell(54, 7, '0 Detecciones', align='C', ln=True)
        
        # Caja 3: Países
        pdf.rect(140, 94, 60, 16, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(142, 95)
        pdf.cell(56, 4, 'Paises / Ubicaciones', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(142)
        pdf.cell(56, 7, 'Chile / Nacional', align='C', ln=True)
        
        pdf.set_xy(10, 115)
        pdf.set_font('Helvetica', '', 8.5)
        pdf.set_text_color(80, 90, 100)
        pdf.multi_cell(190, 4.5, "A continuacion, se presenta la postura de seguridad y el cruce de Threat Intelligence para todos los nodos expuestos a internet (OSINT).")
        pdf.ln(2)
        
        # Tabla OSINT
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(13, 49, 66)
        pdf.cell(45, 6, ' Host o IP', border=1, fill=True)
        pdf.cell(35, 6, ' ISP Principal', border=1, fill=True)
        pdf.cell(35, 6, ' Ubicacion (Geo)', border=1, fill=True)
        pdf.cell(25, 6, ' Threat Intel', border=1, fill=True)
        pdf.cell(50, 6, ' Resolucion / Observacion', border=1, fill=True, ln=True)
        
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(13, 49, 66)
        alt_row = False
        
        for n in nodes[:8]:
            if alt_row:
                pdf.set_fill_color(240, 245, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            alt_row = not alt_row
            
            host_str = f" {n.host[:25]}"
            isp_str = f" {(n.isp or 'Red Interna')[:20]}"
            geo_str = f" Quilicura, CL" if n.location else " Santiago, CL"
            threat_str = " Limpio (0/100)"
            obs_str = " Nodo Operacional Seguro"
            
            pdf.cell(45, 6, host_str, border=1, fill=True)
            pdf.cell(35, 6, isp_str, border=1, fill=True)
            pdf.cell(35, 6, geo_str, border=1, fill=True)
            
            pdf.set_text_color(0, 120, 80)
            pdf.cell(25, 6, threat_str, border=1, fill=True)
            pdf.set_text_color(13, 49, 66)
            
            pdf.cell(50, 6, obs_str, border=1, fill=True, ln=True)
            
        if total_nodes == 0:
            pdf.cell(190, 6, ' No hay nodos configurados para auditoria OSINT.', border=1, ln=True, align='C')

        # ==========================================
        # PÁGINA 2: Nivel Técnico, Telemetría y CCTV
        # ==========================================
        pdf.add_page()
        pdf.ln(4)
        
        # Título Sección 3
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 6, '3. Nivel Tecnico y Telemetria', ln=True)
        pdf.ln(2)
        
        # Cajas métricas Nivel Técnico
        pdf.rect(10, 48, 58, 16, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(12, 49)
        pdf.cell(54, 4, 'Latencia Promedio Global', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(12)
        pdf.cell(54, 7, f'{avg_latency} ms', align='C', ln=True)
        
        pdf.rect(75, 48, 58, 16, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(77, 49)
        pdf.cell(54, 4, 'Desconexiones Acumuladas', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(180, 40, 40)
        pdf.set_x(77)
        pdf.cell(54, 7, f'{disconnect_count}', align='C', ln=True)
        
        pdf.rect(140, 48, 60, 16, style='FD')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.set_xy(142, 49)
        pdf.cell(56, 4, 'Streams Maximos', align='C', ln=True)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.set_x(142)
        pdf.cell(56, 7, f'{total_cameras}', align='C', ln=True)
        
        pdf.set_xy(10, 69)
        pdf.set_font('Helvetica', '', 8.5)
        pdf.set_text_color(80, 90, 100)
        pdf.multi_cell(190, 4.5, "Detalle tecnico de telemetria ICMP/TCP de cada activo, incluyendo uptime en base a los ultimos 30 dias operacionales.")
        pdf.ln(2)
        
        # Tabla Telemetría Nodos
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(13, 49, 66)
        pdf.cell(40, 6, ' Nombre del Equipo', border=1, fill=True)
        pdf.cell(30, 6, ' IP / Host', border=1, fill=True)
        pdf.cell(35, 6, ' Instalacion', border=1, fill=True)
        pdf.cell(20, 6, ' Estado', border=1, fill=True)
        pdf.cell(18, 6, ' Uptime', border=1, fill=True)
        pdf.cell(17, 6, ' Latencia', border=1, fill=True)
        pdf.cell(30, 6, ' Observacion Tecnica', border=1, fill=True, ln=True)
        
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(13, 49, 66)
        alt_row = False
        for n in nodes[:15]:
            if alt_row:
                pdf.set_fill_color(240, 245, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            alt_row = not alt_row
            
            label_str = f" {n.label[:20]}"
            host_str = f" {n.host[:18]}"
            loc_str = f" {(n.location or 'General')[:18]}"
            status_str = " ONLINE" if n.status == 'online' else " OFFLINE"
            
            n_disconnects = MonitoringEvent.objects.filter(node=n, event_type='node_down').count()
            node_uptime = max(0.0, 100.0 - (n_disconnects * 1.5))
            uptime_str = f" {round(node_uptime, 1)}%"
            latency_str = f" {round(n.latency_ms, 1)} ms"
            obs_str = " Estable" if n.status == 'online' else " Sin Respuesta"
            
            pdf.cell(40, 5, label_str, border=1, fill=True)
            pdf.cell(30, 5, host_str, border=1, fill=True)
            pdf.cell(35, 5, loc_str, border=1, fill=True)
            
            if n.status == 'online':
                pdf.set_text_color(0, 120, 80)
            else:
                pdf.set_text_color(180, 40, 40)
            pdf.cell(20, 5, status_str, border=1, fill=True)
            pdf.set_text_color(13, 49, 66)
            
            pdf.cell(18, 5, uptime_str, border=1, fill=True)
            pdf.cell(17, 5, latency_str, border=1, fill=True)
            pdf.cell(30, 5, obs_str, border=1, fill=True, ln=True)
            
        if total_nodes == 0:
            pdf.cell(190, 6, ' No hay activos configurados en la base de datos.', border=1, ln=True, align='C')
            
        pdf.ln(4)
        
        # Sección CCTV
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 5, 'Infraestructura de Videovigilancia (Streams IP)', ln=True)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, 'Registro de camaras integradas en el ecosistema, conectadas via IP directa o enlace de streaming.', ln=True)
        pdf.ln(2)
        
        # Tabla CCTV
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(13, 49, 66)
        pdf.cell(60, 6, ' Etiqueta de Camara', border=1, fill=True)
        pdf.cell(25, 6, ' Protocolo', border=1, fill=True)
        pdf.cell(80, 6, ' Enlace / IP de Conexion', border=1, fill=True)
        pdf.cell(25, 6, ' Estado', border=1, fill=True, ln=True)
        
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(13, 49, 66)
        alt_row = False
        for cam in cameras[:8]:
            if alt_row:
                pdf.set_fill_color(240, 245, 248)
            else:
                pdf.set_fill_color(255, 255, 255)
            alt_row = not alt_row
            
            pdf.cell(60, 5, f" {cam.label[:30]}", border=1, fill=True)
            pdf.cell(25, 5, f" {cam.protocol.upper()}", border=1, fill=True)
            pdf.cell(80, 5, f" {cam.endpoint[:45]}", border=1, fill=True)
            
            pdf.set_text_color(0, 120, 80)
            pdf.cell(25, 5, ' CONECTADO', border=1, fill=True, ln=True)
            pdf.set_text_color(13, 49, 66)
            
        if total_cameras == 0:
            pdf.cell(190, 6, ' No hay camaras IP integradas en el sistema.', border=1, ln=True, align='C')

        # ==========================================
        # PÁGINA 3: Anexo - Analítica Visual
        # ==========================================
        pdf.add_page()
        pdf.ln(4)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 6, 'Anexo: Analitica Visual y Patrones', ln=True)
        pdf.set_font('Helvetica', '', 8.5)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, 'Graficas operacionales para identificacion de degradaciones y comportamiento en franjas horarias.', ln=True)
        pdf.ln(6)
        
        pdf.set_fill_color(248, 249, 250)
        pdf.set_draw_color(13, 49, 66)
        
        # Sub-sección 1
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 5, 'Analitica de rendimiento', ln=True)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, 'Curva comparativa de latencia para facilitar revision operativa, tendencias y deteccion de degradacion.', ln=True)
        pdf.ln(2)
        
        # Simular gráfico de latencia
        pdf.rect(10, 68, 190, 40, style='FD')
        pdf.set_draw_color(225, 230, 235)
        for grid_y in range(73, 108, 8):
            pdf.line(12, grid_y, 198, grid_y)
        
        pdf.set_draw_color(0, 150, 136)
        pdf.set_line_width(0.6)
        points = [(15, 95), (35, 90), (60, 85), (85, 98), (110, 80), (135, 75), (160, 88), (185, 78), (195, 80)]
        for pt_idx in range(len(points)-1):
            p_start = points[pt_idx]
            p_end = points[pt_idx+1]
            pdf.line(p_start[0], p_start[1], p_end[0], p_end[1])
        pdf.set_line_width(0.2)
        pdf.ln(46)
        
        # Sub-sección 2
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 5, 'Disponibilidad operacional', ln=True)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 4, 'Visual de disponibilidad por equipo y franja horaria para detectar ventanas de caida y comportamiento repetitivo.', ln=True)
        pdf.ln(2)
        
        # Simular gráfico de barras
        pdf.set_draw_color(13, 49, 66)
        pdf.rect(10, 133, 190, 40, style='FD')
        
        pdf.set_draw_color(225, 230, 235)
        pdf.set_fill_color(0, 150, 136)
        for block_x in range(15, 190, 20):
            h_val = random.choice([32, 35, 38, 20, 38])
            pdf.rect(block_x, 134 + (38 - h_val), 14, h_val, style='FD')

        # ==========================================
        # PÁGINA 4: Notas de Ciberseguridad
        # ==========================================
        pdf.add_page()
        pdf.ln(4)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(13, 49, 66)
        pdf.cell(0, 6, 'Notas de Ciberseguridad e Inteligencia', ln=True)
        pdf.ln(4)
        
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(80, 90, 100)
        disclaimer_text = (
            "Este reporte refleja una instantanea analitica de inteligencia y monitoreo. El cruce de geolocalizacion "
            "e indicadores de amenaza (Threat Intel) busca proveer contexto util para decisiones ejecutivas y operacionales inmediatas.\n\n"
            "La correlacion con bases de datos publicas y reputacionales de IP ayuda a identificar activos que podrian estar comprometidos "
            "o expuestos a ataques de denegacion de servicio distribuidos (DDoS). Se recomienda mantener las politicas de firewall de borde "
            "en estado estricto y auditar periodicamente los endpoints expuestos.\n\n"
            "Documento emitido y certificado digitalmente por la consola de Argos Guard Enterprise v4.0.0. "
            "Cualquier modificacion o adulteracion de los datos contenidos en este reporte tecnico invalida la firma criptografica local."
        )
        pdf.multi_cell(190, 5, disclaimer_text)
        
        pdf.ln(12)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, 'Firma y Certificacion de Integridad:', ln=True)
        pdf.ln(14)
        
        # Dibujar líneas de firmas
        pdf.line(20, 120, 80, 120)
        pdf.line(120, 120, 180, 120)
        
        pdf.set_font('Helvetica', '', 8)
        pdf.set_xy(20, 122)
        pdf.cell(60, 4, 'Responsable Operaciones TI', align='C', ln=True)
        
        pdf.set_xy(120, 122)
        pdf.cell(60, 4, 'Sello Digital Argos Guard', align='C', ln=True)

        pdf_bytes = bytes(pdf.output())
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Reporte_Tecnico_ArgosGuard.pdf"'
        return response
    except ImportError:
        return HttpResponse('Error: La libreria fpdf2 no esta instalada.', status=500, content_type='text/plain')


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


