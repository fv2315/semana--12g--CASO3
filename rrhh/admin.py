from django.contrib import admin
from django.utils.html import format_html
from .models import Area, Empleado, Asistencia, CorreccionAsistencia, Permiso, AuditLog


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombres', 'apellidos', 'cargo', 'area', 'tipo_contrato', 'antiguedad', 'dias_vacaciones_disponibles')
    list_filter = ('area', 'tipo_contrato')
    search_fields = ('dni', 'nombres', 'apellidos', 'email_corporativo')


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha', 'entrada', 'salida', 'horas_trabajadas', 'horas_extras')
    list_filter = ('fecha', 'empleado__area')
    search_fields = ('empleado__dni', 'empleado__nombres', 'empleado__apellidos')


@admin.register(CorreccionAsistencia)
class CorreccionAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('asistencia', 'motivo', 'creado_por', 'creado_en')
    list_filter = ('motivo', 'creado_en')


@admin.action(description='Aprobar permisos seleccionados')
def aprobar_permisos(modeladmin, request, queryset):
    queryset.update(estado='aprobado', aprobado_por=request.user, notificacion='Solicitud aprobada')


@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo', 'fecha_inicio', 'fecha_fin', 'dias_solicitados', 'estado', 'dias_vacaciones_disponibles')
    list_filter = ('estado', 'tipo', 'fecha_inicio', 'empleado__area')
    search_fields = ('empleado__nombres', 'empleado__apellidos', 'empleado__dni')
    actions = [aprobar_permisos]

    @admin.display(description='Vacaciones disponibles')
    def dias_vacaciones_disponibles(self, obj):
        dias = obj.empleado.dias_vacaciones_disponibles
        color = 'green' if dias >= obj.dias_solicitados else 'red'
        return format_html('<b style="color:{}">{}</b>', color, dias)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_hora', 'ip', 'accion')
    list_filter = ('fecha_hora',)
    search_fields = ('usuario__username', 'accion', 'ip')
