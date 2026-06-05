from django.urls import path
from . import views 

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('register_empresa/', views.registrar_empresa_view, name='register_empresa'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    path('usuario/<int:pk>/aprobar/', views.aprobar_usuario_view, name='aprobar_usuario'), 
    path('usuario/<int:pk>/eliminar-definitivo/', views.eliminar_usuario_definitivo_view, name='eliminar_usuario_definitivo'),
    
    path('usuario/nuevo-admin/', views.crear_usuario_admin_view, name='crear_usuario_admin'),
    path('cambiar-contrasenia-obligatorio/', views.cambiar_contrasenia_obligatorio_view, name='cambiar_contrasenia_obligatorio'),
    
    path('ticket/nuevo/', views.crear_ticket, name='crear_ticket'),
    path('ticket/<int:pk>/', views.detalle_ticket_view, name='detalle_ticket'),
    path('ticket/<int:pk>/eliminar/', views.eliminar_ticket, name='eliminar_ticket'),
    path('ticket/<int:pk>/estado/', views.actualizar_estado, name='actualizar_estado'),
    path('ticket/<int:pk>/cambiar-prioridad/', views.cambiar_prioridad, name='cambiar_prioridad'),
    path('usuario/<int:pk>/quitar-acceso/', views.quitar_acceso_view, name='quitar_acceso'),
    path('usuario/<int:pk>/confirmar-baja/', views.confirmar_baja_view, name='confirmar_baja'),
]
