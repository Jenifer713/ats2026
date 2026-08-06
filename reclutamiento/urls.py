"""
URLs de la aplicación reclutamiento.
Define todas las rutas con names para usar con {% url %} en los templates.
"""
from django.urls import path
from . import views

urlpatterns = [

    # ─── Landing pública / Dashboard ───
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro_publico, name='registro'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('reclutadores/', views.lista_reclutadores, name='lista_reclutadores'),
    path('reclutadores/nuevo/', views.crear_reclutador, name='crear_reclutador'),
    path('reclutadores/<int:pk>/editar/', views.editar_reclutador, name='editar_reclutador'),
    path('reclutadores/<int:pk>/eliminar/', views.eliminar_reclutador, name='eliminar_reclutador'),

    # ─── Vacantes ───
    path('vacantes/', views.lista_vacantes, name='lista_vacantes'),
    path('vacantes/nueva/', views.crear_vacante, name='crear_vacante'),
    path('vacantes/<int:pk>/', views.detalle_vacante, name='detalle_vacante'),
    path('vacantes/<int:pk>/editar/', views.editar_vacante, name='editar_vacante'),
    path('vacantes/<int:pk>/eliminar/', views.eliminar_vacante, name='eliminar_vacante'),

    # ─── Candidatos ───
    path('candidatos/', views.lista_candidatos, name='lista_candidatos'),
    path('candidatos/nuevo/', views.crear_candidato, name='crear_candidato'),
    path('candidatos/<int:pk>/', views.detalle_candidato, name='detalle_candidato'),
    path('candidatos/<int:pk>/editar/', views.editar_candidato, name='editar_candidato'),
    path('candidatos/<int:pk>/eliminar/', views.eliminar_candidato, name='eliminar_candidato'),

    # ─── Entrevistas ───
    path('entrevistas/', views.lista_entrevistas, name='lista_entrevistas'),
    path('entrevistas/nueva/', views.crear_entrevista, name='crear_entrevista'),
    path('entrevistas/<int:pk>/editar/', views.editar_entrevista, name='editar_entrevista'),
    path('entrevistas/<int:pk>/eliminar/', views.eliminar_entrevista, name='eliminar_entrevista'),

    # ─── Evaluaciones ───
    path('evaluaciones/', views.lista_evaluaciones, name='lista_evaluaciones'),
    path('evaluaciones/nueva/', views.crear_evaluacion, name='crear_evaluacion'),
    path('evaluaciones/<int:pk>/editar/', views.editar_evaluacion, name='editar_evaluacion'),
    path('evaluaciones/<int:pk>/eliminar/', views.eliminar_evaluacion, name='eliminar_evaluacion'),
    path('evaluaciones/<int:pk>/puntuacion/', views.guardar_puntuacion_rapida, name='guardar_puntuacion_rapida'),

    # ─── Ofertas ───
    path('ofertas/', views.lista_ofertas, name='lista_ofertas'),
    path('ofertas/nueva/', views.crear_oferta, name='crear_oferta'),
    path('ofertas/<int:pk>/editar/', views.editar_oferta, name='editar_oferta'),
    path('ofertas/<int:pk>/eliminar/', views.eliminar_oferta, name='eliminar_oferta'),

    # ─── Calendario (FullCalendar) ───
    path('calendario/', views.calendario, name='calendario'),
    path('calendario/eventos/', views.entrevistas_json, name='entrevistas_json'),
    path('calendario/crear/', views.crear_entrevista_ajax, name='crear_entrevista_ajax'),
    path('calendario/eliminar/<int:pk>/', views.eliminar_entrevista_ajax, name='eliminar_entrevista_ajax'),

    # ─── Pipeline (jQuery UI) ───
    path('pipeline/', views.pipeline, name='pipeline'),
    path('pipeline/actualizar/', views.actualizar_etapa_candidato, name='actualizar_etapa_candidato'),

    # ─── Reportes ───
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/compartir/', views.compartir_reporte, name='compartir_reporte'),
    path('reportes/exportar/pdf/', views.exportar_reporte_pdf, name='exportar_reporte_pdf'),
    path('reportes/exportar/excel/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
    path('reportes/exportar/<str:tabla>/<str:formato>/', views.exportar_tabla, name='exportar_tabla'),

    # ─── Usuarios y Roles (solo admin) ───
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/nuevo/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/<int:pk>/contrasena/', views.resetear_contrasena, name='resetear_contrasena'),

    # ─── Mi Perfil (todos los usuarios) ───
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),

    # ─── Mis Postulaciones (candidatos) ───
    path('mis-postulaciones/', views.mis_postulaciones, name='mis_postulaciones'),

    # ─── Compartir (correo) ───
    path('candidatos/<int:pk>/compartir/', views.compartir_candidato, name='compartir_candidato'),
]
