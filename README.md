# TecnoAndes - Caso 3

Sistema Django de control de asistencia y permisos de empleados.

## Requisitos

- Python 3.12+
- Django 5.2 o 6.x

## Instalacion

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_caso3
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/login/` o `/admin/`.

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| rrhh | rrhh123 | Admin RRHH |
| jefe | jefe123 | Jefe de Area |
| emp1 | empleado123 | Empleado |
| contador | contador123 | Contador |

## Funcionalidades

- Marcacion diaria de entrada y salida con calculo de horas y extras.
- Solicitud de permisos con validacion de fechas, solapamientos y vacaciones.
- Flujo de aprobacion jerarquico.
- Django Admin con filtros, busqueda y aprobacion masiva.
- Middleware de cuenta bloqueada, recordatorio, horario y auditoria.
- Sesion con timeout de 45 minutos y cookie HttpOnly.
- Reportes y exportacion textual.
