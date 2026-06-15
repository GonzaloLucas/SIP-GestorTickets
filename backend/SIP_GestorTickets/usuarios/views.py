from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils.crypto import get_random_string
from datetime import timedelta

from .models import (FeedbackPlatform,FeedbackService,FeedbackSupportInternal,Empresa,
    Usuario,InfoTicket,TicketComentario,TicketHistorial,TicketAsignacion,FAQDeflexion)
from .forms import (
    LoginForm,SuperAdminPlatformAdminCreateForm,TechnicianFeedbackForm,
    TicketForm,EmpresaRegisterForm,UserFeedbackForm,AdminUsuarioCreateForm,FeedbackPlatformForm)

# ==========================================
# FUNCIONES INTERNAS Y UTILIDADES (HELPERS)
# ==========================================
def _filtrar_tickets_por_plan(empresa, queryset):
    """Filtra la cantidad de tickets visibles según el plan de la empresa."""
    if not empresa:
        return queryset
    plan = empresa.plan
    if plan == 'BASICO':
        limite = timezone.now() - timedelta(days=90)
        return queryset.filter(fecha_creacion__gte=limite)
    elif plan == 'PREMIUM':
        limite = timezone.now() - timedelta(days=365)
        return queryset.filter(fecha_creacion__gte=limite)
    return queryset

def _get_ticket_con_control_empresa(request, pk):
    """Busca un ticket y asegura que pertenezca a la misma empresa del usuario."""
    ticket = get_object_or_404(InfoTicket, pk=pk)
    if ticket.solicitante.empresa != request.user.empresa:
        raise PermissionDenied
        
    if request.user.empresa:
        plan = request.user.empresa.plan
        if plan == 'BASICO' and ticket.fecha_creacion < (timezone.now() - timedelta(days=90)):
            raise PermissionDenied("El plan Básico solo permite acceder a tickets de los últimos 3 meses.")
        elif plan == 'PREMIUM' and ticket.fecha_creacion < (timezone.now() - timedelta(days=365)):
            raise PermissionDenied("El plan Premium solo permite acceder a tickets de hasta 1 año de antigüedad.")
    return ticket

def _obtener_empleado_controlado(request, pk):
    """Garantiza que solo un administrador de empresa pueda gestionar al personal."""
    if request.user.rol != 'admin_cliente':
        raise PermissionDenied
    return get_object_or_404(Usuario, pk=pk)


def _formatear_dias(dias_str):
    """Transforma los índices de días ('0,1,2') en texto legible ('Lu Ma Mi')."""
    if not dias_str: 
        return "Sin definir"
    mapa = {'0': 'Lu', '1': 'Ma', '2': 'Mi', '3': 'Ju', '4': 'Vi', '5': 'Sá', '6': 'Do'}
    return " ".join([mapa.get(d, '') for d in dias_str.split(',')])


def _verificar_horario_laboral(soporte, hora_actual, dia_actual):
    """Determina si un técnico se encuentra dentro de su jornada laboral actual."""
    dias_soporte = soporte.dias_laborales.split(',') if soporte.dias_laborales else []
    if not (soporte.horario_ingreso and soporte.horario_egreso and dia_actual in dias_soporte):
        return False
    
    # Manejo de horarios normales y turnos nocturnos rotativos
    if soporte.horario_ingreso <= soporte.horario_egreso:
        return soporte.horario_ingreso <= hora_actual <= soporte.horario_egreso
    return hora_actual >= soporte.horario_ingreso or hora_actual <= soporte.horario_egreso
# ==========================================
# VISTAS DE AUTENTICACIÓN Y REGISTRO
# ==========================================
def landing_view(request):
    return render(request, 'assistech-landing.html')

def registrar_empresa_view(request):
    if request.method == 'POST':
        form = EmpresaRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(request=request)
            messages.success(
                request, 
                f"¡Empresa registrada con éxito! Te enviamos un correo electrónico a <strong>{user.email}</strong> "
                f"con tu contraseña provisoria aleatoria. Revisá tu bandeja de entrada o Spam."
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

    if request.method == 'POST' and form.is_valid():
        username_or_email = form.cleaned_data['username_or_email']
        password = form.cleaned_data['password']
        filtro = Q(email=username_or_email) if '@' in username_or_email else Q(username=username_or_email)
        try:
            usuario = Usuario.objects.get(filtro)
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
                    error = "La contraseña es incorrecta."            
        except Usuario.DoesNotExist:
            error = "No existe ninguna cuenta con ese email."

    return render(request, 'login.html', {'form': form, 'error': error})

def logout_view(request):
    logout(request)
    return redirect('landing')

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
        elif nueva_pass != confirmar_pass:
            error = "Las contraseñas no coinciden."
        else:
            try:
                validate_password(nueva_pass, user=request.user)
                request.user.set_password(nueva_pass)
                request.user.require_password_change = False
                request.user.save()
                update_session_auth_hash(request, request.user)
                return redirect('dashboard')
            except Exception as e:
                error = e.messages[0] if hasattr(e, 'messages') else str(e)

    return render(request, 'cambiar_contrasenia_obligatorio.html', {'error': error})

# ==========================================
# GESTIÓN DE PERSONAL DE PLATAFORMA Y EMPRESAS
# ==========================================
def crear_platform_admin_view(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        raise PermissionDenied

    if request.method == 'POST':
        form = SuperAdminPlatformAdminCreateForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email_real']
            Usuario.objects.create_user(
                username=email,email=email,password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],last_name=form.cleaned_data['last_name'],
                empresa=None,rol='platform_admin',autorizado=True,)
            messages.success(request, f"Platform Admin {email} creado correctamente.")
            return redirect('dashboard')
    else:
        form = SuperAdminPlatformAdminCreateForm()
    return render(request, 'crear_platform_admin.html', {'form': form})

def crear_usuario_admin_view(request):
    admin_empresa = _obtener_empleado_controlado(request, request.user.pk)

    cantidad_usuarios = Usuario.objects.filter(empresa=request.user.empresa, is_active=True).count()
    plan = request.user.empresa.plan
    if plan == 'GRATIS' and cantidad_usuarios >= 10:
        messages.error(request, "Tu empresa ha alcanzado el límite de 10 usuarios del plan Gratis. <a href='/mi-suscripcion/' class='underline font-bold text-white'>Mejorá tu plan para agregar más equipo</a>.")
        return redirect('dashboard')
    elif plan == 'BASICO' and cantidad_usuarios >= 50:
        messages.error(request, "Tu empresa ha alcanzado el límite de 50 usuarios del plan Básico. <a href='/mi-suscripcion/' class='underline font-bold text-white'>Mejorá tu plan para agregar más equipo</a>.")
        return redirect('dashboard')

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
                        username=email,email=email,password=password_aleatoria,
                        first_name=first_name,last_name=form.cleaned_data['last_name'],
                        telefono=form.cleaned_data['telefono'],empresa=request.user.empresa,
                        rol=form.cleaned_data['rol'],autorizado=True,
                        require_password_change=True
                    )
                    
                    if form.cleaned_data.get('rol') == 'soporte':
                        nuevo_user.horario_ingreso = form.cleaned_data.get('horario_ingreso')
                        nuevo_user.horario_egreso = form.cleaned_data.get('horario_egreso')
                        nuevo_user.dias_laborales = ",".join(form.cleaned_data.get('dias_laborales', []))
                        nuevo_user.save()

                    link_acceso = request.build_absolute_uri('/login/')
                    asunto_empleado = "Te crearon una cuenta en Assistech"
                    mensaje_empleado = f"Hola {first_name},\n\nTe han generado un usuario en Assistech para {request.user.empresa.nombre}.\n\nCredenciales:\n- Acceso: {link_acceso}\n- Usuario: {email}\n- Contraseña provisoria: {password_aleatoria}\n\nDeberás cambiarla al ingresar."

                    send_mail(
                        subject=asunto_empleado,message=mensaje_empleado,
                        from_email='assistech.soporte@gmail.com',recipient_list=[email],fail_silently=False,
                    )
                return redirect('dashboard')
            except Exception:
                messages.error(
                    request,"No se pudo enviar el correo de credenciales. El usuario no fue creado; revisá la configuración de email e intentalo de nuevo."
                )
    else:
        form = AdminUsuarioCreateForm()
    return render(request, 'crear_usuario_admin.html', {'form': form})

def quitar_acceso_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)    
    if empleado.pk != request.user.pk:
        empleado.autorizado = False
        empleado.save()        
    return redirect('dashboard')

def aprobar_usuario_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)    
    empleado.autorizado = True  # Esto es lo que saca la suspensión
    empleado.save()        
    return redirect('dashboard')

def eliminar_usuario_definitivo_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)
    if empleado.pk != request.user.pk:
        empleado.is_active = False  
        empleado.autorizado = False 
        empleado.save()
    return redirect('dashboard')

def confirmar_baja_view(request, pk):
    empleado = _obtener_empleado_controlado(request, pk)
    
    horarios = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]
    dias_semana = [('0', 'Lunes'), ('1', 'Martes'), ('2', 'Miércoles'), ('3', 'Jueves'), ('4', 'Viernes'), ('5', 'Sábado'), ('6', 'Domingo')]
    dias_actuales = empleado.dias_laborales.split(',') if empleado.dias_laborales else []
    
    if request.method == 'POST' and empleado.rol == 'soporte':
        ingreso = request.POST.get('horario_ingreso')
        egreso = request.POST.get('horario_egreso')
        dias_nuevos = request.POST.getlist('dias_laborales')
        if ingreso in horarios and egreso in horarios:
            empleado.horario_ingreso = ingreso
            empleado.horario_egreso = egreso
            empleado.dias_laborales = ",".join(dias_nuevos)
            empleado.save()
            messages.success(request, f'Horarios de {empleado.first_name} actualizados correctamente.')
            return redirect('dashboard')
            
    return render(request, 'confirmar_baja.html', {'empleado': empleado, 'horarios': horarios, 'dias_semana': dias_semana, 'dias_actuales': dias_actuales})

# ==========================================
# SISTEMA DISTRIBUIDO DE DASHBOARDS
# ==========================================

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.require_password_change:
        return redirect('cambiar_contrasenia_obligatorio')

    if request.user.is_superuser:
        return _dashboard_superadmin(request)
    
    dashboards_por_rol = {
        'admin_cliente': _dashboard_admin_cliente,
        'cliente': _dashboard_cliente,
        'soporte': _dashboard_soporte,
        'jefe': dashboard_jefe_soporte,
        'platform_admin': _dashboard_platform_admin,
    }
    controlador_dashboard = dashboards_por_rol.get(request.user.rol)
    if controlador_dashboard:
        return controlador_dashboard(request)
        
    return redirect('landing')

def _dashboard_superadmin (request):
    empresa_id = request.GET.get('empresa')
    tipo_feedback = request.GET.get('tipo', 'todos')
    rating = request.GET.get('rating')
    critico = request.GET.get('critico')
    busqueda = request.GET.get('q', '').strip()

    feedback_servicio = FeedbackService.objects.select_related('ticket','ticket__solicitante','ticket__solicitante__empresa','user','technician',)
    feedback_plataforma = FeedbackPlatform.objects.select_related('ticket','ticket__solicitante','ticket__solicitante__empresa','user',)

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
        filtro_comun = Q(ticket__titulo__icontains=busqueda) | Q(user__username__icontains=busqueda) | Q(user__email__icontains=busqueda) | Q(comment__icontains=busqueda)
        if busqueda.isdigit():
            filtro_comun |= Q(ticket__numero_ticket_empresa=int(busqueda))
            
        feedback_servicio = feedback_servicio.filter(filtro_comun | Q(technician__username__icontains=busqueda) | Q(technician__email__icontains=busqueda))
        feedback_plataforma = feedback_plataforma.filter(filtro_comun | Q(category__icontains=busqueda))

    return render(request, 'dashboard_superadmin.html', {
        'feedback_servicio': feedback_servicio, 'feedback_plataforma': feedback_plataforma,
        'promedio_soporte': feedback_servicio.aggregate(p=Avg('rating'))['p'], 'promedio_plataforma': feedback_plataforma.aggregate(p=Avg('rating'))['p'],
        'feedback_servicio_critico': feedback_servicio.filter(is_critical=True), 'feedback_plataforma_critico': feedback_plataforma.filter(is_critical=True),
        'empresas': Empresa.objects.order_by('nombre'), 'mostrar_soporte': tipo_feedback in ['todos', 'soporte'], 'mostrar_plataforma': tipo_feedback in ['todos', 'plataforma'],
        'filtros': {'empresa': empresa_id or '', 'tipo': tipo_feedback, 'rating': rating or '', 'critico': critico or '', 'q': busqueda}
    })

def _dashboard_admin_cliente(request):
        tickets_qs = InfoTicket.objects.filter(solicitante__empresa=request.user.empresa).order_by('-fecha_creacion')
        hoy = timezone.now()
        tickets_consumidos = tickets_qs.filter(
            fecha_creacion__year=hoy.year,
            fecha_creacion__month=hoy.month
        ).count()
        tickets = _filtrar_tickets_por_plan(request.user.empresa, tickets_qs)
        
        cantidad_usuarios = Usuario.objects.filter(empresa=request.user.empresa, is_active=True).count()
        plan = request.user.empresa.plan
        limite_usuarios_alcanzado = False
        if plan == 'GRATIS' and cantidad_usuarios >= 10:
            limite_usuarios_alcanzado = True
        elif plan == 'BASICO' and cantidad_usuarios >= 50:
            limite_usuarios_alcanzado = True
        
        cant_faq = FAQDeflexion.objects.filter(empresa=request.user.empresa).count()
        
        return render(request, 'dashboard_admin_cliente.html', {
        'tickets': tickets,
        'empleados_activos': Usuario.objects.filter(empresa=request.user.empresa, is_active=True).exclude(pk=request.user.pk),
        'cant_abiertos': tickets.filter(estado='ABIERTO').count(),    
        'cant_proceso': tickets.filter(estado='EN_PROCESO').count(),      
        'cant_resueltos': tickets.filter(estado__in=['RESUELTO']).count(),   
        'cant_autogestionados': cant_faq
        'tickets_consumidos': tickets_consumidos,
        'limite_usuarios_alcanzado': limite_usuarios_alcanzado,
        'cantidad_usuarios': cantidad_usuarios,
    })

def _dashboard_cliente(request):
    tickets = InfoTicket.objects.filter(solicitante=request.user).order_by('-fecha_creacion')
    tickets = _filtrar_tickets_por_plan(request.user.empresa, tickets)
    hoy = timezone.now()
    tickets_consumidos = InfoTicket.objects.filter(
        solicitante__empresa=request.user.empresa,
        fecha_creacion__year=hoy.year,
        fecha_creacion__month=hoy.month
    ).count()
    
    return render(request, 'dashboard_cliente.html', {
        'tickets': tickets,
        'tickets_consumidos': tickets_consumidos
    })

def _dashboard_soporte(request):
        tickets = InfoTicket.objects.filter(asignaciones__soporte=request.user, asignaciones__activo=True,solicitante__empresa=request.user.empresa).distinct()
        tickets = _filtrar_tickets_por_plan(request.user.empresa, tickets)
        hoy = timezone.now().date()
        return render(request, 'dashboard_soporte.html', {
        'tickets': tickets,
        'pendientes': tickets.filter(estado__in=['ABIERTO', 'EN_PROCESO']).count(),
        'urgencia_alta': tickets.filter(estado__in=['ABIERTO', 'EN_PROCESO'], prioridad__in=['ALTA', 'CRITICA', 'alta', 'critica']).count(),
        'resueltos_hoy': InfoTicket.objects.filter(asignaciones__soporte=request.user, estado__in='RESUELTO').filter(Q(fecha_resolucion__date=hoy) | Q(fecha_cierre__date=hoy)).distinct().count()
    })

def dashboard_jefe_soporte (request):
    tickets = InfoTicket.objects.filter(solicitante__empresa=request.user.empresa)
    tickets = _filtrar_tickets_por_plan(request.user.empresa, tickets)
    
    feedback_servicio = FeedbackService.objects.filter(ticket__solicitante__empresa=request.user.empresa)
    feedback_interno = FeedbackSupportInternal.objects.filter(ticket__solicitante__empresa=request.user.empresa)
    
    # 1. Métricas del OKR 2 (Tasa de Deflexión vía FAQ)
    cant_tickets_humanos = tickets.exclude(estado='RESUELTO_FAQ').count()
    cant_deflexiones = tickets.filter(estado='RESUELTO_FAQ').count()
    volumen_total = cant_tickets_humanos + cant_deflexiones
    
    tasa_deflexion = round((cant_deflexiones / volumen_total) * 100, 1) if volumen_total > 0 else 0

    # 2. Filtros de historial según el Plan de la Empresa
    plan = request.user.empresa.plan
    if plan == 'BASICO':
        limite = timezone.now() - timedelta(days=90)
        feedback_servicio = feedback_servicio.filter(created_at__gte=limite)
        feedback_interno = feedback_interno.filter(created_at__gte=limite)
    elif plan == 'PREMIUM':
        limite = timezone.now() - timedelta(days=365)
        feedback_servicio = feedback_servicio.filter(created_at__gte=limite)
        feedback_interno = feedback_interno.filter(created_at__gte=limite)

    # 3. Cálculo de métricas por técnico (Usa el feedback ya filtrado por plan)
    if plan != 'GRATIS':
        metricas_tecnico = feedback_servicio.values(
            'technician__username'
        ).annotate(
            promedio=Avg('rating'),
            cantidad=Count('id')
        ).order_by('technician__username')
    else:
        metricas_tecnico = []
    
    soportes = Usuario.objects.filter(empresa=request.user.empresa, rol='soporte', is_active=True)
    soportes_stats = []
    for soporte in soportes:
        tickets_activos = TicketAsignacion.objects.filter(soporte=soporte, activo=True, ticket__estado__in=['ABIERTO', 'EN_PROCESO']).count()
        tickets_resueltos_qs = InfoTicket.objects.filter(
            asignaciones__soporte=soporte,
            estado__in=['RESUELTO']
        )
        tickets_resueltos = _filtrar_tickets_por_plan(request.user.empresa, tickets_resueltos_qs).distinct().count()
        
        feedback_avg = feedback_servicio.filter(technician=soporte).aggregate(Avg('rating'))['rating__avg']

        soportes_stats.append({
            'soporte': soporte,
            'tickets_activos': tickets_activos,
            'tickets_resueltos': tickets_resueltos,
            'rating_avg': feedback_avg,
            'dias_formateados': _formatear_dias(soporte.dias_laborales),
        })

    return render(request, 'dashboard_jefe_soporte.html', {
        'tickets': tickets,
        'feedback_servicio': feedback_servicio,
        'feedback_interno': feedback_interno,
        'promedio_soporte': feedback_servicio.aggregate(promedio=Avg('rating'))['promedio'],
        'metricas_tecnico': metricas_tecnico,
        'feedback_bajo': feedback_servicio.filter(is_critical=True),
        'soportes_stats': soportes_stats,
        'tasa_deflexion': tasa_deflexion,
        'cant_autogestionados': cant_deflexiones
    })
    
def _dashboard_platform_admin(request):
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

# ==========================================
# GESTIÓN DE SUSCRIPCIÓN
# ==========================================
def mi_suscripcion_view(request):
    if not request.user.is_authenticated or request.user.rol != 'admin_cliente':
        raise PermissionDenied
    
    empresa = request.user.empresa
    cantidad_usuarios = Usuario.objects.filter(empresa=empresa, is_active=True).count()
    
    hoy = timezone.now()
    tickets_consumidos = InfoTicket.objects.filter(
        solicitante__empresa=empresa,
        fecha_creacion__year=hoy.year,
        fecha_creacion__month=hoy.month
    ).count()

    porcentaje_usuarios = 100
    if empresa.plan == 'GRATIS':
        porcentaje_usuarios = min((cantidad_usuarios * 100) // 10, 100)
    elif empresa.plan == 'BASICO':
        porcentaje_usuarios = min((cantidad_usuarios * 100) // 50, 100)
        
    porcentaje_tickets = 100
    if empresa.plan == 'GRATIS':
        porcentaje_tickets = min((tickets_consumidos * 100) // 500, 100)

    return render(request, 'mi_suscripcion.html', {
        'empresa': empresa,
        'cantidad_usuarios': cantidad_usuarios,
        'tickets_consumidos': tickets_consumidos,
        'porcentaje_usuarios': porcentaje_usuarios,
        'porcentaje_tickets': porcentaje_tickets,
    })

def cambiar_suscripcion_view(request):
    if not request.user.is_authenticated or request.user.rol != 'admin_cliente':
        raise PermissionDenied
        
    if request.method == 'POST':
        nuevo_plan = request.POST.get('plan')
        if nuevo_plan in dict(Empresa.PLANES):
            empresa = request.user.empresa
            cantidad_usuarios = Usuario.objects.filter(empresa=empresa, is_active=True).count()
            
            if nuevo_plan == 'GRATIS' and cantidad_usuarios > 10:
                messages.error(request, "No podés bajar al plan Gratis porque superás el límite de 10 usuarios. Eliminá cuentas de tu personal primero.")
                return redirect('mi_suscripcion')
            elif nuevo_plan == 'BASICO' and cantidad_usuarios > 50:
                messages.error(request, "No podés bajar al plan Básico porque superás el límite de 50 usuarios. Eliminá cuentas de tu personal primero.")
                return redirect('mi_suscripcion')
                
            empresa.plan = nuevo_plan
            empresa.save()
            messages.success(request, f"¡Suscripción actualizada al plan {empresa.get_plan_display()} correctamente!")
            
    return redirect('mi_suscripcion')

# ==========================================
# GESTIÓN DE CASOS Y TICKETS
# ==========================================
def crear_ticket(request):
    ticket_creado = False
    
    # KR1: Lista con los 15 problemas técnicos más recurrentes sin tecnicismos
    faqs_top15 = [
        {"id": 1, "titulo": "Mi computadora no enciende o no da video", "solucion": "Verificá que las conexiones de los cables de alimentación estén firmes. Si usas zapatilla, probá conectando directo a la pared. Mantené presionado el botón de encendido por 15 segundos para liberar estática."},
        {"id": 2, "titulo": "No tengo conexión a Internet (Wi-Fi o Cable)", "solucion": "Desconectá el módem de la corriente por 30 segundos y volvelo a conectar. Si estás por cable, desconectá y conectá la ficha RJ45 hasta escuchar el 'clic'."},
        {"id": 3, "titulo": "La plataforma me da error de contraseña o usuario bloqueado", "solucion": "Usá la opción '¿Olvidaste tu contraseña?' en la pantalla de inicio. Recordá que tras 3 intentos fallidos tu usuario puede suspenderse temporalmente por seguridad."},
        {"id": 4, "titulo": "La impresora no imprime o aparece 'Sin conexión'", "solucion": "Apagá y encendé la impresora. Revisá la cola de impresión de tu sistema, cancelá los documentos trabados y verificá que tenga papel y tinta/tóner suficiente."},
        {"id": 5, "titulo": "La aplicación o sistema se quedó congelado", "solucion": "Presioná Ctrl + F5 para forzar la actualización del navegador web borrando la memoria caché activa, o reiniciá la pestaña del navegador."},
        {"id": 6, "titulo": "No me llegan los correos electrónicos de notificación", "solucion": "Revisá las carpetas de 'Spam', 'Correo no deseado' o la pestaña 'Promociones'. Agregá el dominio del sistema a tus remitentes seguros."},
        {"id": 7, "titulo": "Tengo problemas para cargar un archivo o documento", "solucion": "Asegurate de que el archivo no supere el tamaño permitido (generalmente 5MB) y que esté en formatos estándar como PDF, PNG o JPG."},
        {"id": 8, "titulo": "El sistema se ve lento o tarda en procesar las solicitudes", "solucion": "Cerrá otras pestañas o programas pesados abiertos en segundo plano. Comprobá tu velocidad de internet ejecutando un test de velocidad básico."},
        {"id": 9, "titulo": "Falta de permisos para acceder a un módulo específico", "solucion": "Si sos empleado, solicitá al Administrador de tu Empresa que revise tu rol y accesos asignados desde su panel de control."},
        {"id": 10, "titulo": "Error al descargar reportes en formato Excel o PDF", "solucion": "Verificá si tu navegador web tiene bloqueadas las ventanas emergentes (pop-ups). Permitilas para este sitio en la barra de direcciones."},
        {"id": 11, "titulo": "No escucho audio en las reuniones o videos del sistema", "solucion": "Revisá la configuración de salida de audio de tu sistema operativo y asegurate de que los auriculares o parlantes estén seleccionados por defecto."},
        {"id": 12, "titulo": "Los datos del formulario se borraron al enviar", "solucion": "Esto pasa si la sesión expiró por inactividad. Recomendamos copiar textos largos en un bloc de notas antes de enviarlos si vas a tardar mucho tiempo."},
        {"id": 13, "titulo": "El lector de códigos de barras / tarjetas no responde", "solucion": "Desconectá el cable USB del lector, esperá 5 segundos y reconectalo en otro puerto de la computadora para forzar el reconocimiento del dispositivo."},
        {"id": 14, "titulo": "Me aparece un cartel de 'Error 500' en pantalla", "solucion": "Es un inconveniente temporal del servidor del sistema. Esperá un minuto y volvé a intentar la acción presionando el botón de recargar."},
        {"id": 15, "titulo": "Mi perfil muestra información desactualizada", "solucion": "Cerrá tu sesión de usuario por completo, volvé a ingresar con tus credenciales y los cambios se verán reflejados inmediatamente."},
    ]
    
    # 1. Definimos la cantidad de tickets al principio para que siempre exista (GET o POST)
    hoy = timezone.now()
    cantidad_tickets = InfoTicket.objects.filter(
        solicitante__empresa=request.user.empresa,
        fecha_creacion__year=hoy.year,
        fecha_creacion__month=hoy.month
    ).count()
    
    if request.user.empresa.plan == 'GRATIS' and cantidad_tickets >= 500:
        messages.error(request, "Tu empresa ha alcanzado el límite de 500 tickets mensuales del plan Gratis. Solicitale al administrador de tu empresa que mejore la suscripción.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.solicitante = request.user
            ticket.save()
            ticket_creado = True
            form = TicketForm()  
            # Actualizamos la cantidad después de crear uno nuevo
            cantidad_tickets = InfoTicket.objects.filter(
                solicitante__empresa=request.user.empresa,
                fecha_creacion__year=hoy.year,
                fecha_creacion__month=hoy.month
            ).count()
    else:
        form = TicketForm()
    return render(request, 'crear_ticket.html', {'form': form,'ticket_creado': ticket_creado,'faqs': faqs_top15,'tickets_consumidos': cantidad_tickets})

def registrar_deflexion(request):
    """Registra que el usuario solucionó su problema mediante la FAQ (Suma al KPI de Deflexión)"""
    if request.method == 'POST' and request.user.is_authenticated:
        problema = request.POST.get('problema_titulo', 'FAQ General')
        
        titulo_ticket = f"FAQ: {problema}"[:25]

        InfoTicket.objects.create(
            solicitante=request.user,
            titulo=titulo_ticket,
            descripcion=f"El usuario solucionó su inconveniente de manera autónoma usando la enciclopedia de soluciones rápidas. Pregunta consultada: {problema}.",
            categoria='OTRO',
            estado='RESUELTO_FAQ',
            solucion_resumen='Caso resuelto exitosamente por el usuario aplicando la guía de la Enciclopedia Interactiva.',
            fecha_resolucion=timezone.now()
        )
        
        # Guardamos la métrica
        FAQDeflexion.objects.create(
            usuario=request.user,
            empresa=request.user.empresa,
            problema_consultado=problema
        )
        
        return redirect('dashboard')
        
    raise PermissionDenied

def detalle_ticket_view(request, pk):
    ticket = _get_ticket_con_control_empresa(request, pk)
    if request.user.rol == 'cliente' and ticket.solicitante != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        if request.user.rol == 'cliente':
            raise PermissionDenied
        texto = request.POST.get('comentario')
        if texto:
            TicketComentario.objects.create(ticket=ticket, usuario=request.user, comentario=texto)
            return redirect('detalle_ticket', pk=pk)

    puede_dejar_feedback_usuario = (request.user.rol == 'cliente' and ticket.solicitante == request.user and ticket.estado in ['RESUELTO'] and not ticket.feedback_servicio.exists() and not ticket.feedback_plataforma.exists())
    puede_dejar_feedback_tecnico = (
        request.user.rol == 'soporte'and ticket.estado in ['RESUELTO']
        and ticket.asignaciones.filter(soporte=request.user, activo=True).exists()
        and not ticket.feedback_interno_soporte.filter(technician=request.user).exists()
    )

    return render(request, 'detalle_ticket.html', {
        'ticket': ticket,'comentarios': ticket.comentarios.all().order_by('fecha_comentario'),
        'estados_ticket': InfoTicket.ESTADO,'user_feedback_form': UserFeedbackForm(),'technician_feedback_form': TechnicianFeedbackForm(),
        'show_user_feedback_modal': puede_dejar_feedback_usuario,'show_technician_feedback_modal': puede_dejar_feedback_tecnico,
    })

def eliminar_ticket(request, pk):
    ticket = get_object_or_404(InfoTicket, pk=pk)
    if request.user.rol != 'cliente' or ticket.solicitante != request.user:
        raise PermissionDenied
    ticket.delete()
    return redirect('dashboard')

def actualizar_estado(request, pk):
    ticket = _get_ticket_con_control_empresa(request, pk)
    estado_anterior = ticket.estado
    nuevo_estado = request.POST.get('nuevo_estado')
    
    if nuevo_estado not in dict(InfoTicket.ESTADO):
        raise PermissionDenied

    if estado_anterior != nuevo_estado:
        ticket.estado = nuevo_estado
        if nuevo_estado == ['RESUELTO', 'RESUELTO_FAQ']:
            ticket.fecha_resolucion = timezone.now()
        ticket.save()
        
        TicketHistorial.objects.create(
            ticket=ticket,estado_anterior=estado_anterior,estado_nuevo=nuevo_estado,
            realizado_por=request.user,observacion="Cambio de estado desde el panel de control"
        )
    return redirect('detalle_ticket', pk=pk)

def cambiar_prioridad(request, pk):
    if request.user.rol == 'cliente':
        raise PermissionDenied    
    ticket = _get_ticket_con_control_empresa(request, pk)
    
    if ticket.estado in ['RESUELTO', 'RESUELTO_FAQ']:
        messages.error(request, "No se puede cambiar la prioridad de un ticket finalizado.")
        return redirect('dashboard')
    
    ticket.prioridad = request.POST.get('prioridad')
    ticket.save()
    return redirect('dashboard')

# ==========================================
# ENVÍO DE FEEDBACKS
# ==========================================
def guardar_feedback_usuario(request, pk):
    if request.method != 'POST':
        raise PermissionDenied
    ticket = _get_ticket_con_control_empresa(request, pk)

    if request.user.rol != 'cliente' or ticket.solicitante != request.user or ticket.estado not in ['RESUELTO']:
        raise PermissionDenied
    
    form = UserFeedbackForm(request.POST)
    if form.is_valid():
        asignacion = ticket.asignaciones.filter(activo=True).first() or ticket.asignaciones.first()
        if form.cleaned_data['feedback_type'] == 'servicio':
            FeedbackService.objects.get_or_create(
                ticket=ticket,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'], 
                    'comment': form.cleaned_data['comment']
                }
            )

    return redirect('detalle_ticket', pk=pk)

def guardar_feedback_plataforma_general(request):
    if request.method != 'POST':
        raise PermissionDenied

    form = FeedbackPlatformForm(request.POST) 
    
    if form.is_valid():
        FeedbackPlatform.objects.create(
            ticket=None,
            user=request.user,
            rating=form.cleaned_data['rating'],
            comment=form.cleaned_data['comment'],
            category=form.cleaned_data.get('platform_category', form.cleaned_data.get('category')), 
        )
    return redirect('dashboard')

def guardar_feedback_tecnico(request, pk):
    if request.method != 'POST' or request.user.rol != 'soporte':
        raise PermissionDenied
    ticket = _get_ticket_con_control_empresa(request, pk)

    form = TechnicianFeedbackForm(request.POST)
    if form.is_valid() and not ticket.feedback_interno_soporte.filter(technician=request.user).exists():
        feedback = form.save(commit=False)
        feedback.ticket = ticket
        feedback.technician = request.user
        feedback.save()

    return redirect('detalle_ticket', pk=pk)

# ==========================================
# SISTEMA DE ASIGNACIÓN 
# ==========================================
def asignar_ticket_view(request, pk):
    if not request.user.is_authenticated or request.user.rol != 'jefe':
        raise PermissionDenied

    ticket = _get_ticket_con_control_empresa(request, pk)
    
    if ticket.estado in ['RESUELTO', 'RESUELTO_FAQ']:
        messages.error(request, "No se puede modificar la asignación de un ticket ya resuelto.")
        return redirect('dashboard')
    
    soportes = Usuario.objects.filter(empresa=request.user.empresa, rol='soporte', is_active=True, autorizado=True)
    hora_actual = timezone.now().strftime("%H:%M")
    dia_actual = str(timezone.now().weekday())

    soportes_info = []
    for soporte in soportes:
        tickets_activos = TicketAsignacion.objects.filter(soporte=soporte, activo=True, ticket__estado__in=['ABIERTO', 'EN_PROCESO']).count()
        esta_trabajando = _verificar_horario_laboral(soporte, hora_actual, dia_actual)
        
        soportes_info.append({
            'soporte': soporte, 'tickets_activos': tickets_activos, 'esta_trabajando': esta_trabajando,
            'puede_asignar': tickets_activos < 3 and esta_trabajando,
            'es_asignado_actual': ticket.asignaciones.filter(soporte=soporte, activo=True).exists(),
            'dias_formateados': _formatear_dias(soporte.dias_laborales),
        })

    if request.method == 'POST':
        soporte_id = request.POST.get('soporte_id')

        if request.POST.get('action') == 'deassign' and soporte_id:
            soporte_a_desasignar = get_object_or_404(Usuario, pk=soporte_id, empresa=request.user.empresa, rol='soporte')
            TicketAsignacion.objects.filter(ticket=ticket, soporte=soporte_a_desasignar, activo=True).update(activo=False)
            messages.success(request, f'Se desasignó al técnico {soporte_a_desasignar.get_full_name()}.')
            return redirect('asignar_ticket', pk=pk)

        if soporte_id:
            soporte_seleccionado = get_object_or_404(Usuario, pk=soporte_id, empresa=request.user.empresa, rol='soporte')
            trabaja_ahora = _verificar_horario_laboral(soporte_seleccionado, hora_actual, dia_actual)
            tickets_activos_pre = TicketAsignacion.objects.filter(soporte=soporte_seleccionado, activo=True, ticket__estado__in=['ABIERTO', 'EN_PROCESO']).count()
                        
            TicketAsignacion.objects.filter(ticket=ticket, activo=True).update(activo=False)
            TicketAsignacion.objects.create(ticket=ticket, soporte=soporte_seleccionado, asignado_por=request.user, activo=True)
            messages.success(request, f'Ticket asignado a {soporte_seleccionado.get_full_name()} correctamente.')
            
            if not trabaja_ahora:
                messages.warning(request, 'Nota: El técnico fue asignado a pesar de estar fuera de su horario laboral.')
            if tickets_activos_pre >= 3:
                messages.warning(request, 'Nota: El técnico asignado superó el límite recomendado de 3 tickets en progreso.')
                
            return redirect('dashboard')

    return render(request, 'asignar_ticket.html', {'ticket': ticket, 'soportes_info': soportes_info})