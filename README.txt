EL run.py SIRVE PARA CORRER LA PAGINA WEB DIRECTAMENTE. 
ES EL UNICO EJECUTABLE QUE SE TIENE QUE EJECTURAR.

Los __init__.py se usan a modo de reconocimiento.
asgi.py y wsgi.py son Entradas que no se modifican.
Las __pycache__ son carpetas creadas automáticamente por Python para almacenar versiones 
precompiladas del código y acelerar la ejecución de los archivos .py.

El Repositorio esta dividido en 2 secciones:
El backend: Donde se encuentra toda la logica detras de la pagina.
    SIP_GestorTickets: Es la carpeta raiz del proyecto
        SIP_GestorTickets: paquete principal de configuracion de Django.
            (Los siguientes archivos son el nucleo de configuracion de Django.
            Cada uno cumple distintas funciones)
            __pycache__
            __init__.py: Marca la carpeta "SIP_GestorTickets" como paquete Python.
            asgi.py: Entrada para servidores asíncronos modernos.
            settings.py: Configuración global del proyecto.
            urls.py: Define rutas/URLs.
            wsgi.py: Entrada para servidores web tradicionales.
    usuarios: Es la carpeta "app" de Django.
        __pycache__
        migrations: guarda los archivos de migración de la base de datos. (Historial de cambios)
        static: guarda los archivos estáticos de la aplicación web.
        __init__.py: Marca la carpeta "usuarios" como paquete Python.
        admin.py: Sirve para registrar modelos en el panel administrador de Django.
        apps.py: Define la configuración de la app.
        forms.py: Define formularios de Django. (valida datos, genera inputs HTML, maneja errores)
        models.py: Define las tablas de la base de datos.
        tests.py: Sirve para hacer pruebas automáticas.
        urls.py: Define rutas específicas de la app usuarios.
        views.py: Contiene la lógica principal de las páginas. Las views reciben 
        requests y devuelven responses.
    db.sqlite3: es la Base de Datos del proyecto.
    manage.py: es el archivo que le permite a Django funcionar desde la terminal.
El frontend:
    Donde estan todos los archivo .html del proyecto.

Explicacion de la Base de Datos con Django:
Tablas de Django (generadas automáticamente)
auth_group — Grupos de permisos. Permite agrupar usuarios y asignarles permisos en conjunto. 
Por ejemplo un grupo "Administradores" con ciertos permisos.
auth_group_permissions — Tabla intermedia que relaciona cada grupo con sus permisos específicos.
auth_permission — Catálogo de todos los permisos disponibles en el sistema 
(agregar, editar, eliminar, ver por cada modelo).
django_admin_log — Historial de acciones realizadas desde el panel de administración (/admin/). 
Registra quién hizo qué y cuándo.
django_content_type — Registro interno de todos los modelos del proyecto. Django lo usa para el 
sistema de permisos y otras funciones internas.
django_migrations — Historial de todas las migraciones ejecutadas. Django lo consulta para saber 
qué cambios ya se aplicaron a la base de datos.
django_session — Almacena las sesiones activas de usuarios logueados. Cuando alguien inicia sesión, 
acá se guarda su sesión.
sqlite_sequence — Propia de SQLite, lleva el contador de los IDs autoincrementales de las tablas.

Tablas de la app usuarios
usuarios_usuario — Tabla principal. Acá se guardan todos los usuarios del sistema 
(clientes, soporte, jefes) con todos sus datos.
usuarios_usuario_groups — Tabla intermedia que relaciona tus usuarios con los grupos de auth_group.
usuarios_usuario_user_permissions — Tabla intermedia que relaciona tus usuarios con permisos 
individuales específicos.

Notas extras:
Casi nunca se tocan: __init__.py, asgi.py, wsgi.py, apps.py, __pycache__/
A veces se tocan: admin.py, tests.py, migrations/
Se tocan constantemente: views.py, models.py, forms.py. urls.py, settings.py

Comentarios:
La mayoria de estas cosas son creadas automaticamente por Django por defecto.
Y digo la mayoria porque hay otras que se crean manualmente porque no existen por defecto.
(Ej: static/, forms.py, etc)
