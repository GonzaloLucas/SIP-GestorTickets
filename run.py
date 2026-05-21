import subprocess
import webbrowser
import time
import sys
import os

# Ruta al manage.py (relativa desde la raíz del repo)
MANAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'SIP_GestorTickets')

# Arranca el servidor Django
server = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver'],
    cwd=MANAGE_DIR
)

# Espera a que el servidor levante
time.sleep(2)

# Abre el navegador en la landing
webbrowser.open('http://127.0.0.1:8000/')

try:
    server.wait()
except KeyboardInterrupt:
    server.terminate()