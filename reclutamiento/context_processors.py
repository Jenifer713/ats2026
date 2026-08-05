"""
Context processors para el sistema ATS.
Inyecta el perfil y rol del usuario en todos los templates automáticamente.
"""
from .models import PerfilUsuario


def perfil_usuario(request):
    """
    Inyecta 'perfil_usuario' y 'rol_usuario' en el contexto de todos los templates.
    Evita excepciones RelatedObjectDoesNotExist cuando el usuario no tiene perfil.
    """
    if not request.user.is_authenticated:
        return {'perfil_usuario': None, 'rol_usuario': 'anonimo'}

    if request.user.is_superuser:
        return {'perfil_usuario': None, 'rol_usuario': 'admin'}

    try:
        perfil = request.user.perfil
        return {'perfil_usuario': perfil, 'rol_usuario': perfil.rol}
    except PerfilUsuario.DoesNotExist:
        # Usuario sin perfil asignado aún → rol más restrictivo
        return {'perfil_usuario': None, 'rol_usuario': 'coordinador'}
