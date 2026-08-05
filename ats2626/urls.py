"""
URL Configuration del proyecto ATS2626
Centraliza las rutas del proyecto e incluye las URLs de la app reclutamiento.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Autenticación: login y logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # URLs de la aplicación de reclutamiento
    path('', include('reclutamiento.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
