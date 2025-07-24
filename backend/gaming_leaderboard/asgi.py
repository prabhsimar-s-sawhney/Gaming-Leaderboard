"""
ASGI config for gaming_leaderboard project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaming_leaderboard.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

import leaderboard.routing
from .middleware import WebSocketTimeoutMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": WebSocketTimeoutMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                leaderboard.routing.websocket_urlpatterns
            )
        )
    ),
})

# Add timeout configuration for ASGI
import asyncio
if hasattr(asyncio, 'set_event_loop_policy'):
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
