from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    CONTRATO_CHOICES = [('planilla', 'Planilla'), ('locacion', 'Locacion')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dni = models.CharField(max_length=8, unique=True, validators=[RegexValidator(r'^\d{8}$')])
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='empleados')
    fecha_ingreso = models.DateField()
    tipo_contrato = models.CharField(max_length=20, choices=CONTRATO_CHOICES)
    email_corporativo = models.EmailField(unique=True)

    class Meta:
        ordering = ['apellidos', 'nombres']

    def clean(self):
        if self.fecha_ingreso and self.fecha_ingreso > date.today():
            raise ValidationError({'fecha_ingreso': 'La fecha de ingreso no puede ser futura.'})
        if not self.email_corporativo.endswith('@tecnoandes.pe'):
            raise ValidationError({'email_corporativo': 'El correo debe terminar en @tecnoandes.pe'})
        if not self.cargo.strip():
            raise ValidationError({'cargo': 'El cargo no puede estar vacio.'})

    @property
    def antiguedad(self):
        if not self.fecha_ingreso:
            return '0 anos, 0 meses'
        hoy = date.today()
        total_meses = (hoy.year - self.fecha_ingreso.year) * 12 + hoy.month - self.fecha_ingreso.month
        if hoy.day < self.fecha_ingreso.day:
            total_meses -= 1
        return f'{total_meses // 12} anos, {total_meses % 12} meses'

    @property
    def dias_vacaciones_disponibles(self):
        tomados = sum(p.dias_solicitados for p in self.permisos.filter(tipo='vacaciones', estado='aprobado'))
        return max(0, 30 - tomados)

    def __str__(self):
        return f'{self.nombres} {self.apellidos}'


class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField()
    entrada = models.DateTimeField(null=True, blank=True)
    salida = models.DateTimeField(null=True, blank=True)
    horas_trabajadas = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    horas_extras = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('empleado', 'fecha')
        ordering = ['-fecha', 'empleado']

    def save(self, *args, **kwargs):
        if self.entrada and self.salida:
            delta = self.salida - self.entrada
            horas = max(0, delta.total_seconds() / 3600)
            self.horas_trabajadas = round(horas, 2)
            self.horas_extras = round(max(0, horas - 8), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.empleado} - {self.fecha}'


class CorreccionAsistencia(models.Model):
    MOTIVOS = [('sistema', 'Error de sistema'), ('olvido', 'Olvido'), ('otro', 'Otro')]
    asistencia = models.ForeignKey(Asistencia, on_delete=models.CASCADE, related_name='correcciones')
    motivo = models.CharField(max_length=20, choices=MOTIVOS)
    justificacion = models.TextField()
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    creado_en = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if len(self.justificacion.strip()) < 50:
            raise ValidationError({'justificacion': 'La justificacion debe tener al menos 50 caracteres.'})


class Permiso(models.Model):
    TIPOS = [
        ('personal', 'Personal'), ('medico', 'Medico'), ('duelo', 'Duelo'),
        ('maternidad', 'Maternidad/Paternidad'), ('vacaciones', 'Vacaciones'), ('otro', 'Otro'),
    ]
    ESTADOS = [('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado')]
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='permisos')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    motivo = models.TextField()
    adjunto = models.CharField(max_length=255, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    aprobado_por = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    actualizado_en = models.DateTimeField(auto_now=True)
    notificacion = models.CharField(max_length=255, blank=True)

    @property
    def dias_solicitados(self):
        return (self.fecha_fin - self.fecha_inicio).days + 1

    def __str__(self):
        return f'{self.empleado} - {self.tipo} ({self.estado})'


class AuditLog(models.Model):
    usuario = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    accion = models.CharField(max_length=255)
    detalle = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_hora']
