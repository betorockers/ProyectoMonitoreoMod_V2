"""
Argos Guard Enterprise v4.0 - Master URL Configuration.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.monitoring.urls')),
    path('osint/', include('apps.osint.urls')),
    path('security/', include('apps.security.urls')),
    path('licensing/', include('apps.licensing.urls')),
]
