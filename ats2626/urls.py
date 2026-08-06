"""
URL Configuration del proyecto ATS2626
Centraliza las rutas del proyecto e incluye las URLs de la app reclutamiento.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.http import FileResponse, Http404
import os
from reclutamiento import views as rec_views


def serve_sw(request):
    """Sirve el Service Worker desde la raíz del dominio (requerido por spec de PWA)."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    if not os.path.exists(sw_path):
        raise Http404
    response = FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Autenticación: login, logout y registro público
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', rec_views.registro_publico, name='registro'),

    # PWA: Service Worker y página offline
    path('sw.js', serve_sw, name='sw'),
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),

    # URLs de la aplicación de reclutamiento
    path('', include('reclutamiento.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
