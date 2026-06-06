import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, InfoTicket, Empresa
from django.core.mail import send_mail
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
    nombre_empresa = forms.CharField(max_length=255,label="Nombre de la Empresa",help_text="Este nombre definirá tu dominio de email corporativo.")
    cuil = forms.CharField(max_length=11, min_length=11, label="CUIL de la Empresa", help_text="Ingresar los 11 dígitos sin guiones.")

    opciones_plan = [('', 'Seleccionar opción')] + list(Empresa.PLANES)
    plan = forms.ChoiceField(choices=opciones_plan, label="Selecciona tu Plan")    
    
    first_name = forms.CharField(max_length=150, label="Tu Nombre")
    last_name = forms.CharField(max_length=150, label="Tu Apellido")
    email_real = forms.EmailField(label="Tu Email Real")
    telefono = forms.CharField(max_length=20, label="Tu Número de Teléfono")
    
    def clean_nombre_empresa(self):
        nombre = self.cleaned_data.get('nombre_empresa')
        if Empresa.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe una empresa registrada con ese nombre.")
        return nombre
    
    def clean_cuil(self):
        cuil = self.cleaned_data.get('cuil')
        if not cuil.isdigit():
            raise forms.ValidationError("El CUIL solo debe contener números.")
        if Empresa.objects.filter(cuil=cuil).exists():
            raise forms.ValidationError("Este CUIL ya está registrado en el sistema.")
        return cuil
    
    def clean_email_real(self):
        email = self.cleaned_data.get('email_real').lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado con otro usuario.")
        return email

    def save(self):
        from django.db import transaction
        with transaction.atomic():
            nueva_empresa = Empresa.objects.create(nombre=self.cleaned_data['nombre_empresa'],cuil=self.cleaned_data['cuil'],plan=self.cleaned_data['plan'])

            email = self.cleaned_data['email_real']
            first_name = self.cleaned_data['first_name']

            user = Usuario.objects.create_user(
                username=email,
                email=email, 
                password="12345678",
                first_name=first_name,
                last_name=self.cleaned_data['last_name'],
                telefono=self.cleaned_data['telefono'],
                empresa=nueva_empresa,
                rol='admin_cliente',
                autorizado=True
            )
            user.require_password_change = True
            user.save()
            
            asunto = f"¡Bienvenido a Assistech, {first_name}!"
            mensaje_cuerpo = f"""
            Hola {first_name}, tu empresa '{nueva_empresa.nombre}' se registró correctamente.

            Acá tenés tus datos de acceso al sistema:
            - Sitio web:https://assistech.pythonanywhere.com/login/
            - Tu Usuario (Email): {email}
            - Tu Contraseña provisoria: 12345678

            ⚠️ Por motivos de seguridad, el sistema te pedirá cambiar esta contraseña en tu primer ingreso.

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
        ('cliente', 'Cliente'),
        ('soporte', 'Soporte'),
        ('jefe', 'Jefe de Soporte'),
    ]
    first_name = forms.CharField(max_length=150, label="Nombre/s")
    last_name = forms.CharField(max_length=150, label="Apellido/s")
    email_real = forms.EmailField(label="Email Real")
    telefono = forms.CharField(max_length=20, label="Número de Teléfono")
    rol = forms.ChoiceField(choices=ROLES_PERMITIDOS, label="Rol del nuevo usuario")
    
    def clean_email_real(self):
        email = self.cleaned_data.get('email_real').lower().strip()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado en el sistema.")
        return email
    
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