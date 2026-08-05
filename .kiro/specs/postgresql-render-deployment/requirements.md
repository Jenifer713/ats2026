# Requirements Document

## Introduction

Este documento especifica los requisitos funcionales y no funcionales derivados del diseño técnico para la migración de la base de datos del proyecto Django `ats2626` de SQLite a PostgreSQL, y su despliegue en Render.com como servidor de pruebas. La solución emplea `psycopg2-binary`, `dj-database-url`, `python-dotenv`, `whitenoise` y `gunicorn`, con configuración dual (local/producción) gestionada mediante variables de entorno.

---

## Glossary

- **Settings**: Módulo `ats2626/settings.py` que centraliza la configuración del proyecto Django.
- **Build_Script**: Archivo `build.sh` ejecutado por Render en cada despliegue.
- **Render_Config**: Archivo `render.yaml` que define declarativamente los servicios en Render.com.
- **DB_Configurator**: Componente que usa `dj_database_url` para parsear `DATABASE_URL` y configurar `DATABASES['default']`.
- **Static_Collector**: Comando `python manage.py collectstatic` que reúne archivos estáticos en `STATIC_ROOT`.
- **Migration_Runner**: Comando `python manage.py migrate` que aplica migraciones pendientes a la BD.
- **WhiteNoise**: Middleware y storage backend que sirve archivos estáticos directamente desde Django sin necesidad de Nginx.
- **Gunicorn**: Servidor WSGI de producción que sirve la aplicación Django en Render.
- **DATABASE_URL**: Variable de entorno con la cadena de conexión a PostgreSQL en formato `postgres://user:pass@host:port/dbname`.
- **SECRET_KEY**: Variable de entorno con la clave criptográfica secreta de Django, requerida para producción.
- **DEBUG**: Variable de entorno que controla el modo debug (`True` en local, `False` en producción).
- **ALLOWED_HOSTS**: Variable de entorno con la lista de dominios permitidos separados por coma.
- **STATIC_ROOT**: Directorio `staticfiles/` donde `collectstatic` deposita todos los archivos estáticos compilados.
- **Data_Migrator**: Proceso de exportación (`dumpdata`) e importación (`loaddata`) de datos de SQLite a PostgreSQL.

---

## Requirements

### Requisito 1: Configuración de Base de Datos Dual (Local/Producción)

**Historia de Usuario:** Como desarrollador, quiero que el sistema use PostgreSQL cuando `DATABASE_URL` está definida y SQLite como fallback cuando no lo está, para que el entorno local funcione sin configuración adicional y producción use PostgreSQL automáticamente.

#### Criterios de Aceptación

1. WHEN `DATABASE_URL` está definida como una cadena no vacía que comienza con `postgres://` o `postgresql://`, THE `DB_Configurator` SHALL configurar `DATABASES['default']['ENGINE']` como `django.db.backends.postgresql`.
2. WHEN `DATABASE_URL` no está definida en el entorno o tiene valor vacío, THE `DB_Configurator` SHALL configurar `DATABASES['default']` apuntando al archivo `BASE_DIR / 'db.sqlite3'` con ENGINE `django.db.backends.sqlite3`.
3. THE `DB_Configurator` SHALL parsear `DATABASE_URL` usando `dj_database_url.config()` con `conn_max_age=600` y `conn_health_checks=True`.
4. WHEN `DATABASE_URL` tiene un scheme distinto de `postgres://` o `postgresql://`, THE `DB_Configurator` SHALL dejar que la excepción de `dj_database_url` se propague sin capturarla, provocando que el proceso de Django falle al iniciar con el traceback original visible en los logs.

---

### Requisito 2: Instalación de Dependencias de Producción

**Historia de Usuario:** Como desarrollador, quiero que todas las dependencias necesarias estén declaradas en `requirements.txt` con versiones exactas, para que Render las instale correctamente en cada despliegue.

#### Criterios de Aceptación

1. THE `requirements.txt` SHALL incluir `psycopg2-binary==2.9.9` como driver de conexión a PostgreSQL.
2. THE `requirements.txt` SHALL incluir `dj-database-url==2.2.0` para parsear `DATABASE_URL`.
3. THE `requirements.txt` SHALL incluir `whitenoise==6.7.0` para servir archivos estáticos.
4. THE `requirements.txt` SHALL incluir `gunicorn==22.0.0` como servidor WSGI de producción.
5. THE `requirements.txt` SHALL incluir `python-dotenv==1.0.1` para cargar variables de entorno desde `.env` en desarrollo local.
6. THE `requirements.txt` SHALL especificar cada uno de los paquetes de los criterios 1–5 usando el operador `==` (formato `paquete==X.Y.Z`), sin rangos (`>=`, `~=`, `<=`).
7. THE `requirements.txt` SHALL contener cada paquete exactamente una vez, sin líneas duplicadas ni versiones en conflicto para el mismo paquete.

---

### Requisito 3: Configuración de Archivos Estáticos con WhiteNoise

**Historia de Usuario:** Como operador del sistema, quiero que los archivos estáticos (CSS, JS) sean servidos correctamente en producción sin necesidad de Nginx, para simplificar la infraestructura en Render.

#### Criterios de Aceptación

1. THE `Settings` SHALL declarar `whitenoise.middleware.WhiteNoiseMiddleware` en `MIDDLEWARE` en la posición inmediatamente posterior a `django.middleware.security.SecurityMiddleware`.
2. THE `Settings` SHALL configurar `STORAGES['staticfiles']['BACKEND']` como `whitenoise.storage.CompressedManifestStaticFilesStorage`.
3. THE `Settings` SHALL definir `STATIC_ROOT` como `BASE_DIR / 'staticfiles'` y `STATICFILES_DIRS` como `[BASE_DIR / 'static']`.
4. WHEN el `Static_Collector` se ejecuta, THE `Static_Collector` SHALL depositar todos los archivos de los directorios listados en `STATICFILES_DIRS` en `STATIC_ROOT`.
5. WHEN un cliente solicita un archivo en `/static/` que existe en `STATIC_ROOT`, THE `WhiteNoise` SHALL responder con el archivo comprimido en formato gzip y encabezado `Cache-Control` con valor `max-age=31536000, immutable` sin invocar vistas de Django.
6. IF un cliente solicita un archivo en `/static/` que no existe en `STATIC_ROOT`, THEN THE `WhiteNoise` SHALL responder con código de estado HTTP 404.

---

### Requisito 4: Script de Construcción para Render

**Historia de Usuario:** Como operador de despliegue, quiero un script `build.sh` que automatice la instalación de dependencias, colección de estáticos y aplicación de migraciones en cada despliegue, para garantizar que el entorno de Render esté siempre consistente.

#### Criterios de Aceptación

1. THE `Build_Script` SHALL ejecutar `pip install -r requirements.txt` como primer paso.
2. IF `pip install` completa con código de retorno cero, THEN THE `Build_Script` SHALL ejecutar `python manage.py collectstatic --no-input`.
3. IF `collectstatic` completa con código de retorno cero, THEN THE `Build_Script` SHALL ejecutar `python manage.py migrate`.
4. IF cualquier comando del `Build_Script` retorna un código de salida distinto de cero, THEN THE `Build_Script` SHALL abortar la ejecución sin ejecutar los pasos restantes y retornar un código de error al proceso padre.
5. THE `Build_Script` SHALL tener permisos de ejecución (`chmod +x build.sh`) en el repositorio.
6. IF `build.sh` completa con código de retorno cero, THEN THE sistema de Render SHALL iniciar `gunicorn` para aceptar tráfico.

---

### Requisito 5: Configuración Declarativa de Render

**Historia de Usuario:** Como desarrollador, quiero un archivo `render.yaml` en la raíz del proyecto que defina automáticamente el web service y la base de datos PostgreSQL, para que Render aprovisione toda la infraestructura sin configuración manual en el panel.

#### Criterios de Aceptación

1. THE `Render_Config` SHALL ser el archivo `render.yaml` ubicado en la raíz del repositorio, con una sección `services` que contenga exactamente 1 servicio de tipo `web`, y una sección `databases` con exactamente 1 base de datos, con `buildCommand: "./build.sh"` y `startCommand: "gunicorn ats2626.wsgi:application"`.
2. THE `Render_Config` SHALL definir la base de datos con `name: ats2626-db` y `plan: free`, y el web service también con `plan: free`.
3. THE `Render_Config` SHALL inyectar `DATABASE_URL` en el web service usando `fromDatabase.name: ats2626-db` y `fromDatabase.property: connectionString`.
4. THE `Render_Config` SHALL configurar `SECRET_KEY` con `generateValue: true` para que Render genere automáticamente su valor en el momento del despliegue.
5. THE `Render_Config` SHALL establecer `DEBUG: "False"` y `ALLOWED_HOSTS: "ats2626.onrender.com"` como variables de entorno fijas.
6. THE `Render_Config` SHALL especificar `PYTHON_VERSION: "3.11.0"` como variable de entorno del servicio.

---

### Requisito 6: Gestión Segura de Variables de Entorno

**Historia de Usuario:** Como desarrollador, quiero que las credenciales y configuración sensible se gestionen exclusivamente mediante variables de entorno, para evitar que secretos lleguen al repositorio Git.

#### Criterios de Aceptación

1. THE `Settings` SHALL leer `SECRET_KEY` desde `os.environ.get('SECRET_KEY')` con un valor de fallback que contiene la cadena `insecure`, usado únicamente para desarrollo local.
2. THE `Settings` SHALL leer `DEBUG` desde `os.environ.get('DEBUG', 'True')` y convertirlo a booleano comparando con la cadena `'True'`.
3. THE `Settings` SHALL leer `ALLOWED_HOSTS` desde `os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')` y dividirlo por comas en una lista de cadenas, usando `localhost,127.0.0.1` como fallback cuando la variable no está definida.
4. THE `.gitignore` SHALL incluir `.env`, `*.env` y `db.sqlite3` para excluirlos del repositorio Git.
5. WHILE `DEBUG` es `False`, IF `SECRET_KEY` contiene la cadena `insecure`, THEN THE `Settings` SHALL lanzar `ImproperlyConfigured` durante el arranque, impidiendo que Django inicie con credenciales de desarrollo.
6. THE `Settings` SHALL invocar `load_dotenv()` como primera instrucción tras los imports, antes de leer cualquier variable de entorno.
7. WHILE `DEBUG` es `False` y `SECRET_KEY` no contiene `insecure`, THE `Settings` SHALL arrancar sin error relacionado con la clave secreta.

---

### Requisito 7: Seguridad HTTPS en Producción

**Historia de Usuario:** Como administrador del sistema, quiero que la aplicación fuerce HTTPS y configure correctamente las cookies seguras cuando esté en producción, para proteger los datos de los usuarios en tránsito.

#### Criterios de Aceptación

1. WHILE `DEBUG` es `False`, THE `Settings` SHALL establecer `SECURE_SSL_REDIRECT = True`.
2. WHILE `DEBUG` es `False`, THE `Settings` SHALL establecer `SESSION_COOKIE_SECURE = True`.
3. WHILE `DEBUG` es `False`, THE `Settings` SHALL establecer `CSRF_COOKIE_SECURE = True`.
4. WHILE `DEBUG` es `False`, THE `Settings` SHALL establecer `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` para detectar correctamente el protocolo detrás del proxy inverso de Render.
5. WHILE `DEBUG` es `False`, THE `Settings` SHALL establecer `SECURE_HSTS_SECONDS = 31536000` y `SECURE_HSTS_INCLUDE_SUBDOMAINS = False`.
6. WHILE `DEBUG` es `True`, THE `Settings` SHALL establecer `SECURE_SSL_REDIRECT = False`, `SESSION_COOKIE_SECURE = False`, `CSRF_COOKIE_SECURE = False` y omitir `SECURE_HSTS_SECONDS` para no interferir con el servidor de desarrollo local.

---

### Requisito 8: Migración de Datos de SQLite a PostgreSQL

**Historia de Usuario:** Como administrador, quiero migrar los datos existentes de SQLite a PostgreSQL sin pérdida de registros, para preservar la información del sistema durante la transición de base de datos.

#### Criterios de Aceptación

1. WHEN el `Data_Migrator` exporta datos con `python manage.py dumpdata --exclude auth.permission --exclude contenttypes`, THE `Data_Migrator` SHALL generar un archivo JSON codificado en UTF-8 con todos los registros de los modelos `PerfilUsuario`, `Reclutador`, `Vacante`, `Candidato`, `Entrevista`, `Evaluacion`, `Oferta` y `auth.User`.
2. WHEN el `Data_Migrator` importa el archivo JSON en PostgreSQL con `python manage.py loaddata`, con la base de datos destino vacía y las migraciones aplicadas, THE `Data_Migrator` SHALL crear el mismo número de registros que existían en SQLite para cada modelo del criterio anterior.
3. WHEN el `Migration_Runner` ejecuta `python manage.py migrate` contra PostgreSQL vacío, THE `Migration_Runner` SHALL crear las tablas `reclutamiento_reclutador`, `reclutamiento_vacante`, `reclutamiento_candidato`, `reclutamiento_entrevista`, `reclutamiento_evaluacion`, `reclutamiento_oferta` y `reclutamiento_perfilusuario`.
4. IF `python manage.py loaddata` falla por cualquier causa (conflicto de FK, clave primaria duplicada, tipo de dato incompatible u otro), THEN THE `Data_Migrator` SHALL revertir todos los cambios del fixture en curso, restaurar el estado previo de la base de datos y emitir un mensaje de error que identifique el modelo afectado y la causa del fallo.
5. WHEN `loaddata` completa con éxito en PostgreSQL, THE `Data_Migrator` SHALL ejecutar `python manage.py sqlsequencereset reclutamiento | python manage.py dbshell` para actualizar las secuencias de autoincremento y evitar colisiones de PK en inserciones posteriores.

---

### Requisito 9: Servicio WSGI con Gunicorn

**Historia de Usuario:** Como operador de despliegue, quiero que la aplicación Django sea servida por Gunicorn en producción, para reemplazar el servidor de desarrollo de Django con un servidor WSGI apto para producción.

#### Criterios de Aceptación

1. THE `Settings` SHALL exponer `application = get_wsgi_application()` en `ats2626/wsgi.py` con `DJANGO_SETTINGS_MODULE` apuntando a `ats2626.settings`.
2. WHEN Gunicorn ejecuta `gunicorn ats2626.wsgi:application --bind 0.0.0.0:$PORT`, THE Gunicorn SHALL emitir la línea `Booting worker with pid` en stdout dentro de los 30 segundos siguientes al inicio del proceso.
3. WHEN Gunicorn recibe una petición HTTP válida a una ruta existente, THE Gunicorn SHALL retornar una respuesta con código de estado HTTP 2xx o 3xx.
4. IF Gunicorn no puede importar `ats2626.wsgi:application`, THEN THE Gunicorn SHALL emitir el traceback completo en stderr y terminar el proceso con código de salida distinto de cero.

---

### Requisito 10: Manejo de Archivos de Media en Entorno Efímero

**Historia de Usuario:** Como usuario del sistema, quiero que el sistema gestione correctamente la subida de hojas de vida aunque Render use un filesystem efímero, para que el comportamiento sea predecible y documentado.

#### Criterios de Aceptación

1. THE `Settings` SHALL establecer `MEDIA_URL = '/media/'` y `MEDIA_ROOT = BASE_DIR / 'media'`.
2. WHEN un usuario sube un archivo PDF a través del formulario de candidato, THE sistema SHALL almacenarlo en `MEDIA_ROOT/hojas_de_vida/{cedula}/{filename}` y retornar HTTP 200 en la vista de detalle del candidato mientras el contenedor de Render permanezca activo.
3. IF un usuario intenta subir un archivo que no sea PDF a través del `CandidatoForm`, THEN THE sistema SHALL rechazar la subida con un mensaje de error de validación sin almacenar el archivo.
4. WHILE `DEBUG` es `True`, THE `Settings` SHALL incluir la ruta de media en `urlpatterns` usando `django.conf.urls.static.static(MEDIA_URL, document_root=MEDIA_ROOT)` para servir archivos de media en desarrollo local.
5. THE documento `design.md` de la especificación SHALL contener una sección explícita que describa el comportamiento efímero del filesystem de Render y la pérdida de archivos de media en cada nuevo despliegue.
6. WHERE `DEFAULT_FILE_STORAGE` está configurado como un backend externo (distinto de `django.core.files.storage.FileSystemStorage`), THE `FileField` en los modelos existentes de `reclutamiento` SHALL no requerir ninguna modificación para redirigir la subida al backend externo.

---

## Propiedades de Corrección

*Una propiedad es una característica o comportamiento que debe cumplirse para todas las ejecuciones válidas del sistema — una especificación formal de lo que el sistema debe hacer.*

### Propiedad 1: Parseo universal de DATABASE_URL a PostgreSQL

*Para cualquier* cadena `DATABASE_URL` con formato `postgres://user:pass@host:port/dbname`, `dj_database_url.config()` SHALL retornar un diccionario donde `ENGINE` es `django.db.backends.postgresql`.

**Valida: Requisitos 1.1, 1.3**

---

### Propiedad 2: Fallback a SQLite cuando DATABASE_URL está ausente

*Para cualquier* entorno donde `DATABASE_URL` no está definida como variable de entorno, `DATABASES['default']['ENGINE']` SHALL ser `django.db.backends.sqlite3`.

**Valida: Requisito 1.2**

---

### Propiedad 3: Posición invariante de WhiteNoise en MIDDLEWARE

*Para cualquier* configuración válida del sistema, el índice de `whitenoise.middleware.WhiteNoiseMiddleware` en `settings.MIDDLEWARE` SHALL ser exactamente igual al índice de `django.middleware.security.SecurityMiddleware` más uno.

**Valida: Requisito 3.1**

---

### Propiedad 4: HTTPS forzado universalmente cuando DEBUG es False

*Para cualquier* configuración donde `DEBUG=False`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` SHALL ser `True`.

**Valida: Requisitos 7.1, 7.2, 7.3**

---

### Propiedad 5: SECRET_KEY segura en producción

*Para cualquier* instancia del sistema con `DEBUG=False`, `SECRET_KEY` SHALL no contener la subcadena `insecure`.

**Valida: Requisito 6.5**

---

### Propiedad 6: Round-trip de datos SQLite → PostgreSQL preserva registros

*Para cualquier* conjunto de modelos con N registros en SQLite, exportar con `dumpdata` e importar con `loaddata` en PostgreSQL SHALL producir exactamente N registros para cada modelo importado.

**Valida: Requisitos 8.1, 8.2**

---

### Propiedad 7: Conexión PostgreSQL con reconexión automática

*Para cualquier* configuración de `DATABASES['default']` apuntando a PostgreSQL, el parámetro `conn_max_age` SHALL ser 600 y `conn_health_checks` SHALL ser `True`.

**Valida: Requisito 1.3**
