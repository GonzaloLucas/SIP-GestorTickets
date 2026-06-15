from django.contrib.auth.models import AbstractUser
from django.db import models

# ==========================================
# MODELO: EMPRESA
# ==========================================
class Empresa(models.Model):
    PLANES = (
        ('BASICO', 'Básico (Gratis)'),
        ('ESTANDAR', 'Estándar'),
        ('PREMIUM', 'Premium'),
    )
    id_empresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    cuil = models.CharField(max_length=11, unique=True, null=True, blank=True) 
    plan = models.CharField(max_length=20, choices=PLANES, default='BASICO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} (Plan: {self.get_plan_display()})"
    
# ==========================================
# MODELO: USUARIO
# ==========================================
class Usuario(AbstractUser):
    ROLES = (
        ('admin_cliente', 'Administrador de Empresa'),
        ('cliente', 'Cliente'),
        ('soporte', 'Soporte'),
        ('jefe', 'Jefe de Soporte'),
        ('platform_admin', 'Administrador de Plataforma'),
    )
    empresa = models.ForeignKey(
        Empresa, on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='usuarios'
    )    
    rol = models.CharField(max_length=20, choices=ROLES)
    autorizado = models.BooleanField(default=True) 
    telefono = models.CharField(max_length=20, blank=True, null=True)
    horario_ingreso = models.CharField(max_length=5, blank=True, null=True)
    horario_egreso = models.CharField(max_length=5, blank=True, null=True)
    dias_laborales = models.CharField(max_length=50, blank=True, null=True)
    require_password_change = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
    
# ==========================================
# MODELO: INFO TICKET
# ==========================================
class InfoTicket(models.Model):
    ESTADO = (
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En proceso'),
        ('RESUELTO', 'Resuelto'),
        ('RESUELTO_FAQ', 'Resuelto vía FAQ'),
    )

    PRIORIDAD = (
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    )

    CATEGORIAS = (
        ('SOFTWARE', 'Software'),
        ('HARDWARE', 'Hardware'),
        ('RED', 'Red / Conectividad'),
        ('ACCESO', 'Acceso / Permisos'),
        ('SEGURIDAD', 'Seguridad'),
        ('PERIFERICOS', 'Periféricos'),
        ('BASE_DATOS', 'Base de datos'),
        ('OTRO', 'Otro'),
    )

    id_ticket = models.AutoField(primary_key=True)
    numero_ticket_empresa = models.PositiveIntegerField(null=True, blank=True)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADO, default='ABIERTO')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD, null=True, blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    
    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='tickets_creados',
        limit_choices_to={'rol': 'cliente'}
    )
    solucion_resumen = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"#{self.numero_ticket_empresa} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.pk: 
            ultimo_numero = InfoTicket.objects.filter(
                solicitante__empresa=self.solicitante.empresa
            ).aggregate(models.Max('numero_ticket_empresa'))['numero_ticket_empresa__max']
            
            if ultimo_numero is not None:
                self.numero_ticket_empresa = ultimo_numero + 1
            else:
                self.numero_ticket_empresa = 1 
                
        super().save(*args, **kwargs)

# ==========================================
# MODELOS AUXILIARES DE TICKETS
# ==========================================
class TicketHistorial(models.Model):
    id_historial = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket,on_delete=models.CASCADE,related_name='historial')

    estado_anterior = models.CharField(max_length=20, choices=InfoTicket.ESTADO)
    estado_nuevo = models.CharField(max_length=20, choices=InfoTicket.ESTADO)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    realizado_por = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='cambios_realizados')
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Historial #{self.id_historial} - Ticket #{self.ticket.id_ticket}"

class TicketComentario(models.Model):
    id_comentario = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket,on_delete=models.CASCADE,related_name='comentarios')
    usuario = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='comentarios_realizados')
    comentario = models.TextField()
    fecha_comentario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario #{self.id_comentario} - Ticket #{self.ticket.id_ticket}"

class TicketAsignacion(models.Model):
    id_asignacion = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket,on_delete=models.CASCADE,related_name='asignaciones')
    soporte = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='tickets_asignados',limit_choices_to={'rol': 'soporte'})
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='asignaciones_realizadas')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Asignacion #{self.id_asignacion} - Ticket #{self.ticket.id_ticket}"


# ==========================================
# MODELOS ABSTRACTOS DE FEEDBACK
# ==========================================
class BaseFeedback(models.Model):
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

class BaseCustomerFeedback(BaseFeedback):
    rating = models.PositiveSmallIntegerField()
    is_critical = models.BooleanField(default=False)

    class Meta(BaseFeedback.Meta):
        abstract = True

    def save(self, *args, **kwargs):
        self.is_critical = self.rating <= 2
        super().save(*args, **kwargs)
               
# ==========================================
# MODELOS DE FEEDBACK IMPLEMENTADOS
# ==========================================
class FeedbackService(BaseCustomerFeedback):
    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket, on_delete=models.CASCADE, related_name='feedback_servicio')
    user = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='feedback_servicio_realizado')
    technician = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='feedback_servicio_recibido',
        limit_choices_to={'rol': 'soporte'},
        blank=True,
        null=True
    )
    class Meta:
        db_table = 'feedback_service'

    def __str__(self):
        return f"Feedback servicio ticket #{self.ticket.id_ticket} - {self.rating}/5"


class FeedbackPlatform(BaseCustomerFeedback):
    CATEGORIAS = (
        ('BUG', 'Bug'),
        ('MEJORA', 'Sugerencia de mejora'),
        ('UX_UI', 'UX/UI'),
        ('RENDIMIENTO', 'Rendimiento'),
        ('FUNCIONALIDAD', 'Funcionalidad faltante'),
        ('OTRO', 'Otro'),
    )

    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket, on_delete=models.CASCADE, related_name='feedback_plataforma')
    user = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='feedback_plataforma_realizado')
    category = models.CharField(max_length=20, choices=CATEGORIAS, default='OTRO')

    class Meta:
        db_table = 'feedback_platform'

    def __str__(self):
        return f"Feedback plataforma ticket #{self.ticket.id_ticket} - {self.rating}/5"

class FeedbackSupportInternal(BaseFeedback):
    DIFICULTADES = (
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
    )

    id = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket, on_delete=models.CASCADE, related_name='feedback_interno_soporte')
    technician = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='feedback_interno_realizado')
    difficulty = models.CharField(max_length=10, choices=DIFICULTADES)
    problems_found = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'feedback_support_internal'

    def __str__(self):
        return f"Feedback interno ticket #{self.ticket.id_ticket} - {self.get_difficulty_display()}"
    
    
# ==========================================
# MODELO: CONTROL DE AUTOGESTIÓN (OKR 2)
# ==========================================
class FAQDeflexion(models.Model):
    id_deflexion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='deflexiones')
    fecha = models.DateTimeField(auto_now_add=True)
    problema_consultado = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Deflexión exitosa - {self.empresa.nombre} ({self.fecha.strftime('%d/%m/%Y')})"