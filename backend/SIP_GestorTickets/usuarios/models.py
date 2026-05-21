from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):

    ROLES = (
        ('cliente', 'Cliente'),
        ('soporte', 'Soporte'),
        ('jefe', 'JefeSoporte'),
    )

    empresa = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    rol = models.CharField(
        max_length=20,
        choices=ROLES
    )

    def __str__(self):
        return self.username
