import os
import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# Set the environment variable before any Django imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poetry_project.settings')

# Initialize Django setup to ensure models and apps are loaded
django.setup()

# Import routing after setting up Django
import poetry_app.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            poetry_app.routing.websocket_urlpatterns
        ),
    ),
})
