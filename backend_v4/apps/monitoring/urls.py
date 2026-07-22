from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('partial/nodes/', views.telemetry_nodes_partial, name='telemetry_nodes_partial'),
    path('node/add/', views.add_node, name='add_node'),
    path('node/remove/', views.remove_node, name='remove_node'),
    path('partial/map/', views.tactical_map_partial, name='tactical_map_partial'),
    path('partial/history/', views.event_history_partial, name='event_history_partial'),
    path('partial/video/', views.video_surveillance_partial, name='video_surveillance_partial'),
    path('partial/pdf-panel/', views.pdf_report_panel_partial, name='pdf_report_panel_partial'),
    path('export/json/', views.export_nodes_json, name='export_nodes_json'),
    path('import-nodes/', views.import_nodes_json, name='import_nodes_json'),
    path('export/pdf/', views.generate_pdf_report, name='generate_pdf_report'),
    path('export/backup/', views.backup_sqlite, name='backup_sqlite'),
    path('camera/add/', views.add_camera, name='add_camera'),
    path('camera/remove/', views.remove_camera, name='remove_camera'),
]
