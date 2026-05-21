from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario

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