import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, InfoTicket

class RegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        label="Nombre/s"
    )
    last_name = forms.CharField(
        max_length=150,
        label="Apellido/s"
    )
    empresa = forms.CharField(
        max_length=255,
        required=False,
        label="Empresa"
    )
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario"
    )
    email = forms.EmailField(
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Contraseña"
    )

    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'empresa', 'username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este email.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # hashea la contraseña
        user.rol = 'cliente'                               # se autocompleta
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