from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from .models import Usuario, InfoTicket, TicketComentario, TicketHistorial
from .forms import RegisterForm, LoginForm, TicketForm, EmpresaRegisterForm

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
                if not usuario.autorizado:
                    error = "Tu cuenta está pendiente de aprobación por el administrador de tu empresa."
                else:
                    auth_user = authenticate(request, username=usuario.username, password=password)
                    if auth_user is not None:
                        login(request, auth_user)
                        return redirect('dashboard')
                    else:
                        error = "La contraseña es incorrecta."

    return render(request, 'login.html', {'form': form, 'error': error})

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    rol = request.user.rol
    
    if rol == 'admin_cliente':
        tickets = InfoTicket.objects.filter(solicitante__empresa=request.user.empresa).order_by('-fecha_creacion')
        empleados_pendientes = Usuario.objects.filter(empresa=request.user.empresa,autorizado=False)
        empleados_activos = Usuario.objects.filter(empresa=request.user.empresa, autorizado=True).exclude(pk=request.user.pk)
        
        return render(request, 'dashboard_admin_cliente.html', {'tickets': tickets,
        'empleados_pendientes': empleados_pendientes,'empleados_activos': empleados_activos})

    elif rol == 'cliente':
        tickets = InfoTicket.objects.filter(solicitante=request.user).order_by('-fecha_creacion')
        return render(request, 'dashboard_cliente.html', {'tickets': tickets})

    elif rol == 'soporte':
        tickets = InfoTicket.objects.filter(asignaciones__soporte=request.user, asignaciones__activo=True,solicitante__empresa=request.user.empresa).distinct()
        return render(request, 'dashboard_soporte.html', {'tickets': tickets})

    elif rol == 'jefe':
        tickets = InfoTicket.objects.filter(
            solicitante__empresa=request.user.empresa # <--- Encierra al jefe en su empresa
        )        
        return render(request, 'dashboard_jefe_soporte.html', {'tickets': tickets})
    
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
    
    '''
    if request.user.rol == 'cliente':
        raise PermissionDenied
    '''

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

def cambiar_prioridad(request, pk):
    if request.user.rol == 'cliente':
        raise PermissionDenied
    
    ticket = get_object_or_404(InfoTicket, pk=pk)
    nueva_prioridad = request.POST.get('prioridad')

    ticket.prioridad = nueva_prioridad
    ticket.save()
    
    # Guardamos quién hizo el cambio y qué pasó
    #TicketHistorial.objects.create(
    #    ticket=ticket,
    #   prioridad_anterior=prioridad_anterior,
    #    nueva_prioridad=nueva_prioridad,
    #    realizado_por=request.user,
    #    observacion="Cambio de prioridad desde el panel de control"
    #)

    return redirect('dashboard')

def registrar_empresa_view(request):
    if request.method == 'POST':
        form = EmpresaRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = EmpresaRegisterForm()
    return render(request, 'register_empresa.html', {'form': form})

def aprobar_usuario_view(request, pk):
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    
    # Buscamos al empleado que se quiere registrar
    empleado = get_object_or_404(Usuario, pk=pk)
    
    # Validamos que pertenezca a la MISMA empresa que el admin que está haciendo clic
    if empleado.empresa == request.user.empresa:
        empleado.autorizado = True
        empleado.save()
        
    return redirect('dashboard')

def rechazar_usuario_view(request, pk):
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    
    # Buscamos al empleado pendiente
    empleado = get_object_or_404(Usuario, pk=pk)
    
    # Validamos que sea de la misma empresa y que NO esté autorizado todavía
    if empleado.empresa == request.user.empresa and not empleado.autorizado:
        empleado.delete()  # Borra el registro de la base de datos
        
    return redirect('dashboard')

def quitar_acceso_view(request, pk):
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    
    empleado = get_object_or_404(Usuario, pk=pk)
    
    if empleado.empresa == request.user.empresa and empleado.pk != request.user.pk:
        empleado.autorizado = False
        empleado.save()
        
    return redirect('dashboard')

def confirmar_baja_view(request, pk):
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    empleado = get_object_or_404(Usuario, pk=pk)
    return render(request, 'confirmar_baja.html', {'empleado': empleado})