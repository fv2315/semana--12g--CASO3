from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('asistencia/', views.marcar_asistencia, name='marcar_asistencia'),
    path('permisos/', views.solicitar_permiso, name='solicitar_permiso'),
    path('permisos/<int:permiso_id>/resolver/', views.resolver_permiso, name='resolver_permiso'),
    path('reportes/', views.reportes, name='reportes'),
    path('exportar-asistencia/', views.exportar_asistencia, name='exportar_asistencia'),
]
