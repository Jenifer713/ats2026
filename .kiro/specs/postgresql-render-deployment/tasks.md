# Implementation Plan

## Overview

Plan de implementación para migrar la base de datos de SQLite a PostgreSQL y desplegar el sistema ATS en Render.com. Las tareas siguen el orden del flujo de despliegue: preparación local → configuración → verificación → deploy.

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "5"] },
    { "wave": 2, "tasks": ["2", "6"] },
    { "wave": 3, "tasks": ["3"] },
    { "wave": 4, "tasks": ["4", "7"] },
    { "wave": 5, "tasks": ["8"] }
  ],
  "dependencies": {
    "2": ["1"],
    "3": ["2"],
    "4": ["3"],
    "6": ["5"],
    "7": ["3", "4"],
    "8": ["7"]
  }
}
```

## Tasks

- [ ] 1. Instalar dependencias de producción y crear requirements.txt
  - Instalar psycopg2-binary==2.9.9, dj-database-url==2.2.0, whitenoise==6.7.0, gunicorn==22.0.0 y python-dotenv==1.0.1 con pip en el entorno virtual del proyecto
  - Generar requirements.txt con `pip freeze > requirements.txt` asegurando que los 5 paquetes aparecen con el operador `==` y sin duplicados
  - Verificar que el archivo resultante contiene exactamente una entrada por paquete
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] 2. Crear archivo .env local y .gitignore
  - Crear `.env` en la raíz con: `SECRET_KEY=django-insecure-fallback-solo-dev`, `DEBUG=True`, `DATABASE_URL=` (vacío por ahora), `ALLOWED_HOSTS=localhost,127.0.0.1`
  - Crear `.gitignore` que excluya `.env`, `*.env`, `db.sqlite3`, `staticfiles/`, `__pycache__/`, `*.pyc`, `*.pyo` y `media/hojas_de_vida/`
  - _Requirements: 6.4, 6.6, 10.5_

- [ ] 3. Actualizar settings.py con configuración dual local/producción
  - Agregar al inicio del archivo los imports `import os`, `import dj_database_url`, `from dotenv import load_dotenv` y la llamada `load_dotenv()` como primera instrucción ejecutable tras los imports
  - Reemplazar `SECRET_KEY = 'django-insecure-...'` por `SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-solo-dev')`
  - Reemplazar `DEBUG = True` por `DEBUG = os.environ.get('DEBUG', 'True') == 'True'`
  - Reemplazar `ALLOWED_HOSTS = []` por lectura de `os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')` dividido por comas con strip
  - Reemplazar el bloque DATABASES por `{'default': dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600, conn_health_checks=True)}`
  - Insertar `'whitenoise.middleware.WhiteNoiseMiddleware'` en MIDDLEWARE en la segunda posición (índice 1), justo después de `SecurityMiddleware`
  - Agregar el diccionario STORAGES con `"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}`
  - Agregar bloque `if not DEBUG:` con SECURE_SSL_REDIRECT=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True, SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https'), SECURE_HSTS_SECONDS=31536000, SECURE_HSTS_INCLUDE_SUBDOMAINS=False
  - Agregar bloque `else:` con SECURE_SSL_REDIRECT=False, SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False
  - Agregar validación: si `not DEBUG` y `'insecure' in SECRET_KEY`, lanzar `ImproperlyConfigured('SECRET_KEY insegura en producción')`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 3.1, 3.2, 3.3, 6.1, 6.2, 6.3, 6.5, 6.6, 6.7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 10.1_

- [ ] 4. Actualizar urls.py para servir media sólo en desarrollo
  - Envolver el bloque `+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` al final de urlpatterns dentro de una condición `if settings.DEBUG:` para que no esté activo en producción
  - _Requirements: 10.4_

- [ ] 5. Crear build.sh — script de construcción para Render
  - Crear `build.sh` en la raíz con shebang `#!/usr/bin/env bash` y directiva `set -o errexit`
  - Agregar los tres comandos en orden: `pip install -r requirements.txt`, `python manage.py collectstatic --no-input`, `python manage.py migrate`
  - Dar permisos de ejecución al archivo con `chmod +x build.sh`
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [ ] 6. Crear render.yaml — configuración declarativa de Render
  - Crear `render.yaml` en la raíz con sección `services` (1 servicio tipo `web`, runtime: python, buildCommand: `./build.sh`, startCommand: `gunicorn ats2626.wsgi:application`, plan: free) y sección `databases` (name: ats2626-db, databaseName: ats2626, user: ats2626_user, plan: free)
  - Configurar las envVars del servicio web: SECRET_KEY con generateValue:true, DEBUG:"False", ALLOWED_HOSTS:"ats2626.onrender.com", DATABASE_URL con fromDatabase name:ats2626-db property:connectionString, PYTHON_VERSION:"3.11.0"
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 7. Verificar configuración localmente antes del deploy
  - Ejecutar `python manage.py check` para verificar que Django arranca sin errores con la nueva configuración
  - Ejecutar `python manage.py collectstatic --no-input` y verificar que el directorio `staticfiles/` se crea con los archivos CSS/JS del proyecto
  - Ejecutar `python manage.py migrate` para confirmar que las migraciones corren correctamente con el fallback SQLite
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 9.1_

- [ ] 8. Escribir y ejecutar tests de configuración de despliegue
  - Agregar clase `DeploymentConfigTests(TestCase)` en `reclutamiento/tests.py` con tests para: WhiteNoise presente en MIDDLEWARE, posición de WhiteNoise en índice 1 (justo tras SecurityMiddleware), STATIC_ROOT apuntando a BASE_DIR/'staticfiles', MEDIA_URL='/media/', MEDIA_ROOT apuntando a BASE_DIR/'media'
  - Agregar tests con `@override_settings` para verificar que SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE y CSRF_COOKIE_SECURE son True cuando DEBUG=False y False cuando DEBUG=True
  - Ejecutar `python manage.py test reclutamiento.tests.DeploymentConfigTests` y confirmar que todos los tests pasan
  - _Requirements: 3.1, 3.2, 7.1, 7.2, 7.3, 7.5, 7.6_

## Notes

- Las tareas 1, 2, 5 y 6 son independientes entre sí y pueden realizarse en cualquier orden.
- La tarea 3 (settings.py) depende de que las dependencias de la tarea 1 estén instaladas.
- La tarea 7 (verificación) debe ejecutarse después de completar las tareas 3 y 4.
- La tarea 8 (tests) depende de la tarea 3.
- **Nota sobre PostgreSQL local**: el `.env` empieza con `DATABASE_URL` vacío (usa SQLite como fallback). Para probar con PostgreSQL real localmente, instalar PostgreSQL, crear la BD `ats2626_db` y actualizar el `.env`.
- **Nota sobre el filesystem efímero de Render**: los archivos subidos a `media/hojas_de_vida/` se pierden en cada nuevo deploy. Para el entorno de pruebas esto es aceptable.
- **Post-deploy**: tras el primer deploy exitoso en Render, crear el superusuario desde el Shell de Render: `python manage.py createsuperuser`.
