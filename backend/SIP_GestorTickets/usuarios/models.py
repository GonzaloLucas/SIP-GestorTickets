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
        ('CERRADO', 'Cerrado'),
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
        if not self.pk: # Solo si el ticket es NUEVO
            # Buscamos el número más alto de ticket que tenga la empresa de este solicitante
            ultimo_numero = InfoTicket.objects.filter(
                solicitante__empresa=self.solicitante.empresa
            ).aggregate(models.Max('numero_ticket_empresa'))['numero_ticket_empresa__max']
            
            if ultimo_numero is not None:
                self.numero_ticket_empresa = ultimo_numero + 1
            else:
                self.numero_ticket_empresa = 1 # Si es el primero de la empresa, arranca en 1
                
        super().save(*args, **kwargs)

# ==========================================
# MODELO: HISTORIAL TICKET
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

# ==========================================
# MODELO: COMENTARIO TICKET
# ==========================================
class TicketComentario(models.Model):
    id_comentario = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket,on_delete=models.CASCADE,related_name='comentarios')
    usuario = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='comentarios_realizados')
    comentario = models.TextField()
    fecha_comentario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario #{self.id_comentario} - Ticket #{self.ticket.id_ticket}"


# ==========================================
# MODELO: ASIGNACION TICKET
# ==========================================
class TicketAsignacion(models.Model):
    id_asignacion = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(InfoTicket,on_delete=models.CASCADE,related_name='asignaciones')
    soporte = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='tickets_asignados',limit_choices_to={'rol': 'soporte'})
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(Usuario,on_delete=models.PROTECT,related_name='asignaciones_realizadas')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Asignacion #{self.id_asignacion} - Ticket #{self.ticket.id_ticket}"