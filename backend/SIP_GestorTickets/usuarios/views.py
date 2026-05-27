from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from .forms import RegisterForm, LoginForm, TicketForm
from .models import Usuario, InfoTicket, TicketComentario, TicketHistorial

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
# SIEMPRE deslogueamos al usuario apenas entra a esta URL
    # Esto garantiza que vea el formulario limpio
    if request.user.is_authenticated:
        logout(request) 
    
    # Después de limpiar la sesión, procedemos con el formulario normal
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
                    return redirect('dashboard')
                else:
                    error = "La contraseña es incorrecta."

    return render(request, 'login.html', {'form': form, 'error': error})

def dashboard_view(request):
    rol = request.user.rol
    
    if rol == 'cliente':
        # El cliente solo ve sus propios tickets
        tickets = InfoTicket.objects.filter(solicitante=request.user).order_by('-fecha_creacion')
        return render(request, 'dashboard_cliente.html', {'tickets': tickets})

    elif rol == 'soporte':
        # El soporte ve lo que tiene asignado
        tickets = InfoTicket.objects.filter(
            asignaciones__soporte=request.user, 
            asignaciones__activo=True
        ).distinct()
        return render(request, 'dashboard_soporte.html', {'tickets': tickets})

    elif rol == 'jefe':
        # El jefe ve todo el sistema
        tickets = InfoTicket.objects.all().order_by('-prioridad')
        return render(request, 'dashboard_jefe_soporte.html', {'tickets': tickets})
    
    # Si por alguna razón no tiene rol, mandarlo a una página genérica o error
    return redirect('landing')


def logout_view(request):
    logout(request)
    return redirect('landing')

def crear_ticket(request):
    ticket_creado = False

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.solicitante = request.user
            ticket.save()
            ticket_creado = True
            form = TicketForm()  # limpia el formulario después de guardar
    else:
        form = TicketForm()

    return render(request, 'crear_ticket.html', {
        'form': form,
        'ticket_creado': ticket_creado
    })

def detalle_ticket_view(request, pk):
    ticket = get_object_or_404(InfoTicket, pk=pk)
    comentarios = ticket.comentarios.all().order_by('fecha_comentario')

    if request.user.rol == 'cliente' and ticket.solicitante != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.user.rol == 'cliente':
            raise PermissionDenied

        # Lógica para agregar un comentario rápido
        texto = request.POST.get('comentario')
        if texto:
            TicketComentario.objects.create(
                ticket=ticket,
                usuario=request.user,
                comentario=texto
            )
            return redirect('detalle_ticket', pk=pk)

    return render(request, 'detalle_ticket.html', {
        'ticket': ticket,
        'comentarios': comentarios,
        'estados_ticket': InfoTicket.ESTADO
    })

@require_POST
def eliminar_ticket(request, pk):
    ticket = get_object_or_404(InfoTicket, pk=pk)

    if request.user.rol != 'cliente' or ticket.solicitante != request.user:
        raise PermissionDenied

    ticket.delete()
    return redirect('dashboard')

@require_POST
def actualizar_estado(request, pk):
    if request.user.rol == 'cliente':
        raise PermissionDenied

    ticket = get_object_or_404(InfoTicket, pk=pk)
    estado_anterior = ticket.estado
    nuevo_estado = request.POST.get('nuevo_estado')
    estados_validos = dict(InfoTicket.ESTADO)

    if nuevo_estado not in estados_validos:
        raise PermissionDenied

    if estado_anterior != nuevo_estado:
        ticket.estado = nuevo_estado
        ticket.save()
        
        # Guardamos quién hizo el cambio y qué pasó
        TicketHistorial.objects.create(
            ticket=ticket,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            realizado_por=request.user,
            observacion="Cambio de estado desde el panel de control"
        )
    return redirect('detalle_ticket', pk=pk)
