from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import AsistenciaForm, PermisoForm
from .models import Asistencia, Empleado, Permiso


def tiene_grupo(user, nombre):
    return user.is_superuser or user.groups.filter(name=nombre).exists()


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
    else:
        form = AuthenticationForm(request)
    return render(request, 'rrhh/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    empleado = getattr(request.user, 'empleado', None)
    permisos = Permiso.objects.none()
    asistencias = Asistencia.objects.none()
    if empleado:
        permisos = Permiso.objects.filter(empleado=empleado).select_related('empleado', 'aprobado_por')
        asistencias = Asistencia.objects.filter(empleado=empleado).select_related('empleado')
    elif tiene_grupo(request.user, 'Admin RRHH'):
        permisos = Permiso.objects.filter(estado='pendiente').select_related('empleado', 'empleado__area')
    elif tiene_grupo(request.user, 'Jefe de Area'):
        if empleado:
            permisos = Permiso.objects.filter(
                empleado__area=empleado.area,
                estado='pendiente',
            ).select_related('empleado', 'empleado__area')
    return render(request, 'rrhh/dashboard.html', {
        'empleado': empleado, 'permisos': permisos, 'asistencias': asistencias,
    })


@login_required
def marcar_asistencia(request):
    if not hasattr(request.user, 'empleado'):
        raise PermissionDenied
    empleado = request.user.empleado
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        try:
            AsistenciaForm().save(empleado, tipo)
            messages.success(request, f'Marcacion {tipo} registrada.')
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, 'rrhh/asistencia.html', {'empleado': empleado})


@login_required
def solicitar_permiso(request):
    if not hasattr(request.user, 'empleado'):
        raise PermissionDenied
    empleado = request.user.empleado
    if request.method == 'POST':
        form = PermisoForm(request.POST, empleado=empleado)
        if form.is_valid():
            permiso = form.save(commit=False)
            permiso.empleado = empleado
            permiso.save()
            messages.success(request, 'Solicitud registrada y enviada para aprobacion.')
            return redirect('dashboard')
    else:
        form = PermisoForm(empleado=empleado)
    return render(request, 'rrhh/permiso.html', {'form': form})


@login_required
def resolver_permiso(request, permiso_id):
    permiso = get_object_or_404(Permiso.objects.select_related('empleado', 'empleado__area'), pk=permiso_id)
    autorizado = tiene_grupo(request.user, 'Admin RRHH')
    if tiene_grupo(request.user, 'Jefe de Area') and hasattr(request.user, 'empleado'):
        autorizado = permiso.empleado.area_id == request.user.empleado.area_id
    if not autorizado:
        raise PermissionDenied
    if request.method == 'POST':
        estado = request.POST.get('estado')
        if estado in ('aprobado', 'rechazado'):
            permiso.estado = estado
            permiso.aprobado_por = request.user
            permiso.notificacion = f'Solicitud {estado}'
            permiso.save()
            messages.success(request, f'Permiso {estado}.')
    return redirect('dashboard')


@login_required
def reportes(request):
    autorizado = tiene_grupo(request.user, 'Admin RRHH') or tiene_grupo(request.user, 'Contador')
    if tiene_grupo(request.user, 'Jefe de Area') and hasattr(request.user, 'empleado'):
        autorizado = True
    if not autorizado:
        raise PermissionDenied
    asistencias = Asistencia.objects.select_related('empleado', 'empleado__area')
    if tiene_grupo(request.user, 'Jefe de Area') and hasattr(request.user, 'empleado'):
        asistencias = asistencias.filter(empleado__area=request.user.empleado.area)
    return render(request, 'rrhh/reportes.html', {'asistencias': asistencias})


@login_required
def exportar_asistencia(request):
    if not (tiene_grupo(request.user, 'Admin RRHH') or tiene_grupo(request.user, 'Contador')):
        raise PermissionDenied
    filas = ['empleado,area,fecha,entrada,salida,horas,horas_extras']
    for asistencia in Asistencia.objects.select_related('empleado', 'empleado__area'):
        filas.append(
            f'{asistencia.empleado},{asistencia.empleado.area},{asistencia.fecha},'
            f'{asistencia.entrada},{asistencia.salida},{asistencia.horas_trabajadas},{asistencia.horas_extras}'
        )
    return HttpResponse('\n'.join(filas), content_type='text/plain')
