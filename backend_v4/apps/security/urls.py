from django.urls import path
from . import views

urlpatterns = [
    path('setup/', views.setup_view, name='setup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('partial/users/', views.user_management_partial, name='user_management_partial'),

    # Configuration POST endpoints
    path('config/create-user/', views.create_user, name='config_create_user'),
    path('config/telegram/', views.save_telegram, name='config_save_telegram'),
    path('config/api-key/', views.save_api_key, name='config_save_api_key'),
    path('config/webhook/', views.save_webhook, name='config_save_webhook'),
    path('config/sla/', views.save_sla, name='config_save_sla'),
    path('config/params/', views.save_system_params, name='config_save_params'),
    path('config/user/delete/<int:user_id>/', views.delete_user, name='config_delete_user'),
    path('shutdown/', views.shutdown_system, name='shutdown'),
]
