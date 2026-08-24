import subprocess
import webbrowser
import time
import sys
import os
import signal

MANAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'SIP_GestorTickets')

server = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver'],
    cwd=MANAGE_DIR
)

time.sleep(2)

webbrowser.open('http://127.0.0.1:8000/')

def cerrar(sig=None, frame=None):
    print("\nCerrando servidor...")
    server.terminate()
    server.wait()
    sys.exit(0)

signal.signal(signal.SIGINT, cerrar)
signal.signal(signal.SIGTERM, cerrar)

try:
    server.wait()
except KeyboardInterrupt:
    cerrar()