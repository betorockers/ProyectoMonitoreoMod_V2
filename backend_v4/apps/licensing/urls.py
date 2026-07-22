from django.urls import path
from . import views

urlpatterns = [
    path('info/', views.hwid_info_view, name='hwid_info'),
]
