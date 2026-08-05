"""
Comando de gestión para cargar datos de prueba en el sistema ATS.
Uso: python manage.py cargar_datos_prueba
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from reclutamiento.models import (
    PerfilUsuario, Reclutador, Vacante, Candidato,
    Entrevista, Evaluacion, Oferta
)


class Command(BaseCommand):
    help = 'Carga datos de prueba para el sistema ATS'

    def handle(self, *args, **options):
        self.stdout.write('Cargando datos de prueba...')

        # ─── Superusuario ya existe (jeniffer) ───
        # Crear usuarios adicionales con roles
        self._crear_usuarios()
        self._crear_reclutadores()
        self._crear_vacantes()
        self._crear_candidatos()
        self._crear_entrevistas()
        self._crear_evaluaciones()
        self._crear_ofertas()

        self.stdout.write(self.style.SUCCESS('✅ Datos de prueba cargados correctamente.'))

    def _crear_usuarios(self):
        usuarios = [
            ('carlos.mora', 'Carlos', 'Mora', 'carlos.mora@empresa.com', 'reclutador'),
            ('ana.lopez', 'Ana', 'López', 'ana.lopez@empresa.com', 'reclutador'),
            ('coord1', 'Luis', 'Ramírez', 'luis.ramirez@empresa.com', 'coordinador'),
        ]
        for username, first, last, email, rol in usuarios:
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(
                    username=username,
                    first_name=first,
                    last_name=last,
                    email=email,
                    password='Prueba2026!'
                )
                PerfilUsuario.objects.create(user=u, rol=rol)
                self.stdout.write(f'  Usuario creado: {username} ({rol})')

    def _crear_reclutadores(self):
        reclutadores = [
            ('María', 'González', 'maria.gonzalez@empresa.com', '+57 310 111 2233', 'Jefe de Reclutamiento'),
            ('Carlos', 'Mora', 'carlos.mora@empresa.com', '+57 315 222 3344', 'Analista de Selección'),
            ('Ana', 'López', 'ana.lopez@empresa.com', '+57 320 333 4455', 'Coordinadora RRHH'),
            ('Pedro', 'Vargas', 'pedro.vargas@empresa.com', '+57 300 444 5566', 'Especialista en Talento'),
        ]
        for nombres, apellidos, correo, telefono, cargo in reclutadores:
            if not Reclutador.objects.filter(correo=correo).exists():
                Reclutador.objects.create(
                    nombres=nombres, apellidos=apellidos,
                    correo=correo, telefono=telefono,
                    cargo=cargo, estado='activo'
                )
                self.stdout.write(f'  Reclutador: {nombres} {apellidos}')

    def _crear_vacantes(self):
        hoy = date.today()
        r1 = Reclutador.objects.first()
        r2 = Reclutador.objects.all()[1] if Reclutador.objects.count() > 1 else r1
        r3 = Reclutador.objects.all()[2] if Reclutador.objects.count() > 2 else r1

        vacantes = [
            ('Desarrollador Backend Python', 'tecnologia', 'remoto', 4500000, 'linkedin', r1, 'abierta', hoy - timedelta(days=30), hoy + timedelta(days=30)),
            ('Diseñador UX/UI', 'tecnologia', 'hibrido', 3800000, 'portal_web', r2, 'abierta', hoy - timedelta(days=20), hoy + timedelta(days=40)),
            ('Analista de Marketing Digital', 'marketing', 'remoto', 3200000, 'referido', r1, 'abierta', hoy - timedelta(days=15), hoy + timedelta(days=45)),
            ('Gerente de Ventas', 'ventas', 'presencial', 6000000, 'linkedin', r3, 'abierta', hoy - timedelta(days=10), hoy + timedelta(days=50)),
            ('Analista Financiero', 'finanzas', 'presencial', 4200000, 'portal_web', r2, 'cerrada', hoy - timedelta(days=60), hoy - timedelta(days=10)),
            ('Desarrollador Frontend React', 'tecnologia', 'remoto', 4200000, 'linkedin', r1, 'abierta', hoy - timedelta(days=5), hoy + timedelta(days=55)),
            ('Coordinador de Operaciones', 'operaciones', 'presencial', 3500000, 'referido', r3, 'cerrada', hoy - timedelta(days=45), hoy - timedelta(days=5)),
            ('Especialista en RRHH', 'rrhh', 'hibrido', 3300000, 'portal_web', r2, 'abierta', hoy - timedelta(days=8), hoy + timedelta(days=60)),
        ]

        for titulo, depto, modalidad, salario, fuente, reclutador, estado, f_pub, f_cierre in vacantes:
            if not Vacante.objects.filter(titulo=titulo).exists():
                Vacante.objects.create(
                    titulo=titulo, departamento=depto, modalidad=modalidad,
                    salario=salario, fuente=fuente, reclutador=reclutador,
                    estado=estado, fecha_publicacion=f_pub, fecha_cierre=f_cierre,
                    descripcion=f'Descripción detallada para la vacante de {titulo}. '
                                f'Se requiere experiencia mínima de 2 años en el área. '
                                f'Modalidad {modalidad}. Excelentes condiciones laborales.'
                )
                self.stdout.write(f'  Vacante: {titulo}')

    def _crear_candidatos(self):
        hoy = date.today()
        vacantes = list(Vacante.objects.all())
        if not vacantes:
            return

        candidatos_data = [
            ('Laura', 'Pérez', '1098765432', 'laura.perez@gmail.com', '+57 311 000 1111', vacantes[0], 'contratado'),
            ('Andrés', 'Torres', '1087654321', 'andres.torres@gmail.com', '+57 312 000 2222', vacantes[0], 'oferta'),
            ('Sofía', 'Ramírez', '1076543210', 'sofia.ramirez@gmail.com', '+57 313 000 3333', vacantes[1], 'entrevista'),
            ('Diego', 'Martínez', '1065432109', 'diego.martinez@gmail.com', '+57 314 000 4444', vacantes[1], 'evaluacion'),
            ('Valentina', 'Cruz', '1054321098', 'valentina.cruz@gmail.com', '+57 315 000 5555', vacantes[2], 'preseleccion'),
            ('Sebastián', 'Gómez', '1043210987', 'sebastian.gomez@gmail.com', '+57 316 000 6666', vacantes[2], 'contratado'),
            ('Camila', 'Herrera', '1032109876', 'camila.herrera@gmail.com', '+57 317 000 7777', vacantes[3], 'entrevista'),
            ('Juan', 'Jiménez', '1021098765', 'juan.jimenez@gmail.com', '+57 318 000 8888', vacantes[3], 'postulado'),
            ('Isabella', 'Vargas', '1010987654', 'isabella.vargas@gmail.com', '+57 319 000 9999', vacantes[4] if len(vacantes) > 4 else vacantes[0], 'rechazado'),
            ('Mateo', 'Morales', '1009876543', 'mateo.morales@gmail.com', '+57 320 001 0000', vacantes[4] if len(vacantes) > 4 else vacantes[0], 'contratado'),
            ('Valeria', 'Sánchez', '1198765432', 'valeria.sanchez@gmail.com', '+57 321 001 1111', vacantes[5] if len(vacantes) > 5 else vacantes[0], 'preseleccion'),
            ('Felipe', 'Rojas', '1187654321', 'felipe.rojas@gmail.com', '+57 322 001 2222', vacantes[5] if len(vacantes) > 5 else vacantes[0], 'evaluacion'),
            ('Daniela', 'Castro', '1176543210', 'daniela.castro@gmail.com', '+57 323 001 3333', vacantes[6] if len(vacantes) > 6 else vacantes[1], 'oferta'),
            ('Nicolás', 'Mendoza', '1165432109', 'nicolas.mendoza@gmail.com', '+57 324 001 4444', vacantes[6] if len(vacantes) > 6 else vacantes[1], 'contratado'),
            ('Mariana', 'Ríos', '1154321098', 'mariana.rios@gmail.com', '+57 325 001 5555', vacantes[7] if len(vacantes) > 7 else vacantes[2], 'postulado'),
        ]

        for nombres, apellidos, cedula, correo, telefono, vacante, etapa in candidatos_data:
            if not Candidato.objects.filter(cedula=cedula).exists():
                Candidato.objects.create(
                    nombres=nombres, apellidos=apellidos,
                    cedula=cedula, correo=correo, telefono=telefono,
                    vacante=vacante, etapa_actual=etapa, estado='activo'
                )
                self.stdout.write(f'  Candidato: {nombres} {apellidos} → {etapa}')

    def _crear_entrevistas(self):
        hoy = date.today()
        reclutadores = list(Reclutador.objects.all())
        if not reclutadores:
            return

        # Candidatos con etapas que implican entrevista o más avanzadas
        etapas_con_entrevista = ['entrevista', 'evaluacion', 'oferta', 'contratado', 'rechazado']
        candidatos = list(Candidato.objects.filter(etapa_actual__in=etapas_con_entrevista))

        modalidades = ['presencial', 'virtual', 'telefonica']
        entrevistas_creadas = 0

        for i, candidato in enumerate(candidatos):
            if not candidato.entrevistas.exists():
                fecha = hoy - timedelta(days=15 - i * 2) if i < 5 else hoy + timedelta(days=i - 4)
                Entrevista.objects.create(
                    candidato=candidato,
                    reclutador=reclutadores[i % len(reclutadores)],
                    fecha=fecha,
                    hora_inicio='09:00',
                    hora_fin='10:00',
                    modalidad=modalidades[i % 3],
                    observaciones=f'Entrevista técnica para {candidato.vacante.titulo}. '
                                  f'Evaluación de habilidades y experiencia.'
                )
                entrevistas_creadas += 1
                self.stdout.write(f'  Entrevista: {candidato.nombre_completo} ({fecha})')

    def _crear_evaluaciones(self):
        # Evaluar entrevistas de candidatos contratados, en oferta o rechazados
        etapas_evaluadas = ['evaluacion', 'oferta', 'contratado', 'rechazado']
        candidatos_evaluados = Candidato.objects.filter(etapa_actual__in=etapas_evaluadas)

        puntuaciones = [5, 4, 5, 3, 4, 5, 2, 4, 5, 3]
        recomendaciones = ['contratar', 'contratar', 'contratar', 'considerar',
                           'contratar', 'contratar', 'rechazar', 'contratar', 'contratar', 'considerar']

        idx = 0
        for candidato in candidatos_evaluados:
            entrevista = candidato.entrevistas.first()
            if entrevista and not hasattr(entrevista, 'evaluacion'):
                try:
                    Evaluacion.objects.create(
                        entrevista=entrevista,
                        puntuacion=puntuaciones[idx % len(puntuaciones)],
                        comentario=f'El candidato {candidato.nombre_completo} demostró '
                                   f'excelentes habilidades técnicas y comunicativas. '
                                   f'Cumple con los requisitos del perfil solicitado.',
                        recomendacion=recomendaciones[idx % len(recomendaciones)]
                    )
                    idx += 1
                    self.stdout.write(f'  Evaluación: {candidato.nombre_completo}')
                except Exception:
                    pass

    def _crear_ofertas(self):
        hoy = date.today()
        etapas_oferta = ['oferta', 'contratado']
        candidatos = Candidato.objects.filter(etapa_actual__in=etapas_oferta)

        estados = ['aceptada', 'pendiente', 'aceptada', 'aceptada']

        for i, candidato in enumerate(candidatos):
            if not candidato.ofertas.exists():
                Oferta.objects.create(
                    candidato=candidato,
                    salario=candidato.vacante.salario,
                    cargo=candidato.vacante.titulo,
                    fecha=hoy - timedelta(days=5 - i),
                    estado=estados[i % len(estados)],
                    observaciones=f'Oferta formal para {candidato.nombre_completo}. '
                                  f'Incluye beneficios de ley y extras corporativos.'
                )
                self.stdout.write(f'  Oferta: {candidato.nombre_completo} → {estados[i % len(estados)]}')
