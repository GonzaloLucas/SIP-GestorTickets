from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario, Empresa

admin.site.register(Usuario, UserAdmin)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id_empresa', 'nombre', 'cuil', 'plan', 'fecha_creacion')
    search_fields = ('nombre', 'cuil')
    try:
        admin.site.unregister(Usuario)
    except admin.sites.NotRegistered:
        pass

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'empresa', 'rol', 'autorizado')
    list_filter = ('rol', 'autorizado')
    search_fields = ('email', 'first_name', 'last_name')