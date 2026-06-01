from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    ROLES = (
        ('cliente', 'Cliente'),
        ('soporte', 'Soporte'),
        ('jefe', 'JefeSoporte'),
    )

    empresa = models.CharField(max_length=255, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROLES)

    def __str__(self):
        return self.username


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
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=255)
    estado = models.CharField(max_length=20, choices=ESTADO, default='ABIERTO')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD, default='BAJA')
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
        return f"#{self.id_ticket} - {self.titulo}"


class TicketHistorial(models.Model):

    ESTADO = (
        ('ABIERTO', 'Abierto'),
        ('EN_PROCESO', 'En proceso'),
        ('RESUELTO', 'Resuelto'),
        ('CERRADO', 'Cerrado'),
    )

    id_historial = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(
        InfoTicket,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    estado_anterior = models.CharField(max_length=20, choices=ESTADO)
    estado_nuevo = models.CharField(max_length=20, choices=ESTADO)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    realizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='cambios_realizados'
    )
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Historial #{self.id_historial} - Ticket #{self.ticket.id_ticket}"


class TicketComentario(models.Model):

    id_comentario = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(
        InfoTicket,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='comentarios_realizados'
    )
    comentario = models.TextField()
    fecha_comentario = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario #{self.id_comentario} - Ticket #{self.ticket.id_ticket}"


class TicketAsignacion(models.Model):

    id_asignacion = models.AutoField(primary_key=True)
    ticket = models.ForeignKey(
        InfoTicket,
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    soporte = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='tickets_asignados',
        limit_choices_to={'rol': 'soporte'}
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='asignaciones_realizadas'
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Asignacion #{self.id_asignacion} - Ticket #{self.ticket.id_ticket}"