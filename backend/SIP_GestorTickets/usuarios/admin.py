from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .modelos import Usuario


admin.site.register(Usuario, UserAdmin)
