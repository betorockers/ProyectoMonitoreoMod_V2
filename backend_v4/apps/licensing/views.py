from django.http import JsonResponse
from .services import get_system_hwid

def hwid_info_view(request):
    """Retorna información del HWID de la máquina host."""
    hwid = get_system_hwid()
    return JsonResponse({"status": "active", "hwid": hwid, "tier": "ENTERPRISE AIR-GAPPED"})
