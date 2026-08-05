"""
Modelos del Sistema de Reclutamiento (ATS).
Define las entidades: PerfilUsuario (roles), Reclutador, Vacante,
Candidato, Entrevista, Evaluacion y Oferta.

ROLES DEL SISTEMA:
  - admin:       Acceso total (superusuario Django)
  - reclutador:  Gestiona vacantes, candidatos, entrevistas y evaluaciones
  - coordinador: Ve reportes, pipeline y calendario (solo lectura + entrevistas)
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, FileExtensionValidator


# ─────────────────────────────────────────────
# MODELO: PerfilUsuario  (extiende User de Django)
# ─────────────────────────────────────────────
class PerfilUsuario(models.Model):
    """
    Extiende el User de Django con un rol para el sistema ATS.
    Relación 1-a-1 con django.contrib.auth.models.User.
    """
    ROL_CHOICES = [
        ('admin',        'Administrador'),
        ('reclutador',   'Reclutador'),
        ('coordinador',  'Coordinador'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='Usuario'
    )
    rol = models.CharField(
        max_length=15,
        choices=ROL_CHOICES,
        default='reclutador',
        verbose_name='Rol'
    )
    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono'
    )

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_rol_display()})"

    def es_admin(self):
        return self.rol == 'admin' or self.user.is_superuser

    def es_reclutador(self):
        return self.rol == 'reclutador'

    def es_coordinador(self):
        return self.rol == 'coordinador'


# ─────────────────────────────────────────────
# MODELO: Reclutador
# ─────────────────────────────────────────────
class Reclutador(models.Model):
    """Representa a los profesionales de RRHH que gestionan el proceso de selección."""

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    correo = models.EmailField(unique=True, verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    cargo = models.CharField(max_length=100, verbose_name='Cargo')
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='activo',
        verbose_name='Estado'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Reclutador'
        verbose_name_plural = 'Reclutadores'
        ordering = ['apellidos', 'nombres']

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


# ─────────────────────────────────────────────
# MODELO: Vacante
# ─────────────────────────────────────────────
class Vacante(models.Model):
    """Representa una posición o cargo disponible en la organización."""

    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('remoto', 'Remoto'),
        ('hibrido', 'Híbrido'),
    ]

    ESTADO_CHOICES = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
        ('pausada', 'Pausada'),
    ]

    DEPARTAMENTO_CHOICES = [
        ('tecnologia', 'Tecnología'),
        ('marketing', 'Marketing'),
        ('ventas', 'Ventas'),
        ('rrhh', 'Recursos Humanos'),
        ('finanzas', 'Finanzas'),
        ('operaciones', 'Operaciones'),
        ('legal', 'Legal'),
        ('administracion', 'Administración'),
        ('otro', 'Otro'),
    ]

    titulo = models.CharField(max_length=200, verbose_name='Título del Puesto')
    descripcion = models.TextField(verbose_name='Descripción')
    departamento = models.CharField(
        max_length=50,
        choices=DEPARTAMENTO_CHOICES,
        verbose_name='Departamento'
    )
    modalidad = models.CharField(
        max_length=15,
        choices=MODALIDAD_CHOICES,
        verbose_name='Modalidad'
    )
    salario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Salario'
    )
    fecha_publicacion = models.DateField(verbose_name='Fecha de Publicación')
    fecha_cierre = models.DateField(verbose_name='Fecha de Cierre')
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='abierta',
        verbose_name='Estado'
    )
    # Fuente de reclutamiento para reportes de efectividad
    fuente = models.CharField(
        max_length=30,
        choices=[
            ('linkedin', 'LinkedIn'),
            ('portal_web', 'Portal Web'),
            ('referido', 'Referido'),
            ('otro', 'Otro'),
        ],
        default='portal_web',
        verbose_name='Fuente de Reclutamiento'
    )
    reclutador = models.ForeignKey(
        Reclutador,
        on_delete=models.PROTECT,
        related_name='vacantes',
        verbose_name='Reclutador Responsable'
    )

    class Meta:
        verbose_name = 'Vacante'
        verbose_name_plural = 'Vacantes'
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return f"{self.titulo} - {self.get_departamento_display()}"


# ─────────────────────────────────────────────
# MODELO: Candidato
# ─────────────────────────────────────────────
class Candidato(models.Model):
    """Representa a una persona que postula a una vacante."""

    ETAPA_CHOICES = [
        ('postulado', 'Postulado'),
        ('preseleccion', 'Preselección'),
        ('entrevista', 'Entrevista'),
        ('evaluacion', 'Evaluación'),
        ('oferta', 'Oferta'),
        ('contratado', 'Contratado'),
        ('rechazado', 'Rechazado'),
    ]

    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    cedula = models.CharField(max_length=20, unique=True, verbose_name='Cédula')
    correo = models.EmailField(verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=20, verbose_name='Teléfono')
    hoja_de_vida = models.FileField(
        upload_to='hojas_de_vida/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True,
        blank=True,
        verbose_name='Hoja de Vida (PDF)'
    )
    etapa_actual = models.CharField(
        max_length=15,
        choices=ETAPA_CHOICES,
        default='postulado',
        verbose_name='Etapa Actual'
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='activo',
        verbose_name='Estado'
    )
    vacante = models.ForeignKey(
        Vacante,
        on_delete=models.PROTECT,
        related_name='candidatos',
        verbose_name='Vacante Postulada'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Candidato'
        verbose_name_plural = 'Candidatos'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.cedula}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


# ─────────────────────────────────────────────
# MODELO: Entrevista
# ─────────────────────────────────────────────
class Entrevista(models.Model):
    """Programación de entrevistas entre candidatos y reclutadores."""

    MODALIDAD_CHOICES = [
        ('presencial', 'Presencial'),
        ('virtual', 'Virtual'),
        ('telefonica', 'Telefónica'),
    ]

    candidato = models.ForeignKey(
        Candidato,
        on_delete=models.CASCADE,
        related_name='entrevistas',
        verbose_name='Candidato'
    )
    reclutador = models.ForeignKey(
        Reclutador,
        on_delete=models.PROTECT,
        related_name='entrevistas',
        verbose_name='Reclutador'
    )
    fecha = models.DateField(verbose_name='Fecha')
    hora_inicio = models.TimeField(verbose_name='Hora de Inicio')
    hora_fin = models.TimeField(verbose_name='Hora de Fin')
    modalidad = models.CharField(
        max_length=15,
        choices=MODALIDAD_CHOICES,
        verbose_name='Modalidad'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Entrevista'
        verbose_name_plural = 'Entrevistas'
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"Entrevista: {self.candidato} - {self.fecha}"

    def fecha_hora_inicio_iso(self):
        """Retorna fecha y hora de inicio en formato ISO 8601 para FullCalendar."""
        return f"{self.fecha}T{self.hora_inicio}"

    def fecha_hora_fin_iso(self):
        """Retorna fecha y hora de fin en formato ISO 8601 para FullCalendar."""
        return f"{self.fecha}T{self.hora_fin}"


# ─────────────────────────────────────────────
# MODELO: Evaluacion
# ─────────────────────────────────────────────
class Evaluacion(models.Model):
    """Resultado de la evaluación realizada durante o después de una entrevista."""

    RECOMENDACION_CHOICES = [
        ('contratar', 'Contratar'),
        ('considerar', 'Considerar'),
        ('rechazar', 'Rechazar'),
    ]

    entrevista = models.OneToOneField(
        Entrevista,
        on_delete=models.CASCADE,
        related_name='evaluacion',
        verbose_name='Entrevista'
    )
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Puntuación (1-5)'
    )
    comentario = models.TextField(verbose_name='Comentario')
    recomendacion = models.CharField(
        max_length=15,
        choices=RECOMENDACION_CHOICES,
        verbose_name='Recomendación'
    )

    class Meta:
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'

    def __str__(self):
        return f"Evaluación de {self.entrevista.candidato} - Puntuación: {self.puntuacion}"

    def puntuacion_texto(self):
        """Convierte la puntuación numérica a texto descriptivo."""
        textos = {1: 'Muy Malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Excelente'}
        return textos.get(self.puntuacion, 'N/A')


# ─────────────────────────────────────────────
# MODELO: Oferta
# ─────────────────────────────────────────────
class Oferta(models.Model):
    """Oferta laboral formal enviada a un candidato seleccionado."""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida'),
    ]

    candidato = models.ForeignKey(
        Candidato,
        on_delete=models.CASCADE,
        related_name='ofertas',
        verbose_name='Candidato'
    )
    salario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Salario Ofrecido'
    )
    cargo = models.CharField(max_length=200, verbose_name='Cargo')
    fecha = models.DateField(verbose_name='Fecha de Oferta')
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    class Meta:
        verbose_name = 'Oferta'
        verbose_name_plural = 'Ofertas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Oferta para {self.candidato} - {self.get_estado_display()}"
