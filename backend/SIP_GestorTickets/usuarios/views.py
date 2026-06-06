from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, InfoTicket, TicketComentario, TicketHistorial
from .forms import LoginForm, TicketForm, EmpresaRegisterForm
from .forms import limpiar_texto_comun
from django.contrib.auth import update_session_auth_hash
from .forms import AdminUsuarioCreateForm
from django.contrib import messages

# ==========================================
# VISTAS DE AUTENTICACIÓN Y REGISTRO
# ==========================================
def crear_usuario_admin_view(request):
    if not request.user.is_authenticated or request.user.rol != 'admin_cliente':
        raise PermissionDenied

    if request.method == 'POST':
        form = AdminUsuarioCreateForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            rol = form.cleaned_data['rol']

            # Lógica: inicial del nombre + apellido completo (limpios)
            fn_limpio = limpiar_texto_comun(first_name)
            ln_limpio = limpiar_texto_comun(last_name)
            base_username = f"{fn_limpio[0]}{ln_limpio}"

            # Anti-duplicados por si tenés dos empleados llamados igual (ej: jgomez, jgomez1)
            username = base_username
            contador = 1
            while Usuario.objects.filter(username=username).exists():
                username = f"{base_username}{contador}"
                contador += 1

            # Email: username @ empresa_del_admin .com
            dominio_empresa = limpiar_texto_comun(request.user.empresa.nombre)
            email_completo = f"{username}@{dominio_empresa}.com"

            # Creamos el usuario en la base con la clave genérica
            nuevo_user = Usuario.objects.create_user(
                username=username,
                email=email_completo,
                password="12345678", # Contraseña genérica pedida
                first_name=first_name,
                last_name=last_name,
                empresa=request.user.empresa,
                rol=rol,
                autorizado=True # Ya nace autorizado porque lo crea su propio jefe
            )
            nuevo_user.require_password_change = True # Obligatorio cambiar clave
            nuevo_user.save()

            return redirect('dashboard')
    else:
        form = AdminUsuarioCreateForm()
    
    return render(request, 'crear_usuario_admin.html', {'form': form})

def landing_view(request):
    return render(request, 'assistech-landing.html')

def cambiar_contrasenia_obligatorio_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if not request.user.require_password_change:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        nueva_pass = request.POST.get('nueva_password')
        confirmar_pass = request.POST.get('confirmar_password')

        if not nueva_pass:
            error = "La contraseña no puede estar vacía."
        elif nueva_pass == "12345678":
            error = "No podés usar la misma contraseña genérica, poné una tuya."
        elif nueva_pass != confirmar_pass:
            error = "Las contraseñas no coinciden."
        else:
            try:
                # Validamos que cumpla las reglas de Django
                validate_password(nueva_pass, user=request.user)
                request.user.set_password(nueva_pass)
                request.user.require_password_change = False
                request.user.save()
                # Esto es clave para que Django no lo desloguee al cambiar la contraseña
                update_session_auth_hash(request, request.user)
                return redirect('dashboard')
            except Exception as e:
                # Si viene en formato de lista de errores, agarramos el primero
                error = e.messages[0] if hasattr(e, 'messages') else str(e)

    return render(request, 'cambiar_contrasenia_obligatorio.html', {'error': error})

def registrar_empresa_view(request):
    if request.method == 'POST':
        form = EmpresaRegisterForm(request.POST)
        if form.is_valid():
            user=form.save()
            messages.success(
                request, 
                f"🚀 <strong>¡Empresa y Administrador creados!</strong><br>"
                f"Tu nombre de usuario corporativo es: <strong class='text-white underline'>{user.username}</strong><br>"
                f"Tu contraseña provisoria es: <strong class='text-white'>12345678</strong>.<br>"
                f"Ingresalos abajo para configurar tu cuenta."
            )
            return redirect('login')
    else:
        form = EmpresaRegisterForm()
    return render(request, 'register_empresa.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        logout(request) 
    
    form = LoginForm(request.POST or None)
    error = None

    if request.method == 'POST':
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
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

            if usuario is not None:
                if not usuario.autorizado:
                    error = "Tu cuenta ha sido deshabilitada o suspendida por el administrador de tu empresa."
                else:
                    auth_user = authenticate(request, username=usuario.username, password=password)
                    if auth_user is not None:
                        login(request, auth_user)
                        
                        # 🚨 INTERCEPCIÓN AQUÍ: Si debe cambiar la clave, lo desviamos de una
                        if auth_user.require_password_change:
                            return redirect('cambiar_contrasenia_obligatorio')
                            
                        return redirect('dashboard')
                    else:
                        error = "La contraseña es incorrecta."

    return render(request, 'login.html', {'form': form, 'error': error})

def logout_view(request):
    logout(request)
    return redirect('landing')

# ==========================================
# VISTAS DE DASHBOARDS
# ==========================================
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.require_password_change:
        return redirect('cambiar_contrasenia_obligatorio')
    
    rol = request.user.rol
    
    if rol == 'admin_cliente':
        tickets = InfoTicket.objects.filter(solicitante__empresa=request.user.empresa).order_by('-fecha_creacion')
        
        cant_abiertos = tickets.filter(estado='ABIERTO').count()
        cant_proceso = tickets.filter(estado='EN_PROCESO').count()
        cant_resueltos = tickets.filter(estado='RESUELTO').count() + tickets.filter(estado='CERRADO').count()
        
        empleados_empresa = Usuario.objects.filter(empresa=request.user.empresa, is_active=True).exclude(pk=request.user.pk)
                
        return render(request, 'dashboard_admin_cliente.html', {
            'tickets': tickets,
            'empleados_activos': empleados_empresa,
            'cant_abiertos': cant_abiertos,    
            'cant_proceso': cant_proceso,      
            'cant_resueltos': cant_resueltos   
        })

    elif rol == 'cliente':
        tickets = InfoTicket.objects.filter(solicitante=request.user).order_by('-fecha_creacion')
        return render(request, 'dashboard_cliente.html', {'tickets': tickets})

    elif rol == 'soporte':
        tickets = InfoTicket.objects.filter(asignaciones__soporte=request.user, asignaciones__activo=True,solicitante__empresa=request.user.empresa).distinct()
        return render(request, 'dashboard_soporte.html', {'tickets': tickets})

    elif rol == 'jefe':
        tickets = InfoTicket.objects.filter(solicitante__empresa=request.user.empresa)        
        return render(request, 'dashboard_jefe_soporte.html', {'tickets': tickets})
    
    return redirect('landing')

# ==========================================
# VISTAS DE GESTIÓN DE TICKETS
# ==========================================
def crear_ticket(request):
    ticket_creado = False

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.solicitante = request.user
            ticket.save()
            ticket_creado = True
            form = TicketForm()  
    else:
        form = TicketForm()

    return render(request, 'crear_ticket.html', {'form': form,'ticket_creado': ticket_creado})

def detalle_ticket_view(request, pk):
    ticket = get_object_or_404(InfoTicket, pk=pk)
    
    if ticket.solicitante.empresa != request.user.empresa:
        raise PermissionDenied
    
    comentarios = ticket.comentarios.all().order_by('fecha_comentario')

    if request.user.rol == 'cliente' and ticket.solicitante != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.user.rol == 'cliente':
            raise PermissionDenied

        texto = request.POST.get('comentario')
        if texto:
            TicketComentario.objects.create(ticket=ticket,usuario=request.user,comentario=texto)
            return redirect('detalle_ticket', pk=pk)

    return render(request, 'detalle_ticket.html', {'ticket': ticket,'comentarios': comentarios,'estados_ticket': InfoTicket.ESTADO})

def eliminar_ticket(request, pk):
    ticket = get_object_or_404(InfoTicket, pk=pk)

    if request.user.rol != 'cliente' or ticket.solicitante != request.user:
        raise PermissionDenied

    ticket.delete()
    return redirect('dashboard')

def actualizar_estado(request, pk):
    ticket = get_object_or_404(InfoTicket, pk=pk)
    
    if ticket.solicitante.empresa != request.user.empresa:
        raise PermissionDenied
    
    estado_anterior = ticket.estado
    nuevo_estado = request.POST.get('nuevo_estado')
    estados_validos = dict(InfoTicket.ESTADO)

    if nuevo_estado not in estados_validos:
        raise PermissionDenied

    if estado_anterior != nuevo_estado:
        ticket.estado = nuevo_estado
        ticket.save()        
        TicketHistorial.objects.create(ticket=ticket,estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,realizado_por=request.user,observacion="Cambio de estado desde el panel de control"
        )
    return redirect('detalle_ticket', pk=pk)

def cambiar_prioridad(request, pk):
    if request.user.rol == 'cliente':
        raise PermissionDenied
    
    ticket = get_object_or_404(InfoTicket, pk=pk)
    
    if ticket.solicitante.empresa != request.user.empresa:
        raise PermissionDenied
    nueva_prioridad = request.POST.get('prioridad')

    ticket.prioridad = nueva_prioridad
    ticket.save()
    return redirect('dashboard')

# ==========================================
# VISTAS DE ADMINISTRACIÓN DE PERSONAL
# ==========================================

def quitar_acceso_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)    
    if empleado.empresa == request.user.empresa and empleado.pk != request.user.pk:
        empleado.autorizado = False
        empleado.save()        
    return redirect('dashboard')

def eliminar_usuario_definitivo_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)
    if empleado.empresa == request.user.empresa and empleado.pk != request.user.pk:
        
        empleado.is_active = False  
        empleado.autorizado = False 
        empleado.save()
        
    return redirect('dashboard')

def confirmar_baja_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)
    
    return render(request, 'confirmar_baja.html', {'empleado': empleado})

def aprobar_usuario_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)    
    if empleado.empresa == request.user.empresa:
        empleado.autorizado = True  # 👈 Esto es lo que saca la suspensión
        empleado.save()        
    return redirect('dashboard')

# ==========================================
# FUNCIONES AUXILIARES (HELPERS)
# ==========================================
def _obtener_empleado_controlado(request, pk):
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    return get_object_or_404(Usuario, pk=pk)
