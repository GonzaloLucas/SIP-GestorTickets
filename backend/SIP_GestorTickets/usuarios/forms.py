import re

from django import forms
from django_countries import countries
from django.contrib.auth.password_validation import validate_password
from .models import FeedbackPlatform, FeedbackSupportInternal, Usuario, InfoTicket, Empresa
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
import unicodedata

# ==========================================
# 🛠️ FUNCIONES DE AYUDA
# ==========================================
def validar_nombre_usuario(username):
    if Usuario.objects.filter(username=username).exists():
        raise forms.ValidationError("Este nombre de usuario ya está en uso.")
    return username

def limpiar_texto_comun(texto):
    if not texto:
        return ""
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sin_tildes = "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn'])
    return texto_sin_tildes.lower().strip().replace(" ", "")

def validar_contrasenia_segura(password):
    validate_password(password)
    return password

def generar_y_validar_email(nombre_empresa, email_usuario):
    dominio = nombre_empresa.lower().replace(" ", "")
    email_completo = f"{email_usuario.lower()}@{dominio}.com"

    if Usuario.objects.filter(email=email_completo).exists():
        raise forms.ValidationError(f"El email {email_completo} ya está registrado.")        
    return email_completo

# ==========================================
# FORMULARIO: REGISTRO DE EMPRESA
# ==========================================
class EmpresaRegisterForm(forms.Form):
    nombre_empresa = forms.CharField(max_length=255,label="Nombre de la Empresa")
    cuil = forms.CharField(max_length=11, min_length=11, label="CUIT de la Empresa", help_text="Ingresar los 11 dígitos sin guiones.")
    domicilio = forms.CharField(label="Domicilio")
    pais = forms.ChoiceField(choices=[('', 'Seleccioná el País')] + list(countries), label="País") 

    opciones_plan = [('', 'Seleccionar opción')] + list(Empresa.PLANES)
    plan = forms.ChoiceField(choices=opciones_plan, label="Selecciona tu Plan")    
    
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email_real = forms.EmailField(label="Email")
    telefono = forms.CharField(max_length=20, label="Teléfono", required=False)
        
    def clean_cuil(self):
        cuil = self.cleaned_data.get('cuil')
        if not cuil.isdigit():
            raise forms.ValidationError("El CUIL solo debe contener números.")
        if Empresa.objects.filter(cuil=cuil).exists():
            raise forms.ValidationError("Este CUIL ya está registrado en el sistema.")
        return cuil
    
    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono')
        if not tel: 
            return tel
            
        if not re.match(r'^\+?[\d\s\-]+$', tel):
            raise forms.ValidationError("Teléfono inválido. Solo números, espacios, guiones o '+'.")
        return tel

    def clean_first_name(self):
        nombre = self.cleaned_data.get('first_name')
        if any(char.isdigit() for char in nombre):
            raise forms.ValidationError("El nombre no puede contener números.")
        return nombre

    def clean_last_name(self):
        apellido = self.cleaned_data.get('last_name')
        if any(char.isdigit() for char in apellido):
            raise forms.ValidationError("El apellido no puede contener números.")
        return apellido
    
    def clean_email_real(self):
        email = self.cleaned_data.get('email_real').lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado con otro usuario.")
        return email

    def save(self, request=None):
        from django.db import transaction
        with transaction.atomic():
            nueva_empresa = Empresa.objects.create(
                nombre=self.cleaned_data['nombre_empresa'],
                cuil=self.cleaned_data['cuil'],
                plan=self.cleaned_data['plan'],
                domicilio=self.cleaned_data['domicilio'],
                pais=self.cleaned_data['pais']
            )
            
            email = self.cleaned_data['email_real']
            first_name = self.cleaned_data['first_name']
            password_aleatoria = get_random_string(length=8)
            
            user = Usuario.objects.create_user(
                username=email,
                email=email, 
                password=password_aleatoria,
                first_name=first_name,
                last_name=self.cleaned_data['last_name'],
                telefono=self.cleaned_data['telefono'],
                empresa=nueva_empresa,
                rol='admin_cliente',
                autorizado=True
            )
            user.require_password_change = True
            user.save()
            
            if request:
                link_acceso = request.build_absolute_uri('/login/')
            else:
                link_acceso = "http://127.0.0.1:8000/login/"
                
            asunto = f"¡Bienvenido a Assistech, {first_name}!"
            mensaje_cuerpo = f"""
            Hola {first_name}, tu empresa '{nueva_empresa.nombre}' se registró correctamente.

            Acá tenés tus datos de acceso al sistema:
            - Sitio web:{link_acceso}
            - Tu Usuario (Email): {email}
            - Tu Contraseña provisoria: {password_aleatoria}

            Por motivos de seguridad, el sistema te pedirá cambiar esta contraseña en tu primer ingreso.

            ¡Gracias por confiar en Assistech!
            """
            
            send_mail(
                subject=asunto,
                message=mensaje_cuerpo,
                from_email='assistech.soporte@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
            
        return user

# ==========================================
# FORMULARIO: REGISTRO DE EMPLEADOS
# ==========================================
class AdminUsuarioCreateForm(forms.Form):
    ROLES_PERMITIDOS = [
        ('', 'Seleccionar Rol'),
        ('cliente', 'Cliente'),
        ('soporte', 'Soporte'),
        ('jefe', 'Jefe de Soporte'),
    ]
    HORARIOS_PERMITIDOS = [('', 'Seleccionar horario')] + [
        (f"{h:02d}:{m:02d}", f"{h:02d}:{m:02d}")
        for h in range(24) for m in (0, 30)
    ]
    DIAS_SEMANA = [
        ('0', 'Lunes'),
        ('1', 'Martes'),
        ('2', 'Miércoles'),
        ('3', 'Jueves'),
        ('4', 'Viernes'),
        ('5', 'Sábado'),
        ('6', 'Domingo'),
    ]
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email_real = forms.EmailField(label="Email")
    telefono = forms.CharField(max_length=20, label="Teléfono",required=False)
    rol = forms.ChoiceField(choices=ROLES_PERMITIDOS, label="Rol")
    horario_ingreso = forms.ChoiceField(choices=HORARIOS_PERMITIDOS, required=False, label="Horario Ingreso")
    horario_egreso = forms.ChoiceField(choices=HORARIOS_PERMITIDOS, required=False, label="Horario Egreso")
    dias_laborales = forms.MultipleChoiceField(choices=DIAS_SEMANA, widget=forms.CheckboxSelectMultiple, required=False, label="Días Laborales")
        
    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono')
        if not tel: 
            return tel
        if not re.match(r'^\+?[\d\s\-]+$', tel):
            raise forms.ValidationError("Teléfono inválido. Solo números, espacios, guiones o '+'.")
        return tel

    def clean_first_name(self):
        nombre = self.cleaned_data.get('first_name')
        if any(char.isdigit() for char in nombre):
            raise forms.ValidationError("El nombre no puede contener números.")
        return nombre

    def clean_last_name(self):
        apellido = self.cleaned_data.get('last_name')
        if any(char.isdigit() for char in apellido):
            raise forms.ValidationError("El apellido no puede contener números.")
        return apellido
    
    def clean_email_real(self):
        email = self.cleaned_data.get('email_real').lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado en el sistema.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        if rol == 'soporte':
            if not cleaned_data.get('horario_ingreso'):
                self.add_error('horario_ingreso', 'El horario de ingreso es obligatorio para el rol Soporte.')
            if not cleaned_data.get('horario_egreso'):
                self.add_error('horario_egreso', 'El horario de egreso es obligatorio para el rol Soporte.')
            if not cleaned_data.get('dias_laborales'):
                self.add_error('dias_laborales', 'Debes seleccionar al menos un día laboral para el rol Soporte.')
        return cleaned_data
    


class SuperAdminPlatformAdminCreateForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    email_real = forms.EmailField(label="Email")
    password = forms.CharField(label="Contrasenia", widget=forms.PasswordInput)
    confirmar_password = forms.CharField(label="Confirmar contrasenia", widget=forms.PasswordInput)

    def clean_email_real(self):
        email = self.cleaned_data.get('email_real').lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya esta registrado en el sistema.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar_password = cleaned_data.get('confirmar_password')

        if password and confirmar_password and password != confirmar_password:
            self.add_error('confirmar_password', 'Las contrasenias no coinciden.')

        return cleaned_data

# ==========================================
# FORMULARIO: LOGIN
# ==========================================
class LoginForm(forms.Form):
    username_or_email = forms.CharField(label="Usuario o Email")
    password = forms.CharField(widget=forms.PasswordInput,label="Contraseña")

# ==========================================
# FORMULARIO: TICKETS
# ==========================================

class TicketForm(forms.ModelForm):
    titulo = forms.CharField(max_length=25, label="Título", widget=forms.TextInput(attrs={'placeholder': 'Máximo 25 caracteres'}))
    
    categoria = forms.ChoiceField(choices=InfoTicket.CATEGORIAS,label='Categoría')
    categoria_otro = forms.CharField(
        required=False,label='Otra categoría',
        max_length=255,help_text='Complete este campo solo si selecciona Otro.')

    class Meta:
        model = InfoTicket
        fields = ['titulo', 'descripcion', 'categoria', 'categoria_otro']

    def _validate_text_field(self, value, field_name):
        allowed_re = re.compile(
            r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü\s\.\,\:\;\!\?¡¿\(\)\[\]\{\}\-\'\"\/]+$')
        if not allowed_re.match(value):
            raise forms.ValidationError(
                f'El campo {field_name} solo puede contener letras, números, espacios y signos de puntuación comunes.'
            )
        return value

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo', '')
        
        if len(titulo) > 25:
            raise forms.ValidationError('El título debe contener un máximo de 25 caracteres.')
        
        return self._validate_text_field(titulo, 'título')

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '')
        return self._validate_text_field(descripcion, 'descripción')

    def clean(self):
        cleaned_data = super().clean()
        categoria = cleaned_data.get('categoria')
        categoria_otro = cleaned_data.get('categoria_otro', '').strip()

        if categoria == 'OTRO':
            if not categoria_otro:
                self.add_error('categoria_otro', 'Debe ingresar la categoría cuando selecciona Otro.')
            else:
                cleaned_data['categoria'] = self._validate_text_field(categoria_otro, 'categoría')
        return cleaned_data


# ==========================================
# FORMULARIOS: FEEDBACK
# ==========================================
class UserFeedbackForm(forms.Form):
    TIPOS_FEEDBACK = (
        ('servicio', 'Servicio de Soporte'),
        ('plataforma', 'Plataforma'),
    )

    rating = forms.ChoiceField(
        choices=[(str(i), f'{i} estrella{"s" if i > 1 else ""}') for i in range(1, 6)],
        label='Calificacion'
    )
    comment = forms.CharField(
        required=False,
        label='Comentario',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comentario opcional'})
    )
    feedback_type = forms.ChoiceField(choices=TIPOS_FEEDBACK, label='Tipo de feedback')
    platform_category = forms.ChoiceField(
        choices=FeedbackPlatform.CATEGORIAS,
        required=False,
        label='Categoria de plataforma'
    )

    def clean_rating(self):
        return int(self.cleaned_data['rating'])


class TechnicianFeedbackForm(forms.ModelForm):
    class Meta:
        model = FeedbackSupportInternal
        fields = ['difficulty', 'comment', 'problems_found']
        labels = {
            'difficulty': 'Dificultad del caso',
            'comment': 'Comentario sobre el proceso',
            'problems_found': 'Problemas encontrados durante la resolucion',
        }
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Comentario opcional'}),
            'problems_found': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Problemas encontrados'}),
        }
