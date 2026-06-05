import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, InfoTicket, Empresa

class EmpresaRegisterForm(forms.Form):
    nombre_empresa = forms.CharField(
        max_length=255,
        label="Nombre de la Empresa",
        help_text="Este nombre definirá tu dominio de email corporativo."
    )
    first_name = forms.CharField(max_length=150, label="Tu Nombre")
    last_name = forms.CharField(max_length=150, label="Tu Apellido")
    username = forms.CharField(max_length=150, label="Nombre de usuario")
    
    # Cambiamos EmailField por CharField para pedir solo la parte de adelante
    email_usuario = forms.CharField(
        max_length=100, 
        label="Usuario de Email",
        help_text="Solo ingresá lo que va antes del @ (Ej: 'admin', 'jefe', 'ale')"
    )
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    def clean_nombre_empresa(self):
        nombre = self.cleaned_data.get('nombre_empresa')
        if Empresa.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe una empresa registrada con ese nombre.")
        return nombre

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        nombre_empresa = cleaned_data.get('nombre_empresa')
        email_usuario = cleaned_data.get('email_usuario')

        if nombre_empresa and email_usuario:
            # 1. Limpiamos el nombre de la empresa para el dominio (Ej: "Tech Corp" -> "techcorp")
            dominio = nombre_empresa.lower().replace(" ", "")
            # 2. Armamos el mail definitivo
            email_completo = f"{email_usuario.lower()}@{dominio}.com"

            # 3. Validamos que no exista ese mail en la base de datos
            if Usuario.objects.filter(email=email_completo).exists():
                self.add_error('email_usuario', f"El email {email_completo} ya está registrado.")
            
            # Guardamos el mail completo para usarlo en el save
            cleaned_data['email_completo'] = email_completo

        return cleaned_data

    def save(self):
        from django.db import transaction
        with transaction.atomic():
            # 1. Crear la empresa
            nueva_empresa = Empresa.objects.create(
                nombre=self.cleaned_data['nombre_empresa']
            )
            # 2. Crear el usuario con el mail corporativo autogenerado
            user = Usuario.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data['email_completo'], # <--- Acá se guarda el mail armado
                password=self.cleaned_data['password'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                empresa=nueva_empresa,
                rol='admin_cliente'
            )
        return user
    
class RegisterForm(forms.ModelForm):
    rol = forms.ChoiceField(
        choices=[
            ('cliente', 'Usuario'),
            ('soporte', 'Soporte'),
            ('jefe', 'Jefe de soporte')
        ],
        label="Tu Rol en la empresa"
    )
    first_name = forms.CharField(
        max_length=150,
        label="Nombre/s"
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido/s"
    )
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label="Selecciona tu Empresa",
        empty_label="-- Elegir Empresa --"
    )
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario"
    )
    email_usuario = forms.CharField(
        max_length=100, 
        label="Usuario de Email",
        help_text="Solo ingresá lo que va antes del @ (Ej: 'empleado', 'juan')"
    )    
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'username', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        email_usuario = cleaned_data.get('email_usuario')

        if empresa and email_usuario:
            dominio = empresa.nombre.lower().replace(" ", "")
            email_completo = f"{email_usuario.lower()}@{dominio}.com"

            if Usuario.objects.filter(email=email_completo).exists():
                self.add_error('email_usuario', f"El email {email_completo} ya está registrado.")
            
            cleaned_data['email_completo'] = email_completo
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.empresa = self.cleaned_data['empresa']
        user.rol = self.cleaned_data['rol']
        user.email = self.cleaned_data['email_completo']
        user.autorizado = False  # <--- SE CREA DESAUTORIZADO: Requiere aprobación del jefe
        if commit:
            user.save()
        return user
    
class LoginForm(forms.Form):
    username_or_email = forms.CharField(
        label="Usuario o Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña"
    )
    
class TicketForm(forms.ModelForm):
    categoria = forms.ChoiceField(
        choices=InfoTicket.CATEGORIAS,
        label='Categoría'
    )
    categoria_otro = forms.CharField(
        required=False,
        label='Otra categoría',
        max_length=255,
        help_text='Complete este campo solo si selecciona Otro.'
    )

    class Meta:
        model = InfoTicket
        fields = ['titulo', 'descripcion', 'categoria', 'categoria_otro', 'prioridad']

    def _validate_text_field(self, value, field_name):
        allowed_re = re.compile(
            r'^[A-Za-z0-9ÁÉÍÓÚáéíóúÑñÜü\s\.\,\:\;\!\?¡¿\(\)\[\]\{\}\-\'\"\/]+$'
        )
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

    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria', '')
        if categoria == 'OTRO':
            return categoria
        return categoria

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