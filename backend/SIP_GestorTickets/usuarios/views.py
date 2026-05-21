from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from .models import Usuario

def landing_view(request):
    return render(request, 'assistech-landing.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    form = LoginForm(request.POST or None)
    error = None

    if request.method == 'POST':
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Buscar si el campo ingresado es email o username
            usuario = None
            if '@' in username_or_email:
                try:
                    usuario = Usuario.objects.get(email=username_or_email)
                except Usuario.DoesNotExist:
                    error = "No existe ninguna cuenta con ese email."
            else:
                try:
                    usuario = Usuario.objects.get(username=username_or_email)
                except Usuario.DoesNotExist:
                    error = "No existe ninguna cuenta con ese nombre de usuario."

            # Si encontró el usuario, verificar contraseña
            if usuario is not None:
                auth_user = authenticate(request, username=usuario.username, password=password)
                if auth_user is not None:
                    login(request, auth_user)

                    # Redirigir según rol
                    if auth_user.rol == 'jefe':
                        return redirect('dashboard')  # de momento dashboard general
                    elif auth_user.rol == 'soporte':
                        return redirect('dashboard')  # de momento dashboard general
                    elif auth_user.rol == 'cliente':
                        return redirect('dashboard')  # de momento dashboard general
                else:
                    error = "La contraseña es incorrecta."

    return render(request, 'login.html', {'form': form, 'error': error})

def dashboard_view(request):
    return render(request, 'dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('landing')