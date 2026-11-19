import logging
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import AuditLog, Empleado

logger = logging.getLogger(__name__)


def client_ip(request):
    return request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')


class AccountBlockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            logout(request)
            return redirect('login')
        return self.get_response(request)


class AttendanceReminderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            hoy = timezone.localdate()
            if hoy.weekday() < 5:
                try:
                    empleado = request.user.empleado
                except Empleado.DoesNotExist:
                    empleado = None
                if empleado and not empleado.asistencias.filter(fecha=hoy, entrada__isnull=False).exists():
                    request.session.setdefault('attendance_reminder', 'Recuerda registrar tu entrada de hoy.')
                    messages.info(request, 'Recuerda registrar tu entrada de hoy.')
        return self.get_response(request)


class AttendanceTimeValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/asistencia/') and request.method == 'POST' and request.user.is_authenticated:
            ahora = timezone.localtime()
            hora = ahora.hour + ahora.minute / 60
            tipo = request.POST.get('tipo')
            permitido = (tipo == 'entrada' and 6 <= hora <= 10) or (tipo == 'salida' and 15 <= hora <= 20)
            if not permitido:
                return redirect('dashboard')
        return self.get_response(request)


class AttendanceAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method == 'POST' and request.user.is_authenticated:
            if request.path.startswith(('/asistencia/', '/permisos/', '/admin/rrhh/correccion')):
                AuditLog.objects.create(
                    usuario=request.user,
                    ip=client_ip(request),
                    accion=request.path,
                    detalle=f'Metodo POST, estado HTTP {response.status_code}',
                )
                logger.info(
                    'AUDITORIA usuario=%s ip=%s accion=%s estado=%s',
                    request.user.username, client_ip(request), request.path, response.status_code,
                )
        if response.status_code in (403, 401):
            logger.warning(
                'ACCESO_NO_AUTORIZADO usuario=%s ip=%s accion=%s',
                getattr(request.user, 'username', 'anonimo'), client_ip(request), request.path,
            )
        return response
