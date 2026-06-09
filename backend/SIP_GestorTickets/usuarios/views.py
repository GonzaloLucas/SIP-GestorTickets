from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from .models import (
    FeedbackPlatform,
    FeedbackService,
    FeedbackSupportInternal,
    Empresa,
    Usuario,
    InfoTicket,
    TicketComentario,
    TicketHistorial,
)
from .forms import (
    LoginForm,
    SuperAdminPlatformAdminCreateForm,
    TechnicianFeedbackForm,
    TicketForm,
    EmpresaRegisterForm,
    UserFeedbackForm,
)
from django.core.mail import send_mail
from django.contrib.auth import update_session_auth_hash
from .forms import AdminUsuarioCreateForm
from django.contrib import messages
from django.utils.crypto import get_random_string


# ==========================================
# VISTAS DE AUTENTICACIÃ“N Y REGISTRO
# ==========================================
def crear_usuario_admin_view(request):
    if not request.user.is_authenticated or request.user.rol != 'admin_cliente':
        raise PermissionDenied

    if request.method == 'POST':
        form = AdminUsuarioCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email_real']
            first_name = form.cleaned_data['first_name']
            password_aleatoria = get_random_string(length=8)

            try:
                with transaction.atomic():
                    # Creamos el usuario en la base con la clave generica.
                    nuevo_user = Usuario.objects.create_user(
                        username=email,
                        email=email,
                        password=password_aleatoria,
                        first_name=first_name,
                        last_name=form.cleaned_data['last_name'],
                        telefono=form.cleaned_data['telefono'],
                        empresa=request.user.empresa,
                        rol=form.cleaned_data['rol'],
                        autorizado=True
                    )
                    nuevo_user.require_password_change = True
                    nuevo_user.save()

                    link_acceso = request.build_absolute_uri('/login/')
                    asunto_empleado = "Te crearon una cuenta en Assistech"
                    mensaje_empleado = f"""
                    Hola {first_name},

                    El administrador de {request.user.empresa.nombre} te ha generado un usuario con el rol de '{nuevo_user.get_rol_display()}'.

                    Tus datos para loguearte son:
                    - Link de acceso: {link_acceso}
                    - Usuario: {email}
                    - Contrasenia provisoria: {password_aleatoria}

                    Recorda que vas a tener que cambiar esta contrasenia generica apenas ingreses por primera vez.
                    """

                    send_mail(
                        subject=asunto_empleado,
                        message=mensaje_empleado,
                        from_email='assistech.soporte@gmail.com',
                        recipient_list=[email],
                        fail_silently=False,
                    )

                messages.success(request, f"Usuario {email} creado correctamente. Se enviaron las credenciales por correo.")
                return redirect('dashboard')
            except Exception:
                messages.error(
                    request,
                    "No se pudo enviar el correo de credenciales. El usuario no fue creado; revisa la configuracion de email e intentalo de nuevo."
                )
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
            error = "La contraseÃ±a no puede estar vacÃ­a."
        elif nueva_pass != confirmar_pass:
            error = "Las contraseÃ±as no coinciden."
        else:
            try:
                # Validamos que cumpla las reglas de Django
                validate_password(nueva_pass, user=request.user)
                request.user.set_password(nueva_pass)
                request.user.require_password_change = False
                request.user.save()
                # Esto es clave para que Django no lo desloguee al cambiar la contraseÃ±a
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
            user = form.save(request=request)
            
            messages.success(
                request, 
                f"Â¡Empresa registrada con Ã©xito! Generamos tus credenciales de administrador de forma segura. "
                f"<br>Te enviamos un correo electrÃ³nico a <strong>{user.email}</strong> con tu contraseÃ±a provisoria aleatoria. "
                f" <br><br>RevisÃ¡ tu bandeja de entrada (o Spam) para poder ingresar."
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
                        
                        if auth_user.require_password_change:
                            return redirect('cambiar_contrasenia_obligatorio')
                            
                        return redirect('dashboard')
                    else:
                        error = "La contraseÃ±a es incorrecta."

    return render(request, 'login.html', {'form': form, 'error': error})

def logout_view(request):
    logout(request)
    return redirect('landing')


def crear_platform_admin_view(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        form = SuperAdminPlatformAdminCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email_real']
            Usuario.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                empresa=None,
                rol='platform_admin',
                autorizado=True,
                is_staff=False,
                is_superuser=False,
            )
            messages.success(request, f"Platform Admin {email} creado correctamente.")
            return redirect('dashboard')
    else:
        form = SuperAdminPlatformAdminCreateForm()

    return render(request, 'crear_platform_admin.html', {'form': form})

# ==========================================
# VISTAS DE DASHBOARDS
# ==========================================
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.user.require_password_change:
        return redirect('cambiar_contrasenia_obligatorio')

    if request.user.is_superuser:
        empresa_id = request.GET.get('empresa')
        tipo_feedback = request.GET.get('tipo', 'todos')
        rating = request.GET.get('rating')
        critico = request.GET.get('critico')
        busqueda = request.GET.get('q', '').strip()

        feedback_servicio = FeedbackService.objects.select_related(
            'ticket',
            'ticket__solicitante',
            'ticket__solicitante__empresa',
            'user',
            'technician',
        )
        feedback_plataforma = FeedbackPlatform.objects.select_related(
            'ticket',
            'ticket__solicitante',
            'ticket__solicitante__empresa',
            'user',
        )

        if empresa_id:
            feedback_servicio = feedback_servicio.filter(ticket__solicitante__empresa_id=empresa_id)
            feedback_plataforma = feedback_plataforma.filter(ticket__solicitante__empresa_id=empresa_id)

        if rating:
            feedback_servicio = feedback_servicio.filter(rating=rating)
            feedback_plataforma = feedback_plataforma.filter(rating=rating)

        if critico == '1':
            feedback_servicio = feedback_servicio.filter(is_critical=True)
            feedback_plataforma = feedback_plataforma.filter(is_critical=True)

        if busqueda:
            filtro_servicio = (
                Q(ticket__titulo__icontains=busqueda)
                | Q(user__username__icontains=busqueda)
                | Q(user__email__icontains=busqueda)
                | Q(technician__username__icontains=busqueda)
                | Q(technician__email__icontains=busqueda)
                | Q(comment__icontains=busqueda)
            )
            filtro_plataforma = (
                Q(ticket__titulo__icontains=busqueda)
                | Q(user__username__icontains=busqueda)
                | Q(user__email__icontains=busqueda)
                | Q(comment__icontains=busqueda)
                | Q(category__icontains=busqueda)
            )
            if busqueda.isdigit():
                filtro_servicio |= Q(ticket__numero_ticket_empresa=int(busqueda))
                filtro_plataforma |= Q(ticket__numero_ticket_empresa=int(busqueda))

            feedback_servicio = feedback_servicio.filter(filtro_servicio)
            feedback_plataforma = feedback_plataforma.filter(filtro_plataforma)

        mostrar_soporte = tipo_feedback in ['todos', 'soporte']
        mostrar_plataforma = tipo_feedback in ['todos', 'plataforma']

        return render(request, 'dashboard_superadmin.html', {
            'feedback_servicio': feedback_servicio,
            'feedback_plataforma': feedback_plataforma,
            'promedio_soporte': feedback_servicio.aggregate(promedio=Avg('rating'))['promedio'],
            'promedio_plataforma': feedback_plataforma.aggregate(promedio=Avg('rating'))['promedio'],
            'feedback_servicio_critico': feedback_servicio.filter(is_critical=True),
            'feedback_plataforma_critico': feedback_plataforma.filter(is_critical=True),
            'empresas': Empresa.objects.order_by('nombre'),
            'filtros': {
                'empresa': empresa_id or '',
                'tipo': tipo_feedback,
                'rating': rating or '',
                'critico': critico or '',
                'q': busqueda,
            },
            'mostrar_soporte': mostrar_soporte,
            'mostrar_plataforma': mostrar_plataforma,
        })
    
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
        feedback_servicio = FeedbackService.objects.filter(ticket__solicitante__empresa=request.user.empresa)
        feedback_interno = FeedbackSupportInternal.objects.filter(ticket__solicitante__empresa=request.user.empresa)
        metricas_tecnico = feedback_servicio.values(
            'technician__username'
        ).annotate(
            promedio=Avg('rating'),
            cantidad=Count('id')
        ).order_by('technician__username')

        return render(request, 'dashboard_jefe_soporte.html', {
            'tickets': tickets,
            'feedback_servicio': feedback_servicio,
            'feedback_interno': feedback_interno,
            'promedio_soporte': feedback_servicio.aggregate(promedio=Avg('rating'))['promedio'],
            'metricas_tecnico': metricas_tecnico,
            'feedback_bajo': feedback_servicio.filter(is_critical=True),
        })

    elif rol == 'platform_admin':
        feedback_plataforma = FeedbackPlatform.objects.select_related('ticket', 'ticket__solicitante', 'ticket__solicitante__empresa', 'user')
        estadisticas_categoria = feedback_plataforma.values('category').annotate(
            cantidad=Count('id'),
            promedio=Avg('rating')
        ).order_by('category')

        return render(request, 'dashboard_platform_admin.html', {
            'feedback_plataforma': feedback_plataforma,
            'promedio_plataforma': feedback_plataforma.aggregate(promedio=Avg('rating'))['promedio'],
            'feedback_critico': feedback_plataforma.filter(is_critical=True),
            'reportes_bugs': feedback_plataforma.filter(category='BUG'),
            'sugerencias_mejora': feedback_plataforma.filter(category__in=['MEJORA', 'FUNCIONALIDAD']),
            'feedback_ux_ui': feedback_plataforma.filter(category='UX_UI'),
            'estadisticas_categoria': estadisticas_categoria,
        })
    
    return redirect('landing')

# ==========================================
# VISTAS DE GESTIÃ“N DE TICKETS
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

    puede_dejar_feedback_usuario = (
        request.user.rol == 'cliente'
        and ticket.solicitante == request.user
        and ticket.estado in ['RESUELTO', 'CERRADO']
        and not ticket.feedback_servicio.exists()
        and not ticket.feedback_plataforma.exists()
    )
    puede_dejar_feedback_tecnico = (
        request.user.rol == 'soporte'
        and ticket.estado == 'CERRADO'
        and ticket.asignaciones.filter(soporte=request.user, activo=True).exists()
        and not ticket.feedback_interno_soporte.filter(technician=request.user).exists()
    )

    return render(request, 'detalle_ticket.html', {
        'ticket': ticket,
        'comentarios': comentarios,
        'estados_ticket': InfoTicket.ESTADO,
        'user_feedback_form': UserFeedbackForm(),
        'technician_feedback_form': TechnicianFeedbackForm(),
        'show_user_feedback_modal': puede_dejar_feedback_usuario,
        'show_technician_feedback_modal': puede_dejar_feedback_tecnico,
    })

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
        if nuevo_estado == 'RESUELTO':
            ticket.fecha_resolucion = timezone.now()
        elif nuevo_estado == 'CERRADO':
            ticket.fecha_cierre = timezone.now()
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


def guardar_feedback_usuario(request, pk):
    if request.method != 'POST':
        raise PermissionDenied

    ticket = get_object_or_404(InfoTicket, pk=pk)

    if request.user.rol != 'cliente' or ticket.solicitante != request.user:
        raise PermissionDenied
    if ticket.estado not in ['RESUELTO', 'CERRADO']:
        raise PermissionDenied

    form = UserFeedbackForm(request.POST)
    if form.is_valid():
        asignacion = ticket.asignaciones.filter(activo=True).first() or ticket.asignaciones.first()
        feedback_type = form.cleaned_data['feedback_type']

        if feedback_type == 'servicio':
            FeedbackService.objects.get_or_create(
                ticket=ticket,
                user=request.user,
                defaults={
                    'technician': asignacion.soporte if asignacion else None,
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                }
            )
        else:
            FeedbackPlatform.objects.get_or_create(
                ticket=ticket,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                    'category': form.cleaned_data.get('platform_category') or 'OTRO',
                }
            )

    return redirect('detalle_ticket', pk=pk)


def guardar_feedback_tecnico(request, pk):
    if request.method != 'POST':
        raise PermissionDenied

    ticket = get_object_or_404(InfoTicket, pk=pk)

    if request.user.rol != 'soporte':
        raise PermissionDenied
    if ticket.solicitante.empresa != request.user.empresa:
        raise PermissionDenied
    if ticket.estado != 'CERRADO' or not ticket.asignaciones.filter(soporte=request.user, activo=True).exists():
        raise PermissionDenied

    form = TechnicianFeedbackForm(request.POST)
    if form.is_valid() and not ticket.feedback_interno_soporte.filter(technician=request.user).exists():
        feedback = form.save(commit=False)
        feedback.ticket = ticket
        feedback.technician = request.user
        feedback.save()

    return redirect('detalle_ticket', pk=pk)

# ==========================================
# VISTAS DE ADMINISTRACIÃ“N DE PERSONAL
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
        empleado.autorizado = True  # ðŸ‘ˆ Esto es lo que saca la suspensiÃ³n
        empleado.save()        
    return redirect('dashboard')

# ==========================================
# FUNCIONES AUXILIARES (HELPERS)
# ==========================================
def _obtener_empleado_controlado(request, pk):
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    return get_object_or_404(Usuario, pk=pk)
