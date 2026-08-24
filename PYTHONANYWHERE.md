# Deploy en PythonAnywhere

Este proyecto no debe depender del Gmail o cuenta de PythonAnywhere anterior. Si esa cuenta estaba asociada a un correo robado, crear una cuenta nueva y usar la URL nueva.

En una cuenta gratis, la URL normalmente queda:

```txt
https://TU-USUARIO.pythonanywhere.com
```

Si el usuario anterior era `assistech` y no se puede acceder a esa cuenta, probablemente no se pueda reutilizar exactamente `https://assistech.pythonanywhere.com` desde otra cuenta gratis.

## 1. En GitHub

Subir los cambios:

```bash
git add .
git commit -m "Preparar deploy propio en PythonAnywhere"
git push
```

## 2. En PythonAnywhere

Crear una cuenta nueva con un correo controlado por ustedes.

Abrir una Bash Console:

```bash
git clone https://github.com/TU-USUARIO/SIP-GestorTickets.git
cd SIP-GestorTickets
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar variables de entorno

Usar valores propios. No reutilizar claves del Gmail robado.

```bash
export DJANGO_SECRET_KEY="clave-secreta-larga"
export DJANGO_DEBUG="False"
export DJANGO_ALLOWED_HOSTS="TU-USUARIO.pythonanywhere.com"
export DJANGO_CSRF_TRUSTED_ORIGINS="https://TU-USUARIO.pythonanywhere.com"
export EMAIL_HOST_USER="nuevo-correo@gmail.com"
export EMAIL_HOST_PASSWORD="nueva-app-password"
export DEFAULT_FROM_EMAIL="Assistech Soporte <nuevo-correo@gmail.com>"
```

## 4. Migraciones, estáticos y QR

```bash
cd backend/SIP_GestorTickets
python manage.py migrate
python manage.py collectstatic
python generate_qr.py https://TU-USUARIO.pythonanywhere.com
```

## 5. Web app en PythonAnywhere

Crear una web app con configuración manual.

Working directory:

```txt
/home/TU-USUARIO/SIP-GestorTickets/backend/SIP_GestorTickets
```

Virtualenv:

```txt
/home/TU-USUARIO/SIP-GestorTickets/venv
```

Static files:

```txt
URL: /static/
Directory: /home/TU-USUARIO/SIP-GestorTickets/backend/SIP_GestorTickets/staticfiles
```

WSGI:

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

Después tocar Reload en la pestaña Web.
