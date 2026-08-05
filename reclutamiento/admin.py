"""
Registro de modelos en el panel de administración de Django.
Configura las vistas de administración con filtros, búsqueda y campos visibles.
"""
from django.contrib import admin
from .models import PerfilUsuario, Reclutador, Vacante, Candidato, Entrevista, Evaluacion, Oferta


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'telefono')
    list_filter = ('rol',)
    search_fields = ('user__username', 'user__email')


@admin.register(Reclutador)
class ReclutadorAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'correo', 'cargo', 'estado', 'fecha_registro')
    list_filter = ('estado', 'cargo')
    search_fields = ('nombres', 'apellidos', 'correo')
    ordering = ('apellidos',)


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'departamento', 'modalidad', 'salario', 'estado', 'reclutador', 'fecha_publicacion')
    list_filter = ('estado', 'departamento', 'modalidad', 'fuente')
    search_fields = ('titulo', 'descripcion')
    ordering = ('-fecha_publicacion',)
    date_hierarchy = 'fecha_publicacion'


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'cedula', 'correo', 'etapa_actual', 'estado', 'vacante')
    list_filter = ('etapa_actual', 'estado', 'vacante')
    search_fields = ('nombres', 'apellidos', 'cedula', 'correo')
    ordering = ('-fecha_registro',)


@admin.register(Entrevista)
class EntrevistaAdmin(admin.ModelAdmin):
    list_display = ('candidato', 'reclutador', 'fecha', 'hora_inicio', 'hora_fin', 'modalidad')
    list_filter = ('modalidad', 'fecha')
    search_fields = ('candidato__nombres', 'candidato__apellidos', 'reclutador__nombres')
    date_hierarchy = 'fecha'


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('entrevista', 'puntuacion', 'recomendacion')
    list_filter = ('recomendacion', 'puntuacion')
    search_fields = ('entrevista__candidato__nombres', 'comentario')


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ('candidato', 'cargo', 'salario', 'fecha', 'estado')
    list_filter = ('estado',)
    search_fields = ('candidato__nombres', 'cargo')
    date_hierarchy = 'fecha'
