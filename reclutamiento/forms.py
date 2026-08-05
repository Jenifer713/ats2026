"""
Formularios ModelForm para todas las entidades del sistema ATS.
Incluye validaciones tanto en cliente (atributos HTML5) como en servidor.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from .models import PerfilUsuario, Reclutador, Vacante, Candidato, Entrevista, Evaluacion, Oferta

# ─── Tamaño máximo para hoja de vida (5 MB) ───
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB en bytes


# ─────────────────────────────────────────────
# FORM: Crear Usuario con Perfil
# ─────────────────────────────────────────────
class UsuarioCrearForm(UserCreationForm):
    """Formulario para crear un usuario del sistema con rol asignado."""
    rol = forms.ChoiceField(
        choices=PerfilUsuario.ROL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'required': True}),
        label='Rol en el Sistema'
    )
    telefono = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': '+57 300 000 0000'
        }),
        label='Teléfono'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'nombre_usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@empresa.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean_first_name(self):
        v = self.cleaned_data.get('first_name', '').strip()
        if len(v) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return v

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            PerfilUsuario.objects.create(
                user=user,
                rol=self.cleaned_data['rol'],
                telefono=self.cleaned_data.get('telefono', '')
            )
        return user


class UsuarioEditarForm(forms.ModelForm):
    """Formulario para editar datos de un usuario existente."""
    rol = forms.ChoiceField(
        choices=PerfilUsuario.ROL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Rol en el Sistema'
    )
    telefono = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+57 300 000 0000'}),
        label='Teléfono'
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active':  forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-llenar rol y teléfono desde el perfil si existe
        if self.instance and hasattr(self.instance, 'perfil'):
            self.fields['rol'].initial = self.instance.perfil.rol
            self.fields['telefono'].initial = self.instance.perfil.telefono

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        qs = User.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            perfil.rol = self.cleaned_data['rol']
            perfil.telefono = self.cleaned_data.get('telefono', '')
            perfil.save()
        return user


class ReclutadorForm(forms.ModelForm):
    class Meta:
        model = Reclutador
        fields = ['nombres', 'apellidos', 'correo', 'telefono', 'cargo', 'estado']
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres del reclutador',
                'required': True,
                'minlength': '2',
                'maxlength': '100',
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos del reclutador',
                'required': True,
                'minlength': '2',
                'maxlength': '100',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@empresa.com',
                'required': True,
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 300 000 0000',
                'required': True,
                'pattern': r'[\+\d\s\-\(\)]{7,20}',
                'title': 'Ingresa un número de teléfono válido (7-20 dígitos)',
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Analista de Selección',
                'required': True,
                'minlength': '2',
            }),
            'estado': forms.Select(attrs={'class': 'form-select', 'required': True}),
        }

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres', '').strip()
        if len(nombres) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos', '').strip()
        if len(apellidos) < 2:
            raise ValidationError('Los apellidos deben tener al menos 2 caracteres.')
        return apellidos

    def clean_correo(self):
        """Valida formato correo y que no esté duplicado (excluye instancia actual en edición)."""
        correo = self.cleaned_data.get('correo', '').strip().lower()
        qs = Reclutador.objects.filter(correo=correo)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un reclutador registrado con este correo electrónico.')
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        # Solo dígitos, espacios, +, -, paréntesis — entre 7 y 20 chars
        if not re.match(r'^[\+\d\s\-\(\)]{7,20}$', telefono):
            raise ValidationError('Ingresa un teléfono válido (7-20 dígitos, puede incluir +, -, espacios).')
        return telefono

    def clean_cargo(self):
        cargo = self.cleaned_data.get('cargo', '').strip()
        if len(cargo) < 2:
            raise ValidationError('El cargo debe tener al menos 2 caracteres.')
        return cargo


# ─────────────────────────────────────────────
# FORM: Vacante
# ─────────────────────────────────────────────
class VacanteForm(forms.ModelForm):
    class Meta:
        model = Vacante
        fields = [
            'titulo', 'descripcion', 'departamento', 'modalidad',
            'salario', 'fecha_publicacion', 'fecha_cierre',
            'estado', 'fuente', 'reclutador'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del puesto',
                'required': True,
                'minlength': '3',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe el puesto, requisitos y responsabilidades...',
                'required': True,
                'minlength': '10',
            }),
            'departamento': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'modalidad': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'salario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': '0.01',
                'step': '0.01',
                'required': True,
            }),
            'fecha_publicacion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'fecha_cierre': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'estado': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'fuente': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'reclutador': forms.Select(attrs={'class': 'form-select', 'required': True}),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo', '').strip()
        if len(titulo) < 3:
            raise ValidationError('El título debe tener al menos 3 caracteres.')
        return titulo

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '').strip()
        if len(descripcion) < 10:
            raise ValidationError('La descripción debe tener al menos 10 caracteres.')
        return descripcion

    def clean_salario(self):
        """Valida que el salario sea un valor positivo mayor a cero."""
        salario = self.cleaned_data.get('salario')
        if salario is None:
            raise ValidationError('El salario es obligatorio.')
        if salario <= 0:
            raise ValidationError('El salario debe ser un valor positivo mayor a cero.')
        return salario

    def clean(self):
        """Valida que la fecha de cierre sea posterior a la fecha de publicación."""
        cleaned_data = super().clean()
        fecha_publicacion = cleaned_data.get('fecha_publicacion')
        fecha_cierre = cleaned_data.get('fecha_cierre')
        if fecha_publicacion and fecha_cierre:
            if fecha_cierre <= fecha_publicacion:
                self.add_error(
                    'fecha_cierre',
                    'La fecha de cierre debe ser posterior a la fecha de publicación.'
                )
        return cleaned_data


# ─────────────────────────────────────────────
# FORM: Candidato
# ─────────────────────────────────────────────
class CandidatoForm(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = [
            'nombres', 'apellidos', 'cedula', 'correo', 'telefono',
            'hoja_de_vida', 'etapa_actual', 'estado', 'vacante'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres del candidato',
                'required': True,
                'minlength': '2',
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos del candidato',
                'required': True,
                'minlength': '2',
            }),
            'cedula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de cédula (solo dígitos)',
                'required': True,
                'pattern': r'\d{5,15}',
                'title': 'Solo dígitos, entre 5 y 15 caracteres',
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'candidato@email.com',
                'required': True,
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+57 300 000 0000',
                'required': True,
                'pattern': r'[\+\d\s\-\(\)]{7,20}',
                'title': 'Teléfono válido (7-20 dígitos)',
            }),
            'hoja_de_vida': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
            }),
            'etapa_actual': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'estado': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'vacante': forms.Select(attrs={'class': 'form-select', 'required': True}),
        }

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres', '').strip()
        if len(nombres) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos', '').strip()
        if len(apellidos) < 2:
            raise ValidationError('Los apellidos deben tener al menos 2 caracteres.')
        return apellidos

    def clean_cedula(self):
        """Valida formato numérico y unicidad de la cédula."""
        cedula = self.cleaned_data.get('cedula', '').strip()
        if not cedula.isdigit():
            raise ValidationError('La cédula debe contener solo dígitos numéricos.')
        if len(cedula) < 5 or len(cedula) > 15:
            raise ValidationError('La cédula debe tener entre 5 y 15 dígitos.')
        qs = Candidato.objects.filter(cedula=cedula)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Ya existe un candidato registrado con esta cédula.')
        return cedula

    def clean_correo(self):
        correo = self.cleaned_data.get('correo', '').strip().lower()
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not re.match(r'^[\+\d\s\-\(\)]{7,20}$', telefono):
            raise ValidationError('Ingresa un teléfono válido (7-20 dígitos).')
        return telefono

    def clean_hoja_de_vida(self):
        """Valida extensión PDF y tamaño máximo de 5 MB."""
        archivo = self.cleaned_data.get('hoja_de_vida')
        if archivo and hasattr(archivo, 'name'):
            # Verificar extensión
            if not archivo.name.lower().endswith('.pdf'):
                raise ValidationError('Solo se permiten archivos en formato PDF (.pdf).')
            # Verificar tamaño (5 MB máximo)
            if archivo.size > MAX_UPLOAD_SIZE:
                raise ValidationError(
                    f'El archivo no puede superar 5 MB. '
                    f'Tamaño actual: {archivo.size / (1024*1024):.1f} MB.'
                )
        return archivo


# ─────────────────────────────────────────────
# FORM: Entrevista
# ─────────────────────────────────────────────
class EntrevistaForm(forms.ModelForm):
    class Meta:
        model = Entrevista
        fields = [
            'candidato', 'reclutador', 'fecha',
            'hora_inicio', 'hora_fin', 'modalidad', 'observaciones'
        ]
        widgets = {
            'candidato': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'reclutador': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'hora_inicio': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True,
            }),
            'hora_fin': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True,
            }),
            'modalidad': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas o indicaciones para la entrevista...',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Recibir flag para saber si es creación (bloquear fechas pasadas) o edición
        self.es_creacion = kwargs.pop('es_creacion', not kwargs.get('instance'))
        super().__init__(*args, **kwargs)

    def clean(self):
        """Valida horas y — solo en creación — que la fecha no sea pasada."""
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        # Solo validar fecha futura al crear (en edición se permite mantener fecha pasada)
        if self.es_creacion and fecha and fecha < timezone.now().date():
            self.add_error('fecha', 'No se pueden programar entrevistas en fechas pasadas.')

        # Validar hora_fin > hora_inicio
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                self.add_error('hora_fin', 'La hora de fin debe ser posterior a la hora de inicio.')

        return cleaned_data


# ─────────────────────────────────────────────
# FORM: Evaluacion
# ─────────────────────────────────────────────
class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ['entrevista', 'puntuacion', 'comentario', 'recomendacion']
        widgets = {
            'entrevista': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'puntuacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'required': True,
                'id': 'id_puntuacion',  # necesario para Hotkeys-js
                'placeholder': 'Ingresa un valor del 1 al 5',
            }),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comentarios sobre el desempeño del candidato...',
                'required': True,
                'minlength': '5',
            }),
            'recomendacion': forms.Select(attrs={'class': 'form-select', 'required': True}),
        }

    def clean_puntuacion(self):
        """Valida que la puntuación esté estrictamente entre 1 y 5."""
        puntuacion = self.cleaned_data.get('puntuacion')
        if puntuacion is None:
            raise ValidationError('La puntuación es obligatoria.')
        if puntuacion < 1 or puntuacion > 5:
            raise ValidationError(
                'La puntuación debe estar entre 1 (Muy malo) y 5 (Excelente).'
            )
        return puntuacion

    def clean_comentario(self):
        comentario = self.cleaned_data.get('comentario', '').strip()
        if len(comentario) < 5:
            raise ValidationError('El comentario debe tener al menos 5 caracteres.')
        return comentario

    def clean_entrevista(self):
        """Valida que la entrevista no tenga ya una evaluación (solo al crear)."""
        entrevista = self.cleaned_data.get('entrevista')
        if entrevista and not self.instance.pk:
            # Solo verificar unicidad al crear, no al editar
            if Evaluacion.objects.filter(entrevista=entrevista).exists():
                raise ValidationError(
                    'Esta entrevista ya tiene una evaluación registrada. '
                    'Edita la evaluación existente.'
                )
        return entrevista


# ─────────────────────────────────────────────
# FORM: Oferta
# ─────────────────────────────────────────────
class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ['candidato', 'salario', 'cargo', 'fecha', 'estado', 'observaciones']
        widgets = {
            'candidato': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'salario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': '0.01',
                'step': '0.01',
                'required': True,
            }),
            'cargo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cargo ofrecido',
                'required': True,
                'minlength': '2',
            }),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'estado': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Condiciones adicionales, beneficios, fecha límite...',
            }),
        }

    def clean_salario(self):
        """Valida que el salario sea positivo."""
        salario = self.cleaned_data.get('salario')
        if salario is None:
            raise ValidationError('El salario es obligatorio.')
        if salario <= 0:
            raise ValidationError('El salario ofrecido debe ser un valor positivo mayor a cero.')
        return salario

    def clean_cargo(self):
        cargo = self.cleaned_data.get('cargo', '').strip()
        if len(cargo) < 2:
            raise ValidationError('El cargo debe tener al menos 2 caracteres.')
        return cargo

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if not fecha:
            raise ValidationError('La fecha de la oferta es obligatoria.')
        return fecha
