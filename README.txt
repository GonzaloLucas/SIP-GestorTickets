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

Notas extras:
Casi nunca se tocan: __init__.py, asgi.py, wsgi.py, apps.py, __pycache__/
A veces se tocan: admin.py, tests.py, migrations/
Se tocan constantemente: views.py, models.py, forms.py. urls.py, settings.py

Comentarios:
La mayoria de estas cosas son creadas automaticamente por Django por defecto.
Y digo la mayoria porque hay otras que se crean manualmente porque no existen por defecto.
(Ej: static/, forms.py, etc)
