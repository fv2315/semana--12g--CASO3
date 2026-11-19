from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.utils import timezone
from .models import Empleado, Asistencia, Permiso, CorreccionAsistencia


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario corporativo')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


class AsistenciaForm(forms.ModelForm):
    class Meta:
        model = Asistencia
        fields = []

    def save(self, empleado, tipo):
        hoy = timezone.localdate()
        asistencia, creada = Asistencia.objects.get_or_create(empleado=empleado, fecha=hoy)
        ahora = timezone.now()
        if tipo == 'entrada':
            if asistencia.entrada:
                raise ValidationError('Ya existe una entrada hoy.')
            asistencia.entrada = ahora
        else:
            if not asistencia.entrada:
                raise ValidationError('Primero debes registrar tu entrada.')
            if asistencia.salida:
                raise ValidationError('Ya registraste la salida de hoy.')
            if ahora <= asistencia.entrada:
                raise ValidationError('La salida debe ser posterior a la entrada.')
            asistencia.salida = ahora
        asistencia.save()
        return asistencia


class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['tipo', 'fecha_inicio', 'fecha_fin', 'motivo', 'adjunto']

    def __init__(self, *args, empleado=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empleado = empleado

    def clean_motivo(self):
        motivo = strip_tags(self.cleaned_data['motivo']).strip()
        if len(motivo) < 30:
            raise ValidationError('El motivo debe tener al menos 30 caracteres.')
        return motivo

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get('fecha_inicio')
        fin = cleaned.get('fecha_fin')
        if inicio and fin:
            if fin < inicio:
                raise ValidationError('La fecha fin debe ser igual o posterior a la fecha inicio.')
            if self.empleado:
                superpuestos = Permiso.objects.filter(
                    empleado=self.empleado,
                    estado__in=['pendiente', 'aprobado'],
                    fecha_inicio__lte=fin,
                    fecha_fin__gte=inicio,
                ).exists()
                if superpuestos:
                    raise ValidationError('Ya tienes un permiso que se superpone con esas fechas.')
                if cleaned.get('tipo') == 'vacaciones':
                    dias = (fin - inicio).days + 1
                    if dias > self.empleado.dias_vacaciones_disponibles:
                        raise ValidationError('No tienes suficientes dias de vacaciones disponibles.')
        return cleaned


class CorreccionAsistenciaForm(forms.ModelForm):
    class Meta:
        model = CorreccionAsistencia
        fields = ['motivo', 'justificacion']
