# Design Document: Migración PostgreSQL y Despliegue en Render (postgresql-render-deployment)

## Overview

Migrar la base de datos del proyecto Django ATS `ats2626` de SQLite a PostgreSQL mediante `psycopg2-binary` y desplegar el sistema en Render.com como servidor de pruebas. El diseño cubre la configuración dual (local/producción) usando variables de entorno, archivos estáticos con WhiteNoise, manejo de archivos de media, y automatización de migraciones en el despliegue.

---

## Architecture

El sistema sigue una arquitectura de **despliegue en la nube (PaaS)** con separación clara entre entorno local y entorno de producción:

- **Entorno local**: Django + SQLite (fallback) o PostgreSQL local, servidor de desarrollo (`manage.py runserver`), variables cargadas desde `.env` vía `python-dotenv`.
- **Entorno de producción (Render.com)**: Django + PostgreSQL gestionado por Render, servidor WSGI `gunicorn`, archivos estáticos servidos por `WhiteNoise`, configuración inyectada mediante variables de entorno del panel de Render.

El flujo de despliegue es: `git push` → Render detecta el push → ejecuta `build.sh` (install + collectstatic + migrate) → inicia `gunicorn`.

---

## Components and Interfaces

| Componente | Responsabilidad | Interfaz principal |
|---|---|---|
| `settings.py` | Configuración dual local/producción | Variables de entorno: `DATABASE_URL`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` |
| `dj_database_url` | Parsear `DATABASE_URL` a dict de Django | `dj_database_url.config(default, conn_max_age, conn_health_checks)` |
| `python-dotenv` | Cargar `.env` en desarrollo local | `load_dotenv()` al inicio de `settings.py` |
| `WhiteNoise` | Servir archivos estáticos sin Nginx | Middleware `WhiteNoiseMiddleware` + storage `CompressedManifestStaticFilesStorage` |
| `gunicorn` | Servidor WSGI de producción | `gunicorn ats2626.wsgi:application` |
| `build.sh` | Automatizar construcción en Render | Script bash ejecutado como `buildCommand` en `render.yaml` |
| `render.yaml` | Configuración declarativa de infraestructura | Archivo YAML en la raíz del repositorio leído por Render Blueprint |
| `psycopg2-binary` | Driver de conexión Django ↔ PostgreSQL | Usado internamente por Django cuando ENGINE es `postgresql` |

---

## Data Models

Este feature no introduce modelos de datos nuevos. Los modelos existentes de la aplicación `reclutamiento` se migran sin cambios estructurales de SQLite a PostgreSQL. La migración preserva:

- Todos los modelos definidos en `reclutamiento/models.py` (Candidato, Vacante, Entrevista, Evaluación, Oferta, Reclutador, PerfilUsuario, etc.)
- Todas las migraciones existentes en `reclutamiento/migrations/` (`0001_initial.py`, `0002_add_perfil_usuario.py`)
- Las relaciones foráneas y restricciones de integridad referencial, que PostgreSQL aplica de forma más estricta que SQLite

La única diferencia es el motor de base de datos subyacente: `django.db.backends.sqlite3` → `django.db.backends.postgresql`.

---

## Main Algorithm/Workflow

```mermaid
sequenceDiagram
    participant Dev as Developer (Local)
    participant Git as Git Repository
    participant Render as Render.com
    participant PG as PostgreSQL (Render)

    Dev->>Dev: 1. Instalar psycopg2-binary + whitenoise + dj-database-url
    Dev->>Dev: 2. Actualizar settings.py (DB + STATIC + MEDIA)
    Dev->>Dev: 3. Crear .env local con DATABASE_URL
    Dev->>Dev: 4. Ejecutar migraciones locales contra PostgreSQL
    Dev->>Dev: 5. Generar requirements.txt
    Dev->>Dev: 6. Crear build.sh (script de despliegue)
    Dev->>Git: 7. git push (sin .env, sin db.sqlite3)
    Git->>Render: 8. Render detecta push → ejecuta build.sh
    Render->>Render: 9. pip install -r requirements.txt
    Render->>Render: 10. python manage.py collectstatic
    Render->>PG: 11. python manage.py migrate
    PG-->>Render: 12. Tablas creadas/actualizadas
    Render-->>Dev: 13. URL pública disponible (https://ats2626.onrender.com)
```

---

## Core Interfaces/Types

```python
# ── Estructura de variables de entorno requeridas ──────────────────────────

# Archivo: .env (desarrollo local — NO subir a Git)
SECRET_KEY=django-insecure-=+=ps(t=yj4i*%1@!(g141v-9miahl2+169bb$@#p=!(dz4#cp
DEBUG=True
DATABASE_URL=postgres://usuario:contraseña@localhost:5432/ats2626_db
ALLOWED_HOSTS=localhost,127.0.0.1

# Variables de entorno en Render.com (panel Dashboard → Environment)
SECRET_KEY=<nueva-clave-segura-generada>
DEBUG=False
DATABASE_URL=<render-postgresql-internal-url>   # Render la provee automáticamente
ALLOWED_HOSTS=ats2626.onrender.com
PYTHON_VERSION=3.11.0

# ── Dependencias a agregar ──────────────────────────────────────────────────

# requirements.txt (fragmento nuevo)
psycopg2-binary==2.9.9
dj-database-url==2.2.0
whitenoise==6.7.0
gunicorn==22.0.0
python-dotenv==1.0.1
```

---

## Key Functions with Formal Specifications

### Function 1: `settings.py` — Configuración dual local/producción

```python
# ats2626/settings.py — versión actualizada

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Carga variables del archivo .env en desarrollo local
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Seguridad ──────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-fallback-solo-dev')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS_RAW = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_RAW.split(',')]

# ── Base de Datos ──────────────────────────────────────────────────────────
# dj_database_url parsea DATABASE_URL automáticamente.
# Fallback a SQLite sólo si DATABASE_URL no está definida (útil en CI/CD ligero).
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,        # Persistir conexiones hasta 600 s (performance)
        conn_health_checks=True, # Reconectar si la conexión fue cerrada por PG
    )
}

# ── Archivos Estáticos (WhiteNoise) ────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic deposita aquí

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ── Archivos de Media ─────────────────────────────────────────────────────
# En Render (instancias efímeras) los archivos subidos se PIERDEN en cada deploy.
# Para producción real usar almacenamiento externo (Cloudinary, S3).
# En entorno de pruebas, se mantiene la configuración local.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── HTTPS / Seguridad en producción ──────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

**Preconditions:**
- `DATABASE_URL` tiene formato válido: `postgres://user:pass@host:port/dbname`
- `SECRET_KEY` en producción tiene al menos 50 caracteres aleatorios
- `DEBUG=False` cuando `ALLOWED_HOSTS` contiene el dominio de Render

**Postconditions:**
- `DATABASES['default']` apunta a PostgreSQL cuando `DATABASE_URL` está definida
- `DATABASES['default']` hace fallback a SQLite si `DATABASE_URL` no existe
- WhiteNoise comprime y versiona archivos estáticos automáticamente en producción
- Redireccionamiento HTTPS activo sólo cuando `DEBUG=False`

**Loop Invariants:** N/A

---

### Function 2: `MIDDLEWARE` — Insertar WhiteNoise

```python
# ats2626/settings.py — sección MIDDLEWARE actualizada

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← AGREGAR justo después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

**Preconditions:**
- `whitenoise` instalado en el entorno Python
- `whitenoise.middleware.WhiteNoiseMiddleware` debe estar inmediatamente después de `SecurityMiddleware`

**Postconditions:**
- WhiteNoise intercepta peticiones a `/static/` antes de llegar a Django views
- En producción Django no necesita `runserver` ni Nginx para servir estáticos

---

### Function 3: `build.sh` — Script de construcción en Render

```bash
#!/usr/bin/env bash
# build.sh — ejecutado por Render en cada deploy
# Se debe marcar como ejecutable: chmod +x build.sh

set -o errexit  # Abortar si cualquier comando falla

# 1. Instalar dependencias Python
pip install -r requirements.txt

# 2. Recolectar archivos estáticos (WhiteNoise los sirve desde staticfiles/)
python manage.py collectstatic --no-input

# 3. Aplicar migraciones pendientes a PostgreSQL de Render
python manage.py migrate
```

**Preconditions:**
- `DATABASE_URL` definida como variable de entorno en Render Dashboard
- `requirements.txt` incluye todas las dependencias actualizadas
- El archivo `build.sh` tiene permisos de ejecución (`chmod +x build.sh`)

**Postconditions:**
- Todas las dependencias instaladas en el entorno de Render
- Directorio `staticfiles/` poblado con archivos comprimidos y con hash de versión
- Esquema de base de datos PostgreSQL actualizado con todas las migraciones

---

### Function 4: `render.yaml` — Configuración declarativa de Render

```yaml
# render.yaml — en la raíz del proyecto

services:
  - type: web
    name: ats2626
    runtime: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn ats2626.wsgi:application"
    envVars:
      - key: SECRET_KEY
        generateValue: true          # Render genera un valor aleatorio seguro
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: "ats2626.onrender.com"
      - key: DATABASE_URL
        fromDatabase:
          name: ats2626-db           # Nombre del servicio DB en Render
          property: connectionString
      - key: PYTHON_VERSION
        value: "3.11.0"

databases:
  - name: ats2626-db
    databaseName: ats2626
    user: ats2626_user
    plan: free                       # Plan gratuito de Render (90 días)
```

**Preconditions:**
- El repositorio Git tiene `render.yaml` en la raíz
- El nombre del servicio `ats2626-db` en `fromDatabase.name` coincide exactamente con la sección `databases`

**Postconditions:**
- Render crea automáticamente la base de datos PostgreSQL y la web service
- `DATABASE_URL` se inyecta en el entorno del web service apuntando al PostgreSQL interno
- La app queda disponible en `https://ats2626.onrender.com`

---

### Function 5: `wsgi.py` — Sin cambios necesarios

```python
# ats2626/wsgi.py — verificar que no requiere cambios

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ats2626.settings')
application = get_wsgi_application()

# gunicorn lo invoca como:  gunicorn ats2626.wsgi:application
# El startCommand en render.yaml ya está configurado correctamente.
```

**Preconditions:**
- `DJANGO_SETTINGS_MODULE` resuelve a `ats2626.settings`

**Postconditions:**
- `gunicorn` puede importar `application` y servir peticiones WSGI

---

## Algorithmic Pseudocode

### Algoritmo 1: Migración de datos de SQLite a PostgreSQL

```python
# ALGORITMO: Migrar datos existentes de SQLite → PostgreSQL
# Ejecutar UNA SOLA VEZ localmente antes del primer deploy
#
# PRECONDICIÓN: PostgreSQL local corriendo con base de datos vacía
# POSTCONDICIÓN: Todos los datos de SQLite están en PostgreSQL
#
# PASO 1 — Exportar datos de SQLite (con DB_URL apuntando a SQLite)
#   python manage.py dumpdata \
#       --exclude auth.permission \
#       --exclude contenttypes \
#       --indent 2 \
#       > data_backup.json
#
# PASO 2 — Cambiar DATABASE_URL en .env para apuntar a PostgreSQL
#   DATABASE_URL=postgres://usuario:contraseña@localhost:5432/ats2626_db
#
# PASO 3 — Crear el esquema en PostgreSQL
#   python manage.py migrate
#
# PASO 4 — Cargar los datos exportados en PostgreSQL
#   python manage.py loaddata data_backup.json
#
# PASO 5 — Verificar integridad
#   python manage.py check --database default
```

### Algoritmo 2: Generación de SECRET_KEY segura para producción

```python
# ALGORITMO: Generar SECRET_KEY para producción
# Ejecutar en terminal Python o shell

import secrets
import string

alphabet = string.ascii_letters + string.digits + string.punctuation
secret_key = ''.join(secrets.choice(alphabet) for _ in range(64))
print(secret_key)

# Precondición:  Python instalado con módulo secrets (stdlib)
# Postcondición: Cadena de 64 caracteres criptográficamente aleatoria
# Usar el resultado como SECRET_KEY en Render Dashboard → Environment Variables
```

### Algoritmo 3: Flujo completo de deploy en Render paso a paso

```python
# ALGORITMO: Checklist de despliegue — orden secuencial obligatorio

PASOS = [
    # LOCAL — preparación
    "1. pip install psycopg2-binary dj-database-url whitenoise gunicorn python-dotenv",
    "2. Actualizar settings.py con configuración dual (ver Function 1 y 2 arriba)",
    "3. Crear .env con DATABASE_URL local",
    "4. pip freeze > requirements.txt",
    "5. Crear build.sh con permisos ejecutables (chmod +x build.sh)",
    "6. Crear render.yaml en raíz del proyecto",
    "7. Crear .gitignore asegurando que .env y db.sqlite3 estén excluidos",
    "8. python manage.py collectstatic --no-input  (verificar que no hay errores)",
    "9. python manage.py check --deploy  (verificar configuración de producción)",
    "10. git add . && git commit -m 'feat: postgresql + render deployment config'",
    "11. git push origin main",

    # RENDER — configuración
    "12. Crear cuenta en render.com",
    "13. New → Blueprint (si se usa render.yaml) O New → Web Service (manual)",
    "14. Conectar repositorio Git",
    "15. Render detecta render.yaml y crea servicios automáticamente",
    "16. Verificar que DATABASE_URL se inyectó correctamente",
    "17. Esperar build logs — verificar que migrate corrió sin errores",
    "18. Acceder a https://ats2626.onrender.com",

    # POST-DEPLOY
    "19. Crear superusuario: Render Dashboard → Shell → python manage.py createsuperuser",
    "20. Verificar admin en https://ats2626.onrender.com/admin/",
]

# Precondición por paso:
#   Pasos 1-11: Entorno local con Python 3.11, Git configurado
#   Pasos 12-18: Cuenta en render.com, repositorio accesible (GitHub/GitLab)
#   Pasos 19-20: Deploy exitoso (build logs sin errores)
```

---

## Example Usage

### requirements.txt completo

```text
# requirements.txt — generado con pip freeze, incluir versiones exactas
Django==5.0.6
psycopg2-binary==2.9.9
dj-database-url==2.2.0
whitenoise==6.7.0
gunicorn==22.0.0
python-dotenv==1.0.1
# (resto de dependencias existentes del proyecto)
```

### .gitignore — entradas críticas

```gitignore
# .gitignore — verificar que estas líneas existen

# Secretos y base de datos local
.env
*.env
db.sqlite3

# Archivos estáticos compilados (Render los genera en build)
staticfiles/

# Python cache
__pycache__/
*.pyc
*.pyo

# Media local (no versionar archivos subidos por usuarios)
media/hojas_de_vida/
```

### Verificación local previa al deploy

```bash
# Comandos a ejecutar localmente para validar la configuración

# 1. Verificar que Django detecta configuración de producción correctamente
DEBUG=False python manage.py check --deploy

# 2. Verificar conexión a PostgreSQL local
python manage.py dbshell

# 3. Correr migraciones sobre PostgreSQL
python manage.py migrate --verbosity 2

# 4. Recolectar estáticos y verificar output
python manage.py collectstatic --no-input --verbosity 2

# 5. Probar gunicorn localmente (equivalente a lo que hace Render)
gunicorn ats2626.wsgi:application --bind 0.0.0.0:8000
```

### Manejo de archivos de media en Render (consideración importante)

```python
# PROBLEMA: Render usa un filesystem efímero.
# Los archivos subidos a media/hojas_de_vida/ se ELIMINAN en cada deploy.
#
# SOLUCIÓN para entorno de pruebas: aceptar esta limitación.
# SOLUCIÓN para producción real: usar almacenamiento externo.
#
# Ejemplo de integración con Cloudinary (para producción futura):

# pip install cloudinary django-cloudinary-storage

# settings.py — configuración Cloudinary
INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY':    os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
# Con esto, model.FileField sube directamente a Cloudinary sin cambios en models.py
```

---

## Correctness Properties

*Una propiedad es una característica o comportamiento que debe cumplirse para todas las ejecuciones válidas del sistema — una especificación formal de lo que el sistema debe hacer.*

### Property 1: Parseo universal de DATABASE_URL a PostgreSQL

*Para cualquier* cadena `DATABASE_URL` con formato `postgres://user:pass@host:port/dbname`, `dj_database_url.config()` SHALL retornar un diccionario donde `ENGINE` es `django.db.backends.postgresql`.

**Validates: Requirements 1.1, 1.3**

### Property 2: Fallback a SQLite cuando DATABASE_URL está ausente

*Para cualquier* entorno donde `DATABASE_URL` no está definida como variable de entorno, `DATABASES['default']['ENGINE']` SHALL ser `django.db.backends.sqlite3`.

**Validates: Requirements 1.2**

### Property 3: Posición invariante de WhiteNoise en MIDDLEWARE

*Para cualquier* configuración válida del sistema, el índice de `whitenoise.middleware.WhiteNoiseMiddleware` en `settings.MIDDLEWARE` SHALL ser exactamente igual al índice de `django.middleware.security.SecurityMiddleware` más uno.

**Validates: Requirements 3.1**

### Property 4: HTTPS forzado universalmente cuando DEBUG es False

*Para cualquier* configuración donde `DEBUG=False`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` SHALL ser `True`.

**Validates: Requirements 7.1, 7.2, 7.3**

### Property 5: SECRET_KEY segura en producción

*Para cualquier* instancia del sistema con `DEBUG=False`, `SECRET_KEY` SHALL no contener la subcadena `insecure`.

**Validates: Requirements 6.5**

### Property 6: Round-trip de datos SQLite → PostgreSQL preserva registros

*Para cualquier* conjunto de modelos con N registros en SQLite, exportar con `dumpdata` e importar con `loaddata` en PostgreSQL SHALL producir exactamente N registros para cada modelo importado.

**Validates: Requirements 8.1, 8.2**

### Property 7: Conexión PostgreSQL con reconexión automática

*Para cualquier* configuración de `DATABASES['default']` apuntando a PostgreSQL, el parámetro `conn_max_age` SHALL ser 600 y `conn_health_checks` SHALL ser `True`.

**Validates: Requirements 1.3**

---

## Error Handling

### Error 1: `psycopg2.OperationalError: could not connect to server`

**Condición**: `DATABASE_URL` incorrecta o servidor PostgreSQL no disponible  
**Respuesta**: Django lanza `OperationalError` al primer acceso a la BD  
**Recuperación**:
```bash
# Verificar que DATABASE_URL tiene el formato correcto
echo $DATABASE_URL
# postgres://usuario:contraseña@host:5432/nombre_bd
# En Render, copiar la "Internal Database URL" desde el dashboard del DB service
```

### Error 2: `django.core.exceptions.ImproperlyConfigured: ALLOWED_HOSTS`

**Condición**: El dominio de Render no está en `ALLOWED_HOSTS` con `DEBUG=False`  
**Respuesta**: Django rechaza todas las peticiones con HTTP 400  
**Recuperación**:
```python
# En Render Dashboard → Environment Variables
# ALLOWED_HOSTS = ats2626.onrender.com
# (sin https://, sin barra final, sin espacios extra)
```

### Error 3: `staticfiles` no encontrados (HTTP 404 en CSS/JS)

**Condición**: `collectstatic` no se ejecutó o `WhiteNoiseMiddleware` no está en MIDDLEWARE  
**Respuesta**: Archivos estáticos devuelven 404  
**Recuperación**:
```bash
# Verificar en build logs de Render que collectstatic corrió exitosamente
# Verificar orden en MIDDLEWARE: whitenoise debe estar en índice 1
python -c "import django; django.setup(); from django.conf import settings; print(settings.MIDDLEWARE)"
```

### Error 4: `relation does not exist` (tabla no existe en PostgreSQL)

**Condición**: `migrate` no corrió o corrió contra la BD equivocada  
**Respuesta**: `django.db.utils.ProgrammingError` en cualquier query  
**Recuperación**:
```bash
# En Render Dashboard → Shell del web service
python manage.py showmigrations    # Ver estado de cada migración
python manage.py migrate --run-syncdb   # Forzar sincronización
```

### Error 5: Archivos de media perdidos tras deploy

**Condición**: Filesystem efímero de Render — `media/hojas_de_vida/` se borra en cada deploy  
**Respuesta**: Los PDFs de hojas de vida dejan de estar disponibles  
**Recuperación (para entorno de pruebas)**:
- Documentar la limitación para el equipo
- Subir archivos nuevamente después del deploy
- Para producción: implementar Cloudinary (ver Example Usage arriba)

---

## Testing Strategy

### Unit Testing Approach

```python
# Verificar que la configuración de BD cambia según variables de entorno
# reclutamiento/tests.py — test de configuración

import os
from django.test import TestCase, override_settings

class DatabaseConfigTests(TestCase):
    
    @override_settings(DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'test_db',
        }
    })
    def test_postgresql_engine_en_produccion(self):
        from django.conf import settings
        self.assertEqual(
            settings.DATABASES['default']['ENGINE'],
            'django.db.backends.postgresql'
        )
    
    def test_whitenoise_en_middleware(self):
        from django.conf import settings
        self.assertIn(
            'whitenoise.middleware.WhiteNoiseMiddleware',
            settings.MIDDLEWARE
        )
    
    def test_whitenoise_posicion_correcta(self):
        from django.conf import settings
        idx_security = settings.MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        idx_whitenoise = settings.MIDDLEWARE.index('whitenoise.middleware.WhiteNoiseMiddleware')
        self.assertEqual(idx_whitenoise, idx_security + 1)
```

### Pruebas Basadas en Propiedades (Property-Based Testing)

```python
# Propiedad: para cualquier DATABASE_URL de PostgreSQL válida,
# dj_database_url.config() siempre devuelve ENGINE = postgresql

# Librería: hypothesis (pip install hypothesis)
from hypothesis import given, strategies as st
import dj_database_url

@given(st.from_regex(
    r'postgres://[a-z]+:[a-z]+@localhost:\d{4}/[a-z_]+',
    fullmatch=True
))
def test_dj_database_url_siempre_postgresql(database_url):
    config = dj_database_url.parse(database_url)
    assert config['ENGINE'] == 'django.db.backends.postgresql'
```

### Integration Testing Approach

```bash
# Verificación de integración end-to-end antes del deploy

# 1. Con PostgreSQL local configurado en .env:
python manage.py migrate
python manage.py check --deploy 2>&1 | grep -v "WARNINGS"

# 2. Smoke test con gunicorn localmente:
gunicorn ats2626.wsgi:application --bind 0.0.0.0:8000 --daemon
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login/
# Esperado: 200

# 3. Verificar que estáticos son accesibles:
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/static/css/ats.css
# Esperado: 200
```

---

## Performance Considerations

- `conn_max_age=600` en `dj_database_url.config()` mantiene conexiones PostgreSQL persistentes, evitando el overhead de reconexión en cada petición (especialmente importante en el plan gratuito de Render con latencia de red).
- `CompressedManifestStaticFilesStorage` de WhiteNoise comprime automáticamente CSS/JS con gzip y brotli, y agrega hash de versión al nombre del archivo para cache inmutable en el navegador.
- El plan gratuito de PostgreSQL en Render tiene límite de **1 GB** de almacenamiento y la instancia se suspende tras **90 días de inactividad** — suficiente para entorno de pruebas.
- El plan gratuito del web service se suspende tras **15 minutos de inactividad** (cold start de ~30 segundos).

## Security Considerations

- `SECRET_KEY` nunca se hardcodea: se lee de variables de entorno. En Render usar `generateValue: true` para que Render genere una clave criptográficamente segura.
- `DEBUG=False` en producción: evita exposición de stack traces, configuraciones internas y la toolbar de debug.
- `SECURE_SSL_REDIRECT=True`: fuerza HTTPS en todas las peticiones cuando `DEBUG=False`.
- `CSRF_COOKIE_SECURE=True` y `SESSION_COOKIE_SECURE=True`: cookies sólo se envían por HTTPS.
- `.env` y `db.sqlite3` en `.gitignore`: credenciales y datos locales nunca llegan al repositorio.
- PostgreSQL de Render sólo es accesible desde la red interna de Render — no expuesto a internet directamente.

## Dependencies

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `psycopg2-binary` | 2.9.9 | Driver PostgreSQL para Django |
| `dj-database-url` | 2.2.0 | Parsear `DATABASE_URL` a dict de Django |
| `whitenoise` | 6.7.0 | Servir archivos estáticos sin Nginx |
| `gunicorn` | 22.0.0 | Servidor WSGI de producción |
| `python-dotenv` | 1.0.1 | Cargar `.env` en desarrollo local |
| `render.yaml` | — | Configuración declarativa de Render (no es un paquete) |
