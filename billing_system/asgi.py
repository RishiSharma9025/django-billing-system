"""
ASGI config for billing_system project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billing_system.settings')

django_asgi_app = get_asgi_application()

try:
    from channels.auth import AuthMiddlewareStack  # type: ignore
    from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore

    from communication.routing import websocket_urlpatterns

    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        }
    )
except Exception:
    application = django_asgi_app
