from django.db import models

class Cliente(models.Model):
    cliente_id = models.AutoField(primary_key=True)
    username_cliente = models.CharField(max_length=150, unique=True)
    email_cliente = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    empresa = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username_cliente

class Soporte(models.Model):
    soporte_id = models.AutoField(primary_key=True)
    username_soporte = models.CharField(max_length=150, unique=True)
    email_soporte = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    empresa = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username_soporte

class JefeSoporte(models.Model):
    jefe_soporte_id = models.AutoField(primary_key=True)
    username_jefe_soporte = models.CharField(max_length=150, unique=True)
    email_jefe_soporte = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    empresa = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username_jefe_soporte
