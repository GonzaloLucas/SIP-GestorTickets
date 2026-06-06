import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, InfoTicket, Empresa
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
    first_name = forms.CharField(max_length=150, label="Tu Nombre")
    last_name = forms.CharField(max_length=150, label="Tu Apellido")

    def clean_nombre_empresa(self):
        nombre = self.cleaned_data.get('nombre_empresa')
        if Empresa.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe una empresa registrada con ese nombre.")
        return nombre

    def save(self):
        from django.db import transaction
        with transaction.atomic():
            nueva_empresa = Empresa.objects.create(nombre=self.cleaned_data['nombre_empresa'])

            first_name = self.cleaned_data['first_name']
            last_name = self.cleaned_data['last_name']
            
            fn_limpio = limpiar_texto_comun(first_name)
            ln_limpio = limpiar_texto_comun(last_name)
            base_username = f"{fn_limpio[0]}{ln_limpio}"
            
            username = base_username
            contador = 1
            while Usuario.objects.filter(username=username).exists():
                username = f"{base_username}{contador}"
                contador += 1
            
            dominio_empresa = limpiar_texto_comun(nueva_empresa.nombre)
            email_completo = f"{username}@{dominio_empresa}.com"
            
            user = Usuario.objects.create_user(
                username=username,
                email=email_completo, 
                password="12345678",
                first_name=first_name,
                last_name=last_name,
                empresa=nueva_empresa,
                rol='admin_cliente',
                autorizado=True
            )
            user.require_password_change = True
            user.save()
            
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
    rol = forms.ChoiceField(choices=ROLES_PERMITIDOS, label="Rol del nuevo usuario")
    
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