from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    
    path('ticket/nuevo/', views.crear_ticket, name='crear_ticket'),
    path('ticket/<int:pk>/', views.detalle_ticket_view, name='detalle_ticket'),
    path('ticket/<int:pk>/estado/', views.actualizar_estado, name='actualizar_estado'),
]