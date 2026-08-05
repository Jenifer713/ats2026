"""
Módulo de correos electrónicos del sistema ATS.
Maneja envío de bienvenida, notificaciones de candidatos y compartir reportes.
"""
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def _send(subject, to_email, html_content, attachments=None):
    """Función base para envío de correos con fallback silencioso."""
    # Si no hay credenciales configuradas, no intentar enviar
    if not getattr(settings, 'EMAIL_HOST_USER', ''):
        logger.warning(f"EMAIL_HOST_USER no configurado. Correo a {to_email} omitido.")
        return False
    try:
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        if attachments:
            for filename, content, mimetype in attachments:
                msg.attach(filename, content, mimetype)
        msg.send(fail_silently=False)
        logger.info(f"Correo enviado a {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Error enviando correo a {to_email}: {e}")
        return False


def _send_async(subject, to_email, html_content, attachments=None):
    """Envía el correo en un hilo separado para no bloquear la request."""
    import threading
    def _run():
        try:
            _send(subject, to_email, html_content, attachments)
        except Exception as e:
            logger.error(f"Error en hilo de correo a {to_email}: {e}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _html_base(title, content, color="#0d6efd"):
    """Plantilla HTML base para todos los correos."""
    site_url = getattr(settings, 'SITE_URL', 'https://ats2026.onrender.com')
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f0f2f5;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f2f5;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,{color},{color}dd);border-radius:12px 12px 0 0;padding:30px;text-align:center;">
            <div style="font-size:2rem;margin-bottom:8px;">👥</div>
            <h1 style="color:#fff;margin:0;font-size:1.4rem;font-weight:700;">ATS Recluta</h1>
            <p style="color:rgba(255,255,255,.8);margin:4px 0 0;font-size:.85rem;">Sistema de Reclutamiento</p>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="background:#fff;padding:32px;border-radius:0 0 12px 12px;box-shadow:0 4px 20px rgba(0,0,0,.08);">
            {content}
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:20px;text-align:center;font-size:.75rem;color:#9ca3af;">
            © 2026 ATS Recluta — Sistema de Reclutamiento y Selección<br>
            <a href="{site_url}" style="color:{color};text-decoration:none;">{site_url}</a>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ─────────────────────────────────────────────────────────
# 1. Bienvenida al registrarse
# ─────────────────────────────────────────────────────────
def enviar_bienvenida(user):
    """Correo de bienvenida cuando un nuevo usuario se registra."""
    site_url = getattr(settings, 'SITE_URL', 'https://ats2026.onrender.com')
    nombre = user.get_full_name() or user.username
    content = f"""
    <h2 style="color:#1a1d23;margin:0 0 16px;">¡Bienvenido/a, {nombre}! 🎉</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      Tu cuenta ha sido creada exitosamente en <strong>ATS Recluta</strong>.
      Ya puedes acceder al sistema y comenzar a explorar las oportunidades disponibles.
    </p>
    <div style="background:#f8f9fa;border-radius:10px;padding:20px;margin:0 0 24px;">
      <p style="margin:0 0 8px;font-size:.85rem;color:#6b7280;">Tus credenciales de acceso:</p>
      <p style="margin:0;font-size:.9rem;"><strong>Usuario:</strong> {user.username}</p>
      <p style="margin:4px 0 0;font-size:.9rem;"><strong>Correo:</strong> {user.email}</p>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{site_url}/login/" style="background:#0d6efd;color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.95rem;">
        Ingresar al Sistema →
      </a>
    </div>
    <p style="color:#9ca3af;font-size:.8rem;margin:16px 0 0;text-align:center;">
      Si no solicitaste esta cuenta, ignora este mensaje.
    </p>"""
    html = _html_base(f"Bienvenido/a a ATS Recluta — {nombre}", content, "#0d6efd")
    _send_async(f"✅ Bienvenido/a a ATS Recluta, {nombre}", user.email, html)
    return True


# ─────────────────────────────────────────────────────────
# 2. Notificación de candidato aceptado
# ─────────────────────────────────────────────────────────
def enviar_candidato_aceptado(candidato, observaciones=""):
    """Correo al candidato cuando es aceptado (contratado)."""
    site_url = getattr(settings, 'SITE_URL', 'https://ats2026.onrender.com')
    nombre = candidato.nombre_completo
    content = f"""
    <h2 style="color:#166534;margin:0 0 16px;">¡Felicitaciones, {nombre}! 🎊</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      Nos complace informarte que has sido <strong style="color:#166534;">seleccionado/a</strong>
      para la vacante de <strong>{candidato.vacante.titulo}</strong>.
    </p>
    <div style="background:#dcfce7;border-left:4px solid #16a34a;border-radius:0 10px 10px 0;padding:16px 20px;margin:0 0 24px;">
      <p style="margin:0;font-weight:600;color:#166534;">Vacante: {candidato.vacante.titulo}</p>
      <p style="margin:6px 0 0;font-size:.85rem;color:#4b5563;">Departamento: {candidato.vacante.get_departamento_display()}</p>
      <p style="margin:4px 0 0;font-size:.85rem;color:#4b5563;">Modalidad: {candidato.vacante.get_modalidad_display()}</p>
      {f'<p style="margin:8px 0 0;font-size:.85rem;color:#4b5563;">{observaciones}</p>' if observaciones else ''}
    </div>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 24px;">
      Pronto recibirás más información sobre los próximos pasos del proceso de vinculación.
      Adjunto encontrarás el detalle de tu proceso de selección.
    </p>
    <p style="color:#6b7280;font-size:.85rem;margin:0;">
      Equipo de Reclutamiento — ATS Recluta
    </p>"""
    html = _html_base(f"¡Felicitaciones! Seleccionado/a — {candidato.vacante.titulo}", content, "#16a34a")
    _send_async(
        f"🎉 ¡Felicitaciones! Has sido seleccionado/a — {candidato.vacante.titulo}",
        candidato.correo, html
    )
    return True


# ─────────────────────────────────────────────────────────
# 3. Notificación de candidato rechazado
# ─────────────────────────────────────────────────────────
def enviar_candidato_rechazado(candidato, observaciones=""):
    """Correo al candidato cuando es rechazado."""
    nombre = candidato.nombre_completo
    content = f"""
    <h2 style="color:#1a1d23;margin:0 0 16px;">Estimado/a {nombre},</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      Agradecemos tu interés en la vacante de <strong>{candidato.vacante.titulo}</strong>
      y el tiempo que dedicaste a participar en nuestro proceso de selección.
    </p>
    <div style="background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 10px 10px 0;padding:16px 20px;margin:0 0 24px;">
      <p style="margin:0;font-weight:600;color:#991b1b;">Resultado: No seleccionado/a en esta ocasión</p>
      <p style="margin:6px 0 0;font-size:.85rem;color:#4b5563;">Vacante: {candidato.vacante.titulo}</p>
      {f'<p style="margin:8px 0 0;font-size:.85rem;color:#4b5563;">{observaciones}</p>' if observaciones else ''}
    </div>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      Aunque en esta oportunidad no avanzarás en el proceso, valoramos tu perfil y te
      animamos a postularte a futuras vacantes que se ajusten a tu experiencia.
    </p>
    <p style="color:#6b7280;font-size:.85rem;margin:0;">
      Equipo de Reclutamiento — ATS Recluta
    </p>"""
    html = _html_base(f"Resultado proceso — {candidato.vacante.titulo}", content, "#dc2626")
    _send_async(
        f"Resultado de tu proceso — {candidato.vacante.titulo}",
        candidato.correo, html
    )
    return True


# ─────────────────────────────────────────────────────────
# 4. Compartir reporte por correo
# ─────────────────────────────────────────────────────────
def enviar_reporte_compartido(destinatario_email, destinatario_nombre,
                               remitente_nombre, tipo_reporte, contenido_html,
                               pdf_bytes=None):
    """Envía un reporte compartido por correo electrónico."""
    site_url = getattr(settings, 'SITE_URL', 'https://ats2026.onrender.com')
    content = f"""
    <h2 style="color:#1a1d23;margin:0 0 16px;">Reporte compartido: {tipo_reporte}</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      <strong>{remitente_nombre}</strong> ha compartido contigo el reporte
      <strong>{tipo_reporte}</strong> del Sistema ATS Recluta.
    </p>
    <div style="background:#f0f4ff;border-radius:10px;padding:20px;margin:0 0 24px;">
      {contenido_html}
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="{site_url}/reportes/" style="background:#0d6efd;color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.95rem;">
        Ver Reportes Completos →
      </a>
    </div>"""
    html = _html_base(f"Reporte: {tipo_reporte}", content, "#6f42c1")
    attachments = []
    if pdf_bytes:
        attachments.append((f"reporte_{tipo_reporte.lower().replace(' ', '_')}.pdf",
                             pdf_bytes, "application/pdf"))
    return _send(
        f"📊 Reporte compartido: {tipo_reporte}",
        destinatario_email, html,
        attachments=attachments if attachments else None
    )

# ─────────────────────────────────────────────────────────
# 5. Notificación de entrevista programada
# ─────────────────────────────────────────────────────────
def enviar_notificacion_entrevista(candidato, entrevista):
    """Correo al candidato cuando se programa una entrevista."""
    nombre = candidato.nombre_completo
    fecha_str = entrevista.fecha.strftime("%d de %B de %Y")
    content = f"""
    <h2 style="color:#1a1d23;margin:0 0 16px;">Entrevista programada 📅</h2>
    <p style="color:#4b5563;line-height:1.7;margin:0 0 20px;">
      Estimado/a <strong>{nombre}</strong>, tienes una entrevista programada para la
      vacante de <strong>{candidato.vacante.titulo}</strong>.
    </p>
    <div style="background:#fef9c3;border-left:4px solid #f59e0b;border-radius:0 10px 10px 0;padding:16px 20px;margin:0 0 24px;">
      <p style="margin:0;font-weight:700;color:#92400e;font-size:1rem;">📅 {fecha_str}</p>
      <p style="margin:6px 0 0;color:#4b5563;">🕐 {entrevista.hora_inicio} — {entrevista.hora_fin}</p>
      <p style="margin:4px 0 0;color:#4b5563;">📍 Modalidad: {entrevista.get_modalidad_display()}</p>
      <p style="margin:4px 0 0;color:#4b5563;">👤 Reclutador: {entrevista.reclutador.nombre_completo}</p>
      {f'<p style="margin:8px 0 0;font-size:.85rem;color:#6b7280;">{entrevista.observaciones}</p>' if entrevista.observaciones else ''}
    </div>
    <p style="color:#6b7280;font-size:.85rem;margin:0;">
      Si tienes alguna pregunta, contacta a tu reclutador asignado.<br>
      Equipo de Reclutamiento — ATS Recluta
    </p>"""
    html = _html_base(f"Entrevista programada — {candidato.vacante.titulo}", content, "#f59e0b")
    _send_async(
        f"📅 Entrevista programada — {candidato.vacante.titulo} ({fecha_str})",
        candidato.correo, html
    )
    return True
