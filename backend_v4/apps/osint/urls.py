from django.urls import path
from . import views

urlpatterns = [
    path('', views.osint_tab_view, name='osint_main'),
    path('rut/', views.query_rut_partial, name='query_rut_partial'),
    path('ppu/', views.query_ppu_partial, name='query_ppu_partial'),
    path('dns/', views.query_dns_partial, name='query_dns_partial'),
    path('geografia/', views.query_geografia_partial, name='query_geografia_partial'),
    path('fugas/', views.query_fugas_partial, name='query_fugas_partial'),
    path('reputacion/', views.query_reputacion_partial, name='query_reputacion_partial'),
    path('infra/', views.query_infra_partial, name='query_infra_partial'),
    path('whois/', views.query_whois_partial, name='query_whois_partial'),
    path('ipgeo/', views.query_ipgeo_partial, name='query_ipgeo_partial'),
    path('web/', views.query_web_partial, name='query_web_partial'),
    path('puertos/', views.query_puertos_partial, name='query_puertos_partial'),
    path('subdominios/', views.query_subdominios_partial, name='query_subdominios_partial'),
    path('email/', views.query_email_partial, name='query_email_partial'),
    path('traceroute/', views.query_traceroute_partial, name='query_traceroute_partial'),
    path('lan_scan/', views.query_lan_scan_partial, name='query_lan_scan_partial'),
]
