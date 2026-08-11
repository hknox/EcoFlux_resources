"""
WSGI config for EcoFlux project in production.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

from pathlib import Path
from dotenv import load_dotenv

from django.core.wsgi import get_wsgi_application

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

application = get_wsgi_application()
