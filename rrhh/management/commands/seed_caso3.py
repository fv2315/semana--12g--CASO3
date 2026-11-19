from datetime import date, datetime, timedelta
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone
from rrhh.models import Area, Empleado, Asistencia, Permiso


class Command(BaseCommand):
    help = 'Carga datos de prueba del Caso 3'

    def handle(self, *args, **options):
        for nombre in ('Admin RRHH', 'Jefe de Area', 'Empleado', 'Contador'):
            Group.objects.get_or_create(name=nombre)
        for nombre in ('Sistemas', 'Contabilidad', 'Ventas', 'Logistica', 'RRHH'):
            Area.objects.get_or_create(nombre=nombre)

        sistemas = Area.objects.get(nombre='Sistemas')
        rrhh = Area.objects.get(nombre='RRHH')
        rrhh_user, _ = User.objects.get_or_create(username='rrhh', defaults={'is_staff': True, 'is_superuser': True})
        rrhh_user.set_password('rrhh123')
        rrhh_user.is_staff = True
        rrhh_user.is_superuser = True
        rrhh_user.save()
        rrhh_user.groups.add(Group.objects.get(name='Admin RRHH'))

        empleados = []
        for i in range(1, 11):
            area = Area.objects.all()[i % 5]
            user, _ = User.objects.get_or_create(username=f'emp{i}')
            user.set_password('empleado123')
            user.save()
            user.groups.add(Group.objects.get(name='Empleado'))
            empleado, _ = Empleado.objects.get_or_create(
                dni=f'700000{i:02d}',
                defaults={
                    'user': user,
                    'nombres': f'Empleado{i}',
                    'apellidos': 'TecnoAndes',
                    'cargo': 'Analista',
                    'area': area,
                    'fecha_ingreso': date(2024, 1, i),
                    'tipo_contrato': 'planilla',
                    'email_corporativo': f'emp{i}@tecnoandes.pe',
                },
            )
            empleados.append(empleado)

        jefe_user, _ = User.objects.get_or_create(username='jefe', defaults={'is_staff': True})
        jefe_user.set_password('jefe123')
        jefe_user.is_staff = True
        jefe_user.save()
        jefe_user.groups.add(Group.objects.get(name='Jefe de Area'))
        Empleado.objects.get_or_create(
            dni='80000001', defaults={
                'user': jefe_user, 'nombres': 'Jefe', 'apellidos': 'Sistemas',
                'cargo': 'Supervisor', 'area': sistemas, 'fecha_ingreso': date(2022, 1, 1),
                'tipo_contrato': 'planilla', 'email_corporativo': 'jefe@tecnoandes.pe',
            },
        )

        contador, _ = User.objects.get_or_create(username='contador', defaults={'is_staff': True})
        contador.set_password('contador123')
        contador.is_staff = True
        contador.save()
        contador.groups.add(Group.objects.get(name='Contador'))

        hoy = timezone.localdate()
        for empleado in empleados:
            for offset in range(5):
                dia = hoy - timedelta(days=offset)
                entrada = timezone.make_aware(datetime.combine(dia, datetime.min.time()).replace(hour=8, minute=0))
                salida = timezone.make_aware(datetime.combine(dia, datetime.min.time()).replace(hour=17, minute=30))
                Asistencia.objects.update_or_create(
                    empleado=empleado, fecha=dia,
                    defaults={'entrada': entrada, 'salida': salida},
                )
        for i in range(10):
            inicio = hoy + timedelta(days=7 + i)
            Permiso.objects.get_or_create(
                empleado=empleados[i % len(empleados)],
                fecha_inicio=inicio,
                defaults={
                    'tipo': 'personal',
                    'fecha_fin': inicio,
                    'motivo': 'Solicitud de prueba con motivo suficientemente detallado.',
                    'estado': 'pendiente',
                },
            )
        self.stdout.write(self.style.SUCCESS('Datos de prueba cargados.'))
