from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Empresa, FeedbackPlatform, FeedbackService, FeedbackSupportInternal, Usuario

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


@admin.register(FeedbackService)
class FeedbackServiceAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'technician', 'rating', 'is_critical', 'created_at')
    list_filter = ('rating', 'is_critical', 'created_at')
    search_fields = ('ticket__titulo', 'user__email', 'technician__email')


@admin.register(FeedbackPlatform)
class FeedbackPlatformAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'category', 'rating', 'is_critical', 'created_at')
    list_filter = ('category', 'rating', 'is_critical', 'created_at')
    search_fields = ('ticket__titulo', 'user__email', 'comment')


@admin.register(FeedbackSupportInternal)
class FeedbackSupportInternalAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'technician', 'difficulty', 'created_at')
    list_filter = ('difficulty', 'created_at')
    search_fields = ('ticket__titulo', 'technician__email', 'comment', 'problems_found')
