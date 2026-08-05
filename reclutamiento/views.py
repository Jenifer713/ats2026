"""
Vistas basadas en funciones (FBV) para el Sistema ATS.
Roles: admin (acceso total), reclutador (gestión), coordinador (solo lectura + entrevistas)
"""
import json
from datetime import date, timedelta
from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import PerfilUsuario, Reclutador, Vacante, Candidato, Entrevista, Evaluacion, Oferta
from .forms import (
    UsuarioCrearForm, UsuarioEditarForm,
    ReclutadorForm, VacanteForm, CandidatoForm,
    EntrevistaForm, EvaluacionForm, OfertaForm
)
from .emails import (
    enviar_bienvenida, enviar_candidato_aceptado, enviar_candidato_rechazado,
    enviar_notificacion_entrevista, enviar_reporte_compartido
)


# ─── Decoradores de roles ───────────────────────────────────────
def rol_requerido(*roles):
    """
    Decorador que restringe el acceso a vistas según el rol del usuario.
    Los superusuarios siempre tienen acceso total.
    Uso: @rol_requerido('admin') o @rol_requerido('admin', 'reclutador')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                perfil = request.user.perfil
                if perfil.rol in roles:
                    return view_func(request, *args, **kwargs)
            except PerfilUsuario.DoesNotExist:
                pass
            messages.error(request, 'No tienes permiso para realizar esta acción.')
            return redirect('dashboard')
        return wrapper
    return decorator


def get_rol_usuario(user):
    """Retorna el rol del usuario o 'admin' si es superusuario."""
    if user.is_superuser:
        return 'admin'
    try:
        return user.perfil.rol
    except PerfilUsuario.DoesNotExist:
        return 'coordinador'  # rol más restrictivo por defecto


# ═══════════════════════════════════════════════════════════════
# LANDING PAGE PÚBLICA
# ═══════════════════════════════════════════════════════════════
def inicio(request):
    """
    Página de inicio pública.
    Si el usuario ya está autenticado, redirige al dashboard.
    Si no, muestra la landing page.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def registro_publico(request):
    """Registro público de nuevos usuarios (candidatos)."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')

        # Validaciones
        error = None
        if not all([username, first_name, last_name, email, password1, password2]):
            error = 'Todos los campos son obligatorios.'
        elif len(first_name) < 2 or len(last_name) < 2:
            error = 'Nombres y apellidos deben tener al menos 2 caracteres.'
        elif len(username) < 3:
            error = 'El nombre de usuario debe tener al menos 3 caracteres.'
        elif User.objects.filter(username=username).exists():
            error = f'El usuario "{username}" ya está en uso. Elige otro.'
        elif User.objects.filter(email=email).exists():
            error = 'Ya existe una cuenta con ese correo electrónico.'
        elif password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif len(password1) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        else:
            import re
            if not re.match(r'^[a-zA-Z0-9_.@+-]+$', username):
                error = 'Usuario inválido. Solo letras, números y @/./+/-/_'

        if error:
            return render(request, 'login.html', {
                'modo': 'registro',
                'registro_error': error,
                'reg_data': {
                    'username': username, 'first_name': first_name,
                    'last_name': last_name, 'email': email,
                }
            })

        # Crear usuario
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password1,
        )
        PerfilUsuario.objects.create(user=user, rol='coordinador')

        # Enviar correo de bienvenida (no bloquea si falla)
        try:
            enviar_bienvenida(user)
        except Exception:
            pass

        messages.success(
            request,
            f'¡Cuenta creada exitosamente! Bienvenido/a {first_name}. '
            'Revisa tu correo para ver la confirmación.'
        )
        return redirect('/login/')

    return render(request, 'login.html', {'modo': 'registro'})




# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════
@login_required
def dashboard(request):
    """
    Vista principal del dashboard con métricas y gráficos del ATS.
    Si no hay reclutadores ni vacantes, muestra pantalla de onboarding.
    """
    hoy = date.today()

    # ─── Onboarding: detectar si el sistema está recién instalado ───
    total_reclutadores = Reclutador.objects.count()
    total_vacantes_bd  = Vacante.objects.count()

    if total_reclutadores == 0:
        # Sistema vacío: mostrar guía de primeros pasos
        return render(request, 'onboarding.html', {
            'paso': 1,
            'mensaje': 'Bienvenido al Sistema ATS. Comienza creando el primer reclutador.'
        })

    if total_vacantes_bd == 0:
        return render(request, 'onboarding.html', {
            'paso': 2,
            'mensaje': 'Ya tienes reclutadores registrados. Ahora crea tu primera vacante.'
        })

    # ─── Métricas principales ───
    vacantes_abiertas      = Vacante.objects.filter(estado='abierta').count()
    vacantes_cerradas      = Vacante.objects.filter(estado='cerrada').count()
    total_candidatos       = Candidato.objects.count()
    entrevistas_programadas = Entrevista.objects.filter(fecha__gte=hoy).count()
    total_contratados      = Candidato.objects.filter(etapa_actual='contratado').count()

    # ─── Candidatos por etapa ───
    etapas = ['postulado', 'preseleccion', 'entrevista', 'evaluacion', 'oferta', 'contratado', 'rechazado']
    candidatos_por_etapa = [Candidato.objects.filter(etapa_actual=e).count() for e in etapas]

    # ─── Time-to-Hire promedio ───
    contratados = Candidato.objects.filter(etapa_actual='contratado')
    time_to_hire_promedio = 0
    if contratados.exists():
        total_dias = sum((hoy - c.fecha_registro.date()).days for c in contratados)
        time_to_hire_promedio = round(total_dias / contratados.count(), 1)

    # ─── Contrataciones por mes (últimos 6 meses) ───
    meses_labels, contrataciones_por_mes = [], []
    for i in range(5, -1, -1):
        mes = hoy - timedelta(days=30 * i)
        meses_labels.append(mes.strftime('%b %Y'))
        contrataciones_por_mes.append(
            Candidato.objects.filter(
                etapa_actual='contratado',
                fecha_registro__month=mes.month,
                fecha_registro__year=mes.year
            ).count()
        )

    # ─── Últimas 5 entrevistas próximas ───
    proximas_entrevistas = Entrevista.objects.filter(
        fecha__gte=hoy
    ).select_related('candidato', 'reclutador').order_by('fecha', 'hora_inicio')[:5]

    # ─── Candidatos recientes ───
    candidatos_recientes = Candidato.objects.select_related('vacante').order_by('-fecha_registro')[:5]

    context = {
        'vacantes_abiertas':       vacantes_abiertas,
        'vacantes_cerradas':       vacantes_cerradas,
        'total_candidatos':        total_candidatos,
        'entrevistas_programadas': entrevistas_programadas,
        'total_contratados':       total_contratados,
        'time_to_hire_promedio':   time_to_hire_promedio,
        'total_reclutadores':      total_reclutadores,
        'candidatos_por_etapa':    json.dumps(candidatos_por_etapa),
        'etapas_labels':           json.dumps([e.capitalize() for e in etapas]),
        'meses_labels':            json.dumps(meses_labels),
        'contrataciones_por_mes':  json.dumps(contrataciones_por_mes),
        'proximas_entrevistas':    proximas_entrevistas,
        'candidatos_recientes':    candidatos_recientes,
        'rol_usuario':             get_rol_usuario(request.user),
    }
    return render(request, 'dashboard.html', context)


# ═══════════════════════════════════════════════════════════════
# CRUD RECLUTADORES
# ═══════════════════════════════════════════════════════════════
@login_required
def lista_reclutadores(request):
    """Lista todos los reclutadores con búsqueda y paginación."""
    query = request.GET.get('q', '')
    reclutadores = Reclutador.objects.all()
    if query:
        reclutadores = reclutadores.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(correo__icontains=query) |
            Q(cargo__icontains=query)
        )
    paginator = Paginator(reclutadores, 10)
    page = request.GET.get('page')
    reclutadores_paginados = paginator.get_page(page)
    return render(request, 'lista_reclutadores.html', {
        'reclutadores': reclutadores_paginados,
        'query': query,
    })


@login_required
@rol_requerido('admin', 'reclutador')
def crear_reclutador(request):
    """Crea un nuevo reclutador."""
    if request.method == 'POST':
        form = ReclutadorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reclutador creado exitosamente.')
            return redirect('lista_reclutadores')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ReclutadorForm()
    return render(request, 'form_reclutador.html', {'form': form, 'titulo': 'Nuevo Reclutador'})


@login_required
@rol_requerido('admin', 'reclutador')
def editar_reclutador(request, pk):
    """Edita un reclutador existente."""
    reclutador = get_object_or_404(Reclutador, pk=pk)
    if request.method == 'POST':
        form = ReclutadorForm(request.POST, instance=reclutador)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reclutador actualizado correctamente.')
            return redirect('lista_reclutadores')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ReclutadorForm(instance=reclutador)
    return render(request, 'form_reclutador.html', {
        'form': form, 'titulo': 'Editar Reclutador', 'objeto': reclutador
    })


@login_required
@rol_requerido('admin', 'reclutador')
def eliminar_reclutador(request, pk):
    reclutador = get_object_or_404(Reclutador, pk=pk)
    if request.method == 'POST':
        if reclutador.vacantes.exists():
            messages.error(
                request,
                f'No se puede eliminar al reclutador "{reclutador}" porque tiene '
                f'{reclutador.vacantes.count()} vacante(s) asignada(s). '
                'Reasigna o elimina las vacantes primero.'
            )
            return redirect('lista_reclutadores')
        reclutador.delete()
        messages.success(request, f'Reclutador "{reclutador}" eliminado correctamente.')
        return redirect('lista_reclutadores')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': reclutador, 'tipo': 'Reclutador',
        'cancelar_url': 'lista_reclutadores',
        'advertencia': f'Este reclutador tiene {reclutador.vacantes.count()} vacante(s) asignada(s).' if reclutador.vacantes.exists() else None,
    })


# ═══════════════════════════════════════════════════════════════
# CRUD VACANTES
# ═══════════════════════════════════════════════════════════════
@login_required
def lista_vacantes(request):
    """Lista vacantes con búsqueda, filtro por estado y paginación."""
    from datetime import date as _date
    query  = request.GET.get('q', '')
    estado = request.GET.get('estado', '')
    vacantes = Vacante.objects.select_related('reclutador').prefetch_related('candidatos').all()
    if query:
        vacantes = vacantes.filter(
            Q(titulo__icontains=query) |
            Q(departamento__icontains=query) |
            Q(descripcion__icontains=query)
        )
    if estado:
        vacantes = vacantes.filter(estado=estado)
    paginator = Paginator(vacantes, 10)
    page = request.GET.get('page')
    vacantes_paginadas = paginator.get_page(page)
    return render(request, 'lista_vacantes.html', {
        'vacantes': vacantes_paginadas,
        'query':    query,
        'hoy':      _date.today(),
    })


@login_required
@rol_requerido('admin', 'reclutador')
def crear_vacante(request):
    """Crea una nueva vacante."""
    if request.method == 'POST':
        form = VacanteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vacante creada exitosamente.')
            return redirect('lista_vacantes')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = VacanteForm()
    return render(request, 'form_vacante.html', {'form': form, 'titulo': 'Nueva Vacante'})


@login_required
@rol_requerido('admin', 'reclutador')
def editar_vacante(request, pk):
    """Edita una vacante existente."""
    vacante = get_object_or_404(Vacante, pk=pk)
    if request.method == 'POST':
        form = VacanteForm(request.POST, instance=vacante)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vacante actualizada correctamente.')
            return redirect('lista_vacantes')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = VacanteForm(instance=vacante)
    return render(request, 'form_vacante.html', {
        'form': form, 'titulo': 'Editar Vacante', 'objeto': vacante
    })


@login_required
@rol_requerido('admin', 'reclutador')
def eliminar_vacante(request, pk):
    """Elimina una vacante previa confirmación."""
    vacante = get_object_or_404(Vacante, pk=pk)
    if request.method == 'POST':
        # Verificar que no tenga candidatos asociados
        if vacante.candidatos.exists():
            messages.error(
                request,
                f'No se puede eliminar la vacante "{vacante.titulo}" porque tiene '
                f'{vacante.candidatos.count()} candidato(s) asociado(s). '
                'Primero elimina o reasigna los candidatos.'
            )
            return redirect('lista_vacantes')
        vacante.delete()
        messages.success(request, f'Vacante "{vacante.titulo}" eliminada correctamente.')
        return redirect('lista_vacantes')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': vacante, 'tipo': 'Vacante', 'cancelar_url': 'lista_vacantes',
        'advertencia': f'Esta vacante tiene {vacante.candidatos.count()} candidato(s) asociado(s).' if vacante.candidatos.exists() else None,
    })


@login_required
def detalle_vacante(request, pk):
    """Detalle de una vacante con sus candidatos y estadísticas."""
    vacante = get_object_or_404(Vacante, pk=pk)
    candidatos = vacante.candidatos.all().order_by('-fecha_registro')
    etapas_count = {
        etapa: candidatos.filter(etapa_actual=etapa).count()
        for etapa, _ in Candidato.ETAPA_CHOICES
    }
    return render(request, 'detalle_vacante.html', {
        'vacante':      vacante,
        'candidatos':   candidatos,
        'etapas_count': etapas_count,
        'total':        candidatos.count(),
    })


# ═══════════════════════════════════════════════════════════════
# CRUD CANDIDATOS
# ═══════════════════════════════════════════════════════════════
@login_required
def lista_candidatos(request):
    """Lista candidatos con búsqueda, filtro por etapa y paginación."""
    query = request.GET.get('q', '')
    etapa = request.GET.get('etapa', '')
    candidatos = Candidato.objects.select_related('vacante').all()
    if query:
        candidatos = candidatos.filter(
            Q(nombres__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(cedula__icontains=query) |
            Q(correo__icontains=query)
        )
    if etapa:
        candidatos = candidatos.filter(etapa_actual=etapa)
    paginator = Paginator(candidatos, 10)
    page = request.GET.get('page')
    candidatos_paginados = paginator.get_page(page)
    return render(request, 'lista_candidatos.html', {
        'candidatos': candidatos_paginados,
        'query':      query,
        'etapa':      etapa,
    })


@login_required
@rol_requerido('admin', 'reclutador')
def crear_candidato(request):
    """Crea un nuevo candidato."""
    if request.method == 'POST':
        form = CandidatoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Candidato registrado exitosamente.')
            return redirect('lista_candidatos')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CandidatoForm()
    return render(request, 'form_candidato.html', {'form': form, 'titulo': 'Nuevo Candidato'})


@login_required
@rol_requerido('admin', 'reclutador')
def editar_candidato(request, pk):
    """Edita un candidato existente."""
    candidato = get_object_or_404(Candidato, pk=pk)
    etapa_anterior = candidato.etapa_actual
    if request.method == 'POST':
        form = CandidatoForm(request.POST, request.FILES, instance=candidato)
        if form.is_valid():
            candidato_actualizado = form.save()
            nueva_etapa = candidato_actualizado.etapa_actual
            # Enviar correo si cambia a contratado o rechazado
            if etapa_anterior != nueva_etapa:
                try:
                    if nueva_etapa == 'contratado':
                        enviar_candidato_aceptado(candidato_actualizado)
                    elif nueva_etapa == 'rechazado':
                        enviar_candidato_rechazado(candidato_actualizado)
                except Exception:
                    pass
            messages.success(request, 'Candidato actualizado correctamente.')
            return redirect('lista_candidatos')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CandidatoForm(instance=candidato)
    return render(request, 'form_candidato.html', {
        'form': form, 'titulo': 'Editar Candidato', 'objeto': candidato
    })


@login_required
@rol_requerido('admin', 'reclutador')
def eliminar_candidato(request, pk):
    """Elimina un candidato previa confirmación."""
    candidato = get_object_or_404(Candidato, pk=pk)
    if request.method == 'POST':
        candidato.delete()
        messages.success(request, f'Candidato "{candidato}" eliminado correctamente.')
        return redirect('lista_candidatos')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': candidato, 'tipo': 'Candidato', 'cancelar_url': 'lista_candidatos'
    })


@login_required
def detalle_candidato(request, pk):
    """Detalle completo de un candidato: entrevistas, evaluaciones y ofertas."""
    candidato = get_object_or_404(Candidato, pk=pk)
    entrevistas = candidato.entrevistas.select_related('reclutador').order_by('-fecha')
    ofertas = candidato.ofertas.order_by('-fecha')
    return render(request, 'detalle_candidato.html', {
        'candidato':   candidato,
        'entrevistas': entrevistas,
        'ofertas':     ofertas,
    })


# ═══════════════════════════════════════════════════════════════
# CRUD ENTREVISTAS
# ═══════════════════════════════════════════════════════════════
@login_required
def lista_entrevistas(request):
    """Lista entrevistas con búsqueda y paginación."""
    query = request.GET.get('q', '')
    entrevistas = Entrevista.objects.select_related('candidato', 'reclutador').all()
    if query:
        entrevistas = entrevistas.filter(
            Q(candidato__nombres__icontains=query) |
            Q(candidato__apellidos__icontains=query) |
            Q(reclutador__nombres__icontains=query)
        )
    paginator = Paginator(entrevistas, 10)
    page = request.GET.get('page')
    entrevistas_paginadas = paginator.get_page(page)
    return render(request, 'lista_entrevistas.html', {
        'entrevistas': entrevistas_paginadas, 'query': query
    })


@login_required
def crear_entrevista(request):
    """Crea una nueva entrevista. Bloquea fechas pasadas al crear."""
    if request.method == 'POST':
        form = EntrevistaForm(request.POST, es_creacion=True)
        if form.is_valid():
            entrevista = form.save()
            # Notificar al candidato por correo
            try:
                enviar_notificacion_entrevista(entrevista.candidato, entrevista)
            except Exception:
                pass
            messages.success(request, 'Entrevista programada exitosamente.')
            return redirect('lista_entrevistas')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        initial = {}
        if request.GET.get('fecha'):
            initial['fecha'] = request.GET.get('fecha')
        if request.GET.get('candidato'):
            initial['candidato'] = request.GET.get('candidato')
        form = EntrevistaForm(initial=initial, es_creacion=True)
    return render(request, 'form_entrevista.html', {'form': form, 'titulo': 'Nueva Entrevista'})


@login_required
def editar_entrevista(request, pk):
    """Edita una entrevista existente. No valida fecha pasada en edición."""
    entrevista = get_object_or_404(Entrevista, pk=pk)
    if request.method == 'POST':
        form = EntrevistaForm(request.POST, instance=entrevista, es_creacion=False)
        if form.is_valid():
            form.save()
            messages.success(request, 'Entrevista actualizada correctamente.')
            return redirect('lista_entrevistas')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = EntrevistaForm(instance=entrevista, es_creacion=False)
    return render(request, 'form_entrevista.html', {
        'form': form, 'titulo': 'Editar Entrevista', 'objeto': entrevista
    })


@login_required
def eliminar_entrevista(request, pk):
    """Elimina una entrevista previa confirmación."""
    entrevista = get_object_or_404(Entrevista, pk=pk)
    if request.method == 'POST':
        entrevista.delete()
        messages.success(request, 'Entrevista eliminada correctamente.')
        return redirect('lista_entrevistas')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': entrevista, 'tipo': 'Entrevista', 'cancelar_url': 'lista_entrevistas'
    })


# ═══════════════════════════════════════════════════════════════
# CRUD EVALUACIONES
# ═══════════════════════════════════════════════════════════════
@login_required
def lista_evaluaciones(request):
    """Lista evaluaciones con búsqueda y paginación."""
    query = request.GET.get('q', '')
    evaluaciones = Evaluacion.objects.select_related('entrevista__candidato').all()
    if query:
        evaluaciones = evaluaciones.filter(
            Q(entrevista__candidato__nombres__icontains=query) |
            Q(entrevista__candidato__apellidos__icontains=query) |
            Q(comentario__icontains=query)
        )
    paginator = Paginator(evaluaciones, 10)
    page = request.GET.get('page')
    evaluaciones_paginadas = paginator.get_page(page)
    return render(request, 'lista_evaluaciones.html', {
        'evaluaciones': evaluaciones_paginadas, 'query': query
    })


@login_required
def crear_evaluacion(request):
    """Crea una nueva evaluación."""
    if request.method == 'POST':
        form = EvaluacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evaluación registrada exitosamente.')
            return redirect('lista_evaluaciones')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        initial = {}
        if request.GET.get('entrevista_id'):
            initial['entrevista'] = request.GET.get('entrevista_id')
        form = EvaluacionForm(initial=initial)
    return render(request, 'form_evaluacion.html', {
        'form': form, 'titulo': 'Nueva Evaluación'
    })


@login_required
def editar_evaluacion(request, pk):
    """Edita una evaluación existente."""
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    if request.method == 'POST':
        form = EvaluacionForm(request.POST, instance=evaluacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evaluación actualizada correctamente.')
            return redirect('lista_evaluaciones')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = EvaluacionForm(instance=evaluacion)
    return render(request, 'form_evaluacion.html', {
        'form': form, 'titulo': 'Editar Evaluación', 'objeto': evaluacion
    })


@login_required
def eliminar_evaluacion(request, pk):
    """Elimina una evaluación previa confirmación."""
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    if request.method == 'POST':
        evaluacion.delete()
        messages.success(request, 'Evaluación eliminada correctamente.')
        return redirect('lista_evaluaciones')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': evaluacion, 'tipo': 'Evaluación', 'cancelar_url': 'lista_evaluaciones'
    })


# ═══════════════════════════════════════════════════════════════
# CRUD OFERTAS
# ═══════════════════════════════════════════════════════════════
@login_required
def lista_ofertas(request):
    """Lista ofertas con búsqueda y paginación."""
    query = request.GET.get('q', '')
    ofertas = Oferta.objects.select_related('candidato').all()
    if query:
        ofertas = ofertas.filter(
            Q(candidato__nombres__icontains=query) |
            Q(candidato__apellidos__icontains=query) |
            Q(cargo__icontains=query)
        )
    paginator = Paginator(ofertas, 10)
    page = request.GET.get('page')
    ofertas_paginadas = paginator.get_page(page)
    return render(request, 'lista_ofertas.html', {
        'ofertas': ofertas_paginadas, 'query': query
    })


@login_required
def crear_oferta(request):
    """Crea una nueva oferta laboral."""
    if request.method == 'POST':
        form = OfertaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Oferta creada exitosamente.')
            return redirect('lista_ofertas')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = OfertaForm()
    return render(request, 'form_oferta.html', {'form': form, 'titulo': 'Nueva Oferta'})


@login_required
def editar_oferta(request, pk):
    """Edita una oferta existente."""
    oferta = get_object_or_404(Oferta, pk=pk)
    if request.method == 'POST':
        form = OfertaForm(request.POST, instance=oferta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Oferta actualizada correctamente.')
            return redirect('lista_ofertas')
        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = OfertaForm(instance=oferta)
    return render(request, 'form_oferta.html', {
        'form': form, 'titulo': 'Editar Oferta', 'objeto': oferta
    })


@login_required
def eliminar_oferta(request, pk):
    """Elimina una oferta previa confirmación."""
    oferta = get_object_or_404(Oferta, pk=pk)
    if request.method == 'POST':
        oferta.delete()
        messages.success(request, 'Oferta eliminada correctamente.')
        return redirect('lista_ofertas')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': oferta, 'tipo': 'Oferta', 'cancelar_url': 'lista_ofertas'
    })


# ═══════════════════════════════════════════════════════════════
# CALENDARIO - FullCalendar (AJAX endpoints)
# ═══════════════════════════════════════════════════════════════
@login_required
def calendario(request):
    """Renderiza la vista del calendario de entrevistas con FullCalendar."""
    form = EntrevistaForm(es_creacion=True)
    return render(request, 'calendario.html', {'form': form})


@login_required
def entrevistas_json(request):
    """Devuelve todas las entrevistas en formato JSON para FullCalendar."""
    entrevistas = Entrevista.objects.select_related('candidato', 'reclutador').all()
    eventos = []
    colores = {
        'presencial': '#0d6efd',
        'virtual': '#198754',
        'telefonica': '#fd7e14',
    }
    for e in entrevistas:
        eventos.append({
            'id': e.pk,
            'title': f"{e.candidato.nombre_completo}",
            'start': f"{e.fecha}T{e.hora_inicio}",
            'end': f"{e.fecha}T{e.hora_fin}",
            'color': colores.get(e.modalidad, '#6c757d'),
            'extendedProps': {
                'candidato': e.candidato.nombre_completo,
                'reclutador': e.reclutador.nombre_completo,
                'modalidad': e.get_modalidad_display(),
                'observaciones': e.observaciones or '',
                'editar_url': f'/entrevistas/{e.pk}/editar/',
                'eliminar_url': f'/entrevistas/{e.pk}/eliminar/',
            }
        })
    return JsonResponse(eventos, safe=False)


@login_required
@require_POST
def crear_entrevista_ajax(request):
    """Crea una entrevista desde el calendario mediante AJAX."""
    form = EntrevistaForm(request.POST, es_creacion=True)
    if form.is_valid():
        entrevista = form.save()
        return JsonResponse({
            'status': 'ok',
            'id': entrevista.pk,
            'title': entrevista.candidato.nombre_completo,
            'start': f"{entrevista.fecha}T{entrevista.hora_inicio}",
            'end': f"{entrevista.fecha}T{entrevista.hora_fin}",
        })
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


@login_required
@require_POST
def eliminar_entrevista_ajax(request, pk):
    """Elimina una entrevista mediante AJAX desde el calendario."""
    entrevista = get_object_or_404(Entrevista, pk=pk)
    entrevista.delete()
    return JsonResponse({'status': 'ok'})


# ═══════════════════════════════════════════════════════════════
# PIPELINE - jQuery UI Drag & Drop
# ═══════════════════════════════════════════════════════════════
@login_required
def pipeline(request):
    """Vista del pipeline Kanban con arrastrar y soltar por etapas."""
    etapas = [
        ('postulado', 'Postulado', 'secondary'),
        ('preseleccion', 'Preselección', 'info'),
        ('entrevista', 'Entrevista', 'primary'),
        ('evaluacion', 'Evaluación', 'warning'),
        ('oferta', 'Oferta', 'success'),
        ('contratado', 'Contratado', 'dark'),
        ('rechazado', 'Rechazado', 'danger'),
    ]
    pipeline_data = []
    for codigo, nombre, color in etapas:
        candidatos = Candidato.objects.filter(
            etapa_actual=codigo
        ).select_related('vacante')
        pipeline_data.append({
            'codigo': codigo,
            'nombre': nombre,
            'color': color,
            'candidatos': candidatos,
            'total': candidatos.count(),
        })
    return render(request, 'pipeline.html', {'pipeline_data': pipeline_data})


@login_required
@require_POST
def actualizar_etapa_candidato(request):
    """Actualiza la etapa de un candidato vía AJAX cuando se arrastra en el pipeline."""
    candidato_id = request.POST.get('candidato_id')
    nueva_etapa = request.POST.get('etapa')
    etapas_validas = [
        'postulado', 'preseleccion', 'entrevista',
        'evaluacion', 'oferta', 'contratado', 'rechazado'
    ]
    if not candidato_id or nueva_etapa not in etapas_validas:
        return JsonResponse({'status': 'error', 'mensaje': 'Datos inválidos'}, status=400)

    candidato = get_object_or_404(Candidato, pk=candidato_id)
    etapa_anterior = candidato.etapa_actual
    candidato.etapa_actual = nueva_etapa
    candidato.save()
    # Enviar correo si cambia a contratado o rechazado
    if etapa_anterior != nueva_etapa:
        try:
            if nueva_etapa == 'contratado':
                enviar_candidato_aceptado(candidato)
            elif nueva_etapa == 'rechazado':
                enviar_candidato_rechazado(candidato)
        except Exception:
            pass
    return JsonResponse({
        'status': 'ok',
        'candidato': candidato.nombre_completo,
        'nueva_etapa': nueva_etapa,
    })


# ═══════════════════════════════════════════════════════════════
# REPORTES
# ═══════════════════════════════════════════════════════════════
@login_required
def reportes(request):
    """Dashboard de reportes: Time-to-Hire, fuentes, departamentos, contrataciones."""
    hoy = date.today()

    # ─── Time-to-Hire por vacante ───
    contratados = Candidato.objects.filter(etapa_actual='contratado').select_related('vacante')
    time_to_hire_data = []
    for c in contratados:
        dias = (hoy - c.fecha_registro.date()).days
        time_to_hire_data.append({'candidato': c.nombre_completo, 'dias': dias})

    time_to_hire_promedio = 0
    if time_to_hire_data:
        time_to_hire_promedio = round(
            sum(d['dias'] for d in time_to_hire_data) / len(time_to_hire_data), 1
        )

    # ─── Efectividad de fuentes de reclutamiento ───
    fuentes_data = {}
    for fuente, label in [('linkedin', 'LinkedIn'), ('portal_web', 'Portal Web'), ('referido', 'Referido'), ('otro', 'Otro')]:
        total_candidatos_fuente = Candidato.objects.filter(vacante__fuente=fuente).count()
        contratados_fuente = Candidato.objects.filter(
            vacante__fuente=fuente, etapa_actual='contratado'
        ).count()
        efectividad = 0
        if total_candidatos_fuente > 0:
            efectividad = round((contratados_fuente / total_candidatos_fuente) * 100, 1)
        fuentes_data[label] = {
            'total': total_candidatos_fuente,
            'contratados': contratados_fuente,
            'efectividad': efectividad,
        }

    # ─── Vacantes por departamento ───
    vacantes_por_depto = Vacante.objects.values('departamento').annotate(
        total=Count('id')
    ).order_by('-total')

    deptos_labels = [v['departamento'].capitalize() for v in vacantes_por_depto]
    deptos_valores = [v['total'] for v in vacantes_por_depto]

    # ─── Entrevistas realizadas por mes (últimos 6 meses) ───
    meses_labels = []
    entrevistas_por_mes = []
    for i in range(5, -1, -1):
        mes = hoy - timedelta(days=30 * i)
        meses_labels.append(mes.strftime('%b %Y'))
        count = Entrevista.objects.filter(
            fecha__month=mes.month, fecha__year=mes.year
        ).count()
        entrevistas_por_mes.append(count)

    context = {
        'time_to_hire_promedio': time_to_hire_promedio,
        'time_to_hire_data': time_to_hire_data[:10],  # top 10
        'fuentes_data': fuentes_data,
        'fuentes_labels': json.dumps(list(fuentes_data.keys())),
        'fuentes_efectividad': json.dumps([v['efectividad'] for v in fuentes_data.values()]),
        'fuentes_totales': json.dumps([v['total'] for v in fuentes_data.values()]),
        'deptos_labels': json.dumps(deptos_labels),
        'deptos_valores': json.dumps(deptos_valores),
        'meses_labels': json.dumps(meses_labels),
        'entrevistas_por_mes': json.dumps(entrevistas_por_mes),
        'total_contratados': Candidato.objects.filter(etapa_actual='contratado').count(),
        'total_entrevistas': Entrevista.objects.count(),
    }
    return render(request, 'reportes.html', context)


# ═══════════════════════════════════════════════════════════════
# COMPARTIR REPORTE POR CORREO
# ═══════════════════════════════════════════════════════════════
@login_required
@require_POST
def compartir_reporte(request):
    """Envía el resumen del reporte al correo indicado."""
    destinatario = request.POST.get('email_destinatario', '').strip()
    tipo = request.POST.get('tipo_reporte', 'Reporte ATS')
    remitente = request.user.get_full_name() or request.user.username

    if not destinatario:
        messages.error(request, 'Debes ingresar un correo destinatario.')
        return redirect('reportes')

    import re
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', destinatario):
        messages.error(request, 'El correo ingresado no es válido.')
        return redirect('reportes')

    # Construir resumen HTML del reporte
    from datetime import date
    hoy = date.today()
    total_contratados = Candidato.objects.filter(etapa_actual='contratado').count()
    total_entrevistas = Entrevista.objects.count()
    vacantes_abiertas = Vacante.objects.filter(estado='abierta').count()
    total_candidatos  = Candidato.objects.count()

    contenido_html = f"""
    <table style="width:100%;border-collapse:collapse;font-size:.85rem;">
      <tr style="background:#f8f9fa;">
        <td style="padding:8px 12px;font-weight:600;color:#374151;">Métrica</td>
        <td style="padding:8px 12px;font-weight:600;color:#374151;text-align:right;">Valor</td>
      </tr>
      <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb;">Candidatos totales</td>
          <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;">{total_candidatos}</td></tr>
      <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb;">Contratados</td>
          <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;color:#16a34a;">{total_contratados}</td></tr>
      <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb;">Vacantes abiertas</td>
          <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;color:#0d6efd;">{vacantes_abiertas}</td></tr>
      <tr><td style="padding:8px 12px;border-top:1px solid #e5e7eb;">Entrevistas realizadas</td>
          <td style="padding:8px 12px;border-top:1px solid #e5e7eb;text-align:right;font-weight:700;">{total_entrevistas}</td></tr>
    </table>
    <p style="font-size:.75rem;color:#9ca3af;margin-top:12px;">Generado el {hoy.strftime('%d/%m/%Y')}</p>
    """

    ok = enviar_reporte_compartido(
        destinatario_email=destinatario,
        destinatario_nombre=destinatario,
        remitente_nombre=remitente,
        tipo_reporte=tipo,
        contenido_html=contenido_html,
    )

    if ok:
        messages.success(request, f'Reporte enviado exitosamente a {destinatario}.')
    else:
        messages.error(request, 'No se pudo enviar el correo. Verifica la configuración SMTP.')

    return redirect('reportes')


# ═══════════════════════════════════════════════════════════════
# GUARDAR PUNTUACIÓN RÁPIDA (Hotkeys-js) - AJAX
# ═══════════════════════════════════════════════════════════════
@login_required
@require_POST
def guardar_puntuacion_rapida(request, pk):
    """Guarda la puntuación de una evaluación vía AJAX (usado con Hotkeys-js)."""
    evaluacion = get_object_or_404(Evaluacion, pk=pk)
    puntuacion = request.POST.get('puntuacion')
    try:
        puntuacion = int(puntuacion)
        if puntuacion < 1 or puntuacion > 5:
            raise ValueError('Fuera de rango')
        evaluacion.puntuacion = puntuacion
        evaluacion.save()
        textos = {1: 'Muy Malo', 2: 'Malo', 3: 'Regular', 4: 'Bueno', 5: 'Excelente'}
        return JsonResponse({
            'status': 'ok',
            'puntuacion': puntuacion,
            'texto': textos[puntuacion]
        })
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'mensaje': 'Puntuación inválida'}, status=400)

# ═══════════════════════════════════════════════════════════════
# GESTIÓN DE USUARIOS Y ROLES (solo admin)
# ═══════════════════════════════════════════════════════════════

@login_required
@rol_requerido('admin')
def lista_usuarios(request):
    """Lista todos los usuarios del sistema con su rol. Solo admin."""
    usuarios = User.objects.select_related('perfil').order_by('username')
    return render(request, 'lista_usuarios.html', {'usuarios': usuarios})


@login_required
@rol_requerido('admin')
def crear_usuario(request):
    """Crea un nuevo usuario con rol asignado. Solo admin."""
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Usuario "{user.username}" creado con rol '
                f'"{user.perfil.get_rol_display()}". '
                f'Credenciales: usuario={user.username} / contraseña definida al crear.'
            )
            return redirect('lista_usuarios')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = UsuarioCrearForm()
    return render(request, 'form_usuario.html', {
        'form': form, 'titulo': 'Nuevo Usuario'
    })


@login_required
@rol_requerido('admin')
def editar_usuario(request, pk):
    """Edita un usuario existente. Solo admin."""
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No puedes editar al superusuario.')
        return redirect('lista_usuarios')
    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario "{usuario.username}" actualizado.')
            return redirect('lista_usuarios')
        messages.error(request, 'Corrige los errores del formulario.')
    else:
        form = UsuarioEditarForm(instance=usuario)
    return render(request, 'form_usuario.html', {
        'form': form, 'titulo': f'Editar Usuario: {usuario.username}', 'objeto': usuario
    })


@login_required
@rol_requerido('admin')
def eliminar_usuario(request, pk):
    """Elimina un usuario. No permite eliminar superusuarios ni al propio usuario."""
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser:
        messages.error(request, 'No se puede eliminar al superusuario.')
        return redirect('lista_usuarios')
    if usuario == request.user:
        messages.error(request, 'No puedes eliminar tu propio usuario.')
        return redirect('lista_usuarios')
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario "{username}" eliminado.')
        return redirect('lista_usuarios')
    return render(request, 'confirmar_eliminar.html', {
        'objeto': usuario,
        'tipo': 'Usuario',
        'cancelar_url': 'lista_usuarios',
    })


@login_required
@rol_requerido('admin')
def resetear_contrasena(request, pk):
    """Permite al admin cambiar la contraseña de cualquier usuario."""
    from django.contrib.auth.forms import SetPasswordForm
    usuario = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Contraseña de "{usuario.username}" actualizada correctamente.'
            )
            return redirect('lista_usuarios')
        messages.error(request, 'Corrige los errores.')
    else:
        form = SetPasswordForm(usuario)
    # Aplicar clases Bootstrap a los campos
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    return render(request, 'form_resetear_contrasena.html', {
        'form': form,
        'usuario': usuario,
    })


@login_required
def mi_perfil(request):
    """Permite al usuario ver y editar su propio perfil y cambiar contraseña."""
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash

    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=request.user,
        defaults={'rol': 'admin' if request.user.is_superuser else 'reclutador'}
    )

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'datos':
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()
            email      = request.POST.get('email', '').strip()
            telefono   = request.POST.get('telefono', '').strip()

            if not first_name or not last_name or not email:
                messages.error(request, 'Nombre, apellidos y correo son obligatorios.')
            else:
                # Verificar que el correo no pertenezca a otro usuario
                from django.contrib.auth.models import User as _User
                if _User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                    messages.error(request, 'Ese correo ya está en uso por otro usuario.')
                else:
                    request.user.first_name = first_name
                    request.user.last_name  = last_name
                    request.user.email      = email
                    request.user.save()
                    perfil.telefono = telefono
                    perfil.save()
                    messages.success(request, 'Perfil actualizado correctamente.')

        elif accion == 'contrasena':
            form_pwd = PasswordChangeForm(request.user, request.POST)
            if form_pwd.is_valid():
                user = form_pwd.save()
                # Mantener la sesión activa después del cambio
                update_session_auth_hash(request, user)
                messages.success(request, '¡Contraseña cambiada exitosamente!')
            else:
                for field, error_list in form_pwd.errors.items():
                    for error in error_list:
                        messages.error(request, error)

        return redirect('mi_perfil')

    rol_display = (
        'Administrador' if request.user.is_superuser
        else perfil.get_rol_display()
    )
    return render(request, 'mi_perfil.html', {
        'perfil': perfil,
        'rol_display': rol_display,
    })


# ═══════════════════════════════════════════════════════════════
# COMPARTIR CANDIDATO POR CORREO
# ═══════════════════════════════════════════════════════════════
@login_required
@require_POST
def compartir_candidato(request, pk):
    """Envía el perfil de un candidato por correo electrónico."""
    candidato = get_object_or_404(Candidato, pk=pk)
    destinatario = request.POST.get('email_destinatario', '').strip()
    mensaje_extra = request.POST.get('mensaje', '').strip()
    remitente = request.user.get_full_name() or request.user.username

    import re
    if not destinatario or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', destinatario):
        messages.error(request, 'Correo destinatario inválido.')
        return redirect('detalle_candidato', pk=pk)

    from django.conf import settings as django_settings
    site_url = getattr(django_settings, 'SITE_URL', 'https://ats2026.onrender.com')

    contenido_html = f"""
    <p style="color:#4b5563;margin:0 0 16px;">
      <strong>{remitente}</strong> ha compartido contigo el perfil de un candidato.
    </p>
    <table style="width:100%;border-collapse:collapse;font-size:.85rem;">
      <tr><td style="padding:8px;font-weight:600;color:#374151;width:40%;">Nombre</td>
          <td style="padding:8px;color:#111;">{candidato.nombre_completo}</td></tr>
      <tr style="background:#f9fafb;"><td style="padding:8px;font-weight:600;color:#374151;">Cédula</td>
          <td style="padding:8px;color:#111;">{candidato.cedula}</td></tr>
      <tr><td style="padding:8px;font-weight:600;color:#374151;">Correo</td>
          <td style="padding:8px;color:#111;">{candidato.correo}</td></tr>
      <tr style="background:#f9fafb;"><td style="padding:8px;font-weight:600;color:#374151;">Vacante</td>
          <td style="padding:8px;color:#111;">{candidato.vacante.titulo}</td></tr>
      <tr><td style="padding:8px;font-weight:600;color:#374151;">Etapa</td>
          <td style="padding:8px;color:#111;">{candidato.get_etapa_actual_display()}</td></tr>
    </table>
    {f'<div style="background:#f0f4ff;border-radius:8px;padding:12px;margin-top:12px;font-size:.85rem;color:#4b5563;">{mensaje_extra}</div>' if mensaje_extra else ''}
    <div style="text-align:center;margin-top:20px;">
      <a href="{site_url}/candidatos/{candidato.pk}/" style="background:#0d6efd;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.875rem;">Ver Perfil Completo →</a>
    </div>
    """

    ok = enviar_reporte_compartido(
        destinatario_email=destinatario,
        destinatario_nombre=destinatario,
        remitente_nombre=remitente,
        tipo_reporte=f"Perfil: {candidato.nombre_completo}",
        contenido_html=contenido_html,
    )

    if ok:
        messages.success(request, f'Perfil enviado exitosamente a {destinatario}.')
    else:
        messages.error(request, 'No se pudo enviar el correo. Verifica la configuración SMTP.')

    return redirect('detalle_candidato', pk=pk)
