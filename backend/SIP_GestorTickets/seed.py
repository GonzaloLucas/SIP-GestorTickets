import os
import django

# 1. ESTO TIENE QUE IR ARRIBA DE TODO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SIP_GestorTickets.settings')
django.setup()

import random
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from usuarios.models import (
    Empresa, InfoTicket, TicketAsignacion, TicketComentario,
    FeedbackService, FeedbackPlatform, FeedbackSupportInternal, FAQDeflexion
)

Usuario = get_user_model()

print('🚀 Iniciando inyección aditiva blindada... (Sin borrar nada)')

password_generica = "assistech"

# 🏢 1. CONFIGURACIÓN DE EMPRESAS
empresas_config = [
    {'nombre': 'Banco Mango', 'plan': 'PREMIUM', 'slug': 'bancomango'},
    {'nombre': 'UADE Tech Corp', 'plan': 'PREMIUM', 'slug': 'uade'},
    {'nombre': 'Coto C.I.C.S.A', 'plan': 'BASICO', 'slug': 'coto'},
    {'nombre': 'Pyme Gratis SRL', 'plan': 'GRATIS', 'slug': 'pymegratis'},
]

nombres_pila = ['Diego', 'Florencia', 'Martín', 'Camila', 'Gonzalo', 'Agustina', 'Facundo', 'Sofía', 'Lautaro', 'Valentina', 'Nicolás', 'Matías', 'Lucas', 'Mariano', 'Esteban', 'Victoria', 'Juan', 'Andrés', 'Belén', 'Clara']
apellidos_pool = ['Gómez', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Díaz', 'Álvarez', 'Romero', 'Sánchez', 'Pérez', 'Torres', 'Ramírez', 'Benítez', 'Medina', 'Herrera']

titulos_por_cat = {
    'SOFTWARE': ["Caída de Home Banking transaccional", "Error 500 en Pasarela de Cobros", "Fallo en API de clearing bancario", "Crash en módulo de transferencias externas"],
    'HARDWARE': ["Notebook de Tesorería no enciende", "Fallo de memoria RAM en cajero automático", "Terminal financiera tildada", "Sobrecalentamiento de rack en servidor"],
    'RED': ["Corte total enlace de Fibra en Casa Central", "Fallo en VPN de contingencia sucursales", "Inestabilidad en la red de cajas rápidas", "Conflicto de IP duplicadas en terminales"],
    'ACCESO': ["Bloqueo de token corporativo", "Permisos denegados en base SQL de saldos", "Falta acceso a carpetas de auditoría", "Solicitud urgente de credenciales de red"],
    'SEGURIDAD': ["Alerta de intento de phishing detectado", "Bloqueo preventivo por IP sospechosa", "Análisis de malware en terminal contable", "Contraseña del sistema bloqueada"],
    'PERIFERICOS': ["Impresora de comprobantes trabada en cajas", "Lector de tarjetas magnéticas dañado", "Monitor de atención comercial parpadea", "Fallo de sensor biométrico"],
    'BASE_DATOS': ["Query indexada bloquea tabla transaccional", "Fallo de réplica en cluster Oracle principal", "Saturación crítica en pool de conexiones", "Corrupción de logs de auditoría transaccional"],
    'OTRO': ["Revisión de hardware para recambio", "Consulta de licencias Office365", "Mudanza de terminales de oficina", "Actualización general de políticas de IT"]
}

comentarios_pool = [
    "Se verificó el canal transaccional y el firewall responde de forma exitosa.",
    "Iniciamos el protocolo de mitigación preventivo para la mesa operativa afectada.",
    "Dejo constancia de que se actualizó el firmware periférico y el error cesó.",
    "Se coordinó la solución definitiva mediante el equipo técnico de base de datos.",
    "Se modificaron los permisos locales y se realizaron las pruebas transaccionales."
]

estados = ['ABIERTO', 'EN_PROCESO', 'RESUELTO', 'RESUELTO_FAQ']
prioridades = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA']
hoy = timezone.now()

contadores = {'tickets': 0, 'feedbacks': 0, 'deflexiones': 0}

# 🔄 2. BUCLE PRINCIPAL MULTI-TENANT
for conf in empresas_config:
    # 🛡️ SOLUCIÓN EVITAR CRASH: Filtrar y tomar la primera que coincida
    empresa = Empresa.objects.filter(nombre=conf['nombre']).first()
    if not empresa:
        empresa = Empresa.objects.create(
            nombre=conf['nombre'],
            plan=conf['plan'],
            domicilio='Av. Corrientes 1200, CABA',
            pais='Argentina'
        )
    
    print(f"🏢 Procesando de forma aditiva: {empresa.nombre}")

    # ✉️ A. Admin de la Empresa
    admin_user, _ = Usuario.objects.get_or_create(
        username=f"admin_{conf['slug']}",
        defaults={'email': f"admin@{conf['slug']}.com", 'rol': 'admin_cliente', 'empresa': empresa, 'first_name': random.choice(nombres_pila), 'last_name': random.choice(apellidos_pool), 'require_password_change': False}
    )
    if _: admin_user.set_password(password_generica); admin_user.save()

    # ✉️ B. Jefe de Soporte
    jefe_user, _ = Usuario.objects.get_or_create(
        username=f"jefe_{conf['slug']}",
        defaults={'email': f"jefesoporte_1@{conf['slug']}.com", 'rol': 'jefe', 'empresa': empresa, 'first_name': random.choice(nombres_pila), 'last_name': random.choice(apellidos_pool), 'require_password_change': False}
    )
    if _: jefe_user.set_password(password_generica); jefe_user.save()

    # Asegurar que el admin principal de la captura se llame Marcelo
    if conf['slug'] == 'bancomango':
        admin_user.first_name = "Marcelo"
        admin_user.save()

    # ✉️ C. Soportes Técnicos Aditivos Secuenciales (Del 20 al 50 para Banco Mango)
    lista_soportes = []
    rango_soportes = range(20, 51) if conf['slug'] == 'bancomango' else range(1, 9)
    
    for i in rango_soportes:
        sop_name = random.choice(nombres_pila)
        sop_user, creado = Usuario.objects.get_or_create(
            username=f"soporte_{sop_name.lower()}_{conf['slug']}_{i}",
            defaults={'email': f"soporte_{i}@{conf['slug']}.com", 'rol': 'soporte', 'empresa': empresa, 'first_name': sop_name, 'last_name': random.choice(apellidos_pool), 'require_password_change': False, 'dias_laborales': 'L,M,X,J,V'}
        )
        if creado:
            sop_user.set_password(password_generica); sop_user.save()
        lista_soportes.append(sop_user)

    # ✉️ D. Clientes/Solicitantes Aditivos Secuenciales (Del 30 al 90 para Banco Mango)
    lista_clientes = []
    rango_clientes = range(30, 91) if conf['slug'] == 'bancomango' else range(1, 16)
    
    for i in rango_clientes:
        cli_name = random.choice(nombres_pila)
        cli_user, creado = Usuario.objects.get_or_create(
            username=f"cliente_{cli_name.lower()}_{conf['slug']}_{i}",
            defaults={'email': f"cliente_{i}@{conf['slug']}.com", 'rol': 'cliente', 'empresa': empresa, 'first_name': cli_name, 'last_name': random.choice(apellidos_pool), 'require_password_change': False}
        )
        if creado:
            cli_user.set_password(password_generica); cli_user.save()
        lista_clientes.append(cli_user)

    # Asegurar contraseñas "assistech" globales
    for u in Usuario.objects.filter(empresa=empresa):
        if u.password == "" or u.check_password(password_generica) is False:
            u.set_password(password_generica)
            u.save()

    # E. FAQ DEFLEXIONES (Últimos 11 días)
    cant_deflexiones = 55 if conf['slug'] == 'bancomango' else 25
    for d_idx in range(cant_deflexiones):
        contadores['deflexiones'] += 1
        cat_random = random.choice(list(titulos_por_cat.keys()))
        prob_str = random.choice(titulos_por_cat[cat_random])
        dias_atras_def = random.randint(0, 11)
        fecha_def = hoy - timedelta(days=dias_atras_def, hours=random.randint(1, 12))
        
        deflexion = FAQDeflexion.objects.create(
            usuario=random.choice(lista_clientes),
            empresa=empresa,
            problema_consultado=f"FAQ Auto: {prob_str}"
        )
        FAQDeflexion.objects.filter(pk=deflexion.pk).update(fecha=fecha_def)

    # F. GENERACIÓN DE TICKETS CONTROLADOS
    cant_tickets = 220 if conf['slug'] == 'bancomango' else 40
    
    for t_idx in range(1, cant_tickets + 1):
        contadores['tickets'] += 1
        cat_random = random.choice(list(titulos_por_cat.keys()))
        titulo_random = random.choice(titulos_por_cat[cat_random])
        prioridad_random = random.choice(prioridades)
        cliente_random = random.choice(lista_clientes)
        estado_random = random.choice(estados)

        dias_atras_ticket = random.randint(0, 11)
        fecha_creacion_ficticia = hoy - timedelta(days=dias_atras_ticket, hours=random.randint(1, 23), minutes=random.randint(0, 59))

        ticket = InfoTicket.objects.create(
            titulo=f"{titulo_random} (Carga Estrés #{t_idx})",
            descripcion=f"Incidente transaccional masivo inyectado de forma puramente aditiva para pruebas de estrés y SLA en {empresa.nombre}.",
            categoria=cat_random,
            estado=estado_random,
            prioridad=prioridad_random,
            solicitante=cliente_random
        )

        TicketComentario.objects.create(ticket=ticket, usuario=random.choice(lista_soportes), comentario=random.choice(comentarios_pool))

        fecha_res_final = None
        solucion_txt = ""

        if estado_random in ['EN_PROCESO', 'RESUELTO']:
            soporte_seleccionado = random.choice(lista_soportes)
            TicketAsignacion.objects.create(ticket=ticket, soporte=soporte_seleccionado, activo=True, asignado_por=jefe_user)

            if estado_random == 'RESUELTO':
                limite_max_segundos = min(3 * 86400, (hoy - fecha_creacion_ficticia).total_seconds())
                limite_min_segundos = 6 * 3600

                if limite_max_segundos > limite_min_segundos:
                    segundos_duracion = random.randint(int(limite_min_segundos), int(limite_max_segundos))
                else:
                    segundos_duracion = int(limite_max_segundos)

                fecha_res_final = fecha_creacion_ficticia + timedelta(seconds=segundos_duracion)
                solucion_txt = "Mitigado exitosamente dentro del bloque estipulado de SLA corporativo."

                contadores['feedbacks'] += 1
                rating_servicio = random.choice([5, 5, 5, 4, 4, 3, 2, 1])
                FeedbackService.objects.create(ticket=ticket, user=cliente_random, technician=soporte_seleccionado, rating=rating_servicio, comment="SLA validado.")
                
                cat_plat = random.choice(['BUG', 'MEJORA', 'UX_UI', 'RENDIMIENTO', 'FUNCIONALIDAD'])
                FeedbackPlatform.objects.create(ticket=ticket, user=cliente_random, category=cat_plat, rating=random.randint(3, 5), comment="Rendimiento UX ok.")

                dif_plat = random.choice(['BAJA', 'MEDIA', 'ALTA'])
                FeedbackSupportInternal.objects.create(ticket=ticket, technician=soporte_seleccionado, difficulty=dif_plat, problems_found="SLA cumplido.")
        
        elif estado_random == 'RESUELTO_FAQ':
            fecha_res_final = fecha_creacion_ficticia
            solucion_txt = "Solución auto-gestionada mediante FAQ corporativo."

        elif estado_random == 'ABIERTO':
            if random.random() > 0.5:
                TicketAsignacion.objects.create(ticket=ticket, soporte=random.choice(lista_soportes), activo=True, asignado_por=jefe_user)

        InfoTicket.objects.filter(pk=ticket.pk).update(
            fecha_creacion=fecha_creacion_ficticia,
            fecha_actualizacion=fecha_creacion_ficticia,
            fecha_resolucion=fecha_res_final,
            solucion_resumen=solucion_txt
        )

print('\n🎉 ¡INYECCIÓN ADITIVA COMPLETADA EXITOSAMENTE SIN ERRORES!')