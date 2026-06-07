from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario, Empresa


admin.site.register(Usuario, UserAdmin)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Esto define las columnas que se van a ver en el listado web
    list_display = ('id_empresa', 'nombre', 'cuil', 'plan', 'fecha_creacion')
    # Esto te agrega una barra de búsqueda por nombre o CUIL
    search_fields = ('nombre', 'cuil')


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'empresa', 'rol', 'autorizado')
    list_filter = ('rol', 'autorizado')
    search_fields = ('email', 'first_name', 'last_name')