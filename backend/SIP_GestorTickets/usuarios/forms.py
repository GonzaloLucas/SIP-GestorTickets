import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, InfoTicket, Empresa

# ==========================================
# 🛠️ FUNCIONES DE AYUDA
# ==========================================
def validar_nombre_usuario(username):
    if Usuario.objects.filter(username=username).exists():
        raise forms.ValidationError("Este nombre de usuario ya está en uso.")
    return username

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
    username = forms.CharField(max_length=150, label="Nombre de usuario")
    
    email_usuario = forms.CharField(max_length=100, label="Usuario de Email",help_text="Solo ingresá lo que va antes del @")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    def clean_nombre_empresa(self):
        nombre = self.cleaned_data.get('nombre_empresa')
        if Empresa.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe una empresa registrada con ese nombre.")
        return nombre

    def clean_username(self):
        return validar_nombre_usuario(self.cleaned_data.get("username"))

    def clean_password(self):
        return validar_contrasenia_segura(self.cleaned_data.get('password'))

    def clean(self):
        cleaned_data = super().clean()
        nombre_empresa = cleaned_data.get('nombre_empresa')
        email_usuario = cleaned_data.get('email_usuario')

        if nombre_empresa and email_usuario:
            try:
                cleaned_data['email_completo'] = generar_y_validar_email(nombre_empresa, email_usuario)
            except forms.ValidationError as e:
                self.add_error('email_usuario', e)
        return cleaned_data

    def save(self):
        from django.db import transaction
        with transaction.atomic():
            nueva_empresa = Empresa.objects.create(nombre=self.cleaned_data['nombre_empresa'])
            user = Usuario.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email_completo'], 
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                empresa=nueva_empresa,
                rol='admin_cliente'
            )
        return user

# ==========================================
# FORMULARIO: REGISTRO DE EMPLEADOS
# ==========================================

class RegisterForm(forms.ModelForm):
    rol = forms.ChoiceField(
        choices=[
            ('cliente', 'Usuario'),
            ('soporte', 'Soporte'),
            ('jefe', 'Jefe de soporte')
        ],
        label="Tu Rol en la empresa"
    )
    first_name = forms.CharField(max_length=150,label="Nombre/s")
    last_name = forms.CharField(max_length=150,label="Apellido/s")
    empresa = forms.CharField(
        max_length=255,
        label="Nombre de tu Empresa",
        help_text="Ingresá el nombre exacto de la organización a la que pertenecés."
    )
    username = forms.CharField(max_length=150,label="Nombre de usuario")
    email_usuario = forms.CharField(
        max_length=100, 
        label="Usuario de Email",
        help_text="Solo ingresá lo que va antes del @"
    )    
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'username', 'password']

    def clean_username(self):
        return validar_nombre_usuario(self.cleaned_data.get('username'))
    def clean_password(self):
        return validar_contrasenia_segura(self.cleaned_data.get('password'))

    def clean(self):
        cleaned_data = super().clean()
        nombre_empresa_tipeado = cleaned_data.get('empresa')
        email_usuario = cleaned_data.get('email_usuario')

        if nombre_empresa_tipeado and email_usuario:
            try:
                empresa_obj = Empresa.objects.get(nombre__iexact=nombre_empresa_tipeado)
                cleaned_data['empresa_objeto'] = empresa_obj
            except Empresa.DoesNotExist:
                # Si no existe, tiramos el error en el campo de la empresa y frenamos el flujo
                self.add_error('empresa', "La empresa ingresada no está registrada en el sistema. Verificá el nombre.")
                return cleaned_data
            
            try:
                cleaned_data['email_completo'] = generar_y_validar_email(empresa_obj.nombre, email_usuario)
            except forms.ValidationError as e:
                self.add_error('email_usuario', e)
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.rol = self.cleaned_data['rol']
        user.email = self.cleaned_data['email_completo']
        user.empresa = self.cleaned_data['empresa_objeto']
        user.autorizado = False 
        if commit:
            user.save()
        return user
    
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
    categoria = forms.ChoiceField(choices=InfoTicket.CATEGORIAS,label='Categoría')
    categoria_otro = forms.CharField(
        required=False,label='Otra categoría',
        max_length=255,help_text='Complete este campo solo si selecciona Otro.')

    class Meta:
        model = InfoTicket
        fields = ['titulo', 'descripcion', 'categoria', 'categoria_otro', 'prioridad']

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