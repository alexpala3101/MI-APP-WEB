import sys
import os

# Añade tu directorio de proyecto al path
path = '/home/tuusuario/mi-app-web'
if path not in sys.path:
    sys.path.append(path)

from app import app as application

if __name__ == "__main__":
    application.run()