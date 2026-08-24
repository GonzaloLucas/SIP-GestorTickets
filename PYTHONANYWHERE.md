# Deploy en PythonAnywhere

URL objetivo:

```txt
https://assistech.pythonanywhere.com
```

## 1. Clonar el proyecto

```bash
git clone https://github.com/TU-USUARIO/SIP-GestorTickets.git
cd SIP-GestorTickets
```

## 2. Crear entorno virtual

Usar Python 3.12 o 3.13.

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Variables de entorno

En PythonAnywhere, configurar estas variables antes de recargar la web app:

```bash
export DJANGO_SECRET_KEY="clave-secreta-larga"
export DJANGO_DEBUG="False"
export DJANGO_ALLOWED_HOSTS="assistech.pythonanywhere.com"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://assistech.pythonanywhere.com"
export EMAIL_HOST_USER="assistech.soporte@gmail.com"
export EMAIL_HOST_PASSWORD="app-password-de-gmail"
```

No subir la contraseña real de Gmail al repositorio.

## 4. Migraciones y archivos estáticos

```bash
cd backend/SIP_GestorTickets
python manage.py migrate
python manage.py collectstatic
python generate_qr.py
```

## 5. Configuración WSGI

En la pestaña Web de PythonAnywhere, usar configuración manual.

Working directory:

```txt
/home/TU-USUARIO/SIP-GestorTickets/backend/SIP_GestorTickets
```

Virtualenv:

```txt
/home/TU-USUARIO/SIP-GestorTickets/venv
```

Archivo WSGI:

```python
import os
import sys

path = "/home/TU-USUARIO/SIP-GestorTickets/backend/SIP_GestorTickets"
if path not in sys.path:
    sys.path.append(path)

os.environ["DJANGO_SETTINGS_MODULE"] = "SIP_GestorTickets.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 6. Archivos estáticos

En Static files:

```txt
URL: /static/
Directory: /home/TU-USUARIO/SIP-GestorTickets/backend/SIP_GestorTickets/staticfiles
```

Luego presionar Reload.

## 7. Código QR

El QR queda en:

```txt
backend/SIP_GestorTickets/usuarios/static/usuarios/qr-assistech.png
```

Ese QR apunta a:

```txt
https://assistech.pythonanywhere.com
```
